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
        """, ("fouad fathi", hash_password("fathi@44"), "admin"))
        
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

# Mistakes Section Functions
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
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to add mistake: {e}")
        return False
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

# Group Chat Functions
def send_group_message(sender, message):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        
        # Extract mentions
        mentions = re.findall(r'@(\w+)', message)
        
        cursor.execute("""
            INSERT INTO group_messages (sender, message, timestamp, mentions) 
            VALUES (?, ?, ?, ?)
        """, (sender, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ','.join(mentions)))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to send message: {e}")
        return False
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
            LIMIT 50
        """)
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to fetch group messages: {e}")
        return []
    finally:
        if conn:
            conn.close()

# Admin Panel Functions
def get_all_users():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM users")
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to fetch users: {e}")
        return []
    finally:
        if conn:
            conn.close()

def add_user(username, password, role):
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
        st.error(f"Failed to add user: {e}")
        return False
    finally:
        if conn:
            conn.close()

def delete_user(user_id):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to delete user: {e}")
        return False
    finally:
        if conn:
            conn.close()

# New functions for clearing data
def clear_all_requests():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM requests")
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to clear requests: {e}")
        return False
    finally:
        if conn:
            conn.close()

def clear_all_mistakes():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM mistakes")
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to clear mistakes: {e}")
        return False
    finally:
        if conn:
            conn.close()

def clear_all_group_messages():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM group_messages")
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to clear group messages: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Existing functions from previous implementation...
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

def add_hold_image(uploader, image_data):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hold_images (uploader, image_data, timestamp) 
            VALUES (?, ?, ?)
        """, (uploader, image_data, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Failed to add HOLD image: {e}")
    finally:
        if conn:
            conn.close()

def get_hold_images():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM hold_images 
            ORDER BY timestamp DESC
        """)
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to fetch HOLD images: {e}")
        return []
    finally:
        if conn:
            conn.close()

def clear_hold_images():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM hold_images")
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to clear HOLD images: {e}")
        return False
    finally:
        if conn:
            conn.close()

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

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.current_section = "requests"
    st.session_state.last_message_count = 0

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
            ("🖼️ HOLD", "hold"),
            ("❌ Ticket Mistakes", "mistakes"),
            ("💬 Group Chat", "chat")
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
    st.title(f"{'📋' if st.session_state.current_section == 'requests' else ''}"
             f"{'🖼️' if st.session_state.current_section == 'hold' else ''}"
             f"{'❌' if st.session_state.current_section == 'mistakes' else ''}"
             f"{'💬' if st.session_state.current_section == 'chat' else ''}"
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

    # Ticket Mistakes Section
    elif st.session_state.current_section == "mistakes":
        st.subheader("Report a Ticket Mistake")
        with st.form("mistake_form"):
            ticket_id = st.text_input("Ticket ID")
            agent_name = st.text_input("Agent Name")
            error_description = st.text_area("Error Description")
            
            if st.form_submit_button("Report Mistake"):
                if ticket_id and agent_name and error_description:
                    if add_mistake(st.session_state.username, agent_name, ticket_id, error_description):
                        st.success("Mistake reported successfully!")
        
        st.subheader("Ticket Mistakes Log")
        mistakes = get_mistakes()
        if mistakes:
            for mistake in mistakes:
                mistake_id, team_leader, agent_name, ticket_id, error_desc, timestamp = mistake
                st.markdown(f"""
                <div class="card">
                    <div style="display: flex; justify-content: space-between;">
                        <h4>Mistake #{mistake_id}</h4>
                        <small>{timestamp}</small>
                    </div>
                    <p><strong>Team Leader:</strong> {team_leader}</p>
                    <p><strong>Agent:</strong> {agent_name}</p>
                    <p><strong>Ticket ID:</strong> {ticket_id}</p>
                    <p><strong>Error Description:</strong> {error_desc}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No mistakes reported.")

    # Group Chat Section
    elif st.session_state.current_section == "chat":
        st.subheader("Group Chat")
        
        # Display messages
        messages = get_group_messages()
        for msg in reversed(messages):
            msg_id, sender, message, timestamp, mentions = msg
            is_mentioned = st.session_state.username in (mentions.split(',') if mentions else [])
            
            st.markdown(f"""
            <div class="message {'sent' if sender == st.session_state.username else 'received'}" 
                 style="{'background-color: #3b82f6; color: white;' if is_mentioned else ''}">
                <strong>{sender}</strong> {message}
                <br><small>{timestamp}</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Send message form
        with st.form("chat_form"):
            message = st.text_input("Type your message (use @username to mention)")
            
            if st.form_submit_button("Send"):
                if message:
                    if send_group_message(st.session_state.username, message):
                        st.rerun()

    # Admin Panel Section
    elif st.session_state.current_section == "admin" and st.session_state.role == "admin":
        st.subheader("User Management")
        
        # Add User Form
        with st.form("add_user_form"):
            new_username = st.text_input("New Username")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["agent", "admin"])
            
            if st.form_submit_button("Add User"):
                if new_username and new_password:
                    if add_user(new_username, new_password, new_role):
                        st.success(f"User {new_username} added successfully!")
        
        # User List
        st.subheader("Existing Users")
        users = get_all_users()
        for user_id, username, role in users:
            cols = st.columns([0.6, 0.2, 0.2])
            with cols[0]:
                st.write(f"{username}")
            with cols[1]:
                st.write(role)
            with cols[2]:
                if st.button(f"Delete {username}", key=f"delete_{user_id}"):
                    if delete_user(user_id):
                        st.success(f"User {username} deleted!")
                        st.rerun()
        
        # Data Management Section
        st.markdown("---")
        st.subheader("🗑️ Data Management")
        
        # Requests Clearing
        st.markdown("#### Clear Requests")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear All Requests", key="clear_requests"):
                if clear_all_requests():
                    st.success("All requests have been cleared!")
                    st.rerun()
        
        # Mistakes Clearing
        st.markdown("#### Clear Mistakes")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear All Mistakes", key="clear_mistakes"):
                if clear_all_mistakes():
                    st.success("All mistakes have been cleared!")
                    st.rerun()
        
        # Group Messages Clearing
        st.markdown("#### Clear Group Messages")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear All Group Messages", key="clear_group_messages"):
                if clear_all_group_messages():
                    st.success("All group messages have been cleared!")
                    st.rerun()
        
        # HOLD Images Clearing
        st.markdown("#### Clear HOLD Images")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear All HOLD Images", key="clear_hold_images"):
                if clear_hold_images():
                    st.success("All HOLD images have been cleared!")
                    st.rerun()

# HOLD Section
if st.session_state.current_section == "hold":
    # Admin-only upload section
    if st.session_state.role == "admin":
        with st.container():
            st.subheader("Upload Image to HOLD")
            uploaded_image = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])
            
            if uploaded_image:
                image_data = uploaded_image.read()
                add_hold_image(st.session_state.username, image_data)
                st.success("Image uploaded successfully!")
                st.image(uploaded_image, caption="Uploaded Image", use_container_width=True)  # Fixed here
    else:
        st.info("🔒 Only administrators can upload images to HOLD")

    # Display section (visible to all)
    st.subheader("Check HOLD Images")
    hold_images = get_hold_images()
    
    if hold_images:
        for img in hold_images:
            img_id, uploader, image_data, timestamp = img
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <div style="display: flex; justify-content: space-between;">
                        <h4>Image #{img_id}</h4>
                        <small>{timestamp}</small>
                    </div>
                    <p><strong>Uploaded by:</strong> {uploader}</p>
                </div>
                """, unsafe_allow_html=True)
                st.image(Image.open(io.BytesIO(image_data)), caption=f"Image {img_id}", use_container_width=True)  # Fixed here

    # Admin-only clear button
    if st.session_state.role == "admin" and st.button("🗑️ Clear All HOLD Images"):
        if clear_hold_images():
            st.success("All HOLD images cleared!")
# Run the app
if __name__ == "__main__":
    st.write("Request Management System")
