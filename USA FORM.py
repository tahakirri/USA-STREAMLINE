import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, timedelta
import os
import re
from PIL import Image
import io
import pandas as pd
import json

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
        cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", 
                      (username, hashed_password))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT CHECK(role IN ('agent', 'admin')),
                team TEXT,
                shift TEXT)
        """)
        
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
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_leader TEXT,
                agent_name TEXT,
                ticket_id TEXT,
                error_description TEXT,
                timestamp TEXT)
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                message TEXT,
                timestamp TEXT,
                mentions TEXT)
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hold_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uploader TEXT,
                image_data BLOB,
                timestamp TEXT)
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY DEFAULT 1,
                killswitch_enabled INTEGER DEFAULT 0)
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS breaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                break_name TEXT,
                start_time TEXT,
                end_time TEXT,
                max_users INTEGER,
                current_users INTEGER DEFAULT 0,
                created_by TEXT,
                timestamp TEXT,
                shift TEXT,
                team TEXT,
                is_template INTEGER DEFAULT 0,
                template_name TEXT)
        """)
        
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
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS break_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT UNIQUE,
                template_data TEXT,
                created_by TEXT,
                timestamp TEXT)
        """)
        
        cursor.execute("INSERT OR IGNORE INTO system_settings (id, killswitch_enabled) VALUES (1, 0)")
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, password, role, team, shift) 
            VALUES (?, ?, ?, ?, ?)
        """, ("taha kirri", hash_password("arise@99"), "admin", "all", "all"))
        
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

def get_all_users():
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, team, shift FROM users")
        return cursor.fetchall()
    finally:
        conn.close()

def add_user(username, password, role, team="all", shift="all"):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role, team, shift) VALUES (?, ?, ?, ?, ?)",
                      (username, hash_password(password), role, team, shift))
        conn.commit()
        return True
    finally:
        conn.close()

def update_user(user_id, username, role, team, shift):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET username = ?, role = ?, team = ?, shift = ?
            WHERE id = ?
        """, (username, role, team, shift, user_id))
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

def add_break_slot(break_name, start_time, end_time, max_users, created_by, shift="all", team="all", is_template=False, template_name=None):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO breaks (
                break_name, start_time, end_time, max_users, created_by, timestamp,
                shift, team, is_template, template_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            break_name, start_time, end_time, max_users, created_by,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            shift, team, 1 if is_template else 0, template_name
        ))
        conn.commit()
        return True
    finally:
        conn.close()

def get_all_break_slots(team=None, shift=None, is_template=False):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        
        query = "SELECT * FROM breaks WHERE is_template = ?"
        params = [1 if is_template else 0]
        
        if team and team != "all":
            query += " AND (team = ? OR team = 'all')"
            params.append(team)
            
        if shift and shift != "all":
            query += " AND (shift = ? OR shift = 'all')"
            params.append(shift)
            
        query += " ORDER BY start_time"
        
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    finally:
        conn.close()

def get_available_break_slots(date, team=None, shift=None):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        
        query = """
            SELECT b.* 
            FROM breaks b
            WHERE b.max_users > (
                SELECT COUNT(*) 
                FROM break_bookings bb 
                WHERE bb.break_id = b.id 
                AND bb.booking_date = ?
            )
            AND b.is_template = 0
        """
        params = [date]
        
        if team and team != "all":
            query += " AND (b.team = ? OR b.team = 'all')"
            params.append(team)
            
        if shift and shift != "all":
            query += " AND (b.shift = ? OR b.shift = 'all')"
            params.append(shift)
            
        query += " ORDER BY b.start_time"
        
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    finally:
        conn.close()

def book_break_slot(break_id, user_id, username, booking_date):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO break_bookings (break_id, user_id, username, booking_date, timestamp) 
            VALUES (?, ?, ?, ?, ?)
        """, (break_id, user_id, username, booking_date,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    finally:
        conn.close()

def get_user_bookings(username, date):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT bb.*, b.break_name, b.start_time, b.end_time
            FROM break_bookings bb
            JOIN breaks b ON bb.break_id = b.id
            WHERE bb.username = ? AND bb.booking_date = ?
        """, (username, date))
        return cursor.fetchall()
    finally:
        conn.close()

def get_all_bookings(date):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT bb.*, b.break_name, b.start_time, b.end_time, u.role, u.team, u.shift
            FROM break_bookings bb
            JOIN breaks b ON bb.break_id = b.id
            JOIN users u ON bb.user_id = u.id
            WHERE bb.booking_date = ?
            ORDER BY b.start_time, bb.username
        """, (date,))
        return cursor.fetchall()
    finally:
        conn.close()

def delete_break_slot(break_id):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
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
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM break_bookings")
        conn.commit()
        return True
    finally:
        conn.close()

def save_break_template(template_name, break_slots, created_by):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        
        # First mark existing template breaks as non-template
        cursor.execute("UPDATE breaks SET is_template = 0 WHERE template_name = ?", (template_name,))
        
        # Save the template metadata
        cursor.execute("""
            INSERT OR REPLACE INTO break_templates (template_name, template_data, created_by, timestamp)
            VALUES (?, ?, ?, ?)
        """, (
            template_name,
            json.dumps(break_slots),
            created_by,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        
        # Save each break slot as a template
        for slot in break_slots:
            add_break_slot(
                slot['break_name'],
                slot['start_time'],
                slot['end_time'],
                slot['max_users'],
                created_by,
                slot.get('shift', 'all'),
                slot.get('team', 'all'),
                True,
                template_name
            )
        
        conn.commit()
        return True
    finally:
        conn.close()

def get_break_templates():
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM break_templates ORDER BY template_name")
        return cursor.fetchall()
    finally:
        conn.close()

def apply_break_template(template_name, target_date, created_by):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        
        # Get the template data
        cursor.execute("SELECT template_data FROM break_templates WHERE template_name = ?", (template_name,))
        result = cursor.fetchone()
        if not result:
            return False
            
        break_slots = json.loads(result[0])
        
        # Clear existing breaks for this date
        cursor.execute("""
            DELETE FROM breaks 
            WHERE is_template = 0 
            AND date(timestamp) = date(?)
        """, (target_date,))
        
        # Create the breaks for the target date
        for slot in break_slots:
            add_break_slot(
                slot['break_name'],
                slot['start_time'],
                slot['end_time'],
                slot['max_users'],
                created_by,
                slot.get('shift', 'all'),
                slot.get('team', 'all')
            )
        
        conn.commit()
        return True
    finally:
        conn.close()

def get_user_team_and_shift(username):
    conn = sqlite3.connect("data/requests.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT team, shift FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        return result if result else ("all", "all")
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
    .break-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        margin-right: 5px;
    }
    .team-badge {
        background-color: #3b82f6;
        color: white;
    }
    .shift-badge {
        background-color: #10b981;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state.update({
        "authenticated": False,
        "role": None,
        "username": None,
        "current_section": "requests",
        "last_request_count": 0,
        "last_mistake_count": 0,
        "last_message_ids": []
    })

init_db()

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏢 Request Management System")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if username and password:
                    role = authenticate(username, password)
                    if role:
                        st.session_state.update({
                            "authenticated": True,
                            "role": role,
                            "username": username,
                            "last_request_count": len(get_requests()),
                            "last_mistake_count": len(get_mistakes()),
                            "last_message_ids": [msg[0] for msg in get_group_messages()]
                        })
                        st.rerun()
                    else:
                        st.error("Invalid credentials")

else:
    if is_killswitch_enabled():
        st.markdown("""
        <div class="killswitch-active">
            <h3>⚠️ SYSTEM LOCKED ⚠️</h3>
            <p>The system is currently in read-only mode.</p>
        </div>
        """, unsafe_allow_html=True)

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

    show_notifications()

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

    st.title(st.session_state.current_section.title())

    if st.session_state.current_section == "requests":
        if not is_killswitch_enabled():
            with st.expander("➕ Submit New Request"):
                with st.form("request_form"):
                    cols = st.columns([1, 3])
                    request_type = cols[0].selectbox("Type", ["Email", "Phone", "Ticket"])
                    identifier = cols[1].text_input("Identifier")
                    comment = st.text_area("Comment")
                    if st.form_submit_button("Submit"):
                        if identifier and comment:
                            add_request(st.session_state.username, request_type, identifier, comment)
        
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

    elif st.session_state.current_section == "dashboard":
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

    elif st.session_state.current_section == "breaks":
        today = datetime.now().strftime("%Y-%m-%d")
        selected_date = st.date_input("Select date", datetime.now())
        formatted_date = selected_date.strftime("%Y-%m-%d")
        
        # Get user's team and shift for filtering
        user_team, user_shift = get_user_team_and_shift(st.session_state.username)
        
        if st.session_state.role == "admin":
            st.subheader("Admin: Break Schedule Management")
            
            with st.expander("➕ Add New Break Slot"):
                with st.form("add_break_form"):
                    cols = st.columns(3)
                    break_name = cols[0].text_input("Break Name")
                    start_time = cols[1].time_input("Start Time")
                    end_time = cols[2].time_input("End Time")
                    
                    cols = st.columns(2)
                    max_users = cols[0].number_input("Max Users", min_value=1, value=1)
                    shift = cols[1].selectbox("Shift", ["all", "first", "second"])
                    
                    cols = st.columns(2)
                    team = cols[0].selectbox("Team", ["all", "english", "spanish"])
                    is_template = cols[1].checkbox("Save as template")
                    template_name = st.text_input("Template Name (if saving as template)") if is_template else None
                    
                    if st.form_submit_button("Add Break Slot"):
                        if break_name:
                            add_break_slot(
                                break_name,
                                start_time.strftime("%H:%M"),
                                end_time.strftime("%H:%M"),
                                max_users,
                                st.session_state.username,
                                shift,
                                team,
                                is_template,
                                template_name
                            )
                            st.rerun()
            
            with st.expander("📁 Manage Templates"):
                st.subheader("Save Current Breaks as Template")
                with st.form("save_template_form"):
                    template_name = st.text_input("Template Name")
                    if st.form_submit_button("Save as Template"):
                        current_breaks = get_all_break_slots(is_template=False)
                        break_slots = []
                        for b in current_breaks:
                            break_slots.append({
                                'break_name': b[1],
                                'start_time': b[2],
                                'end_time': b[3],
                                'max_users': b[4],
                                'shift': b[7],
                                'team': b[8]
                            })
                        if save_break_template(template_name, break_slots, st.session_state.username):
                            st.success("Template saved successfully!")
                            st.rerun()
                
                st.subheader("Apply Template")
                templates = get_break_templates()
                if templates:
                    selected_template = st.selectbox("Select Template", [t[1] for t in templates])
                    apply_date = st.date_input("Apply to date", datetime.now())
                    if st.button("Apply Template"):
                        if apply_break_template(selected_template, apply_date.strftime("%Y-%m-%d"), st.session_state.username):
                            st.success(f"Template '{selected_template}' applied successfully!")
                            st.rerun()
                else:
                    st.info("No templates available")
            
            st.subheader("Current Break Schedule")
            breaks = get_all_break_slots(is_template=False)
            for b in breaks:
                b_id, name, start, end, max_u, curr_u, created_by, ts, shift, team, is_template, template_name = b
                with st.container():
                    cols = st.columns([3, 2, 2, 1, 1])
                    cols[0].markdown(f"""
                    <div>
                        <strong>{name}</strong> ({start} - {end})
                        <span class="break-badge team-badge">{team}</span>
                        <span class="break-badge shift-badge">{shift}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    cols[1].write(f"Max: {max_u}")
                    cols[2].write(f"Created by: {created_by}")
                    
                    if cols[3].button("✏️", key=f"edit_{b_id}"):
                        pass  # Add edit functionality if needed
                    
                    if cols[4].button("❌", key=f"del_{b_id}"):
                        delete_break_slot(b_id)
                        st.rerun()
            
            st.markdown("---")
            st.subheader("All Bookings for Selected Date")
            bookings = get_all_bookings(formatted_date)
            if bookings:
                for b in bookings:
                    b_id, break_id, user_id, username, date, ts, break_name, start, end, role, team, shift = b
                    st.markdown(f"""
                    <div>
                        {username} ({role}) - {break_name} ({start} - {end})
                        <span class="break-badge team-badge">{team}</span>
                        <span class="break-badge shift-badge">{shift}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No bookings for selected date")
            
            if st.button("Clear All Bookings", key="clear_all_bookings"):
                clear_all_break_bookings()
                st.rerun()
        
        else:
            st.subheader("Available Break Slots")
            available_breaks = get_available_break_slots(formatted_date, user_team, user_shift)
            
            if available_breaks:
                for b in available_breaks:
                    b_id, name, start, end, max_u, curr_u, created_by, ts, shift, team, is_template, template_name = b
                    
                    # Get current bookings for this break
                    conn = sqlite3.connect("data/requests.db")
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM break_bookings 
                        WHERE break_id = ? AND booking_date = ?
                    """, (b_id, formatted_date))
                    booked_count = cursor.fetchone()[0]
                    conn.close()
                    
                    remaining = max_u - booked_count
                    
                    with st.container():
                        cols = st.columns([3, 2, 1])
                        cols[0].markdown(f"""
                        <div>
                            <strong>{name}</strong> ({start} - {end})
                            <span class="break-badge team-badge">{team}</span>
                            <span class="break-badge shift-badge">{shift}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        cols[1].write(f"Available slots: {remaining}/{max_u}")
                        
                        if cols[2].button("Book", key=f"book_{b_id}"):
                            # Get user ID
                            conn = sqlite3.connect("data/requests.db")
                            cursor = conn.cursor()
                            cursor.execute("SELECT id FROM users WHERE username = ?", 
                                         (st.session_state.username,))
                            user_id = cursor.fetchone()[0]
                            conn.close()
                            
                            book_break_slot(b_id, user_id, st.session_state.username, formatted_date)
                            st.rerun()
            
            st.markdown("---")
            st.subheader("Your Bookings")
            user_bookings = get_user_bookings(st.session_state.username, formatted_date)
            
            if user_bookings:
                for b in user_bookings:
                    b_id, break_id, user_id, username, date, ts, break_name, start, end = b
                    st.write(f"{break_name} ({start} - {end})")
            else:
                st.info("You have no bookings for selected date")

    elif st.session_state.current_section == "mistakes":
        if not is_killswitch_enabled():
            with st.expander("➕ Report New Mistake"):
                with st.form("mistake_form"):
                    cols = st.columns(3)
                    agent_name = cols[0].text_input("Agent Name")
                    ticket_id = cols[1].text_input("Ticket ID")
                    error_description = st.text_area("Error Description")
                    if st.form_submit_button("Submit"):
                        if agent_name and ticket_id and error_description:
                            add_mistake(st.session_state.username, agent_name, ticket_id, error_description)
        
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

    elif st.session_state.current_section == "chat":
        messages = get_group_messages()
        for msg in reversed(messages):
            msg_id, sender, message, ts, mentions = msg
            is_mentioned = st.session_state.username in (mentions.split(',') if mentions else [])
            st.markdown(f"""
            <div class="message {'sent' if sender == st.session_state.username else 'received'}"
                style="{'background-color: #3b82f6' if is_mentioned else ''}">
                <strong>{sender}</strong>: {message}<br>
                <small>{ts}</small>
            </div>
            """, unsafe_allow_html=True)
        
        if not is_killswitch_enabled():
            with st.form("chat_form"):
                message = st.text_input("Type your message...")
                if st.form_submit_button("Send"):
                    if message:
                        send_group_message(st.session_state.username, message)
                        st.rerun()

    elif st.session_state.current_section == "hold":
        if st.session_state.role == "admin" and not is_killswitch_enabled():
            with st.expander("📤 Upload Image"):
                img = st.file_uploader("Choose image", type=["jpg", "png", "jpeg"])
                if img:
                    add_hold_image(st.session_state.username, img.read())
        
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

    elif st.session_state.current_section == "admin" and st.session_state.role == "admin":
        if st.session_state.username.lower() == "taha kirri":
            st.subheader("🚨 System Killswitch")
            current = is_killswitch_enabled()
            status = "🔴 ACTIVE" if current else "🟢 INACTIVE"
            st.write(f"Current Status: {status}")
            
            col1, col2 = st.columns(2)
            if current:
                if col1.button("Deactivate Killswitch"):
                    toggle_killswitch(False)
                    st.rerun()
            else:
                if col1.button("Activate Killswitch"):
                    toggle_killswitch(True)
                    st.rerun()
            st.markdown("---")
        
        st.subheader("🧹 Data Management")
        
        with st.expander("❌ Clear All Requests"):
            with st.form("clear_requests_form"):
                st.warning("This will permanently delete ALL requests!")
                if st.form_submit_button("Clear All Requests"):
                    if clear_all_requests():
                        st.success("All requests deleted!")
                        st.rerun()

        with st.expander("❌ Clear All Mistakes"):
            with st.form("clear_mistakes_form"):
                st.warning("This will permanently delete ALL mistakes!")
                if st.form_submit_button("Clear All Mistakes"):
                    if clear_all_mistakes():
                        st.success("All mistakes deleted!")
                        st.rerun()

        with st.expander("❌ Clear All Chat Messages"):
            with st.form("clear_chat_form"):
                st.warning("This will permanently delete ALL chat messages!")
                if st.form_submit_button("Clear All Chat"):
                    if clear_all_group_messages():
                        st.success("All chat messages deleted!")
                        st.rerun()

        with st.expander("❌ Clear All HOLD Images"):
            with st.form("clear_hold_form"):
                st.warning("This will permanently delete ALL HOLD images!")
                if st.form_submit_button("Clear All HOLD Images"):
                    if clear_hold_images():
                        st.success("All HOLD images deleted!")
                        st.rerun()

        with st.expander("❌ Clear All Break Bookings"):
            with st.form("clear_breaks_form"):
                st.warning("This will permanently delete ALL break bookings!")
                if st.form_submit_button("Clear All Break Bookings"):
                    if clear_all_break_bookings():
                        st.success("All break bookings deleted!")
                        st.rerun()

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
        
        st.markdown("---")
        st.subheader("User Management")
        if not is_killswitch_enabled():
            with st.form("add_user"):
                cols = st.columns(2)
                user = cols[0].text_input("Username")
                pwd = cols[1].text_input("Password", type="password")
                
                cols = st.columns(3)
                role = cols[0].selectbox("Role", ["agent", "admin"])
                team = cols[1].selectbox("Team", ["all", "english", "spanish"])
                shift = cols[2].selectbox("Shift", ["all", "first", "second"])
                
                if st.form_submit_button("Add User"):
                    if user and pwd:
                        add_user(user, pwd, role, team, shift)
                        st.rerun()
        
        st.subheader("Existing Users")
        users = get_all_users()
        for uid, uname, urole, uteam, ushift in users:
            cols = st.columns([2, 1, 1, 1, 1])
            cols[0].write(uname)
            cols[1].write(urole)
            cols[2].markdown(f'<span class="break-badge team-badge">{uteam}</span>', unsafe_allow_html=True)
            cols[3].markdown(f'<span class="break-badge shift-badge">{ushift}</span>', unsafe_allow_html=True)
            
            if cols[4].button("Delete", key=f"del_{uid}") and not is_killswitch_enabled():
                delete_user(uid)
                st.rerun()

if __name__ == "__main__":
    st.write("Request Management System")
