import os
import re
import tempfile
from flask import request, jsonify
import PyPDF2
import docx
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
        """Extract text from document based on file type"""
        try:
            if self.file_extension == '.pdf':
                self.text_content = self._extract_from_pdf()
            elif self.file_extension in ['.docx', '.doc']:
                self.text_content = self._extract_from_docx()
            elif self.file_extension == '.txt':
                self.text_content = self.file.read().decode('utf-8')
            else:
                return False
            
            self.text_content = self._clean_text(self.text_content)
            return True
        except Exception as e:
            print(f"Error extracting text: {str(e)}")
            return False
    
    def _extract_from_pdf(self):
        """Extract text from PDF document"""
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(self.file.read())
            temp_path = temp.name
        
        text = ""
        try:
            with open(temp_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
        finally:
        
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        return text
    
    def _extract_from_docx(self):
        """Extract text from DOCX document"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp:
            temp.write(self.file.read())
            temp_path = temp.name
        
        text = ""
        try:
            doc = docx.Document(temp_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        finally:
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        return text
    
    def _clean_text(self, text):
        """Clean extracted text"""
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('\f', ' ')
        # Clean up any other non-printable characters
        text = ''.join(char for char in text if char.isprintable() or char in ['\n', '\t'])
        return text.strip()
    
    def _analyze_content(self):
        """Generate summary and key points from document content"""
        try:
            # Limit content length for  the  API call
            content_for_analysis = self.text_content[:15000]  # Limiting to first 15000 chars
            
            doc_type = self._get_document_type()
            
            # Create prompt based on document type
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
            response = client.chat.completions.create(
                model="gpt-4-1106-preview",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a legal assistant that specializes in explaining legal documents in simple terms."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            # Extract and process the response
            analysis = response.choices[0].message.content
            
            
            import json
            try:
                analysis_json = json.loads(analysis)
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
    
    # Check the  file extensions
    allowed_extensions = {'.pdf', '.docx', '.doc', '.txt'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        return jsonify({
            "success": False,
            "error": f"File type not supported. Please upload a PDF, Word document, or text file"
        }), 400
    
    # Process mydoc
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

# I am writing Function to register document analysis routes
def register_document_analysis_routes(app):
    """Register routes for document analysis"""
    app.add_url_rule('/api/upload-document', view_func=handle_document_upload, methods=['POST'])