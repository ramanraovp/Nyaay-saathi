from flask import Flask, render_template, session, redirect, url_for
import os
from dotenv import load_dotenv
from datetime import timedelta
from functools import wraps

# Import from other modules
from user_management import load_users, create_login_template
from api_routes import register_api_routes
from document_routes import register_document_routes
from document_analysis import register_document_analysis_routes  # New import
from language_utils import LANGUAGE_TRANSLATIONS
from legal_data import legal_db, LEGAL_JARGON, LEGAL_TIMELINES, DOCUMENT_TEMPLATES

# Create the Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Load my  environment variables
load_dotenv()

# Use a strong secret key for sessions
app.secret_key = os.getenv("SECRET_KEY", "nyaay-saathi-random-key")

# Use secure cookies in production
app.config['SESSION_COOKIE_SECURE'] = os.environ.get("FLASK_DEBUG", "False").lower() != "true"
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'temp_uploads')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Initialize global conversation history
conversation_history = []

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# Main routes
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login_page():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/static/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

# Register routes from other modules
def initialize_app():
    # Register API routes for me
    register_api_routes(app, conversation_history)
    
    # Register document routes
    register_document_routes(app)
    
    register_document_analysis_routes(app)
    
    # Create template directories and files if needed
    create_login_template()

@app.route('/test')
def test_route():
    # Check if we can write to the filesystem
    try:
        with open('test_file.txt', 'w') as f:
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
    '''
# Create a demo account
def ensure_demo_account():
    from werkzeug.security import generate_password_hash
    import uuid
    from datetime import datetime
    
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

# Add this to your initialization code
with app.app_context():
    # Other initialization code
    ensure_demo_account()

# Run the application
if __name__ == '__main__':
    with app.app_context():
        create_login_template()
        
        if not os.path.exists('user_db.json'):
            with open('user_db.json', 'w') as f:
                f.write('{"users": {}}')
        
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Initialize app routes 
    initialize_app()
    
    # Get port from environment variable for Render compatibility
    port = int(os.environ.get("PORT", 5000))
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=os.environ.get("FLASK_DEBUG", "False").lower() == "true")
