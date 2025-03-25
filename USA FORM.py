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

def get_requests():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM requests 
            ORDER BY completed, timestamp DESC
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
            SET completed=? 
            WHERE id=?
        """, (int(completed), request_id))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Failed to update request status: {e}")
    finally:
        if conn:
            conn.close()

def add_mistake(team_leader, agent_name, ticket_id, error_description):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO mistakes (team_leader, agent_name, ticket_id, error_description, timestamp) 
            VALUES (?, ?, ?, ?, ?)
        """, (team_leader, agent_name, ticket_id, error_description, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Failed to add mistake: {e}")
    finally:
        if conn:
            conn.close()

def get_mistakes():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM mistakes 
            ORDER BY timestamp DESC
        """)
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to fetch mistakes: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_all_users():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM users ORDER BY username")
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to fetch users: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_all_users_except(username):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username != ? ORDER BY username", (username,))
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        st.error(f"Failed to fetch users: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_admins():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE role='admin'")
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        st.error(f"Failed to fetch admins: {e}")
        return []
    finally:
        if conn:
            conn.close()

def create_user(username, password, role):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, role) 
            VALUES (?, ?, ?)
        """, (username, hash_password(password), role))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to create user: {e}")
        return False
    finally:
        if conn:
            conn.close()

def update_user_role(user_id, new_role):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET role=? 
            WHERE id=?
        """, (new_role, user_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to update user role: {e}")
        return False
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

def delete_user(user_id):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to delete user: {e}")
        return False
    finally:
        if conn:
            conn.close()

def add_group_message(sender, message, mentions=None):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO group_messages (sender, message, timestamp, mentions) 
            VALUES (?, ?, ?, ?)
        """, (sender, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ",".join(mentions) if mentions else ""))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Failed to add group message: {e}")
    finally:
        if conn:
            conn.close()

def get_group_messages():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM group_messages 
            ORDER BY timestamp DESC
            LIMIT 100
        """)
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to fetch group messages: {e}")
        return []
    finally:
        if conn:
            conn.close()

def add_private_message(sender, receiver, message):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO private_messages (sender, receiver, message, timestamp) 
            VALUES (?, ?, ?, ?)
        """, (sender, receiver, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Failed to add private message: {e}")
    finally:
        if conn:
            conn.close()

def get_private_messages(username):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM private_messages 
            WHERE receiver=? OR sender=?
            ORDER BY timestamp DESC
            LIMIT 100
        """, (username, username))
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to fetch private messages: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_conversation_history(user1, user2):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM private_messages 
            WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
            ORDER BY timestamp ASC
        """, (user1, user2, user2, user1))
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to fetch conversation history: {e}")
        return []
    finally:
        if conn:
            conn.close()

def mark_as_read(message_id):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE private_messages 
            SET is_read=1 
            WHERE id=?
        """, (message_id,))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Failed to mark message as read: {e}")
    finally:
        if conn:
            conn.close()

def get_unread_count(username):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM private_messages 
            WHERE receiver=? AND is_read=0
        """, (username,))
        return cursor.fetchone()[0]
    except sqlite3.Error as e:
        st.error(f"Failed to get unread count: {e}")
        return 0
    finally:
        if conn:
            conn.close()

def get_unread_messages(username):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM private_messages 
            WHERE receiver=? AND is_read=0
            ORDER BY timestamp DESC
        """, (username,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to fetch unread messages: {e}")
        return []
    finally:
        if conn:
            conn.close()

def extract_mentions(text):
    return set(re.findall(r'@(\w+)', text))

def show_notification(message):
    js = f"""
    <script>
        if (Notification.permission === "granted") {{
            new Notification("{message}");
        }} else if (Notification.permission !== "denied") {{
            Notification.requestPermission().then(function(permission) {{
                if (permission === "granted") {{
                    new Notification("{message}");
                }}
            }});
        }}
    </script>
    """
    html(js)

# --------------------------
# Streamlit UI
# --------------------------

# Set page config
st.set_page_config(
    page_title="Request Management System", 
    page_icon=":office:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom Tailwind-like CSS
st.markdown("""
<style>
    .stApp {
        background-color: #f4f4f5;
        font-family: 'Inter', sans-serif;
    }
    .stButton>button {
        background-color: #3b82f6;
        color: white;
        border-radius: 0.5rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #2563eb;
        transform: scale(1.05);
    }
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stTextArea>div>div>textarea {
        border-radius: 0.5rem;
        border: 1px solid #e5e7eb;
        padding: 0.5rem;
        transition: all 0.3s ease;
    }
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>select:focus, .stTextArea>div>div>textarea:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
    }
    .stExpander {
        border-radius: 0.75rem;
        background-color: white;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.last_unread_count = 0
    st.session_state.last_message_count = 0

# Initialize database
init_db()

# Login Page
if not st.session_state.authenticated:
    st.title("🏢 Request Management System")
    
    # Create a centered login container
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.header("Login")
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            login_button = st.form_submit_button("Login")
            
            if login_button:
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
    # Navigation menu
    with st.sidebar:
        st.title(f"👋 Welcome, {st.session_state.username}")
        
        # Unread message count
        unread_count = get_unread_count(st.session_state.username)
        
        nav_options = [
            "📋 Requests", 
            "🔍 Hold", 
            "❌ Ticket Mistakes", 
            f"💬 Conversations ({unread_count})"
        ]
        
        if st.session_state.role == "admin":
            nav_options.append("⚙️ Admin Panel")
        
        # Logout button
        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.role = None
            st.session_state.username = None
            st.rerun()
        
        section = st.radio("Navigation", nav_options)

    # Rest of the application logic remains the same as in the previous code
    # ... (You can copy the entire existing application logic from the previous code)
    
    # The main sections (Requests, Hold, Ticket Mistakes, Conversations, Admin Panel) 
    # would follow the same structure as in the previous code

# The rest of the application logic remains the same

# Add this at the end of the script to handle message notifications
if st.session_state.get("authenticated", False):
    current_message_count = len(get_group_messages())
    if current_message_count > st.session_state.get("last_message_count", 0):
        st.session_state.last_message_count = current_message_count
        show_notification("New message in group chat")
    
    unread_count = get_unread_count(st.session_state.username)
    if unread_count > st.session_state.get("last_unread_count", 0):
        st.session_state.last_unread_count = unread_count
        show_notification(f"You have {unread_count} new messages")
