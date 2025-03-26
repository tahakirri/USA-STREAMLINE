import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import os
import re
from PIL import Image
import io

# Initialize session state variables if they don't exist
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.current_section = 'requests'

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_connection():
    """Create a database connection"""
    conn = sqlite3.connect('user_database.db')
    return conn

def create_users_table():
    """Create users table if not exists"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT DEFAULT 'user',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

def register_user(username, password, role='user'):
    """Register a new user"""
    conn = create_connection()
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    try:
        cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', 
                       (username, hashed_password, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_login(username, password):
    """Verify user login credentials"""
    conn = create_connection()
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                   (username, hashed_password))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def is_fancy_number(phone_number):
    """
    Determine if a phone number is 'fancy' based on various patterns
    
    Args:
        phone_number (str): The phone number to check
    
    Returns:
        dict: A dictionary with fancy status and reasoning
    """
    # Remove any non-digit characters
    digits = re.sub(r'\D', '', phone_number)
    
    # Check if shorter than 10 digits or not a valid phone number
    if len(digits) < 10:
        return {
            "is_fancy": False,
            "reason": "Invalid phone number length"
        }
    
    # More comprehensive fancy patterns to check
    fancy_patterns = [
        # Strict repeating digits - at least 4 consecutive identical digits
        (r'(\d)\1{3,}', "Has four or more consecutive repeating digits"),
        
        # Sequential patterns (including non-continuous)
        (lambda x: all(int(x[i]) + 1 == int(x[i+1]) for i in range(len(x)-1)), "Contains perfect ascending sequence"),
        (lambda x: all(int(x[i]) - 1 == int(x[i+1]) for i in range(len(x)-1)), "Contains perfect descending sequence"),
        
        # True palindromes (using full number)
        (lambda x: x == x[::-1] and len(x) >= 10, "Is a full palindrome number"),
        
        # Rare sequential patterns
        (r'101010|123123|234234', "Contains rare repeating sequential pattern"),
        
        # Super minimal unique digits
        (lambda x: len(set(x)) <= 1, "Consists of single unique digit"),
        
        # Extremely lucky/symbolic numbers
        (r'888888|666666|999999', "Contains extremely lucky/symbolic number"),
    ]
    
    # Counter to track how many patterns match
    pattern_matches = 0
    matched_reasons = []
    
    for pattern in fancy_patterns:
        # Handle both regex and lambda pattern checks
        try:
            if isinstance(pattern[0], str):
                match = re.search(pattern[0], digits)
                if match:
                    pattern_matches += 1
                    matched_reasons.append(pattern[1])
            elif callable(pattern[0]):
                if pattern[0](digits):
                    pattern_matches += 1
                    matched_reasons.append(pattern[1])
        except:
            pass
    
    # Only consider very fancy if multiple patterns match
    if pattern_matches >= 1:
        return {
            "is_fancy": True,
            "reason": " and ".join(matched_reasons)
        }
    
    return {
        "is_fancy": False,
        "reason": "Standard phone number"
    }

def login_page():
    """Login page for authentication"""
    st.title("📱 Fancy Number Checker Login")
    
    # Create tabs for Login and Register
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.header("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="login_button"):
            if verify_login(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                # Determine role (you might want to fetch this from database)
                st.session_state.role = "admin" if username == "admin" else "user"
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    with tab2:
        st.header("Register New Account")
        new_username = st.text_input("Choose Username", key="register_username")
        new_password = st.text_input("Choose Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password")
        
        if st.button("Register", key="register_button"):
            if new_password != confirm_password:
                st.error("Passwords do not match")
            elif len(new_username) < 3:
                st.error("Username must be at least 3 characters long")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters long")
            else:
                if register_user(new_username, new_password):
                    st.success("Registration successful! You can now log in.")
                else:
                    st.error("Username already exists")

def main_app():
    """Main application for authenticated users"""
    # Sidebar Navigation
    with st.sidebar:
        st.title(f"👋 Welcome, {st.session_state.username}")
        st.markdown("---")
        
        nav_options = [
            ("📱 Fancy Number", "fancy_number"),
            ("📋 Requests", "requests"),
        ]
        
        if st.session_state.role == "admin":
            nav_options.append(("⚙️ Admin Panel", "admin"))
        
        for option, value in nav_options:
            if st.button(option, key=f"nav_{value}"):
                st.session_state.current_section = value
        
        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.role = None
            st.session_state.username = None
            st.rerun()
    
    # Main Content
    st.title(f"{'📱' if st.session_state.current_section == 'fancy_number' else '📋'} {st.session_state.current_section.title()}")

    # Fancy Number Section
    if st.session_state.current_section == "fancy_number":
        st.subheader("📱 Fancy Number Checker")
        
        st.markdown("""
        ### Discover if Your Phone Number is Fancy! 🌟
        
        What makes a phone number "fancy"?
        - Four or more consecutive repeating digits
        - Perfect ascending or descending sequences
        - Full palindrome numbers
        - Rare repeating sequential patterns
        - Extremely lucky number combinations
        """)
        
        with st.form("fancy_number_form"):
            phone_number = st.text_input("Enter Full Phone Number", 
                                         placeholder="e.g., +1 (555) 123-4567")
            
            if st.form_submit_button("Check If Fancy"):
                if phone_number:
                    result = is_fancy_number(phone_number)
                    
                    if result['is_fancy']:
                        st.success(f"🌟 Fancy Number Detected! {result['reason']}")
                        st.balloons()
                        
                        # Additional fancy details
                        st.markdown("""
                        ### 🎉 Congratulations! 
                        Your phone number has exceptional characteristics that make it stand out!
                        
                        #### What does this mean?
                        - Your number is extremely unique
                        - It has rare mathematical or visual patterns
                        - It could be considered highly memorable or special
                        """)
                    else:
                        st.info(f"📞 {result['reason']}")
                        
                        # Consolation for non-fancy numbers
                        st.markdown("""
                        ### 💡 Tip
                        While your number isn't considered "fancy" right now, 
                        you can always look for interesting patterns when choosing future numbers!
                        """)
                else:
                    st.warning("Please enter a complete phone number")

def app():
    """Initialize database and run main application flow"""
    # Create users table if not exists
    create_users_table()
    
    # Main authentication flow
    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()

# Run the application
if __name__ == "__main__":
    app()
