Nyaay Saathi - Indian Legal Assistant
Project Overview
Nyaay Saathi is an AI-powered legal assistant specifically designed for Indian laws and legal procedures. The application helps users understand their legal rights, navigate the Indian legal system, and access relevant legal resources in multiple Indian languages.
Features

AI-powered legal assistance
Multi-language support (English, Hindi, Bengali, Tamil, etc.)
Legal jargon simplification
Document templates (Police Complaint, RTI Application, etc.)
Legal process timelines
Nearby legal resources locator
User authentication and chat history
Document analysis for legal documents

Setup Instructions
Option 1: Local Development
Prerequisites

Python 3.8+
Flask
OpenAI API key

Installation Steps

Clone the repository:
git clone https://github.com/ramanraovp/nyaay-saathi.git
cd nyaay-saathi

Create a virtual environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies:
pip install -r requirements.txt

Create a .env file with the following content:
OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your_secret_key_for_sessions
FLASK_DEBUG=True

Run the application:
python main.py

Access the application:
Open your browser and go to http://127.0.0.1:5000/

Option 2: Deployment on Render
Prerequisites

GitHub account with this repository uploaded
Render.com account
OpenAI API key

Deployment Steps

Log in to Render.com and create a new Web Service
Connect your GitHub repository
Configure the service:

Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn main:app


Add the following environment variables:

OPENAI_API_KEY: Your OpenAI API key
SECRET_KEY: A secure random string for session management
FLASK_DEBUG: Set to "False" for production


Deploy and access your app at the provided URL

Notes

The free tier on Render will put your app to sleep after inactivity
First access after sleep may take 30-60 seconds to wake up

Project Structure
nyaay-saathi/
├── static/                 # Static assets
├── templates/              # HTML templates
├── api_routes.py           # API endpoint routes
├── document_analysis.py    # Document processing logic
├── document_routes.py      # Document generation routes
├── language_utils.py       # Multilingual support
├── legal_data.py           # Legal information database
├── legal_knowledge_base.json # Legal Q&A database
├── main.py                 # Main application file
├── requirements.txt        # Dependencies
├── user_management.py      # User authentication logic
├── Procfile                # For deployment on Render
└── README.md               # This file
Usage Instructions

Login/Register:

Use the login page to sign in or create a new account
Your chat history will be saved to your account


Ask Legal Questions:

Type your legal question in the input box
Toggle "Simplify" to get explanations for legal terms
Select your preferred language from the dropdown


Use Additional Features:

Legal Documents: Generate document templates
Legal Timelines: View procedural timelines
Nearby Resources: Find legal resources near you
Legal FAQs: Browse frequently asked legal questions
Document Analysis: Upload and analyze legal documents


Manage Chat History:

Click on your profile to access chat history
Save conversations for future reference
Load or delete previous chats



Troubleshooting
If you encounter any issues:

Check your OpenAI API key is correctly set in the .env file
Ensure Flask is running without any errors in the console
Clear your browser cache if the UI is not loading correctly
Check file permissions for the user database file
For deployment issues on Render:

Check the logs in Render dashboard for specific error messages
Ensure all environment variables are correctly set
Verify that the requirements.txt includes all necessary dependencies



Contributions
Contributions are welcome! If you'd like to improve Nyaay Saathi, please:

Fork the repository
Create a feature branch
Submit a pull request

License
This project is intended for educational purposes only and should not be used as a replacement for professional legal advice.
Disclaimer
The legal information provided by Nyaay Saathi is for general informational purposes only and should not be relied upon as legal advice. Please consult with a qualified legal professional for specific legal matters.