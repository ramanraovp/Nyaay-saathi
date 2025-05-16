from flask import Flask, render_template, session, redirect, url_for, jsonify, request
import os
import uuid
import hashlib
import json
import tempfile
import re
import requests
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Configure session
app.secret_key = os.getenv("SECRET_KEY", "nyaay-saathi-random-key")
app.config['SESSION_COOKIE_SECURE'] = os.environ.get("FLASK_DEBUG", "False").lower() != "true"
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# File upload configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['UPLOAD_FOLDER'] = os.path.join('/tmp', 'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Use /tmp directory on Render which is writable
USER_DB_FILE = os.path.join('/tmp', 'user_db.json')

# Initialize global conversation history
conversation_history = []

# Define system message for OpenAI
SYSTEM_MESSAGE = """
You are a knowledgeable and trustworthy legal assistant trained in Indian laws, legal processes, and rights.
You assist users in understanding their legal position and navigating the Indian legal system.
Your responses should be easy to understand and conversational (in English or Hinglish), while maintaining legal precision and clarity.

Capabilities:
- Offer insights on Indian legislation (IPC, CrPC, IT Act, Consumer Protection Act, etc.)
- Clarify legal entitlements in common scenarios (arrest, FIR, landlord-tenant issues, consumer grievances, traffic offenses, etc.)
- Explain legal procedures (how to lodge an FIR, how to seek bail, structure of courts, etc.)
- Provide general guidance, not legal advice or representation
- Recommend official resources or consulting a qualified lawyer when necessary

Guidelines & Conduct:
- Refer only to existing Indian laws and publicly accessible legal information; do not create legal interpretations.
- Clearly state when a topic requires professional legal counsel or is beyond your scope.
- Always include the disclaimer: "I am an AI assistant and not a licensed legal advisor. Please consult a lawyer for serious or urgent matters."
- Ask follow-up questions if the user's query lacks clarity.
- Keep responses concise and clear unless the user asks for more detail.
"""

# Set up OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("WARNING: No OpenAI API key found")

#==========================================================================
# User database functions
#==========================================================================
def load_users():
    """Load user data from the database file"""
    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupted or can't be read, create a new one
            pass
    
    # Create default user database if file doesn't exist
    users = {'users': {}}
    save_users(users)
    return users

def save_users(users):
    """Save user data to the database file"""
    with open(USER_DB_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def ensure_demo_account():
    """Create a demo account"""
    users = load_users()
    demo_email = 'demo@nyaaysaathi.com'
    
    if demo_email not in users['users']:
        print("Creating demo account...")
        user_id = str(uuid.uuid4())
        users['users'][demo_email] = {
            'id': user_id,
            'name': 'Demo User',
            'email': demo_email,
            'password': generate_password_hash('demo123'),
            'created_at': datetime.now().isoformat(),
            'last_login': datetime.now().isoformat(),
            'chat_history': []
        }
        save_users(users)
        print("Demo account created!")

#==========================================================================
# OpenAI API Functions
#==========================================================================
def call_openai_api(messages, model="gpt-4", temperature=0.3, max_tokens=1000):
    """Call OpenAI API directly using requests to avoid client initialization issues"""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        if 'response' in locals():
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
        raise

#==========================================================================
# Helper Functions
#==========================================================================
# Storage for caching responses
response_cache = {}

@lru_cache(maxsize=100)
def get_cached_response(question_hash, language):
    """Get cached response"""
    if question_hash in response_cache:
        return response_cache[question_hash]
    return None

# Legal jargon simplification
LEGAL_JARGON = {
    "cognizable offense": "crimes where police can arrest without a warrant",
    "non-cognizable offense": "crimes where police need court permission to arrest",
    "bail": "temporary release during trial proceedings",
    "anticipatory bail": "bail obtained in anticipation of arrest",
    "habeas corpus": "legal order to bring a detained person to court",
    "affidavit": "written statement confirmed by oath",
    "plaintiff": "person who initiates a lawsuit",
    "defendant": "person against whom legal action is brought",
    "deposition": "recorded testimony under oath",
    "jurisdiction": "authority of a court to hear a case",
    "suo moto": "action taken by a court on its own initiative",
    "writ petition": "court application for an order directing someone to act/not act",
    "respondent": "person who answers a court petition",
    "petitioner": "person who files a formal petition in court"
}

def simplify_legal_jargon(text):
    """Simplify legal jargon in the response"""
    for term, explanation in LEGAL_JARGON.items():
        if term.lower() in text.lower():
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            text = pattern.sub(f"{term} ({explanation})", text)
    return text

#==========================================================================
# Language Translation Functions
#==========================================================================
# Multilingual support dictionary
LANGUAGE_TRANSLATIONS = {
    "hindi": {
        "I am an AI assistant": "मैं एक AI सहायक हूँ",
        "Please consult a lawyer": "कृपया एक वकील से परामर्श करें",
        "for serious or urgent matters": "गंभीर या जरूरी मामलों के लिए",
        "How can I help you today?": "मैं आपकी कैसे सहायता कर सकता हूँ?",
        "Rights during arrest": "गिरफ्तारी के दौरान अधिकार",
        "How to file an FIR?": "FIR कैसे दर्ज करें?",
        "Consumer complaint process": "उपभोक्ता शिकायत प्रक्रिया",
        "RTI application procedure": "RTI आवेदन प्रक्रिया"
    },
    "bengali": {
        "I am an AI assistant": "আমি একটি AI সহায়ক",
        "Please consult a lawyer": "অনুগ্রহ করে একজন আইনজীবীর সাথে পরামর্শ করুন",
        "for serious or urgent matters": "গুরুতর বা জরুরি বিষয়ের জন্য"
    }
}

def translate_to_language(text, target_language):
    """
    Translate text to the target language using translation dictionary
    """
    # Return original text for English or Hinglish
    if target_language == 'English' or target_language == 'Hinglish':
        return text
    
    target_language = target_language.lower()
    
    # If target language not supported, return original text
    if target_language not in LANGUAGE_TRANSLATIONS:
        return text
    
    translations = LANGUAGE_TRANSLATIONS[target_language]
    
    # Replace English phrases with their translations
    for english, translated in translations.items():
        text = text.replace(english, translated)
        
        # Also try case-insensitive replacement for common phrases
        if english.lower() != english:
            text = text.replace(english.lower(), translated)
            text = text.replace(english.capitalize(), translated)
                
    return text

#==========================================================================
# Document Templates & Timelines Data
#==========================================================================
# Document templates
DOCUMENT_TEMPLATES = {
    "police_complaint": {
        "title": "Police Complaint Template",
        "template": """To,
The Station House Officer,
{police_station} Police Station,
{police_station_address}

Subject: Complaint regarding {complaint_subject}

Respected Sir/Madam,

I, {complainant_name}, resident of {complainant_address}, wish to report the following incident:

Date of Incident: {incident_date}
Time of Incident: {incident_time}
Place of Incident: {incident_place}

Details of the incident:
{incident_details}

Names and details of persons involved (if known):
{persons_involved}

Names and contact details of witnesses (if any):
{witnesses}

I request you to register my complaint and take appropriate action as per law.

Yours sincerely,
{complainant_name}
Contact: {complainant_phone}
Date: {current_date}
"""
    },
    "rti_application": {
        "title": "RTI Application Template",
        "template": """To,
The Public Information Officer,
{department_name},
{department_address}

Subject: Application under Right to Information Act, 2005

Respected Sir/Madam,

I, {applicant_name}, resident of {applicant_address}, wish to seek information under the Right to Information Act, 2005.

The details of the information sought are as follows:
{information_sought}

Period for which information is sought: {information_period}

I state that the information sought does not fall within the restrictions contained in Section 8 and 9 of the RTI Act and to the best of my knowledge it pertains to your department.

A fee of Rs. 10/- has been deposited vide receipt number {receipt_number} dated {receipt_date} / is enclosed herewith as IPO/DD.

Yours faithfully,
{applicant_name}
Address: {applicant_address}
Phone: {applicant_phone}
Date: {current_date}
"""
    },
    "consumer_complaint": {
        "title": "Consumer Complaint Template",
        "template": """To,
The District Consumer Disputes Redressal Forum,
{district}, {state}

Subject: Complaint under the Consumer Protection Act, 2019

Complainant:
{complainant_name}
{complainant_address}
{complainant_phone}

Opposite Party:
{seller_name}
{seller_address}
{seller_phone}

COMPLAINT

1. Details of transaction:
   Date of purchase/service: {transaction_date}
   Amount paid: Rs. {amount_paid}
   Mode of payment: {payment_mode}
   Receipt/Invoice number: {receipt_number}

2. Details of the product/service:
   {product_details}

3. Complaint details:
   {complaint_details}

4. Deficiency in service/defect in goods:
   {deficiency_details}

5. Steps taken to resolve the issue with the opposite party:
   {resolution_attempts}

6. Relief sought:
   {relief_sought}

7. Declaration:
   I/We declare that the information given above is true to the best of my/our knowledge and belief.

Place: {place}
Date: {current_date}

Signature of the Complainant
{complainant_name}

Attachments:
1. Copy of bill/receipt
2. Copy of correspondence with opposite party
3. Samples/photographs (if applicable)
"""
    }
}

# Legal timelines
LEGAL_TIMELINES = {
    "fir_to_chargesheet": [
        {"step": "File FIR", "timeframe": "Day 1", "details": "Visit police station with jurisdiction"},
        {"step": "Police Investigation", "timeframe": "Day 1-90", "details": "Collection of evidence, statements"},
        {"step": "Arrest (if applicable)", "timeframe": "Varies", "details": "Based on evidence gathering"},
        {"step": "Chargesheet Filing", "timeframe": "Within 90 days", "details": "For serious offenses (60 days for less serious)"},
        {"step": "Court Proceedings", "timeframe": "After chargesheet", "details": "Trial begins after chargesheet"}
    ],
    "consumer_complaint_process": [
        {"step": "Written Complaint to Business", "timeframe": "Day 1", "details": "First attempt at resolution"},
        {"step": "Wait for Response", "timeframe": "15-30 days", "details": "Allow reasonable time for response"},
        {"step": "File Complaint with Consumer Forum", "timeframe": "After trying resolution", "details": "Submit required documents and fee"},
        {"step": "Notice to Opposite Party", "timeframe": "Within 21 days", "details": "Forum sends notice to business"},
        {"step": "Response from Opposite Party", "timeframe": "Within 30 days", "details": "Business submits their response"},
        {"step": "Hearing", "timeframe": "Scheduled by Forum", "details": "Both parties present their case"},
        {"step": "Order/Judgment", "timeframe": "Typically 3-6 months", "details": "Decision by the Consumer Forum"}
    ],
    "civil_case_procedure": [
        {"step": "Filing Plaint", "timeframe": "Day 1", "details": "Submit case to appropriate court with fees"},
        {"step": "Scrutiny & Registration", "timeframe": "7-14 days", "details": "Court checks for defects and registers"},
        {"step": "Summons to Defendant", "timeframe": "Within 30 days", "details": "Court notifies the opposite party"},
        {"step": "Filing Written Statement", "timeframe": "30-90 days", "details": "Defendant responds to allegations"},
        {"step": "Framing of Issues", "timeframe": "Next hearing", "details": "Court defines points of contention"},
        {"step": "Evidence Submission", "timeframe": "Multiple hearings", "details": "Documents and witness testimony"},
        {"step": "Final Arguments", "timeframe": "After evidence", "details": "Lawyers present final case"},
        {"step": "Judgment", "timeframe": "Typically 1-3 years", "details": "Court gives final decision"},
        {"step": "Execution", "timeframe": "If judgment not followed", "details": "Enforcement of court order"}
    ]
}

# FAQs data
LEGAL_FAQ_PAIRS = [
    {
        "question": "What are my rights during an arrest?",
        "answer": "During an arrest in India, you have several rights under Section 41 and 50 of the CrPC and Article 22 of the Constitution:\n\n1. Right to know the grounds of arrest\n2. Right to inform a relative or friend about your arrest\n3. Right to legal representation/meet a lawyer of your choice\n4. Right to be produced before a magistrate within 24 hours\n5. Right to medical examination\n6. Right against self-incrimination (you can remain silent)\n7. Right against torture or illegal detention\n\nWomen cannot be arrested after sunset and before sunrise except in exceptional circumstances, and only by female police officers.\n\nI am an AI assistant and not a licensed legal advisor. Please consult a lawyer for serious or urgent matters."
    },
    {
        "question": "How do I file an FIR?",
        "answer": "To file a First Information Report (FIR) in India:\n\n1. Visit the police station having jurisdiction where the crime occurred\n2. Provide details of the incident to the officer in charge (date, time, place, description of the event, names of suspects if known)\n3. The police officer must register your FIR for cognizable offenses (under Section 154 of CrPC)\n4. Review the FIR before signing it\n5. Collect a free copy of the FIR\n\nIf the police refuse to register your FIR:\n- Approach the Superintendent of Police or other higher officers\n- File a complaint to the Judicial Magistrate under Section 156(3) CrPC\n- File a complaint online on the state police portal\n\nI am an AI assistant and not a licensed legal advisor. Please consult a lawyer for serious or urgent matters."
    },
    {
        "question": "What is the process for filing a consumer complaint?",
        "answer": "Consumers in India are protected under the Consumer Protection Act, 2019, which provides for grievance redressal:\n\n1. Try to resolve the issue directly with the seller or service provider.\n2. If unresolved, file a complaint with:\n   - District Commission: claims up to ₹1 crore\n   - State Commission: ₹1-10 crore\n   - National Commission: above ₹10 crore\n\n3. Documents needed:\n   - Purchase proof\n   - Communication records\n   - Complaint letter detailing the grievance\n\n4. File online through consumerhelpline.gov.in\n\nThe complaint must be filed within 2 years from the date of cause of action. Relief may include refund, replacement, compensation, or penalty.\n\nI am an AI assistant and not a licensed legal advisor. Please consult a lawyer for serious or urgent matters."
    },
    {
        "question": "How do I apply for RTI?",
        "answer": "The Right to Information Act, 2005 enables citizens to access information from public authorities:\n\n1. Draft your RTI request in English/Hindi/official language with your contact details.\n2. Clearly mention what information you seek and the department concerned.\n3. Pay ₹10 application fee via cash, demand draft, Indian Postal Order, or online.\n4. Submit to the Public Information Officer (PIO) by post, in person, or online (for Central Govt at rtionline.gov.in)\n\nResponse time is 30 days (48 hours for life/death matters). If denied or no reply is given, file a First Appeal within 30 days.\n\nI am an AI assistant and not a licensed legal advisor. Please consult a lawyer for serious or urgent matters."
    }
]

# Mock nearby resources data
NEARBY_RESOURCES = {
    "police_station": [
        {"name": "Kumbalagodu Police Station", "address": "Kumbalagodu, Mysore Road", "phone": "N/A", "distance": "1.2 km"},
        {"name": "Kengeri Police Station", "address": "Mysore Road, Kengeri Satellite Town", "phone": "080-28484210", "distance": "5.5 km"},
        {"name": "Rajarajeshwari Nagar Police Station", "address": "Jawaharlal Nehru Road, Rajarajeshwari Nagar", "phone": "080-22942559", "distance": "8.0 km"}
    ],
    "consumer_court": [
        {"name": "Bangalore Urban District Consumer Forum", "address": "Shantinagar, Bangalore", "phone": "080-22861043", "distance": "4.3 km"},
        {"name": "Karnataka State Consumer Disputes Redressal Commission", "address": "Palace Road, Bangalore", "phone": "080-22033857", "distance": "6.7 km"}
    ],
    "legal_aid": [
        {"name": "District Legal Services Authority", "address": "City Civil Court Complex, Mayo Hall", "phone": "080-25321411", "distance": "4.8 km"},
        {"name": "Karnataka State Legal Services Authority", "address": "Nyaya Degula, HCS Layout", "phone": "080-22111714", "distance": "7.2 km"}
    ]
}

#==========================================================================
# Document Analysis Functions
#==========================================================================
class DocumentProcessor:
    """Process uploaded legal documents and extract relevant information"""
    
    def __init__(self, file_object, filename):
        self.file = file_object
        self.filename = filename
        self.file_extension = self._get_file_extension()
        self.text_content = ""
        self.summary = ""
        self.key_points = []
    
    def _get_file_extension(self):
        """Extract file extension from filename"""
        return os.path.splitext(self.filename)[1].lower()
    
    def process(self):
        """Process the document based on its type"""
        if self._extract_text():
            self._analyze_content()
            return {
                "success": True,
                "summary": self.summary,
                "key_points": self.key_points,
                "word_count": len(self.text_content.split()),
                "document_type": self._get_document_type()
            }
        else:
            return {
                "success": False,
                "error": "Failed to extract text from document"
            }
    
    def _extract_text(self):
        """Extract text from document (simplified version)"""
        try:
            # For simplicity, just read the file as text
            text = self.file.read().decode('utf-8', errors='ignore')
            self.text_content = text
            return True
        except Exception as e:
            print(f"Error extracting text: {str(e)}")
            return False
    
    def _analyze_content(self):
        """Generate summary and key points from document content using OpenAI"""
        try:
            # Limit content length for the API call
            content_for_analysis = self.text_content[:5000]  # Limit to first 5000 chars
            
            doc_type = self._get_document_type()
            
            # Create prompt for OpenAI
            prompt = f"""You're a legal assistant analyzing a {doc_type}. 
            Please provide:
            1. A concise summary (3-4 sentences) explaining what this document is about
            2. Key points that a layperson should understand (bullet points)
            3. Any obligations, rights, or deadlines mentioned
            4. Explain any complex legal terminology in simple terms
            
            Format your response as JSON with these keys: "summary", "key_points", "obligations_and_rights", "terminology_explained"
            
            Here's the document text:
            {content_for_analysis}
            """
            
            # Call OpenAI API to analyze the document
            messages = [
                {"role": "system", "content": "You are a legal assistant that specializes in explaining legal documents in simple terms."},
                {"role": "user", "content": prompt}
            ]
            
            response = call_openai_api(messages=messages, max_tokens=1500)
            
            # Process the response
            try:
                # Try to parse as JSON
                import json
                analysis_json = json.loads(response)
                self.summary = analysis_json.get("summary", "Summary not available")
                
                # Combine key points, obligations and terminology
                self.key_points = analysis_json.get("key_points", [])
                
                # Add obligations and rights as key points if available
                if "obligations_and_rights" in analysis_json:
                    if isinstance(analysis_json["obligations_and_rights"], list):
                        self.key_points.extend(analysis_json["obligations_and_rights"])
                    else:
                        self.key_points.append(analysis_json["obligations_and_rights"])
                
                # Add explained terminology as key points if available
                if "terminology_explained" in analysis_json:
                    if isinstance(analysis_json["terminology_explained"], dict):
                        for term, explanation in analysis_json["terminology_explained"].items():
                            self.key_points.append(f"{term}: {explanation}")
                    elif isinstance(analysis_json["terminology_explained"], list):
                        self.key_points.extend(analysis_json["terminology_explained"])
                    else:
                        self.key_points.append(analysis_json["terminology_explained"])
                
            except json.JSONDecodeError:
                # Fallback if response isn't valid JSON
                self.summary = "The document appears to be a legal text. Due to its complexity, I can only provide a basic analysis."
                self.key_points = ["Please review the document carefully", "Consider consulting a lawyer for detailed understanding"]
                
        except Exception as e:
            print(f"Error analyzing content: {str(e)}")
            self.summary = "Unable to analyze document content"
            self.key_points = ["Error processing document"]
    
    def _get_document_type(self):
        """Identify the type of legal document based on content and filename"""
        lower_text = self.text_content.lower()
        lower_filename = self.filename.lower()
        
        # Check for common document types
        if any(x in lower_text for x in ["agreement", "contract", "between", "parties", "agreed", "terms"]):
            if "rent" in lower_text or "lease" in lower_text or "tenant" in lower_text:
                return "Rental Agreement"
            elif "employment" in lower_text or "job" in lower_text or "salary" in lower_text:
                return "Employment Contract"
            elif "non-disclosure" in lower_text or "confidential" in lower_text or "nda" in lower_text:
                return "Non-Disclosure Agreement"
            else:
                return "Legal Agreement"
        
        elif any(x in lower_text for x in ["notice", "hereby", "inform", "notification"]):
            return "Legal Notice"
        
        elif any(x in lower_text for x in ["affidavit", "solemnly", "affirm", "sworn"]):
            return "Affidavit"
        
        elif "will" in lower_filename or any(x in lower_text for x in ["testament", "bequeath", "executor", "probate"]):
            return "Will or Testament"
        
        elif any(x in lower_text for x in ["petition", "court", "honorable", "plaintiff", "defendant"]):
            return "Court Petition"
        
        else:
            return "Legal Document"

#==========================================================================
# API Routes
#==========================================================================
@app.route('/api/login', methods=['POST'])
def handle_login():
    """Handle login API request"""
    try:
        data = request.json
        email = data.get('email', '').lower()
        password = data.get('password', '')
        
        print(f"Login attempt for: {email}")
        
        users = load_users()
        
        if email in users['users'] and check_password_hash(users['users'][email]['password'], password):
            user = users['users'][email]
            session['user_id'] = user['id']
            session['user_email'] = email
            session['user_name'] = user['name']
            session.permanent = True  # Make session persistent
            
            # Update last login
            users['users'][email]['last_login'] = datetime.now().isoformat()
            save_users(users)
            
            print(f"Login successful for: {email}")
            return jsonify({'success': True, 'message': 'Login successful'})
        
        print(f"Login failed for: {email}")
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error during login: {str(e)}'}), 500

@app.route('/api/register', methods=['POST'])
def handle_register():
    """Handle registration API request"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        # Basic validation
        if not name or not email or not password:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
        
        users = load_users()
        
        if email in users['users']:
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Create new user
        user_id = str(uuid.uuid4())
        users['users'][email] = {
            'id': user_id,
            'name': name,
            'email': email,
            'password': generate_password_hash(password),
            'created_at': datetime.now().isoformat(),
            'last_login': datetime.now().isoformat(),
            'chat_history': []
        }
        
        save_users(users)
        
        # Auto login
        session['user_id'] = user_id
        session['user_email'] = email
        session['user_name'] = name
        session.permanent = True
        
        return jsonify({'success': True, 'message': 'Registration successful'})
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error during registration: {str(e)}'}), 500

@app.route('/api/logout', methods=['POST'])
def handle_logout():
    """Handle logout API request"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/user', methods=['GET'])
def handle_get_user():
    """Handle get user information API request"""
    if 'user_id' not in session:
        return jsonify({'logged_in': False}), 401
    
    return jsonify({
        'logged_in': True,
        'user_id': session['user_id'],
        'email': session['user_email'],
        'name': session['user_name']
    })

@app.route('/api/chat', methods=['POST'])
def handle_chat_endpoint():
    """Handle chat API request"""
    global conversation_history
    
    try:
        data = request.json
        user_message = data.get('message', '')
        simplify = data.get('simplify', False)
        language = data.get('language', 'English')
        
        print(f"Chat request - Message: {user_message[:50]}..., Language: {language}, Simplify: {simplify}")
        
        # Add user message to conversation history
        conversation_history.append({"role": "user", "content": user_message})
        
        try:
            # Prepare messages for OpenAI API
            messages = [
                {"role": "system", "content": SYSTEM_MESSAGE}
            ]
            
            # Add conversation history (limit to last 5 messages for context)
            messages.extend(conversation_history[-5:])
            
            # Call OpenAI API
            assistant_response = call_openai_api(
                messages=messages,
                model="gpt-3.5-turbo",  # Using a more widely available model
                temperature=0.3,
                max_tokens=1000
            )
            
        except Exception as e:
            print(f"Error calling OpenAI: {str(e)}")
            return jsonify({"error": f"Error generating response: {str(e)}"}), 500
        
        # Simplify legal terms if requested
        if simplify:
            assistant_response = simplify_legal_jargon(assistant_response)
        
        # Translate to selected language if not English
        if language != 'English':
            assistant_response = translate_to_language(assistant_response, language)
        
        # Add response to conversation history
        conversation_history.append({"role": "assistant", "content": assistant_response})
        
        return jsonify({"response": assistant_response})
    except Exception as e:
        print(f"Chat error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def handle_reset_conversation_endpoint():
    """Reset conversation history"""
    global conversation_history
    conversation_history.clear()
    return jsonify({"status": "conversation reset"})

@app.route('/api/document_templates', methods=['GET'])
def handle_get_document_templates():
    """Handle get document templates API request"""
    templates = list(DOCUMENT_TEMPLATES.keys())
    return jsonify({"templates": templates})

@app.route('/api/document_template/<template_id>', methods=['GET'])
def handle_get_document_template_endpoint(template_id):
    """Handle get specific document template API request"""
    if template_id in DOCUMENT_TEMPLATES:
        return jsonify(DOCUMENT_TEMPLATES[template_id])
    else:
        return jsonify({"error": "Template not found"}), 404

@app.route('/api/generate_document', methods=['POST'])
def handle_generate_document():
    """Handle generate document API request"""
    try:
        data = request.json
        template_id = data.get('template_id')
        fields = data.get('fields', {})
        
        if template_id not in DOCUMENT_TEMPLATES:
            return jsonify({"error": "Template not found"}), 404
        
        # Add the current date if not provided
        if 'current_date' not in fields:
            fields['current_date'] = datetime.now().strftime("%d/%m/%Y")
        
        # Fill the template with provided fields
        template = DOCUMENT_TEMPLATES[template_id]['template']
        for key, value in fields.items():
            placeholder = "{" + key + "}"
            template = template.replace(placeholder, value)
        
        return jsonify({
            "title": DOCUMENT_TEMPLATES[template_id]['title'],
            "document": template
        })
    except Exception as e:
        print(f"Error generating document: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/legal_timeline/<timeline_id>', methods=['GET'])
def handle_get_legal_timeline_endpoint(timeline_id):
    """Handle get legal timeline API request"""
    if timeline_id in LEGAL_TIMELINES:
        return jsonify({"timeline": LEGAL_TIMELINES[timeline_id]})
    else:
        return jsonify({"error": "Timeline not found"}), 404

@app.route('/api/nearby_resources', methods=['POST'])
def handle_get_nearby_resources():
    """Handle get nearby resources API request"""
    try:
        data = request.json
        lat = data.get('latitude')
        lon = data.get('longitude')
        resource_type = data.get('type', 'police_station')
        
        # Use mock data for now
        if resource_type in NEARBY_RESOURCES:
            return jsonify({"resources": NEARBY_RESOURCES[resource_type]})
        else:
            return jsonify({"error": "Resource type not found"}), 404
    except Exception as e:
        print(f"Error getting nearby resources: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/faqs', methods=['GET'])
def handle_get_faqs():
    """Handle get FAQs API request"""
    return jsonify({"faqs": LEGAL_FAQ_PAIRS})

@app.route('/api/languages', methods=['GET'])
def handle_get_languages():
    """Handle get languages API request"""
    languages = ['English', 'Hinglish', 'Hindi', 'Bengali', 'Tamil', 'Telugu', 'Marathi', 'Gujarati', 'Kannada']
    return jsonify({"languages": languages})

@app.route('/api/upload-document', methods=['POST'])
def handle_document_upload():
    """Process uploaded legal document and return analysis"""
    if 'document' not in request.files:
        return jsonify({
            "success": False,
            "error": "No document part in the request"
        }), 400
    
    file = request.files['document']
    
    if file.filename == '':
        return jsonify({
            "success": False,
            "error": "No file selected"
        }), 400
    
    # Process document
    try:
        processor = DocumentProcessor(file, file.filename)
        result = processor.process()
        return jsonify(result)
    except Exception as e:
        print(f"Document processing error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to process document"
        }), 500

#==========================================================================
# Web Routes
#==========================================================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/static/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

@app.route('/test')
def test_route():
    # Check if we can write to the filesystem
    try:
        with open('/tmp/test_file.txt', 'w') as f:
            f.write('Test successful')
        file_write = 'Success'
    except Exception as e:
        file_write = f'Error: {str(e)}'
    
    # Test session
    if 'test_count' not in session:
        session['test_count'] = 1
    else:
        session['test_count'] += 1
    
    # Return diagnostic info
    return f'''
    <h1>Diagnostic Page</h1>
    <p>File write test: {file_write}</p>
    <p>Session count: {session.get('test_count')}</p>
    <p>Session working: {'Yes' if session.get('test_count') > 0 else 'No'}</p>
    <p>Current working directory: {os.getcwd()}</p>
    <p>Environment: {os.environ.get('FLASK_ENV', 'Not set')}</p>
    <p>OpenAI API Key set: {'Yes' if openai_api_key else 'No'}</p>
    '''

# Initialize demo account
ensure_demo_account()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
