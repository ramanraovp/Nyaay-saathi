from flask import Flask, render_template, session, redirect, url_for, jsonify, request
import os
import uuid
import hashlib
import json
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
# Add to the top of the file
from functools import lru_cache
import requests
# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Configure session
app.secret_key = os.getenv("SECRET_KEY", "nyaay-saathi-random-key")
app.config['SESSION_COOKIE_SECURE'] = os.environ.get("FLASK_DEBUG", "False").lower() != "true"
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

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

# User database functions
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

# Create a demo account
def ensure_demo_account():
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

# Fixed OpenAI client implementation using requests directly
def call_openai_api(messages, model="gpt-4", temperature=0.3, max_tokens=1000):
    """Call OpenAI API directly using requests to avoid client initialization issues"""
    import requests
    
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
        if response:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
        raise

# Storage for caching responses
response_cache = {}

@lru_cache(maxsize=100)
def get_cached_response(question_hash, language):
    if question_hash in response_cache:
        return response_cache[question_hash]
    return None

# Legal jargon simplification (simplified version)
LEGAL_JARGON = {
    "cognizable offense": "crimes where police can arrest without a warrant",
    "non-cognizable offense": "crimes where police need court permission to arrest",
    "bail": "temporary release during trial proceedings",
    "anticipatory bail": "bail obtained in anticipation of arrest",
    "habeas corpus": "legal order to bring a detained person to court",
    "affidavit": "written statement confirmed by oath",
    "plaintiff": "person who initiates a lawsuit",
    "defendant": "person against whom legal action is brought"
}

def simplify_legal_jargon(text):
    """Simplify legal jargon in the response"""
    for term, explanation in LEGAL_JARGON.items():
        if term in text.lower():
            text = text.replace(term, f"{term} ({explanation})")
    return text

# Check knowledge base (simplified version)
def check_knowledge_base(user_message):
    """Check if user message matches known questions (simplified)"""
    return None  # Skip knowledge base for now

# API Routes
@app.route('/api/login', methods=['POST'])
def handle_login():
    """Handle login API request"""
    try:
        data = request.json
        email = data.get('email', '').lower()
        password = data.get('password', '')
        
        print(f"Login attempt for: {email}")  # Debug log
        
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
            
            print(f"Login successful for: {email}")  # Debug log
            return jsonify({'success': True, 'message': 'Login successful'})
        
        print(f"Login failed for: {email}")  # Debug log
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
    except Exception as e:
        print(f"Login error: {str(e)}")  # Debug log
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
        
        # Try to find a direct match in knowledge base
        direct_answer = check_knowledge_base(user_message)
        
        if direct_answer:
            assistant_response = direct_answer
        else:
            # Check cache
            question_hash = hashlib.md5(user_message.encode()).hexdigest()
            cached_response = get_cached_response(question_hash, language)
            
            if cached_response:
                assistant_response = cached_response
            else:
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
                        model="gpt-4",
                        temperature=0.3,
                        max_tokens=1000
                    )
                    
                    # Cache the response
                    response_cache[question_hash] = assistant_response
                    
                except Exception as e:
                    print(f"Error calling OpenAI: {str(e)}")
                    return jsonify({"error": f"Error generating response: {str(e)}"}), 500
        
        # Simplify legal terms if requested
        if simplify:
            assistant_response = simplify_legal_jargon(assistant_response)
        
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

# Routes
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
