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
        
        # HOLD images table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hold_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uploader TEXT,
                image_data BLOB,
                timestamp TEXT
            )
        """)
        
        # Default admin accounts
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, password, role) 
            VALUES (?, ?, ?)
        """, ("admin", hash_password("admin123"), "admin"))
        
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, password, role) 
            VALUES (?, ?, ?)
        """, ("taha kirri", hash_password("arise@99"), "admin"))
        
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
        lambda n: len(set(n)) == 1,               # All digits same
        lambda n: n == n[::-1],                   # Palindrome
        lambda n: all(int(n[i+1])-int(n[i]) == 1 for i in range(len(n)-1)),  # Sequential up
        lambda n: all(int(n[i])-int(n[i+1]) == 1 for i in range(len(n)-1)),  # Sequential down
        lambda n: n[:3] == n[3:6] == n[6:],       # Triple repeat
        lambda n: n[:5] == n[5:],                 # Mirror pattern
    ]
    
    return any(pattern(clean_num) for pattern in patterns)

# --------------------------
# Other Database Functions
# --------------------------

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
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to add request: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_requests():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM requests 
            ORDER BY timestamp DESC
        """)
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to fetch requests: {e}")
        return []
    finally:
        if conn:
            conn.close()

# ... [Keep all other existing database functions] ...

# --------------------------
# Streamlit App Configuration
# --------------------------

st.set_page_config(
    page_title="Request Management System", 
    page_icon=":office:",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { 
        background-color: #ffffff; 
        border-right: 1px solid #e9ecef; 
    }
    .stButton>button {
        background-color: #3b82f6;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    .card {
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .message {
        max-width: 70%;
        padding: 0.75rem 1rem;
        border-radius: 1rem;
        margin-bottom: 0.5rem;
    }
    .sent {
        background-color: #3b82f6;
        color: white;
        margin-left: auto;
    }
    .received {
        background-color: #e9ecef;
        margin-right: auto;
    }
</style>
""", unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.current_section = "requests"

init_db()

# --------------------------
# Login Page
# --------------------------

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏢 Request Management System")
        st.markdown("---")
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
            ("🔢 Number Checker", "number_checker")
        ]
        
        if st.session_state.role == "admin":
            nav_options.append(("⚙️ Admin Panel", "admin"))
        
        for option, value in nav_options:
            if st.button(option, key=f"nav_{value}"):
                st.session_state.current_section = value
        
        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.rerun()

    st.title(f"{'📋' if st.session_state.current_section == 'requests' else ''}"
             f"{'🖼️' if st.session_state.current_section == 'hold' else ''}"
             f"{'❌' if st.session_state.current_section == 'mistakes' else ''}"
             f"{'💬' if st.session_state.current_section == 'chat' else ''}"
             f"{'🔢' if st.session_state.current_section == 'number_checker' else ''}"
             f"{'⚙️' if st.session_state.current_section == 'admin' else ''}"
             f" {st.session_state.current_section.title()}")

    # Requests Section
    if st.session_state.current_section == "requests":
        with st.container():
            st.subheader("Submit a Request")
            with st.form("request_form"):
                request_type = st.selectbox("Request Type", ["Email", "Phone Number", "Ticket ID"])
                identifier = st.text_input("Identifier")
                comment = st.text_area("Comment")
                
                if st.form_submit_button("Submit Request"):
                    if identifier and comment:
                        if add_request(st.session_state.username, request_type, identifier, comment):
                            st.success("Request submitted!")
        
        st.subheader("All Requests")
        requests = get_requests()
        for req in requests:
            req_id, agent, req_type, identifier, comment, timestamp, completed = req
            with st.container():
                cols = st.columns([0.1, 0.9])
                with cols[0]:
                    st.checkbox(
                        "Done",
                        value=bool(completed),
                        key=f"check_{req_id}",
                        on_change=update_request_status,
                        args=(req_id, not completed))
                with cols[1]:
                    st.markdown(f"""
                    <div class="card">
                        <div style="display: flex; justify-content: space-between;">
                            <h4>Request #{req_id} - {req_type}</h4>
                            <small>{timestamp}</small>
                        </div>
                        <p><strong>Agent:</strong> {agent}</p>
                        <p><strong>Identifier:</strong> {identifier}</p>
                        <p><strong>Comment:</strong> {comment}</p>
                    </div>
                    """, unsafe_allow_html=True)

    # Number Checker Section
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

    # ... [Keep other existing sections (hold, mistakes, chat, admin) unchanged] ...

if __name__ == "__main__":
    st.write("Request Management System - Ready for Use!")
