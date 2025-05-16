from flask import Flask, render_template, session, redirect, url_for, jsonify
import os
import uuid
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import json

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Configure session
app.secret_key = os.getenv("SECRET_KEY", "nyaay-saathi-random-key")
app.config['SESSION_COOKIE_SECURE'] = os.environ.get("FLASK_DEBUG", "False").lower() != "true"
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Use /tmp directory on Render which is writable
USER_DB_FILE = os.path.join('/tmp', 'user_db.json')

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

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

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
    <p>User DB: {load_users()}</p>
    '''

# Initialize demo account
ensure_demo_account()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
