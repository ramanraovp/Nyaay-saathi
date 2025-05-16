import hashlib
import os
import json
from flask import request, jsonify
from functools import lru_cache
import openai
from dotenv import load_dotenv
# Importing necessary modules from oother files
from language_utils import translate_to_language
from legal_data import legal_db, LEGAL_JARGON
from user_management import (
    handle_login, handle_register, handle_logout, handle_get_user,
    handle_save_chat, handle_get_chat_history, handle_get_chat, handle_delete_chat
)
# I am trying to load my environment variables from a existing env file I created.
load_dotenv()
# I am trying to load my environment variables from a existing env file I created.
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("No OpenAI API key found")

# Initialize OpenAI client safely
try:
    client = openai.OpenAI(api_key=openai_api_key)
except TypeError as e:
    if 'proxies' in str(e):
        from openai import Client
        client = Client(api_key=openai_api_key)
    else:
        raise

# it is a System message for chat API that will be sent to openAI
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


# Storage for replying next in the sequence
@lru_cache(maxsize=100)
def get_cached_response(question_hash, language):
    return None  # Initial cache miss

# I shall match the user's question with my extremely efficient kawledge database
def check_knowledge_base(user_message):
    user_message_lower = user_message.lower()
    
    for qa_pair in legal_db["legal_qa_pairs"]:
        keywords = qa_pair["question"].lower().split()
        # Verify if the primary keywords from the knowledge base inquiry are present in the user's message
        match_score = sum(1 for word in keywords if word in user_message_lower and len(word) > 3)
        if match_score >= 2 or qa_pair["question"].lower() in user_message_lower:
            return qa_pair["answer"]
            
    return None

# Simplify legal stuff into simple words for users to understnad and comprehend
def simplify_legal_jargon(text):
    for term, explanation in LEGAL_JARGON.items():
        if term in text.lower():
            text = text.replace(term, f"{term} ({explanation})")
    return text

# Manage API requests and handle them effociently
def handle_chat_endpoint(conversation_history):
    data = request.json
    user_message = data.get('message', '')
    simplify = data.get('simplify', False)
    language = data.get('language', 'English')
    
    # Add my user message to conversation history
    conversation_history.append({"role": "user", "content": user_message})
    
    # Try to find a direct match in our knowledge base first
    direct_answer = check_knowledge_base(user_message)
    
    if direct_answer:
        # Use our own knowledge base to avoid API call
        assistant_response = direct_answer
    else:
        
        question_hash = hashlib.md5(user_message.encode()).hexdigest()
        
        cached_response = get_cached_response(question_hash, language)
        
        if cached_response:
            assistant_response = cached_response
        else:
            try:
                # Prepare messages for my OpenAI API
                messages = [
                    {"role": "system", "content": SYSTEM_MESSAGE}
                ]
                
                # Add conversation history (limit to last 5 messages for context length)
                messages.extend(conversation_history[-5:])
                
            
                response = client.chat.completions.create(
                    model="gpt-4",  
                    messages=messages,
                    temperature=0.3,  # 0.3 is mosst efficient
                    max_tokens=1000  
                )
                
                assistant_response = response.choices[0].message.content
                
                
                get_cached_response.cache_info()
                get_cached_response.__wrapped__.__dict__[question_hash] = assistant_response
                
            except Exception as e:
                print(f"Error: {str(e)}")
                return jsonify({"error": str(e)}), 500
    
    # Simplify legal words for users
    if simplify:
        assistant_response = simplify_legal_jargon(assistant_response)
    
    # Translation
    if language != 'English':
        assistant_response = translate_to_language(assistant_response, language)
    
    # Add Nyaay Saathi's response to conversation history
    conversation_history.append({"role": "assistant", "content": assistant_response})
    
    return jsonify({"response": assistant_response})

# Reset conversation history
def handle_reset_conversation_endpoint(conversation_history):
    conversation_history.clear()
    return jsonify({"status": "conversation reset"})
# Handle FAQ 
def handle_get_faqs():
    # Get FAQs from the legal knowledge base
    faqs = []
    for qa_pair in legal_db["legal_qa_pairs"]:
        faqs.append({
            "question": qa_pair["question"],
            "answer": qa_pair["answer"]
        })
    
    return jsonify({"faqs": faqs})


def handle_simplify_text():
    data = request.json
    text = data.get('text', '')
    simplified = simplify_legal_jargon(text)
    return jsonify({"simplified": simplified})

def handle_get_languages():
    languages = ['English', 'Hinglish', 'Hindi', 'Bengali', 'Tamil', 'Telugu', 'Marathi', 'Gujarati', 'Kannada']
    return jsonify({"languages": languages})


def handle_get_nearby_resources():
    data = request.json
    lat = data.get('latitude')
    lon = data.get('longitude')
    resource_type = data.get('type', 'police_station')
    
    mock_resources = {
        "police_station": [
            {"name": "Kumbalagodu Police Station", "address": "Kumbalagodu, Mysore Road", "phone": "N/A", "distance": "1.2 km"},
            {"name": "Kengeri Police Station", "address": "Mysore Road, Kengeri Satellite Town", "phone": "080-28484210", "distance": "5.5 km"},
            {"name": "Rajarajeshwari Nagar Police Station", "address": "Jawaharlal Nehru Road, Rajarajeshwari Nagar", "phone": "080-22942559", "distance": "8.0 km"},
            {"name": "Koramangala Police Station", "address": "80 Feet Road, Koramangala", "phone": "080-22943900", "distance": "18.7 km"},
            {"name": "Indiranagar Police Station", "address": "CMH Road, Indiranagar", "phone": "080-22943930", "distance": "21.9 km"},
            {"name": "Cubbon Park Police Station", "address": "MG Road, Cubbon Park", "phone": "080-22943940", "distance": "16.9 km"}
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
    
    if resource_type in mock_resources:
        return jsonify({"resources": mock_resources[resource_type]})
    else:
        return jsonify({"error": "Resource type not found"}), 404

# Function to handle GET request for a specific chat
def get_chat_endpoint(chat_id):
    return handle_get_chat(chat_id)

# Function to handle DELETE request for a specific chat
def delete_chat_endpoint(chat_id):
    return handle_delete_chat(chat_id)

# Register all my  API routes
def register_api_routes(app, conversation_history):
    # User management routes
    app.add_url_rule('/api/login', view_func=handle_login, methods=['POST'])
    app.add_url_rule('/api/register', view_func=handle_register, methods=['POST'])
    app.add_url_rule('/api/logout', view_func=handle_logout, methods=['POST'])
    app.add_url_rule('/api/user', view_func=handle_get_user, methods=['GET'])
    
    # Chat history routes
    app.add_url_rule('/api/save_chat', view_func=handle_save_chat, methods=['POST'])
    app.add_url_rule('/api/chat_history', view_func=handle_get_chat_history, methods=['GET'])
    
    # Fixed: Use different endpoint functions for GET and DELETE
    app.add_url_rule('/api/chat/<chat_id>', view_func=get_chat_endpoint, methods=['GET'])
    app.add_url_rule('/api/chat/<chat_id>', view_func=delete_chat_endpoint, methods=['DELETE'])
    
    def handle_chat_with_history():
        return handle_chat_endpoint(conversation_history)
    
    def handle_reset_with_history():
        return handle_reset_conversation_endpoint(conversation_history)
    
    # Chatbot routes 
    app.add_url_rule('/api/chat', view_func=handle_chat_with_history, methods=['POST'])
    app.add_url_rule('/api/reset', view_func=handle_reset_with_history, methods=['POST'])
    app.add_url_rule('/api/simplify', view_func=handle_simplify_text, methods=['POST'])
    
    # Legal data routes
    app.add_url_rule('/api/faqs', view_func=handle_get_faqs, methods=['GET'])
    app.add_url_rule('/api/languages', view_func=handle_get_languages, methods=['GET'])
    app.add_url_rule('/api/nearby_resources', view_func=handle_get_nearby_resources, methods=['POST'])
