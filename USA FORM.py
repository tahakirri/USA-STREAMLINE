import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import pandas as pd
import os
import re
from streamlit.components.v1 import html

# --------------------------
# Database Functions
# --------------------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = None
    try:
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT CHECK(role IN ('agent', 'admin'))
            )
        """)
        
        # Requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                request_type TEXT,
                identifier TEXT,
                comment TEXT,
                timestamp TEXT,
                completed INTEGER DEFAULT 0
            )
        """)
        
        # Mistakes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_leader TEXT,
                agent_name TEXT,
                ticket_id TEXT,
                error_description TEXT,
                timestamp TEXT
            )
        """)
        
        # Group messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                message TEXT,
                timestamp TEXT,
                mentions TEXT
            )
        """)
        
        # Private messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS private_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                receiver TEXT,
                message TEXT,
                timestamp TEXT,
                is_read INTEGER DEFAULT 0
            )
        """)
        
        # Default admin account
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, password, role) 
            VALUES (?, ?, ?)
        """, ("admin", hash_password("admin123"), "admin"))
        
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def authenticate(username, password):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role FROM users 
            WHERE username=? AND password=?
        """, (username, hash_password(password)))
        user = cursor.fetchone()
        return user[0] if user else None
    except sqlite3.Error as e:
        st.error(f"Authentication error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def reset_user_password(user_id, new_password):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET password=? 
            WHERE id=?
        """, (hash_password(new_password), user_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to reset password: {e}")
        return False
    finally:
        if conn:
            conn.close()

# ... [Rest of the previous database functions remain the same]

def add_request(agent_name, request_type, identifier, comment):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO requests (agent_name, request_type, identifier, comment, timestamp) 
            VALUES (?, ?, ?, ?, ?)
        """, (agent_name, request_type, identifier, comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Failed to add request: {e}")
    finally:
        if conn:
            conn.close()

# Main Streamlit App Configuration
st.set_page_config(
    page_title="Request Management System", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom Tailwind-inspired CSS
st.markdown("""
<style>
    /* Base Styles */
    .stApp {
        background-color: #f4f4f5;
        font-family: 'Inter', sans-serif;
    }
    
    /* Card Styles */
    .custom-card {
        background-color: white;
        border-radius: 0.75rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* Button Styles */
    .custom-button {
        background-color: #3b82f6;
        color: white;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        transition: background-color 0.3s ease;
    }
    
    .custom-button:hover {
        background-color: #2563eb;
    }
    
    /* Input Styles */
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea {
        border-radius: 0.5rem;
        border: 1px solid #e5e7eb;
        padding: 0.5rem;
    }
    
    /* Message Styles */
    .message-container {
        max-height: 400px;
        overflow-y: auto;
        background-color: #f9fafb;
        border-radius: 0.75rem;
        padding: 1rem;
    }
    
    .sent-message {
        background-color: #3b82f6;
        color: white;
        align-self: flex-end;
        border-radius: 0.75rem;
        padding: 0.75rem;
        max-width: 70%;
        margin-bottom: 0.5rem;
    }
    
    .received-message {
        background-color: #e5e7eb;
        color: black;
        align-self: flex-start;
        border-radius: 0.75rem;
        padding: 0.75rem;
        max-width: 70%;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None

# Initialize database
init_db()

def login_page():
    st.title("🔐 Request Management System")
    st.subheader("Login to Continue")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
    
    with col2:
        st.write("") # Spacer
        st.write("") # Spacer
        
        login_col1, login_col2 = st.columns([1, 1])
        
        with login_col1:
            if st.button("Login", use_container_width=True, type="primary"):
                if username and password:
                    role = authenticate(username, password)
                    if role:
                        st.session_state.authenticated = True
                        st.session_state.role = role
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                else:
                    st.warning("Please enter both username and password")
        
        with login_col2:
            st.write("Forgot password? Contact admin.")

def main_dashboard():
    st.sidebar.title(f"👋 Welcome, {st.session_state.username}")
    
    # Sidebar Navigation
    menu_options = [
        "📋 Requests", 
        "💬 Messaging", 
        "🚨 Issue Tracking", 
        "🔍 Search"
    ]
    
    if st.session_state.role == "admin":
        menu_options.append("⚙️ Admin Tools")
    
    selected_menu = st.sidebar.radio("Navigation", menu_options)
    
    # Main Content Area
    if selected_menu == "📋 Requests":
        requests_section()
    elif selected_menu == "💬 Messaging":
        messaging_section()
    elif selected_menu == "🚨 Issue Tracking":
        issue_tracking_section()
    elif selected_menu == "🔍 Search":
        search_section()
    elif selected_menu == "⚙️ Admin Tools" and st.session_state.role == "admin":
        admin_tools_section()

def requests_section():
    st.header("📋 Request Management")
    
    # Request Submission
    with st.expander("Submit New Request"):
        col1, col2 = st.columns(2)
        
        with col1:
            request_type = st.selectbox("Request Type", ["Email", "Phone", "Ticket"])
        
        with col2:
            identifier = st.text_input("Identifier")
        
        comment = st.text_area("Additional Comments")
        
        if st.button("Submit Request"):
            if identifier and comment:
                add_request(st.session_state.username, request_type, identifier, comment)
                st.success("Request submitted successfully!")
            else:
                st.warning("Please fill all required fields")
    
    # Request List
    st.subheader("Recent Requests")
    requests = get_requests()
    
    if requests:
        for req in requests:
            with st.container():
                st.markdown(f"""
                **Request ID:** {req[0]}  
                **Agent:** {req[1]} | **Type:** {req[2]}  
                **Identifier:** {req[3]}  
                **Comments:** {req[4]}  
                **Timestamp:** {req[5]}
                """)
                st.checkbox("Completed", key=f"request_{req[0]}")
                st.divider()
    else:
        st.info("No requests found.")

def messaging_section():
    st.header("💬 Messaging Center")
    # Placeholder for messaging functionality
    st.write("Messaging section coming soon!")

def issue_tracking_section():
    st.header("🚨 Issue Tracking")
    # Placeholder for issue tracking functionality
    st.write("Issue tracking section coming soon!")

def search_section():
    st.header("🔍 Search")
    # Placeholder for search functionality
    st.write("Search section coming soon!")

def admin_tools_section():
    st.header("⚙️ Admin Tools")
    # Placeholder for admin tools
    st.write("Admin tools section coming soon!")

# Main App Flow
def main():
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()
        
        # Logout functionality
        if st.sidebar.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.role = None
            st.session_state.username = None
            st.rerun()

# Run the app
if __name__ == "__main__":
    main()
