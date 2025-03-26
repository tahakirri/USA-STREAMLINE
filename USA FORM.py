import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
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

# Set page config with your preferred settings
st.set_page_config(
    page_title="Request Management System", 
    page_icon=":office:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS for styling
st.markdown("""
<style>
    /* Main app background */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e9ecef;
    }
    
    /* Button styling */
    .stButton>button {
        background-color: #3b82f6;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #2563eb;
        transform: translateY(-1px);
    }
    
    /* Input field styling */
    .stTextInput>div>div>input, 
    .stSelectbox>div>div>select, 
    .stTextArea>div>div>textarea {
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        padding: 0.5rem;
    }
    
    /* Card-like containers */
    .card {
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    
    /* Message bubbles */
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
    .timestamp {
        font-size: 0.75rem;
        color: #6b7280;
        text-align: right;
        margin-top: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.last_message_count = 0
    st.session_state.last_request_count = 0
    st.session_state.current_section = "requests"

# Initialize database
init_db()

# Login Page
if not st.session_state.authenticated:
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏢 Request Management System")
        st.markdown("---")
        
        with st.container():
            st.header("Login")
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
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
        
        # Navigation options
        nav_options = [
            ("📋 Requests", "requests"),
            ("🖼️ HOLD", "hold"),
            ("❌ Ticket Mistakes", "mistakes"),
            ("💬 Group Chat", "chat")
        ]
        
        if st.session_state.role == "admin":
            nav_options.append(("⚙️ Admin Panel", "admin"))
        
        # Display navigation buttons
        for option, value in nav_options:
            if st.button(option, key=f"nav_{value}"):
                st.session_state.current_section = value
        
        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.role = None
            st.session_state.username = None
            st.rerun()
    
    # Main Content Area
    st.title(f"{'📋' if st.session_state.current_section == 'requests' else ''} "
             f"{'🖼️' if st.session_state.current_section == 'hold' else ''} "
             f"{'❌' if st.session_state.current_section == 'mistakes' else ''} "
             f"{'💬' if st.session_state.current_section == 'chat' else ''} "
             f"{'⚙️' if st.session_state.current_section == 'admin' else ''} "
             f"{st.session_state.current_section.title()}")
    
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
                            show_notification("New request submitted!")
                        else:
                            st.error("Failed to submit request")
                    else:
                        st.warning("Please fill all required fields")
        
        st.subheader("All Requests")
        requests = get_requests()
        if requests:
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
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <h4>Request #{req_id} - {req_type}</h4>
                                <small>{timestamp}</small>
                            </div>
                            <p><strong>Agent:</strong> {agent}</p>
                            <p><strong>Identifier:</strong> {identifier}</p>
                            <p><strong>Comment:</strong> {comment}</p>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("No requests found.")

    # HOLD Section
    elif st.session_state.current_section == "hold":
        with st.container():
            st.subheader("Upload Image to HOLD")
            uploaded_image = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])
            if uploaded_image:
                st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
                st.success("Image uploaded successfully!")

    # Ticket Mistakes Section
    elif st.session_state.current_section == "mistakes":
        with st.container():
            st.subheader("Report Ticket Mistake")
            with st.form("mistake_form"):
                team_leader = st.text_input("Team Leader Name")
                agent_name = st.text_input("Agent Name")
                ticket_id = st.text_input("Ticket ID")
                error_description = st.text_area("Error Description")
                
                if st.form_submit_button("Submit Mistake"):
                    if team_leader and agent_name and ticket_id and error_description:
                        add_mistake(team_leader, agent_name, ticket_id, error_description)
                        st.success("Mistake submitted!")
                    else:
                        st.warning("Please fill all fields")
        
        st.subheader("Reported Mistakes")
        mistakes = get_mistakes()
        if mistakes:
            for mistake in mistakes:
                m_id, tl, agent, t_id, desc, ts = mistake
                st.markdown(f"""
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4>Mistake #{m_id}</h4>
                        <small>{ts}</small>
                    </div>
                    <p><strong>Team Leader:</strong> {tl}</p>
                    <p><strong>Agent:</strong> {agent}</p>
                    <p><strong>Ticket ID:</strong> {t_id}</p>
                    <p><strong>Description:</strong> {desc}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No mistakes found.")

    # Group Chat Section
    elif st.session_state.current_section == "chat":
        # Messages container
        st.subheader("Group Chat")
        with st.container():
            st.markdown('<div style="max-height: 500px; overflow-y: auto; padding: 1rem; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 1rem;">', unsafe_allow_html=True)
            
            messages = get_group_messages()
            for msg in reversed(messages):  # Show newest at bottom
                msg_id, sender, message, timestamp, mentions = msg
                
                # Check if current user sent the message
                is_sent = sender == st.session_state.username
                
                # Format mentions
                formatted_message = message
                if mentions:
                    for mention in mentions.split(","):
                        formatted_message = formatted_message.replace(
                            f"@{mention}", 
                            f'<span style="color: #3b82f6; font-weight: bold;">@{mention}</span>'
                        )
                
                # Format timestamp
                msg_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                formatted_time = msg_time.strftime("%I:%M %p")
                
                if is_sent:
                    st.markdown(f"""
                    <div class="message sent">
                        <div>{formatted_message}</div>
                        <div class="timestamp">{formatted_time}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="message received">
                        <div><strong>{sender}</strong></div>
                        <div>{formatted_message}</div>
                        <div class="timestamp">{formatted_time}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Message input
            with st.form("message_form"):
                new_message = st.text_area("Type your message...", key="new_message")
                if st.form_submit_button("Send"):
                    if new_message.strip():
                        mentions = extract_mentions(new_message)
                        valid_mentions = []
                        
                        all_users = [user[1] for user in get_all_users()]
                        for mention in mentions:
                            if mention in all_users:
                                valid_mentions.append(mention)
                            else:
                                st.warning(f"User @{mention} not found")
                        
                        add_group_message(st.session_state.username, new_message, valid_mentions)
                        st.rerun()

    # Admin Panel Section
    elif st.session_state.current_section == "admin" and st.session_state.role == "admin":
        tab1, tab2 = st.tabs(["User Management", "System Tools"])
        
        with tab1:
            st.subheader("Create New User")
            with st.form("create_user_form"):
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("Role", ["agent", "admin"])
                if st.form_submit_button("Create User"):
                    if new_username and new_password:
                        if create_user(new_username, new_password, new_role):
                            st.success("User created successfully!")
                            st.rerun()
                    else:
                        st.warning("Please enter both username and password")
            
            st.subheader("Manage Users")
            users = get_all_users()
            if users:
                for user in users:
                    user_id, username, role = user
                    
                    with st.expander(f"{username} ({role})"):
                        cols = st.columns([1, 1, 1])
                        
                        # Change Role
                        with cols[0]:
                            new_role = st.selectbox(
                                "Role",
                                ["agent", "admin"],
                                index=0 if role == "agent" else 1,
                                key=f"role_{user_id}"
                            )
                            if st.button("Update Role", key=f"update_{user_id}"):
                                if update_user_role(user_id, new_role):
                                    st.success("Role updated!")
                                    st.rerun()
                        
                        # Reset Password
                        with cols[1]:
                            with st.form(key=f"reset_{user_id}"):
                                new_password = st.text_input("New Password", type="password", key=f"pass_{user_id}")
                                if st.form_submit_button("Reset Password"):
                                    if new_password:
                                        if reset_user_password(user_id, new_password):
                                            st.success("Password reset successfully!")
                                    else:
                                        st.warning("Please enter a new password")
                        
                        # Delete User
                        with cols[2]:
                            if st.button("Delete User", key=f"delete_{user_id}"):
                                if delete_user(user_id):
                                    st.success("User deleted!")
                                    st.rerun()
            else:
                st.info("No users found")
        
        with tab2:
            st.subheader("System Tools")
            if st.button("Clear All Requests"):
                conn = None
                try:
                    conn = sqlite3.connect("data/requests.db")
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM requests")
                    conn.commit()
                    st.success("All requests cleared!")
                except sqlite3.Error as e:
                    st.error(f"Failed to clear requests: {e}")
                finally:
                    if conn:
                        conn.close()
            
            if st.button("Clear All Mistakes"):
                conn = None
                try:
                    conn = sqlite3.connect("data/requests.db")
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM mistakes")
                    conn.commit()
                    st.success("All mistakes cleared!")
                except sqlite3.Error as e:
                    st.error(f"Failed to clear mistakes: {e}")
                finally:
                    if conn:
                        conn.close()
            
            if st.button("Refresh Database"):
                init_db()
                st.success("Database refreshed!")

# Check for new messages and requests
if st.session_state.get("authenticated", False):
    current_message_count = len(get_group_messages())
    if current_message_count > st.session_state.get("last_message_count", 0):
        st.session_state.last_message_count = current_message_count
        if st.session_state.current_section != "chat":
            show_notification("New message in group chat")
    
    current_request_count = len(get_requests())
    if current_request_count > st.session_state.get("last_request_count", 0):
        st.session_state.last_request_count = current_request_count
        if st.session_state.current_section != "requests" and st.session_state.role == "admin":
            show_notification("New request submitted!")
