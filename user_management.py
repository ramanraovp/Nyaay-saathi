import json
import os
import uuid
from datetime import datetime
from flask import jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash

# Constants
# Constants
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

def create_login_template():
    """Create the login.html template if it doesn't exist"""
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    if not os.path.exists('templates/login.html'):
        # Check if login.html exists in the current directory
        if os.path.exists('login.html'):
            with open('templates/login.html', 'w') as dest:
                with open('login.html', 'r') as source:
                    dest.write(source.read())
        else:
            # Create a basic login template
            with open('templates/login.html', 'w') as f:
                f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nyaay Saathi - Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f8f9fa;
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        
        .login-container {
            max-width: 400px;
            width: 100%;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .login-header {
            background-color: #2e3c87;
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .login-body {
            padding: 30px;
        }
        
        .tabs {
            display: flex;
            margin-bottom: 20px;
        }
        
        .tab {
            flex: 1;
            padding: 10px;
            text-align: center;
            border-bottom: 2px solid #e9ecef;
            cursor: pointer;
            font-weight: 600;
        }
        
        .tab.active {
            border-bottom: 2px solid #2e3c87;
            color: #2e3c87;
        }
        
        .form-container {
            display: none;
        }
        
        .form-container.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h2>Nyaay Saathi</h2>
            <p>Your Indian Legal Guide</p>
        </div>
        
        <div class="login-body">
            <div class="tabs">
                <div class="tab active" id="login-tab">Login</div>
                <div class="tab" id="register-tab">Register</div>
            </div>
            
            <div id="status-message"></div>
            
            <div class="form-container active" id="login-form">
                <form id="login-form-element">
                    <div class="mb-3">
                        <label for="login-email" class="form-label">Email</label>
                        <input type="email" class="form-control" id="login-email" required>
                    </div>
                    
                    <div class="mb-3">
                        <label for="login-password" class="form-label">Password</label>
                        <input type="password" class="form-control" id="login-password" required>
                    </div>
                    
                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-primary">Login</button>
                    </div>
                </form>
            </div>
            
            <div class="form-container" id="register-form">
                <!-- Register form fields -->
            </div>
        </div>
    </div>
    
    <script>
        // Basic functionality - you can expand this
        document.addEventListener('DOMContentLoaded', function() {
            const loginTab = document.getElementById('login-tab');
            const registerTab = document.getElementById('register-tab');
            const loginForm = document.getElementById('login-form');
            const registerForm = document.getElementById('register-form');
            
            loginTab.addEventListener('click', function() {
                loginTab.classList.add('active');
                registerTab.classList.remove('active');
                loginForm.classList.add('active');
                registerForm.classList.remove('active');
            });
            
            registerTab.addEventListener('click', function() {
                registerTab.classList.add('active');
                loginTab.classList.remove('active');
                registerForm.classList.add('active');
                loginForm.classList.remove('active');
            });
            
            // Rest of login/registration logic would go here
        });
    </script>
</body>
</html>''')

# User authentication routes handlers
def handle_login():
    """Handle login API request"""
    data = request.json
    email = data.get('email', '').lower()
    password = data.get('password', '')
    
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
        
        return jsonify({'success': True, 'message': 'Login successful'})
    
    return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

def handle_register():
    """Handle registration API request"""
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

def handle_logout():
    """Handle logout API request"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

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

def handle_save_chat():
    """Handle save chat API request"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.json
    chat_messages = data.get('messages', [])
    
    users = load_users()
    email = session['user_email']
    
    chat_id = str(uuid.uuid4())
    chat_data = {
        'id': chat_id,
        'title': chat_messages[0]['content'][:50] if chat_messages else 'New Chat',
        'timestamp': datetime.now().isoformat(),
        'messages': chat_messages
    }
    
    users['users'][email]['chat_history'].append(chat_data)
    save_users(users)
    
    return jsonify({'success': True, 'chat_id': chat_id})

def handle_get_chat_history():
    """Handle get chat history API request"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    users = load_users()
    email = session['user_email']
    
    if email in users['users']:
        chats = users['users'][email]['chat_history']
        return jsonify({'success': True, 'chats': chats})
    
    return jsonify({'success': False, 'message': 'User not found'}), 404

def handle_get_chat(chat_id):
    """Handle get specific chat API request"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    users = load_users()
    email = session['user_email']
    
    if email in users['users']:
        for chat in users['users'][email]['chat_history']:
            if chat['id'] == chat_id:
                return jsonify({'success': True, 'chat': chat})
    
    return jsonify({'success': False, 'message': 'Chat not found'}), 404

def handle_delete_chat(chat_id):
    """Handle delete chat API request"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    users = load_users()
    email = session['user_email']
    
    if email in users['users']:
        users['users'][email]['chat_history'] = [
            chat for chat in users['users'][email]['chat_history'] if chat['id'] != chat_id
        ]
        save_users(users)
        return jsonify({'success': True, 'message': 'Chat deleted'})
    
    return jsonify({'success': False, 'message': 'User not found'}), 404
