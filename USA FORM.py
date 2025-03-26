import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import os
import re
from PIL import Image
import io

# --------------------------
# Fancy Number Checker Function
# --------------------------
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
    
    # Fancy patterns to check
    fancy_patterns = [
        # Repeating digits
        (r'(\d)\1{2,}', "Has repeating digits"),
        
        # Ascending or descending sequences
        (r'012|123|234|345|456|567|678|789', "Contains ascending sequence"),
        (r'987|876|765|654|543|432|321|210', "Contains descending sequence"),
        
        # Palindrome numbers
        (lambda x: x == x[::-1], "Is a palindrome"),
        
        # Sequential patterns
        (r'(01|12|23|34|45|56|67|78|89)', "Contains sequential digits"),
        
        # Mirror numbers
        (lambda x: len(set(x)) <= 2, "Consists of minimal unique digits"),
        
        # Special number patterns
        (r'8888|6666|9999', "Contains lucky/symbolic numbers"),
    ]
    
    for pattern in fancy_patterns:
        # Handle both regex and lambda pattern checks
        if isinstance(pattern[0], str):
            if re.search(pattern[0], digits):
                return {
                    "is_fancy": True,
                    "reason": pattern[1]
                }
        elif callable(pattern[0]):
            try:
                if pattern[0](digits):
                    return {
                        "is_fancy": True,
                        "reason": pattern[1]
                    }
            except:
                pass
    
    return {
        "is_fancy": False,
        "reason": "Standard phone number"
    }

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
        
        # Hash the provided password
        hashed_password = hash_password(password)
        
        # Check credentials against users table
        cursor.execute("""
            SELECT role FROM users 
            WHERE username = ? AND password = ?
        """, (username, hashed_password))
        
        result = cursor.fetchone()
        
        # Return role if credentials are valid, otherwise return None
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

# Existing database functions (add_request, get_requests, etc.) remain the same as in the previous code...
# [Include all the previous database functions here]

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

def update_request_status(request_id, completed):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE requests 
            SET completed = ? 
            WHERE id = ?
        """, (1 if completed else 0, request_id))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Failed to update request status: {e}")
    finally:
        if conn:
            conn.close()

# [Include all other database functions from the previous code]

# Streamlit App Configuration
st.set_page_config(
    page_title="Request Management System", 
    page_icon=":office:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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

# Login Page
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏢 Request Management System")
        st.markdown("---")
        
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
                    else:
                        st.warning("Please enter both username and password")

# Main Application
else:
    # Sidebar Navigation
    with st.sidebar:
        st.title(f"👋 Welcome, {st.session_state.username}")
        st.markdown("---")
        
        nav_options = [
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
    st.title(f"{'📋' if st.session_state.current_section == 'requests' else '⚙️'} {st.session_state.current_section.title()}")

    # Requests Section
    if st.session_state.current_section == "requests":
        with st.container():
            # Existing request submission form
            st.subheader("Submit a Request")
            with st.form("request_form"):
                request_type = st.selectbox("Request Type", ["Email", "Phone Number", "Ticket ID"])
                identifier = st.text_input("Identifier")
                comment = st.text_area("Comment")
                
                if st.form_submit_button("Submit Request"):
                    if identifier and comment:
                        if add_request(st.session_state.username, request_type, identifier, comment):
                            st.success("Request submitted!")
        
            # Fancy Number Checker
            st.markdown("---")
            st.subheader("📱 Fancy Number Checker")
            with st.form("fancy_number_form"):
                phone_number = st.text_input("Enter Phone Number")
                
                if st.form_submit_button("Check Number"):
                    if phone_number:
                        result = is_fancy_number(phone_number)
                        
                        if result['is_fancy']:
                            st.success(f"🌟 Fancy Number Detected! {result['reason']}")
                            st.balloons()
                        else:
                            st.info(f"📞 {result['reason']}")
                    else:
                        st.warning("Please enter a phone number")
        
        # Display Requests
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

    # Admin Panel Section
    elif st.session_state.current_section == "admin" and st.session_state.role == "admin":
        st.subheader("User Management")
        
        # Existing admin panel code would go here
        st.write("Admin panel content")

# Run the app
if __name__ == "__main__":
    st.write("Request Management System")
