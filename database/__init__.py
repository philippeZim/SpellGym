# database/__init__.py
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'users.db')

def init_db():
    """Initializes the database and creates the user table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    """Establishes a connection to the database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_user(username, password):
    """Creates a new user in the database."""
    password_hash = generate_password_hash(password)
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                     (username, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_username(username):
    """Retrieves a user by username."""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user

def verify_user(username, password):
    """Verifies a user's credentials."""
    user = get_user_by_username(username)
    if user and check_password_hash(user['password_hash'], password):
        return user
    return None