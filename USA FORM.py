import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import os
import re
from PIL import Image
import io

# --------------------------
# Database Functions
# --------------------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        hashed_password = hash_password(password)
        cursor.execute("""
            SELECT role FROM users 
            WHERE username = ? AND password = ?
        """, (username, hashed_password))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        st.error(f"Authentication error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def init_db():
    conn = None
    try:
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        
        # Tables creation (same as before)
        # ... [keep all existing table creation code] ...
        
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

# --------------------------
# Number Checker Functions
# --------------------------

def is_fancy_number(phone_number):
    """Check if a phone number has fancy patterns"""
    clean_num = re.sub(r'\D', '', phone_number)
    
    if len(clean_num) != 10:
        return False
    
    patterns = [
        lambda n: len(set(n)) == 1,
        lambda n: n == n[::-1],
        lambda n: all(int(n[i+1])-int(n[i]) == 1 for i in range(len(n)-1)),
        lambda n: all(int(n[i])-int(n[i+1]) == 1 for i in range(len(n)-1)),
        lambda n: n[:3] == n[3:6] == n[6:],
        lambda n: n[:5] == n[5:],
    ]
    
    return any(pattern(clean_num) for pattern in patterns)

# --------------------------
# Other Existing Functions 
# (add_request, get_requests, etc. - keep all previous functionality)
# ... [keep all existing database functions] ...

# --------------------------
# Streamlit App Configuration
# --------------------------

st.set_page_config(
    page_title="Request Management System", 
    page_icon=":office:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (keep existing styles)
st.markdown("""
<style>
    /* ... [keep all existing CSS styles] ... */
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.current_section = "requests"

# Initialize database
init_db()

# --------------------------
# Login Page
# --------------------------

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏢 Request Management System")
        with st.container():
            st.header("Login")
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Login"):
                    if username and password:
                        role = authenticate(username, password)
                        if role:
                            st.session_state.authenticated = True
                            st.session_state.role = role
                            st.session_state.username = username
                            st.rerun()
                        else:
                            st.error("Invalid credentials")

# --------------------------
# Main Application
# --------------------------

else:
    with st.sidebar:
        st.title(f"👋 Welcome, {st.session_state.username}")
        st.markdown("---")
        
        nav_options = [
            ("📋 Requests", "requests"),
            ("🖼️ HOLD", "hold"),
            ("❌ Ticket Mistakes", "mistakes"),
            ("💬 Group Chat", "chat"),
            ("🔢 Number Checker", "number_checker"),  # New section
            ("⚙️ Admin Panel", "admin") if st.session_state.role == "admin" else None
        ]
        nav_options = [item for item in nav_options if item is not None]
        
        for option, value in nav_options:
            if st.button(option, key=f"nav_{value}"):
                st.session_state.current_section = value
        
        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.rerun()

    # --------------------------
    # Section Handling
    # --------------------------

    st.title(st.session_state.current_section.title())

    # Existing sections (requests, hold, mistakes, chat, admin)
    # ... [keep all existing section handling code] ...

    # --------------------------
    # Number Checker Section
    # --------------------------

    elif st.session_state.current_section == "number_checker":
        st.subheader("Fancy Number Checker")
        
        with st.form("number_check_form"):
            number_input = st.text_input(
                "Enter phone number to check:",
                placeholder="e.g., (555) 555-5555",
                help="Enter any formatted phone number"
            )
            
            if st.form_submit_button("Check Number"):
                if number_input:
                    if is_fancy_number(number_input):
                        st.success("🎉 This is a FANCY number!")
                        st.balloons()
                    else:
                        st.error("❌ This is NOT a fancy number")
                else:
                    st.warning("Please enter a phone number to check")

        st.markdown("---")
        st.subheader("What counts as a fancy number?")
        st.markdown("""
        We consider these patterns as fancy:
        - All identical digits: 555-555-5555
        - Palindrome numbers: 123-454-321
        - Sequential numbers: 123-456-7890 or 987-654-3210
        - Repeated patterns: 123-123-1234 or 12345-12345
        - Any other interesting numerical pattern
        """)

# --------------------------
# Run the App
# --------------------------

if __name__ == "__main__":
    st.write("Request Management System - Powered by Streamlit")
