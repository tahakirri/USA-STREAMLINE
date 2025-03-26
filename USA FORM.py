import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import os
import re
from PIL import Image
import io
import pandas as pd

# --------------------------
# Database Functions
# --------------------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        hashed_password = hash_password(password)
        cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, hashed_password))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT CHECK(role IN ('agent', 'admin')))
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
                completed INTEGER DEFAULT 0)
        """)
        
        # Mistakes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_leader TEXT,
                agent_name TEXT,
                ticket_id TEXT,
                error_description TEXT,
                timestamp TEXT)
        """)
        
        # Group messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                message TEXT,
                timestamp TEXT,
                mentions TEXT)
        """)
        
        # HOLD images table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hold_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uploader TEXT,
                image_data BLOB,
                timestamp TEXT)
        """)
        
        # System settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY DEFAULT 1,
                killswitch_enabled INTEGER DEFAULT 0)
        """)
        
        # Initialize default settings
        cursor.execute("""
            INSERT OR IGNORE INTO system_settings (id, killswitch_enabled) 
            VALUES (1, 0)
        """)
        
        # Default admin accounts
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, password, role) 
            VALUES (?, ?, ?)
        """, ("taha kirri", hash_password("arise@99"), "admin"))
        
        conn.commit()
    finally:
        conn.close()

def is_killswitch_enabled():
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT killswitch_enabled FROM system_settings WHERE id = 1")
        result = cursor.fetchone()
        return bool(result[0]) if result else False
    finally:
        conn.close()

def toggle_killswitch(enable):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE system_settings 
            SET killswitch_enabled = ?
            WHERE id = 1
        """, (1 if enable else 0,))
        conn.commit()
        return True
    finally:
        conn.close()

def add_request(agent_name, request_type, identifier, comment):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO requests (agent_name, request_type, identifier, comment, timestamp) 
            VALUES (?, ?, ?, ?, ?)
        """, (agent_name, request_type, identifier, comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    finally:
        conn.close()

def get_requests():
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM requests ORDER BY timestamp DESC")
        return cursor.fetchall()
    finally:
        conn.close()

def search_requests(query):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        query = f"%{query.lower()}%"
        cursor.execute("""
            SELECT * FROM requests 
            WHERE LOWER(agent_name) LIKE ? 
            OR LOWER(request_type) LIKE ? 
            OR LOWER(identifier) LIKE ? 
            OR LOWER(comment) LIKE ?
            ORDER BY timestamp DESC
        """, (query, query, query, query))
        return cursor.fetchall()
    finally:
        conn.close()

def update_request_status(request_id, completed):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE requests 
            SET completed = ? 
            WHERE id = ?
        """, (1 if completed else 0, request_id))
        conn.commit()
        return True
    finally:
        conn.close()

def add_mistake(team_leader, agent_name, ticket_id, error_description):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO mistakes (team_leader, agent_name, ticket_id, error_description, timestamp) 
            VALUES (?, ?, ?, ?, ?)
        """, (team_leader, agent_name, ticket_id, error_description, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    finally:
        conn.close()

def get_mistakes():
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mistakes ORDER BY timestamp DESC")
        return cursor.fetchall()
    finally:
        conn.close()

def search_mistakes(query):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        query = f"%{query.lower()}%"
        cursor.execute("""
            SELECT * FROM mistakes 
            WHERE LOWER(agent_name) LIKE ? 
            OR LOWER(ticket_id) LIKE ? 
            OR LOWER(error_description) LIKE ?
            ORDER BY timestamp DESC
        """, (query, query, query))
        return cursor.fetchall()
    finally:
        conn.close()

def send_group_message(sender, message):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        mentions = re.findall(r'@(\w+)', message)
        cursor.execute("""
            INSERT INTO group_messages (sender, message, timestamp, mentions) 
            VALUES (?, ?, ?, ?)
        """, (sender, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ','.join(mentions)))
        conn.commit()
        return True
    finally:
        conn.close()

def get_group_messages():
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM group_messages ORDER BY timestamp DESC LIMIT 50")
        return cursor.fetchall()
    finally:
        conn.close()

def get_all_users():
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM users")
        return cursor.fetchall()
    finally:
        conn.close()

def add_user(username, password, role):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, role) 
            VALUES (?, ?, ?)
        """, (username, hash_password(password), role))
        conn.commit()
        return True
    finally:
        conn.close()

def delete_user(user_id):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True
    finally:
        conn.close()

def add_hold_image(uploader, image_data):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hold_images (uploader, image_data, timestamp) 
            VALUES (?, ?, ?)
        """, (uploader, image_data, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    finally:
        conn.close()

def get_hold_images():
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hold_images ORDER BY timestamp DESC")
        return cursor.fetchall()
    finally:
        conn.close()

def clear_hold_images():
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM hold_images")
        conn.commit()
        return True
    finally:
        conn.close()

def clear_all_requests():
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM requests")
        conn.commit()
        return True
    finally:
        conn.close()

def clear_all_mistakes():
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM mistakes")
        conn.commit()
        return True
    finally:
        conn.close()

def clear_all_group_messages():
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM group_messages")
        conn.commit()
        return True
    finally:
        conn.close()

# --------------------------
# Streamlit App
# --------------------------

st.set_page_config(
    page_title="Request Management System", 
    page_icon=":office:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp { background-color: #121212; color: #E0E0E0; }
    
    [data-testid="stSidebar"] { 
        background-color: #1E1E1E; 
        border-right: 1px solid #3A3A3A; 
    }

    .stButton>button {
        background-color: #2563EB;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        border: none;
    }

    .card {
        background-color: #1F1F1F;
        color: #E0E0E0;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(255, 255, 255, 0.1);
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
        background-color: #2563EB;
        color: white;
        margin-left: auto;
    }

    .received {
        background-color: #2C2C2C;
        color: #E0E0E0;
        margin-right: auto;
    }

    .killswitch-active {
        background-color: #4A1E1E;
        border-left: 5px solid #D32F2F;
        padding: 1rem;
        margin-bottom: 1rem;
        color: #FFCDD2;
    }

    .killswitch-control {
        background-color: #333333;
        color: #E0E0E0;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }

    .metric-card {
        background-color: #1F2937;
        border-radius: 10px;
        padding: 20px;
        margin: 10px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }

    .search-box {
        margin-bottom: 20px;
        background-color: #1F2937;
        padding: 15px;
        border-radius: 10px;
    }

    /* Scrollbar customization */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-thumb {
        background: #555;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-track {
        background: #222;
    }
</style>
""", unsafe_allow_html=True)

# Session State
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.current_section = "requests"
    st.session_state.last_request_count = 0
    st.session_state.last_mistake_count = 0
    st.session_state.last_message_count = 0
    st.session_state.last_message_ids = []

# Initialize DB
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
                            st.session_state.last_request_count = len(get_requests())
                            st.session_state.last_mistake_count = len(get_mistakes())
                            st.session_state.last_message_ids = [msg[0] for msg in get_group_messages()]
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                    else:
                        st.warning("Please enter both username and password")

# Main Application
else:
    # Display killswitch warning if active
    if is_killswitch_enabled():
        st.markdown("""
        <div class="killswitch-active">
            <h3>⚠️ SYSTEM LOCKED ⚠️</h3>
            <p>The system is currently in read-only mode. Please contact the developer for assistance.</p>
        </div>
        """, unsafe_allow_html=True)

    # Notification System
    def show_notifications():
        current_requests = get_requests()
        current_mistakes = get_mistakes()
        current_messages = get_group_messages()
        
        # Request notifications
        new_requests = len(current_requests) - st.session_state.last_request_count
        if new_requests > 0 and st.session_state.last_request_count > 0:
            st.toast(f"📋 {new_requests} new request(s) submitted!", icon="📋")
        st.session_state.last_request_count = len(current_requests)
        
        # Mistake notifications
        new_mistakes = len(current_mistakes) - st.session_state.last_mistake_count
        if new_mistakes > 0 and st.session_state.last_mistake_count > 0:
            st.toast(f"❌ {new_mistakes} new mistake(s) reported!", icon="❌")
        st.session_state.last_mistake_count = len(current_mistakes)
        
        # Message notifications
        current_message_ids = [msg[0] for msg in current_messages]
        new_messages = [msg for msg in current_messages if msg[0] not in st.session_state.last_message_ids]
        for msg in new_messages:
            if msg[1] != st.session_state.username:
                mentions = msg[4].split(',') if msg[4] else []
                if st.session_state.username in mentions:
                    st.toast(f"💬 You were mentioned by {msg[1]}!", icon="💬")
                else:
                    st.toast(f"💬 New message from {msg[1]}!", icon="💬")
        st.session_state.last_message_ids = current_message_ids

    show_notifications()

    # Sidebar Navigation
    with st.sidebar:
        st.title(f"👋 Welcome, {st.session_state.username}")
        st.markdown("---")
        
        nav_options = [
            ("📋 Requests", "requests"),
            ("📊 Dashboard", "dashboard"),
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
        
        # Notification Badges
        pending_requests = len([r for r in get_requests() if not r[6]])
        new_mistakes = len(get_mistakes())
        unread_messages = len([m for m in get_group_messages() 
                             if m[0] not in st.session_state.last_message_ids 
                             and m[1] != st.session_state.username])
        
        st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <h4>🔔 Notifications</h4>
            <p>📋 Pending requests: {pending_requests}</p>
            <p>❌ Recent mistakes: {new_mistakes}</p>
            <p>💬 Unread messages: {unread_messages}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.role = None
            st.session_state.username = None
            st.rerun()
    
    # Main Content
    st.title(f"{'📋' if st.session_state.current_section == 'requests' else ''}"
             f"{'📊' if st.session_state.current_section == 'dashboard' else ''}"
             f"{'🖼️' if st.session_state.current_section == 'hold' else ''}"
             f"{'❌' if st.session_state.current_section == 'mistakes' else ''}"
             f"{'💬' if st.session_state.current_section == 'chat' else ''}"
             f"{'⚙️' if st.session_state.current_section == 'admin' else ''}"
             f" {st.session_state.current_section.title()}")

    # Requests Section
    if st.session_state.current_section == "requests":
        if not is_killswitch_enabled():
            with st.expander("➕ Submit New Request", expanded=False):
                with st.form("request_form"):
                    cols = st.columns([1, 3])
                    request_type = cols[0].selectbox("Request Type", ["Email", "Phone Number", "Ticket ID"])
                    identifier = cols[1].text_input("Identifier")
                    comment = st.text_area("Comment")
                    
                    if st.form_submit_button("Submit Request"):
                        if identifier and comment:
                            if add_request(st.session_state.username, request_type, identifier, comment):
                                st.success("Request submitted!")
        else:
            st.warning("⚠️ System is currently locked. You cannot submit new requests.")
        
        st.subheader("🔍 Search Requests")
        search_query = st.text_input("Search by agent, identifier, or comment", key="request_search")
        requests = search_requests(search_query) if search_query else get_requests()
        
        st.subheader("All Requests")
        for req in requests:
            req_id, agent, req_type, identifier, comment, timestamp, completed = req
            
            with st.container():
                cols = st.columns([0.1, 0.9])
                with cols[0]:
                    if not is_killswitch_enabled():
                        st.checkbox(
                            "Done",
                            value=bool(completed),
                            key=f"check_{req_id}",
                            on_change=update_request_status,
                            args=(req_id, not completed))
                    else:
                        st.checkbox(
                            "Done",
                            value=bool(completed),
                            key=f"check_{req_id}",
                            disabled=True)
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

    # Dashboard Section
   elif st.session_state.current_section == "dashboard":
    st.subheader("📊 Request Completion Dashboard")
    
    # Get all requests
    all_requests = get_requests()
    total_requests = len(all_requests)
    completed_requests = sum(1 for r in all_requests if r[6])
    completion_rate = (completed_requests / total_requests * 100) if total_requests > 0 else 0
    
    # Metrics - using Streamlit's native metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Requests", total_requests)
    with col2:
        st.metric("Completed", completed_requests, delta=f"{completed_requests - (total_requests - completed_requests)}")
    with col3:
        st.metric("Completion Rate", f"{completion_rate:.1f}%")
    
    # Visualization Section
    st.subheader("Request Trends")
    
    # Create dataframe for visualization
    df = pd.DataFrame({
        'Date': [datetime.strptime(r[5], "%Y-%m-%d %H:%M:%S").date() for r in all_requests],
        'Status': ['Completed' if r[6] else 'Pending' for r in all_requests],
        'Type': [r[2] for r in all_requests]
    })
    
    # Daily request volume
    st.write("### Daily Request Volume")
    daily_counts = df['Date'].value_counts().sort_index()
    st.bar_chart(daily_counts)
    
    # Status distribution
    st.write("### Request Status")
    status_counts = df['Status'].value_counts()
    st.bar_chart(status_counts)
    
    # Request type distribution
    st.write("### Request Type Distribution")
    type_counts = df['Type'].value_counts()
    st.bar_chart(type_counts)


    # Ticket Mistakes Section
    elif st.session_state.current_section == "mistakes":
        if not is_killswitch_enabled():
            with st.expander("➕ Report New Mistake", expanded=False):
                with st.form("mistake_form"):
                    cols = st.columns(3)
                    agent_name = cols[0].text_input("Agent Name")
                    ticket_id = cols[1].text_input("Ticket ID")
                    error_description = st.text_area("Error Description")
                    
                    if st.form_submit_button("Report Mistake"):
                        if ticket_id and agent_name and error_description:
                            if add_mistake(st.session_state.username, agent_name, ticket_id, error_description):
                                st.success("Mistake reported successfully!")
        else:
            st.warning("⚠️ System is currently locked. You cannot report new mistakes.")
        
        st.subheader("🔍 Search Mistakes")
        search_query = st.text_input("Search by agent, ticket ID, or error", key="mistake_search")
        mistakes = search_mistakes(search_query) if search_query else get_mistakes()
        
        st.subheader("Ticket Mistakes Log")
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
        if not is_killswitch_enabled():
            with st.form("chat_form"):
                message = st.text_input("Type your message (use @username to mention)")
                
                if st.form_submit_button("Send"):
                    if message:
                        if send_group_message(st.session_state.username, message):
                            st.rerun()
        else:
            st.warning("⚠️ System is currently locked. You cannot send messages.")

    # Admin Panel Section
    elif st.session_state.current_section == "admin" and st.session_state.role == "admin":
        st.subheader("User Management")
        
        # Killswitch control (only for Taha Kirri)
        if st.session_state.username.lower() == "taha kirri":
            st.markdown("---")
            st.subheader("🚨 System Killswitch")
            
            current_status = is_killswitch_enabled()
            status_text = "🔴 ACTIVATED" if current_status else "🟢 DEACTIVATED"
            st.markdown(f"### Current Status: {status_text}")
            
            if current_status:
                if st.button("🟢 Deactivate Killswitch"):
                    if toggle_killswitch(False):
                        st.success("Killswitch deactivated! System functions restored.")
                        st.rerun()
            else:
                if st.button("🔴 Activate Killswitch"):
                    if toggle_killswitch(True):
                        st.success("Killswitch activated! All modification functions disabled.")
                        st.rerun()
            
            st.markdown("---")
        
        # Add User Form
        if not is_killswitch_enabled():
            with st.form("add_user_form"):
                new_username = st.text_input("New Username")
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("Role", ["agent", "admin"])
                
                if st.form_submit_button("Add User"):
                    if new_username and new_password:
                        if add_user(new_username, new_password, new_role):
                            st.success(f"User {new_username} added successfully!")
        else:
            st.warning("⚠️ System is currently locked. You cannot add new users.")
        
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
                if not is_killswitch_enabled():
                    if st.button(f"Delete {username}", key=f"delete_{user_id}"):
                        if delete_user(user_id):
                            st.success(f"User {username} deleted!")
                            st.rerun()
                else:
                    st.button(f"Delete {username}", key=f"delete_{user_id}", disabled=True)
        
        # Data Management Section
        st.markdown("---")
        st.subheader("🗑️ Data Management")
        
        col1, col2 = st.columns(2)
        with col1:
            if not is_killswitch_enabled():
                if st.button("🗑️ Clear All Requests", key="clear_requests"):
                    if clear_all_requests():
                        st.success("All requests have been cleared!")
                        st.rerun()
            else:
                st.button("🗑️ Clear All Requests", key="clear_requests", disabled=True)
        
        with col2:
            if not is_killswitch_enabled():
                if st.button("🗑️ Clear All Mistakes", key="clear_mistakes"):
                    if clear_all_mistakes():
                        st.success("All mistakes have been cleared!")
                        st.rerun()
            else:
                st.button("🗑️ Clear All Mistakes", key="clear_mistakes", disabled=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if not is_killswitch_enabled():
                if st.button("🗑️ Clear All Group Messages", key="clear_group_messages"):
                    if clear_all_group_messages():
                        st.success("All group messages have been cleared!")
                        st.rerun()
            else:
                st.button("🗑️ Clear All Group Messages", key="clear_group_messages", disabled=True)
        
        with col2:
            if not is_killswitch_enabled():
                if st.button("🗑️ Clear All HOLD Images", key="clear_hold_images"):
                    if clear_hold_images():
                        st.success("All HOLD images have been cleared!")
                        st.rerun()
            else:
                st.button("🗑️ Clear All HOLD Images", key="clear_hold_images", disabled=True)

    # HOLD Section
    elif st.session_state.current_section == "hold":
        # Admin-only upload section
        if st.session_state.role == "admin":
            if not is_killswitch_enabled():
                with st.expander("📤 Upload Image to HOLD", expanded=False):
                    uploaded_image = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])
                    
                    if uploaded_image:
                        image_data = uploaded_image.read()
                        if add_hold_image(st.session_state.username, image_data):
                            st.success("Image uploaded successfully!")
                            st.image(uploaded_image, caption="Uploaded Image", use_container_width=True)
            else:
                st.warning("⚠️ System is currently locked. You cannot upload images.")
        else:
            st.info("🔒 Only administrators can upload images to HOLD")

        # Display section (visible to all)
        st.subheader("📥 Check HOLD Images")
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
                    st.image(Image.open(io.BytesIO(image_data)), caption=f"Image {img_id}", use_container_width=True)
        else:
            st.info("No images in HOLD")

# Run the app
if __name__ == "__main__":
    st.write("Request Management System")
