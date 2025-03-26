import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, date
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
        cursor.execute("SELECT role, id FROM users WHERE username = ? AND password = ?", 
                      (username, hashed_password))
        result = cursor.fetchone()
        return (result[0], result[1]) if result else (None, None)
    finally:
        conn.close()

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        
        # Users Table with team leader relationship
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT CHECK(role IN ('agent', 'team_leader', 'admin')),
                team_leader_id INTEGER,
                FOREIGN KEY(team_leader_id) REFERENCES users(id))
        """)
        
        # Skillsets Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skillsets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT)
        """)
        
        # User-Skillset Mapping
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_skillsets (
                user_id INTEGER,
                skillset_id INTEGER,
                PRIMARY KEY (user_id, skillset_id),
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(skillset_id) REFERENCES skillsets(id))
        """)
        
        # Requests Table
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
        
        # Mistakes Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_leader TEXT,
                agent_name TEXT,
                ticket_id TEXT,
                error_description TEXT,
                timestamp TEXT)
        """)
        
        # Group Messages Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                message TEXT,
                timestamp TEXT,
                mentions TEXT)
        """)
        
        # Hold Images Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hold_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uploader TEXT,
                image_data BLOB,
                timestamp TEXT)
        """)
        
        # System Settings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY DEFAULT 1,
                killswitch_enabled INTEGER DEFAULT 0)
        """)
        
        # Breaks Table (modified with skillset_id)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS breaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                break_name TEXT,
                start_time TEXT,
                end_time TEXT,
                max_users INTEGER,
                current_users INTEGER DEFAULT 0,
                created_by TEXT,
                skillset_id INTEGER,
                timestamp TEXT,
                FOREIGN KEY(skillset_id) REFERENCES skillsets(id))
        """)
        
        # Break Bookings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS break_bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                break_id INTEGER,
                user_id INTEGER,
                username TEXT,
                booking_date TEXT,
                timestamp TEXT,
                FOREIGN KEY(break_id) REFERENCES breaks(id))
        """)
        
        # Initialize system settings
        cursor.execute("INSERT OR IGNORE INTO system_settings (id, killswitch_enabled) VALUES (1, 0)")
        
        # Create default admin
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, password, role) 
            VALUES (?, ?, ?)
        """, ("taha kirri", hash_password("arise@99"), "admin"))
        
        conn.commit()
    finally:
        conn.close()

# --------------------------
# Skillset Functions
# --------------------------

def create_skillset(name, description=""):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO skillsets (name, description) VALUES (?, ?)", 
                      (name, description))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_all_skillsets():
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description FROM skillsets ORDER BY name")
        return cursor.fetchall()
    finally:
        conn.close()

def delete_skillset(skillset_id):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM skillsets WHERE id = ?", (skillset_id,))
        cursor.execute("DELETE FROM user_skillsets WHERE skillset_id = ?", (skillset_id,))
        conn.commit()
        return True
    finally:
        conn.close()

def assign_skillset_to_user(user_id, skillset_id):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO user_skillsets (user_id, skillset_id) VALUES (?, ?)",
                      (user_id, skillset_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def remove_skillset_from_user(user_id, skillset_id):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_skillsets WHERE user_id = ? AND skillset_id = ?",
                      (user_id, skillset_id))
        conn.commit()
        return True
    finally:
        conn.close()

def get_user_skillsets(user_id):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, s.name 
            FROM skillsets s
            JOIN user_skillsets us ON s.id = us.skillset_id
            WHERE us.user_id = ?
        """, (user_id,))
        return cursor.fetchall()
    finally:
        conn.close()

def get_skillset_users(skillset_id):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.username, u.role 
            FROM users u
            JOIN user_skillsets us ON u.id = us.user_id
            WHERE us.skillset_id = ?
        """, (skillset_id,))
        return cursor.fetchall()
    finally:
        conn.close()

# --------------------------
# User Management Functions
# --------------------------

def add_user(username, password, role, team_leader_id=None, skillsets=None):
    if skillsets is None:
        skillsets = []
        
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, role, team_leader_id)
            VALUES (?, ?, ?, ?)
        """, (username, hash_password(password), role, team_leader_id))
        user_id = cursor.lastrowid
        
        for skillset_id in skillsets:
            cursor.execute("INSERT OR IGNORE INTO user_skillsets VALUES (?, ?)",
                          (user_id, skillset_id))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_all_users():
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.username, u.role, u.team_leader_id, tl.username as team_leader_name
            FROM users u
            LEFT JOIN users tl ON u.team_leader_id = tl.id
            ORDER BY u.role, u.username
        """)
        return cursor.fetchall()
    finally:
        conn.close()

def get_team_leaders():
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users WHERE role = 'team_leader'")
        return cursor.fetchall()
    finally:
        conn.close()

def get_agents_for_team_leader(team_leader_id):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username 
            FROM users 
            WHERE team_leader_id = ?
        """, (team_leader_id,))
        return cursor.fetchall()
    finally:
        conn.close()

def delete_user(user_id):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        cursor.execute("DELETE FROM user_skillsets WHERE user_id = ?", (user_id,))
        conn.commit()
        return True
    finally:
        conn.close()

# --------------------------
# Break Management Functions
# --------------------------

def add_break_slot(break_name, start_time, end_time, max_users, created_by, skillset_id):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO breaks 
            (break_name, start_time, end_time, max_users, created_by, skillset_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (break_name, start_time, end_time, max_users, created_by, skillset_id,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    finally:
        conn.close()

def get_all_break_slots():
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.*, s.name as skillset_name
            FROM breaks b
            LEFT JOIN skillsets s ON b.skillset_id = s.id
            ORDER BY b.start_time
        """)
        return cursor.fetchall()
    finally:
        conn.close()

def get_available_breaks_for_user(user_id, booking_date):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.*, s.name as skillset_name
            FROM breaks b
            JOIN skillsets s ON b.skillset_id = s.id
            JOIN user_skillsets us ON b.skillset_id = us.skillset_id
            WHERE us.user_id = ?
            AND DATE(b.timestamp) = DATE(?)
            AND b.max_users > (
                SELECT COUNT(*) 
                FROM break_bookings bb 
                WHERE bb.break_id = b.id 
                AND bb.booking_date = ?
            )
            AND NOT EXISTS (
                SELECT 1 FROM break_bookings bb
                WHERE bb.user_id = ?
                AND bb.booking_date = ?
            )
            ORDER BY b.start_time
        """, (user_id, booking_date, booking_date, user_id, booking_date))
        return cursor.fetchall()
    finally:
        conn.close()

def book_break_slot(break_id, user_id, username, booking_date):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO break_bookings 
            (break_id, user_id, username, booking_date, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (break_id, user_id, username, booking_date,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    finally:
        conn.close()

def get_user_bookings(user_id, booking_date):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT bb.*, b.break_name, b.start_time, b.end_time, s.name as skillset_name
            FROM break_bookings bb
            JOIN breaks b ON bb.break_id = b.id
            LEFT JOIN skillsets s ON b.skillset_id = s.id
            WHERE bb.user_id = ? AND bb.booking_date = ?
        """, (user_id, booking_date))
        return cursor.fetchall()
    finally:
        conn.close()

def get_all_bookings(booking_date):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT bb.*, b.break_name, b.start_time, b.end_time, 
                   u.username, u.role, s.name as skillset_name
            FROM break_bookings bb
            JOIN breaks b ON bb.break_id = b.id
            JOIN users u ON bb.user_id = u.id
            LEFT JOIN skillsets s ON b.skillset_id = s.id
            WHERE bb.booking_date = ?
            ORDER BY b.start_time, bb.username
        """, (booking_date,))
        return cursor.fetchall()
    finally:
        conn.close()

def delete_break_slot(break_id):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM breaks WHERE id = ?", (break_id,))
        cursor.execute("DELETE FROM break_bookings WHERE break_id = ?", (break_id,))
        conn.commit()
        return True
    finally:
        conn.close()

def clear_all_break_bookings():
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM break_bookings")
        conn.commit()
        return True
    finally:
        conn.close()

# --------------------------
# Other System Functions (unchanged from original)
# --------------------------

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
        cursor.execute("UPDATE system_settings SET killswitch_enabled = ? WHERE id = 1",
                      (1 if enable else 0,))
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
        """, (agent_name, request_type, identifier, comment, 
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
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
        cursor.execute("UPDATE requests SET completed = ? WHERE id = ?",
                      (1 if completed else 0, request_id))
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
        """, (team_leader, agent_name, ticket_id, error_description,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
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
        """, (sender, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
             ','.join(mentions)))
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
# Streamlit UI Components
# --------------------------

def setup_page():
    st.set_page_config(
        page_title="Request Management System",
        page_icon=":office:",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown("""
    <style>
        .stApp { background-color: #121212; color: #E0E0E0; }
        [data-testid="stSidebar"] { background-color: #1E1E1E; }
        .stButton>button { background-color: #2563EB; color: white; }
        .card { background-color: #1F1F1F; border-radius: 12px; padding: 1.5rem; }
        .metric-card { background-color: #1F2937; border-radius: 10px; padding: 20px; }
        .killswitch-active {
            background-color: #4A1E1E;
            border-left: 5px solid #D32F2F;
            padding: 1rem;
            margin-bottom: 1rem;
            color: #FFCDD2;
        }
        .message.sent { background-color: #2E2E2E; padding: 10px; border-radius: 10px; margin: 5px 0; }
        .message.received { background-color: #1E3A8A; padding: 10px; border-radius: 10px; margin: 5px 0; }
    </style>
    """, unsafe_allow_html=True)

def login_section():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏢 Request Management System")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if username and password:
                    role, user_id = authenticate(username, password)
                    if role:
                        st.session_state.update({
                            "authenticated": True,
                            "role": role,
                            "user_id": user_id,
                            "username": username,
                            "current_section": "requests",
                            "last_request_count": len(get_requests()),
                            "last_mistake_count": len(get_mistakes()),
                            "last_message_ids": [msg[0] for msg in get_group_messages()]
                        })
                        st.rerun()
                    else:
                        st.error("Invalid credentials")

def show_notifications():
    current_requests = get_requests()
    current_mistakes = get_mistakes()
    current_messages = get_group_messages()
    
    new_requests = len(current_requests) - st.session_state.last_request_count
    if new_requests > 0 and st.session_state.last_request_count > 0:
        st.toast(f"📋 {new_requests} new request(s) submitted!")
    st.session_state.last_request_count = len(current_requests)
    
    new_mistakes = len(current_mistakes) - st.session_state.last_mistake_count
    if new_mistakes > 0 and st.session_state.last_mistake_count > 0:
        st.toast(f"❌ {new_mistakes} new mistake(s) reported!")
    st.session_state.last_mistake_count = len(current_mistakes)
    
    current_message_ids = [msg[0] for msg in current_messages]
    new_messages = [msg for msg in current_messages if msg[0] not in st.session_state.last_message_ids]
    for msg in new_messages:
        if msg[1] != st.session_state.username:
            mentions = msg[4].split(',') if msg[4] else []
            if st.session_state.username in mentions:
                st.toast(f"💬 You were mentioned by {msg[1]}!")
            else:
                st.toast(f"💬 New message from {msg[1]}!")
    st.session_state.last_message_ids = current_message_ids

def render_sidebar():
    with st.sidebar:
        st.title(f"👋 Welcome, {st.session_state.username.title()}")
        st.markdown("---")
        
        nav_options = [
            ("📋 Requests", "requests"),
            ("📊 Dashboard", "dashboard"),
            ("☕ Breaks", "breaks"),
            ("🖼️ HOLD", "hold"),
            ("❌ Mistakes", "mistakes"),
            ("💬 Chat", "chat")
        ]
        if st.session_state.role == "admin":
            nav_options.append(("⚙️ Admin", "admin"))
        
        for option, value in nav_options:
            if st.button(option, key=f"nav_{value}"):
                st.session_state.current_section = value
                
        st.markdown("---")
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
            st.rerun()

def requests_section():
    st.title("Requests")
    
    if not is_killswitch_enabled():
        with st.expander("➕ Submit New Request"):
            with st.form("request_form"):
                cols = st.columns([1, 3])
                request_type = cols[0].selectbox("Type", ["Email", "Phone", "Ticket"])
                identifier = cols[1].text_input("Identifier")
                comment = st.text_area("Comment")
                if st.form_submit_button("Submit"):
                    if identifier and comment:
                        if add_request(st.session_state.username, request_type, identifier, comment):
                            st.success("Request submitted!")
                        else:
                            st.error("Failed to submit request")
    
    st.subheader("🔍 Search Requests")
    search_query = st.text_input("Search requests...")
    requests = search_requests(search_query) if search_query else get_requests()
    
    st.subheader("All Requests")
    for req in requests:
        req_id, agent, req_type, identifier, comment, timestamp, completed = req
        with st.container():
            cols = st.columns([0.1, 0.9])
            with cols[0]:
                if not is_killswitch_enabled():
                    st.checkbox("Done", value=bool(completed), 
                               key=f"check_{req_id}", 
                               on_change=update_request_status,
                               args=(req_id, not completed))
                else:
                    st.checkbox("Done", value=bool(completed), disabled=True)
            with cols[1]:
                st.markdown(f"""
                <div class="card">
                    <div style="display: flex; justify-content: space-between;">
                        <h4>#{req_id} - {req_type}</h4>
                        <small>{timestamp}</small>
                    </div>
                    <p>Agent: {agent}</p>
                    <p>Identifier: {identifier}</p>
                    <p>Comment: {comment}</p>
                </div>
                """, unsafe_allow_html=True)

def dashboard_section():
    st.title("Dashboard")
    
    st.subheader("📊 Request Completion Dashboard")
    all_requests = get_requests()
    total = len(all_requests)
    completed = sum(1 for r in all_requests if r[6])
    rate = (completed/total*100) if total > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Requests", total)
    with col2:
        st.metric("Completed", completed)
    with col3:
        st.metric("Completion Rate", f"{rate:.1f}%")
    
    df = pd.DataFrame({
        'Date': [datetime.strptime(r[5], "%Y-%m-%d %H:%M:%S").date() for r in all_requests],
        'Status': ['Completed' if r[6] else 'Pending' for r in all_requests],
        'Type': [r[2] for r in all_requests]
    })
    
    st.subheader("Request Trends")
    st.bar_chart(df['Date'].value_counts())
    
    st.subheader("Request Type Distribution")
    type_counts = df['Type'].value_counts().reset_index()
    type_counts.columns = ['Type', 'Count']
    st.bar_chart(type_counts.set_index('Type'))

def breaks_section():
    st.title("Breaks Management")
    today = date.today().strftime("%Y-%m-%d")
    selected_date = st.date_input("Select date", date.today())
    formatted_date = selected_date.strftime("%Y-%m-%d")
    
    if st.session_state.role == "admin":
        admin_breaks_section(formatted_date)
    else:
        user_breaks_section(formatted_date, today)

def admin_breaks_section(formatted_date):
    st.subheader("Admin: Break Schedule Management")
    
    with st.expander("➕ Add New Break Slot"):
        with st.form("add_break_form"):
            skillsets = get_all_skillsets()
            skillset_choices = {s[1]: s[0] for s in skillsets}
            
            cols = st.columns(3)
            break_name = cols[0].text_input("Break Name")
            start_time = cols[1].time_input("Start Time")
            end_time = cols[2].time_input("End Time")
            
            cols = st.columns(2)
            max_users = cols[0].number_input("Max Users", min_value=1, value=1)
            selected_skillset = cols[1].selectbox("Skillset", skillset_choices.keys())
            
            if st.form_submit_button("Add Break Slot"):
                if break_name:
                    skillset_id = skillset_choices[selected_skillset]
                    if add_break_slot(
                        break_name,
                        start_time.strftime("%H:%M"),
                        end_time.strftime("%H:%M"),
                        max_users,
                        st.session_state.username,
                        skillset_id
                    ):
                        st.success("Break slot added!")
                    else:
                        st.error("Failed to add break slot")
    
    st.subheader("Current Break Schedule")
    breaks = get_all_break_slots()
    if not breaks:
        st.info("No break slots scheduled")
    else:
        for b in breaks:
            b_id, name, start, end, max_u, curr_u, created_by, skillset_id, ts, skillset_name = b
            with st.container():
                cols = st.columns([3, 2, 2, 1, 1])
                cols[0].write(f"{name} ({start} - {end})")
                cols[1].write(f"Max: {max_u} | Skillset: {skillset_name}")
                cols[2].write(f"Created by: {created_by}")
                
                if cols[3].button("✏️", key=f"edit_{b_id}"):
                    pass  # Edit functionality placeholder
                
                if cols[4].button("❌", key=f"del_{b_id}"):
                    if delete_break_slot(b_id):
                        st.success("Break slot deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete break slot")
    
    st.markdown("---")
    st.subheader(f"All Bookings for {formatted_date}")
    bookings = get_all_bookings(formatted_date)
    if bookings:
        for b in bookings:
            b_id, break_id, user_id, username, date, ts, break_name, start, end, role, skillset_name = b
            st.write(f"{username} ({role}) - {break_name} ({start} - {end}) - Skillset: {skillset_name}")
    else:
        st.info("No bookings for selected date")
    
    if st.button("Clear All Bookings", key="clear_all_bookings"):
        if clear_all_break_bookings():
            st.success("All bookings cleared!")
            st.rerun()
        else:
            st.error("Failed to clear bookings")

def user_breaks_section(formatted_date, today):
    st.subheader("Available Break Slots")
    
    if formatted_date != today:
        st.warning("You can only book breaks for today!")
    
    available_breaks = get_available_breaks_for_user(st.session_state.user_id, today)
    
    if not available_breaks:
        st.info("No available break slots for your skillset")
    else:
        for b in available_breaks:
            b_id, name, start, end, max_u, curr_u, created_by, skillset_id, ts, skillset_name = b
            
            # Get current bookings for this break
            conn = sqlite3.connect("data/requests.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) 
                FROM break_bookings 
                WHERE break_id = ? AND booking_date = ?
            """, (b_id, today))
            booked_count = cursor.fetchone()[0]
            conn.close()
            
            remaining = max_u - booked_count
            
            with st.container():
                cols = st.columns([3, 2, 1])
                cols[0].write(f"**{name}** ({start} - {end})")
                cols[1].write(f"Available slots: {remaining}/{max_u} | Skillset: {skillset_name}")
                
                if cols[2].button("Book", key=f"book_{b_id}"):
                    if formatted_date == today:
                        if book_break_slot(b_id, st.session_state.user_id, st.session_state.username, today):
                            st.success("Break booked successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to book break")
                    else:
                        st.error("You can only book breaks for today!")
    
    st.markdown("---")
    st.subheader("Your Bookings")
    user_bookings = get_user_bookings(st.session_state.user_id, today)
    
    if user_bookings:
        for b in user_bookings:
            b_id, break_id, user_id, username, date, ts, break_name, start, end, skillset_name = b
            st.write(f"{break_name} ({start} - {end}) - Skillset: {skillset_name}")
    else:
        st.info("You have no bookings for today")

def hold_section():
    st.title("HOLD Images")
    
    if st.session_state.role == "admin" and not is_killswitch_enabled():
        with st.expander("📤 Upload Image"):
            img = st.file_uploader("Choose image", type=["jpg", "png", "jpeg"])
            if img:
                if add_hold_image(st.session_state.username, img.read()):
                    st.success("Image uploaded!")
                else:
                    st.error("Failed to upload image")
    
    images = get_hold_images()
    if images:
        for img in images:
            iid, uploader, data, ts = img
            st.markdown(f"""
            <div class="card">
                <div style="display: flex; justify-content: space-between;">
                    <h4>Image #{iid}</h4>
                    <small>{ts}</small>
                </div>
                <p>Uploaded by: {uploader}</p>
            </div>
            """, unsafe_allow_html=True)
            st.image(Image.open(io.BytesIO(data)), use_column_width=True)
    else:
        st.info("No images in HOLD")

def mistakes_section():
    st.title("Mistakes Log")
    
    if not is_killswitch_enabled():
        with st.expander("➕ Report New Mistake"):
            with st.form("mistake_form"):
                cols = st.columns(3)
                agent_name = cols[0].text_input("Agent Name")
                ticket_id = cols[1].text_input("Ticket ID")
                error_description = st.text_area("Error Description")
                if st.form_submit_button("Submit"):
                    if agent_name and ticket_id and error_description:
                        if add_mistake(st.session_state.username, agent_name, ticket_id, error_description):
                            st.success("Mistake reported!")
                        else:
                            st.error("Failed to report mistake")
    
    st.subheader("🔍 Search Mistakes")
    search_query = st.text_input("Search mistakes...")
    mistakes = search_mistakes(search_query) if search_query else get_mistakes()
    
    st.subheader("Mistakes Log")
    for mistake in mistakes:
        m_id, tl, agent, ticket, error, ts = mistake
        st.markdown(f"""
        <div class="card">
            <div style="display: flex; justify-content: space-between;">
                <h4>#{m_id}</h4>
                <small>{ts}</small>
            </div>
            <p>Agent: {agent}</p>
            <p>Ticket: {ticket}</p>
            <p>Error: {error}</p>
        </div>
        """, unsafe_allow_html=True)

def chat_section():
    st.title("Group Chat")
    
    messages = get_group_messages()
    for msg in reversed(messages):
        msg_id, sender, message, ts, mentions = msg
        is_mentioned = st.session_state.username in (mentions.split(',') if mentions else [])
        <div class="message {'sent' if sender == st.session_state.username else 'received'}"
            style="{'background-color: #3b82f6' if is_mentioned else ''}">
            <strong>{sender}</strong>: {message}<br>
            <small>{ts}</small>
        </div>
        """, unsafe_allow_html=True)
    
    if not is_killswitch_enabled():
        with st.form("chat_form"):
            message = st.text_input("Type your message... (use @username to mention)")
            if st.form_submit_button("Send"):
                if message:
                    if send_group_message(st.session_state.username, message):
                        st.rerun()
                    else:
                        st.error("Failed to send message")

def admin_section():
    if st.session_state.role != "admin":
        st.warning("You don't have permission to access this section")
        return
    
    st.title("Admin Panel")
    
    if st.session_state.username.lower() == "taha kirri":
        st.subheader("🚨 System Killswitch")
        current = is_killswitch_enabled()
        status = "🔴 ACTIVE" if current else "🟢 INACTIVE"
        st.write(f"Current Status: {status}")
        
        col1, col2 = st.columns(2)
        if current:
            if col1.button("Deactivate Killswitch"):
                if toggle_killswitch(False):
                    st.success("Killswitch deactivated!")
                    st.rerun()
                else:
                    st.error("Failed to deactivate killswitch")
        else:
            if col1.button("Activate Killswitch"):
                if toggle_killswitch(True):
                    st.success("Killswitch activated!")
                    st.rerun()
                else:
                    st.error("Failed to activate killswitch")
        
        # Fixed killswitch-active div
        killswitch_html = '''
        <div class="killswitch-active">
            <h3>⚠️ SYSTEM LOCKED ⚠️</h3>
            <p>The system is currently in read-only mode.</p>
        </div>
        '''
        st.markdown(killswitch_html, unsafe_allow_html=True)
    
    skillset_management()
    user_management()
    data_management()

def skillset_management():
    st.subheader("Skillset Management")
    
    with st.expander("Create New Skillset"):
        with st.form("new_skillset_form"):
            name = st.text_input("Skillset Name")
            description = st.text_area("Description")
            if st.form_submit_button("Create"):
                if name:
                    if create_skillset(name, description):
                        st.success("Skillset created!")
                    else:
                        st.error("Skillset already exists!")
    
    st.subheader("Existing Skillsets")
    skillsets = get_all_skillsets()
    if not skillsets:
        st.info("No skillsets defined")
    else:
        for s in skillsets:
            s_id, name, desc = s
            with st.expander(f"{name} (ID: {s_id})"):
                cols = st.columns([3, 1])
                cols[0].write(desc if desc else "No description")
                
                if cols[1].button("Delete", key=f"del_skillset_{s_id}"):
                    if delete_skillset(s_id):
                        st.success("Skillset deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete skillset")
                
                st.subheader("Assigned Users")
                users = get_skillset_users(s_id)
                if users:
                    for u in users:
                        u_id, username, role = u
                        st.write(f"- {username} ({role})")
                else:
                    st.info("No users assigned to this skillset")

def user_management():
    st.subheader("User Management")
    
    with st.expander("Add New User"):
        with st.form("add_user_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["agent", "team_leader", "admin"])
            
            team_leaders = []
            if role == "agent":
                team_leaders = get_team_leaders()
            team_leader_choices = [""] + [f"{tl[1]} (ID: {tl[0]})" for tl in team_leaders]
            team_leader = st.selectbox("Team Leader", team_leader_choices)
            
            available_skillsets = get_all_skillsets()
            skillset_names = [s[1] for s in available_skillsets]
            selected_skillsets = st.multiselect("Assign Skillsets", skillset_names)
            
            if st.form_submit_button("Add User"):
                if username and password:
                    # Convert skillset names to IDs
                    skillset_ids = []
                    for name in selected_skillsets:
                        for s in available_skillsets:
                            if s[1] == name:
                                skillset_ids.append(s[0])
                                break
                    
                    # Convert team leader selection to ID
                    tl_id = None
                    if team_leader:
                        tl_id = int(team_leader.split("ID: ")[1].rstrip(")"))
                    
                    if add_user(username, password, role, tl_id, skillset_ids):
                        st.success("User added successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to add user (username may already exist)")
    
    st.subheader("Existing Users")
    users = get_all_users()
    if not users:
        st.info("No users in system")
    else:
        for u in users:
            u_id, username, role, tl_id, tl_name = u
            with st.expander(f"{username} ({role})"):
                cols = st.columns([3, 1])
                if tl_name:
                    cols[0].write(f"Team Leader: {tl_name}")
                
                # Show assigned skillsets
                skillsets = get_user_skillsets(u_id)
                if skillsets:
                    cols[0].write("Skillsets:")
                    for s in skillsets:
                        cols[0].write(f"- {s[1]}")
                
                if cols[1].button("Delete", key=f"del_user_{u_id}"):
                    if delete_user(u_id):
                        st.success("User deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete user")

def data_management():
    st.subheader("🧹 Data Management")
    
    with st.expander("❌ Clear All Requests"):
        with st.form("clear_requests_form"):
            st.warning("This will permanently delete ALL requests!")
            if st.form_submit_button("Clear All Requests"):
                if clear_all_requests():
                    st.success("All requests deleted!")
                    st.rerun()
                else:
                    st.error("Failed to clear requests")

    with st.expander("❌ Clear All Mistakes"):
        with st.form("clear_mistakes_form"):
            st.warning("This will permanently delete ALL mistakes!")
            if st.form_submit_button("Clear All Mistakes"):
                if clear_all_mistakes():
                    st.success("All mistakes deleted!")
                    st.rerun()
                else:
                    st.error("Failed to clear mistakes")

    with st.expander("❌ Clear All Chat Messages"):
        with st.form("clear_chat_form"):
            st.warning("This will permanently delete ALL chat messages!")
            if st.form_submit_button("Clear All Chat"):
                if clear_all_group_messages():
                    st.success("All chat messages deleted!")
                    st.rerun()
                else:
                    st.error("Failed to clear chat messages")

    with st.expander("❌ Clear All HOLD Images"):
        with st.form("clear_hold_form"):
            st.warning("This will permanently delete ALL HOLD images!")
            if st.form_submit_button("Clear All HOLD Images"):
                if clear_hold_images():
                    st.success("All HOLD images deleted!")
                    st.rerun()
                else:
                    st.error("Failed to clear HOLD images")

    with st.expander("❌ Clear All Break Bookings"):
        with st.form("clear_breaks_form"):
            st.warning("This will permanently delete ALL break bookings!")
            if st.form_submit_button("Clear All Break Bookings"):
                if clear_all_break_bookings():
                    st.success("All break bookings deleted!")
                    st.rerun()
                else:
                    st.error("Failed to clear break bookings")

    with st.expander("💣 Clear ALL Data"):
        with st.form("nuclear_form"):
            st.error("THIS WILL DELETE EVERYTHING IN THE SYSTEM!")
            if st.form_submit_button("🚨 Execute Full System Wipe"):
                try:
                    clear_all_requests()
                    clear_all_mistakes()
                    clear_all_group_messages()
                    clear_hold_images()
                    clear_all_break_bookings()
                    st.success("All system data deleted!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error during deletion: {str(e)}")

# --------------------------
# Main App Logic
# --------------------------

def main():
    setup_page()
    init_db()
    
    if not st.session_state.get("authenticated"):
        login_section()
    else:
        if is_killswitch_enabled():
            st.markdown("""
<div class="killswitch-active">
    <h3>&#x26A0; SYSTEM LOCKED &#x26A0;</h3>
    <p>The system is currently in read-only mode.</p>
</div>
""", unsafe_allow_html=True)
        
        show_notifications()
        render_sidebar()
        
        if st.session_state.current_section == "requests":
            requests_section()
        elif st.session_state.current_section == "dashboard":
            dashboard_section()
        elif st.session_state.current_section == "breaks":
            breaks_section()
        elif st.session_state.current_section == "hold":
            hold_section()
        elif st.session_state.current_section == "mistakes":
            mistakes_section()
        elif st.session_state.current_section == "chat":
            chat_section()
        elif st.session_state.current_section == "admin":
            admin_section()

if __name__ == "__main__":
    main()
