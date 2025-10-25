# auth/__init__.py
from functools import wraps
from flask import session, redirect, url_for, request, flash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def login_user(user):
    """Logs in a user by setting session variables."""
    session['user_id'] = user['id']
    session['username'] = user['username']

def logout_user():
    """Logs out a user by removing session variables."""
    session.pop('user_id', None)
    session.pop('username', None)

def validate_registration(username, password, confirm_password):
    """Validates registration form data."""
    errors = []
    
    if not username or not password:
        errors.append('Bitte füllen Sie alle Felder aus.')
    
    if password != confirm_password:
        errors.append('Die Passwörter stimmen nicht überein.')
    
    if len(password) < 8:
        errors.append('Das Passwort muss mindestens 8 Zeichen lang sein.')
    
    return errors