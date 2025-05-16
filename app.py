from flask import Flask, render_template, session, redirect, url_for, jsonify, request
import os
import uuid
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
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
    '''

# Initialize demo account
ensure_demo_account()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
