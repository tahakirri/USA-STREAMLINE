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
        cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, hashed_password))
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
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT CHECK(role IN ('agent', 'admin')))
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
            INSERT OR IGNORE INTO system_settings (id, killswitch_enabled) 
            VALUES (1, 0)
        """)
        
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

def is_killswitch_enabled():  # ADD THIS FUNCTION EARLY
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY DEFAULT 1,
                killswitch_enabled INTEGER DEFAULT 0)
        """)
        cursor.execute("SELECT killswitch_enabled FROM system_settings WHERE id = 1")
        result = cursor.fetchone()
        return bool(result[0]) if result else False
    except sqlite3.Error as e:
        st.error(f"Error checking killswitch: {e}")
        return False
    finally:
        if conn:
            conn.close()

def toggle_killswitch(enable):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO system_settings (id, killswitch_enabled) 
            VALUES (1, 0)
        """)
        cursor.execute("""
            UPDATE system_settings 
            SET killswitch_enabled = ?
            WHERE id = 1
        """, (1 if enable else 0,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Error toggling killswitch: {e}")
        return False
    finally:
        if conn:
            conn.close()

def add_request(agent_name, request_type, identifier, comment):
    if is_killswitch_enabled():
        st.error("System locked. Contact administrator.")
        return False
        
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
        st.error(f"Request submission failed: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_requests():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM requests ORDER BY timestamp DESC")
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to load requests: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_request_status(request_id, completed):
    if is_killswitch_enabled():
        st.error("System locked. Contact administrator.")
        return False
        
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
        return True
    except sqlite3.Error as e:
        st.error(f"Status update failed: {e}")
        return False
    finally:
        if conn:
            conn.close()

def add_mistake(team_leader, agent_name, ticket_id, error_description):
    if is_killswitch_enabled():
        st.error("System locked. Contact administrator.")
        return False
        
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
        st.error(f"Error reporting mistake: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_mistakes():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mistakes ORDER BY timestamp DESC")
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to load mistakes: {e}")
        return []
    finally:
        if conn:
            conn.close()

def send_group_message(sender, message):
    if is_killswitch_enabled():
        st.error("System locked. Contact administrator.")
        return False
        
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        mentions = re.findall(r'@(\w+)', message)
        cursor.execute("""
            INSERT INTO group_messages (sender, message, timestamp, mentions) 
            VALUES (?, ?, ?, ?)
        """, (sender, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ','.join(mentions)))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Message send failed: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_group_messages():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM group_messages ORDER BY timestamp DESC LIMIT 50")
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to load messages: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_all_users():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM users")
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"User load failed: {e}")
        return []
    finally:
        if conn:
            conn.close()

def add_user(username, password, role):
    if is_killswitch_enabled():
        st.error("System locked. Contact administrator.")
        return False
        
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
        st.error(f"User creation failed: {e}")
        return False
    finally:
        if conn:
            conn.close()

def delete_user(user_id):
    if is_killswitch_enabled():
        st.error("System locked. Contact administrator.")
        return False
        
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"User deletion failed: {e}")
        return False
    finally:
        if conn:
            conn.close()

def add_hold_image(uploader, image_data):
    if is_killswitch_enabled():
        st.error("System locked. Contact administrator.")
        return False
        
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hold_images (uploader, image_data, timestamp) 
            VALUES (?, ?, ?)
        """, (uploader, image_data, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Image upload failed: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_hold_images():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hold_images ORDER BY timestamp DESC")
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Image load failed: {e}")
        return []
    finally:
        if conn:
            conn.close()

def clear_hold_images():
    if is_killswitch_enabled():
        st.error("System locked. Contact administrator.")
        return False
        
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM hold_images")
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Image clearance failed: {e}")
        return False
    finally:
        if conn:
            conn.close()

def clear_all_requests():
    if is_killswitch_enabled():
        st.error("System locked. Contact administrator.")
        return False
        
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM requests")
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Request clearance failed: {e}")
        return False
    finally:
        if conn:
            conn.close()

def clear_all_mistakes():
    if is_killswitch_enabled():
        st.error("System locked. Contact administrator.")
        return False
        
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM mistakes")
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Mistake clearance failed: {e}")
        return False
    finally:
        if conn:
            conn.close()

def clear_all_group_messages():
    if is_killswitch_enabled():
        st.error("System locked. Contact administrator.")
        return False
        
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM group_messages")
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Message clearance failed: {e}")
        return False
    finally:
        if conn:
            conn.close()

# --------------------------
# Streamlit UI Configuration
# --------------------------

st.set_page_config(
    page_title="RMS Pro",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    :root {
        --primary: #2C3E50;
        --secondary: #3498DB;
        --background: #F8F9FA;
        --card-bg: #FFFFFF;
    }
    
    .stApp { background-color: var(--background); }
    
    [data-testid="stSidebar"] { 
        background-color: var(--card-bg);
        box-shadow: 2px 0 15px rgba(0,0,0,0.1);
    }
    
    .stButton>button {
        background-color: var(--secondary) !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover {
        opacity: 0.9;
        transform: translateY(-1px);
    }
    
    .card {
        background: var(--card-bg);
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid var(--secondary);
    }
    
    .status-indicator {
        font-size: 0.9rem;
        padding: 4px 12px;
        border-radius: 20px;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    
    .system-alert {
        background: #FFEBEE;
        border-left: 4px solid #D32F2F;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 6px;
    }
    
    .mention-highlight {
        background: #E3F2FD;
        border-left: 4px solid #2196F3;
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
# Authentication Page
# --------------------------

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; margin-bottom: 2rem; color: var(--primary);'>🔒 RMS Pro Login</h1>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("""
            <div style='background: var(--card-bg); padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>
                <h2 style='color: var(--primary); margin-bottom: 1.5rem;'>System Access</h2>
            """, unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter credentials")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                
                if st.form_submit_button("Authenticate", use_container_width=True):
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
                        st.warning("Both fields required")
            
            st.markdown("</div>", unsafe_allow_html=True)

# --------------------------
# Main Application
# --------------------------

else:
    if is_killswitch_enabled():
        st.markdown("""
        <div class='system-alert'>
            <h3 style='margin: 0; color: #D32F2F;'>⚠️ System Lock Active</h3>
            <p style='margin: 0.5rem 0 0;'>All modifications disabled. Contact administrator.</p>
        </div>
        """, unsafe_allow_html=True)

    with st.sidebar:
       st.markdown(
        f"<h1 style='color: var(--primary);'>{nav_items[st.session_state.current_section][0]} {nav_items[st.session_state.current_section][1]}</h1>",
        unsafe_allow_html=True
    )
        
        nav_items = {
            "requests": ("📥", "Requests"),
            "mistakes": ("⚠️", "Quality"),
            "chat": ("💬", "Comms"),
            "hold": ("🖼️", "Media"),
            "admin": ("⚙️", "Admin")
        }
        
        if st.session_state.role != "admin":
            del nav_items["admin"]
            
        for section, (icon, label) in nav_items.items():
            if st.button(
                f"{icon} {label}",
                use_container_width=True,
                key=f"nav_{section}"
            ):
                st.session_state.current_section = section
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

 st.markdown(
    f"<h1 style='color: var(--primary);'>{nav_items[st.session_state.current_section][0]} {nav_items[st.session_state.current_section][1]}</h1>",
    unsafe_allow_html=True
)


    if st.session_state.current_section == "requests":
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if not is_killswitch_enabled():
                with st.container():
                    st.markdown("### 📝 New Request")
                    with st.form("request_form"):
                        request_type = st.selectbox("Type", ["Email", "Phone", "Ticket ID"])
                        identifier = st.text_input("Identifier")
                        comment = st.text_area("Details", height=150)
                        
                        if st.form_submit_button("Submit Request"):
                            if identifier and comment:
                                if add_request(st.session_state.username, request_type, identifier, comment):
                                    st.success("Request submitted!")
            else:
                st.warning("Submission disabled")
        
        with col2:
            st.markdown("### 📋 Active Requests")
            requests = get_requests()
            
            if not requests:
                st.markdown("<div class='card'>No active requests</div>", unsafe_allow_html=True)
            
            for req in requests:
                req_id, agent, req_type, identifier, comment, timestamp, completed = req
                status = "completed" if completed else "pending"
                
                # Checkbox and status update
                checkbox_state = st.checkbox(
                    "Done",
                    value=bool(completed),
                    key=f"check_{req_id}",
                    help="Mark request as completed",
                    disabled=is_killswitch_enabled()
                )
                
                if checkbox_state != bool(completed):
                    update_request_status(req_id, checkbox_state)
                    st.rerun()
                
                st.markdown(f"""
                <div class='card'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                        <h3 style='margin: 0;'>#{req_id} - {req_type}</h3>
                        <span class='status-indicator {"completed" if completed else "pending"}'>
                            {'✅' if completed else '🔄'} {status.capitalize()}
                        </span>
                    </div>
                    <p><strong>Identifier:</strong> {identifier}</p>
                    <p><strong>Details:</strong> {comment}</p>
                    <div style='color: #666; font-size: 0.9rem; margin-top: 1rem;'>
                        {agent} • {timestamp.split()[0]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        for req in requests:
            req_id, agent, req_type, identifier, comment, timestamp, completed = req
            status = "completed" if completed else "pending"
            
            # Use a unique key for each checkbox
            checkbox_state = st.checkbox(
                "Done",
                value=bool(completed),
                key=f"check_{req_id}",
                help="Mark request as completed",
                disabled=is_killswitch_enabled()
            )
            
            # Update status when checkbox changes
            if checkbox_state != bool(completed):
                if update_request_status(req_id, checkbox_state):
                    st.rerun()
            
            st.markdown(f"""
            <div class='card'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                    <h3 style='margin: 0;'>#{req_id} - {req_type}</h3>
                    <span class='status-indicator {"completed" if completed else "pending"}'>
                        {'✅' if completed else '🔄'} {status.capitalize()}
                    </span>
                </div>
                <p><strong>Identifier:</strong> {identifier}</p>
                <p><strong>Details:</strong> {comment}</p>
                <div style='color: #666; font-size: 0.9rem; margin-top: 1rem;'>
                    {agent} • {timestamp.split()[0]}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            for req in requests:
                req_id, agent, req_type, identifier, comment, timestamp, completed = req
                status = "completed" if completed else "pending"
                
                st.markdown(f"""
                <div class='card'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                        <h3 style='margin: 0;'>#{req_id} - {req_type}</h3>
                        <span class='status-indicator {"completed" if completed else "pending"}'>
                            {'✅' if completed else '🔄'} {status.capitalize()}
                        </span>
                    </div>
                    <p><strong>Identifier:</strong> {identifier}</p>
                    <p><strong>Details:</strong> {comment}</p>
                    <div style='color: #666; font-size: 0.9rem; margin-top: 1rem;'>
                        {agent} • {timestamp.split()[0]}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Quality Section
    elif st.session_state.current_section == "mistakes":
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if not is_killswitch_enabled():
                with st.container():
                    st.markdown("### ⚠️ Report Issue")
                    with st.form("mistake_form"):
                        ticket_id = st.text_input("Ticket ID")
                        agent_name = st.text_input("Agent Name")
                        error_description = st.text_area("Description", height=150)
                        
                        if st.form_submit_button("Submit Report"):
                            if ticket_id and agent_name and error_description:
                                if add_mistake(st.session_state.username, agent_name, ticket_id, error_description):
                                    st.success("Report submitted!")
            else:
                st.warning("Reporting disabled")
        
        with col2:
            st.markdown("### 📋 Quality Log")
            mistakes = get_mistakes()
            
            if not mistakes:
                st.markdown("<div class='card'>No issues reported</div>", unsafe_allow_html=True)
            
            for mistake in mistakes:
                mistake_id, team_leader, agent_name, ticket_id, error_desc, timestamp = mistake
                
                st.markdown(f"""
                <div class='card'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                        <h3 style='margin: 0;'>Case #{mistake_id}</h3>
                        <span style='color: #666; font-size: 0.9rem;'>{timestamp.split()[0]}</span>
                    </div>
                    <p><strong>Agent:</strong> {agent_name}</p>
                    <p><strong>Ticket ID:</strong> {ticket_id}</p>
                    <p><strong>Description:</strong> {error_desc}</p>
                    <div style='color: #666; font-size: 0.9rem; margin-top: 1rem;'>
                        Reported by {team_leader}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Comms Section
    elif st.session_state.current_section == "chat":
        st.markdown("### 💬 Team Communications")
        
        messages = get_group_messages()
        for msg in reversed(messages):
            msg_id, sender, message, timestamp, mentions = msg
            is_mentioned = st.session_state.username in (mentions.split(',') if mentions else [])
            
            st.markdown(f"""
            <div class='card {"mention-highlight" if is_mentioned else ""}'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                    <div style='font-weight: 500;'>{sender}</div>
                    <small style='color: #666;'>{timestamp.split()[1]}</small>
                </div>
                <div style='color: #333;'>
                    {re.sub(r'@(\w+)', r'<span style="color: #1976D2;">@\1</span>', message)}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if not is_killswitch_enabled():
            with st.form("chat_form"):
                message = st.text_input("Type message (use @mention)")
                
                if st.form_submit_button("Send", use_container_width=True):
                    if message:
                        send_group_message(st.session_state.username, message)
                        st.rerun()
        else:
            st.warning("Messaging disabled")

    # Admin Section
    elif st.session_state.current_section == "admin" and st.session_state.role == "admin":
        tab1, tab2, tab3 = st.tabs(["👥 Users", "⚙️ System", "🗑️ Data"])
        
        with tab1:
            st.markdown("### User Management")
            
            if not is_killswitch_enabled():
                with st.expander("➕ Add User", expanded=True):
                    with st.form("add_user_form"):
                        new_username = st.text_input("Username")
                        new_password = st.text_input("Password", type="password")
                        new_role = st.selectbox("Role", ["agent", "admin"])
                        
                        if st.form_submit_button("Create User"):
                            if new_username and new_password:
                                add_user(new_username, new_password, new_role)
                                st.rerun()
            
            st.markdown("### Active Users")
            users = get_all_users()
            for user in users:
                cols = st.columns([4, 2, 1])
                cols[0].markdown(f"**{user[1]}**")
                cols[1].markdown(f"`{user[2]}`")
                if cols[2].button("Delete", key=f"del_{user[0]}"):
                    delete_user(user[0])
                    st.rerun()
        
        with tab2:
            st.markdown("### System Controls")
            
            if st.session_state.username.lower() == "taha kirri":
                current_status = is_killswitch_enabled()
                
                col1, col2 = st.columns(2)
                col1.markdown(f"""
                <div class='card'>
                    <h3 style='margin: 0 0 1rem 0;'>System Status</h3>
                    <div style='font-size: 1.5rem;'>
                        {"🔴 Locked" if current_status else "🟢 Operational"}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if current_status:
                    if col2.button("🟢 Restore System", type="primary"):
                        toggle_killswitch(False)
                        st.rerun()
                else:
                    if col2.button("🔴 Activate Lock", type="secondary"):
                        toggle_killswitch(True)
                        st.rerun()
            else:
                st.warning("Restricted access")
        
        with tab3:
            st.markdown("### Data Management")
            st.markdown("<div class='system-alert'>⚠️ Irreversible actions</div>", unsafe_allow_html=True)
            
            cols = st.columns(2)
            with cols[0]:
                if st.button("Clear Requests"):
                    clear_all_requests()
            with cols[1]:
                if st.button("Clear Quality Logs"):
                    clear_all_mistakes()
            
            cols = st.columns(2)
            with cols[0]:
                if st.button("Clear Chat"):
                    clear_all_group_messages()
            with cols[1]:
                if st.button("Clear Media"):
                    clear_hold_images()

    # Media Section
    elif st.session_state.current_section == "hold":
        if st.session_state.role == "admin":
            if not is_killswitch_enabled():
                with st.container():
                    st.markdown("### 📤 Upload Media")
                    uploaded_file = st.file_uploader("Select file", type=["png", "jpg", "jpeg"])
                    
                    if uploaded_file and st.button("Confirm Upload"):
                        image_data = uploaded_file.read()
                        add_hold_image(st.session_state.username, image_data)
                        st.rerun()
            else:
                st.warning("Uploads disabled")
        else:
            st.warning("Administrator access required")

        st.markdown("### 📥 Stored Media")
        hold_images = get_hold_images()
        
        if not hold_images:
            st.markdown("<div class='card'>No media files</div>", unsafe_allow_html=True)
        
        for img in hold_images:
            img_id, uploader, image_data, timestamp = img
            try:
                image = Image.open(io.BytesIO(image_data))
                st.markdown(f"""
                <div class='card'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                        <h3 style='margin: 0;'>Media #{img_id}</h3>
                        <small style='color: #666;'>{timestamp.split()[0]}</small>
                    </div>
                    <p><strong>Uploaded by:</strong> {uploader}</p>
                </div>
                """, unsafe_allow_html=True)
                st.image(image, use_container_width=True)
            except:
                st.error(f"Error displaying image {img_id}")

if __name__ == "__main__":
    st.write("System ready")
