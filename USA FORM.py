import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import os
import re
from PIL import Image
import io

# --------------------------
# Database Functions (Unchanged)
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

# ... (Keep all other database functions exactly as in original) ...

# --------------------------
# Streamlit App Configuration
# --------------------------

st.set_page_config(
    page_title="Request Management System",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    :root {
        --primary: #2F4F4F;
        --secondary: #4682B4;
        --background: #F8F9FA;
        --card-bg: #FFFFFF;
    }
    
    .stApp { background-color: var(--background); }
    
    [data-testid="stSidebar"] { 
        background-color: var(--card-bg);
        box-shadow: 2px 0 15px rgba(0,0,0,0.1);
    }
    
    .stButton>button {
        background-color: var(--secondary);
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        opacity: 0.9;
        transform: translateY(-1px);
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
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
    }
    
    .pending { background: #FFF3E0; color: #EF6C00; }
    .completed { background: #E8F5E9; color: #2E7D32; }
    
    .system-alert {
        background: #FFEBEE;
        border-left: 4px solid #D32F2F;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 6px;
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

# --------------------------
# Authentication Page
# --------------------------

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; margin-bottom: 2rem; color: var(--primary);'>🔐 Request Management System</h1>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("""
            <div style='background: var(--card-bg); padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>
                <h2 style='color: var(--primary); margin-bottom: 1.5rem;'>System Access</h2>
            """, unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your credentials")
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
                        st.warning("Please provide both username and password")
            
            st.markdown("</div>", unsafe_allow_html=True)

# --------------------------
# Main Application
# --------------------------

else:
    # System status banner
    if is_killswitch_enabled():
        st.markdown("""
        <div class='system-alert'>
            <h3 style='margin: 0; color: #D32F2F;'>⚠️ System Lock Active</h3>
            <p style='margin: 0.5rem 0 0;'>All write operations are disabled. Contact system administrator.</p>
        </div>
        """, unsafe_allow_html=True)

    # Sidebar Navigation
    with st.sidebar:
        st.markdown(f"""
        <div style='background: var(--background); padding: 1rem; border-radius: 10px; margin-bottom: 2rem;'>
            <div style='font-size: 1.1rem; font-weight: 500;'>👤 {st.session_state.username}</div>
            <div style='color: #666; font-size: 0.9rem;'>{st.session_state.role.capitalize()} Access</div>
        </div>
        """, unsafe_allow_html=True)
        
        nav_items = {
            "requests": ("📥", "Request Management"),
            "hold": ("🖼️", "Media Hold"),
            "mistakes": ("⚠️", "Quality Control"),
            "chat": ("💬", "Team Communication"),
            "admin": ("⚙️", "Administration")
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

    # --------------------------
    # Main Content Sections
    # --------------------------

    st.markdown(f"<h1 style='color: var(--primary);'>{nav_items[st.session_state.current_section][0]} {nav_items[st.session_state.current_section][1]}</h1>", unsafe_allow_html=True)

    # Requests Section
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
                                    st.success("Request submitted successfully!")
            else:
                st.warning("Submission disabled during system lock")
        
        with col2:
            st.markdown("### 📋 Active Requests")
            requests = get_requests()
            
            if not requests:
                st.markdown("<div class='card'>No active requests found</div>", unsafe_allow_html=True)
            
            for req in requests:
                req_id, agent, req_type, identifier, comment, timestamp, completed = req
                status = "completed" if completed else "pending"
                
                st.markdown(f"""
                <div class='card'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                        <h3 style='margin: 0;'>#{req_id} - {req_type}</h3>
                        <span class='status-indicator {status}'>
                            {'✅' if completed else '🔄'} {status.capitalize()}
                        </span>
                    </div>
                    <p><strong>Identifier:</strong> {identifier}</p>
                    <p><strong>Details:</strong> {comment}</p>
                    <div style='color: #666; font-size: 0.9rem; margin-top: 1rem;'>
                        Submitted by {agent} at {timestamp.split()[1]}
                    </div>
                </div>
                """, unsafe_allow_html=True)

       # Ticket Mistakes Section
    elif st.session_state.current_section == "mistakes":
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if not is_killswitch_enabled():
                with st.container():
                    st.markdown("### ⚠️ Report Quality Issue")
                    with st.form("mistake_form"):
                        ticket_id = st.text_input("Ticket ID")
                        agent_name = st.text_input("Agent Name")
                        error_description = st.text_area("Issue Description", height=150)
                        
                        if st.form_submit_button("Submit Report"):
                            if ticket_id and agent_name and error_description:
                                if add_mistake(st.session_state.username, agent_name, ticket_id, error_description):
                                    st.success("Issue reported successfully!")
            else:
                st.warning("Reporting disabled during system lock")
        
        with col2:
            st.markdown("### 📋 Quality Issues Log")
            mistakes = get_mistakes()
            
            if not mistakes:
                st.markdown("<div class='card'>No quality issues reported</div>", unsafe_allow_html=True)
            
            for mistake in mistakes:
                mistake_id, team_leader, agent_name, ticket_id, error_desc, timestamp = mistake
                
                st.markdown(f"""
                <div class='card'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                        <h3 style='margin: 0;'>Issue #{mistake_id}</h3>
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

    # Group Chat Section
    elif st.session_state.current_section == "chat":
        st.markdown("### 💬 Team Communications")
        
        # Chat Messages
        messages = get_group_messages()
        for msg in reversed(messages):
            msg_id, sender, message, timestamp, mentions = msg
            is_mentioned = st.session_state.username in (mentions.split(',') if mentions else False)
            
            st.markdown(f"""
            <div class='card' style='{"background: #E3F2FD; border-left: 4px solid #2196F3;" if is_mentioned else ""}'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                    <div style='font-weight: 500;'>{sender}</div>
                    <small style='color: #666;'>{timestamp.split()[1]}</small>
                </div>
                <div style='color: #333;'>
                    {re.sub(r'@(\w+)', r'<span style="color: #1976D2;">@\1</span>', message)}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Message Input
        if not is_killswitch_enabled():
            with st.form("chat_form"):
                message = st.text_input("Type your message (use @username to mention)")
                
                if st.form_submit_button("Send Message"):
                    if message:
                        if send_group_message(st.session_state.username, message):
                            st.rerun()
        else:
            st.warning("Messaging disabled during system lock")

    # Admin Panel Section
    elif st.session_state.current_section == "admin" and st.session_state.role == "admin":
        tab1, tab2, tab3 = st.tabs(["👥 User Management", "⚙️ System Controls", "🗑️ Data Maintenance"])
        
        with tab1:
            st.markdown("### User Accounts Management")
            
            if not is_killswitch_enabled():
                with st.expander("➕ Add New User", expanded=True):
                    with st.form("add_user_form"):
                        new_username = st.text_input("Username")
                        new_password = st.text_input("Password", type="password")
                        new_role = st.selectbox("Access Level", ["agent", "admin"])
                        
                        if st.form_submit_button("Create User"):
                            if new_username and new_password:
                                if add_user(new_username, new_password, new_role):
                                    st.success("User account created successfully!")
            
            st.markdown("### Active Users List")
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
                    if col2.button("🔴 Initiate System Lock", type="secondary"):
                        toggle_killswitch(True)
                        st.rerun()
            else:
                st.warning("⚠️ Restricted to system administrator")
        
        with tab3:
            st.markdown("### Data Maintenance")
            st.markdown("<div class='system-alert'>⚠️ These actions are irreversible</div>", unsafe_allow_html=True)
            
            cols = st.columns(2)
            with cols[0]:
                if st.button("Clear All Requests"):
                    clear_all_requests()
            with cols[1]:
                if st.button("Clear Quality Issues"):
                    clear_all_mistakes()
            
            cols = st.columns(2)
            with cols[0]:
                if st.button("Clear Chat History"):
                    clear_all_group_messages()
            with cols[1]:
                if st.button("Clear Media Hold"):
                    clear_hold_images()

    # Media Hold Section
    elif st.session_state.current_section == "hold":
        if st.session_state.role == "admin":
            if not is_killswitch_enabled():
                with st.container():
                    st.markdown("### 📤 Upload to Media Hold")
                    uploaded_file = st.file_uploader("Select image file", type=["png", "jpg", "jpeg"])
                    
                    if uploaded_file is not None:
                        if st.button("Confirm Upload"):
                            image_data = uploaded_file.read()
                            if add_hold_image(st.session_state.username, image_data):
                                st.success("Image uploaded successfully!")
            else:
                st.warning("Uploads disabled during system lock")
        else:
            st.warning("🔒 Media upload requires administrator privileges")

        st.markdown("### 📥 Held Media Files")
        hold_images = get_hold_images()
        
        if not hold_images:
            st.markdown("<div class='card'>No images in media hold</div>", unsafe_allow_html=True)
        
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
                st.image(image, use_column_width=True)
            except:
                st.error(f"Error displaying image {img_id}")

if __name__ == "__main__":
    st.write("System initialized successfully")
