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
        """, (completed, request_id))
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
# Streamlit UI with Tailwind
# --------------------------

st.set_page_config(
    page_title="Request Management System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tailwind CSS
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css');
</style>
""", unsafe_allow_html=True)

# Custom Styles
st.markdown("""
<style>
    .message-container {
        max-height: 60vh;
        overflow-y: auto;
        padding: 1rem;
    }
    .mention {
        color: #3b82f6;
        font-weight: bold;
    }
    .unread-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background-color: #3b82f6;
        color: white;
        font-size: 0.7rem;
        margin-left: 0.5rem;
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

# Initialize database
init_db()

# Login form
if not st.session_state.authenticated:
    st.markdown("""
    <div class="flex items-center justify-center min-h-screen bg-gray-100">
        <div class="w-full max-w-md p-8 space-y-8 bg-white rounded-lg shadow-md">
            <h2 class="text-2xl font-bold text-center text-gray-900">Login</h2>
            <form class="mt-8 space-y-6">
    """, unsafe_allow_html=True)
    
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Login"):
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
    
    st.markdown("""
            </form>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    # Main layout with sidebar
    st.markdown("""
    <div class="flex h-screen bg-gray-100">
        <!-- Sidebar -->
        <div class="w-64 bg-white shadow-md">
            <div class="p-4 border-b border-gray-200">
                <h3 class="text-lg font-medium text-gray-900">Welcome, {username}</h3>
            </div>
            <nav class="p-4 space-y-2">
    """.format(username=st.session_state.username), unsafe_allow_html=True)
    
    with st.sidebar:
        # Show unread message count
        unread_count = len(get_group_messages())
        badge = f'<span class="unread-badge">{unread_count}</span>' if unread_count > 0 else ""
        
        nav_options = [
            ("📋 Request", "request"),
            ("🖼️ HOLD", "hold"),
            ("❌ Ticket Mistakes", "mistakes"),
            (f"💬 Group Chat{badge}", "chat")
        ]
        
        if st.session_state.role == "admin":
            nav_options.append(("⚙ Admin Panel", "admin"))
        
        for option, value in nav_options:
            if st.button(option, key=f"nav_{value}"):
                st.session_state.current_section = value
    
    st.markdown("""
            </nav>
        </div>
        
        <!-- Main content -->
        <div class="flex-1 overflow-auto">
    """, unsafe_allow_html=True)

    # Request Section
    if getattr(st.session_state, 'current_section', 'request') == "request":
        st.markdown("""
        <div class="p-6">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">Submit a Request</h2>
            <div class="bg-white rounded-lg shadow p-6 mb-6">
        """, unsafe_allow_html=True)
        
        request_type = st.selectbox("Request Type", ["Email", "Phone Number", "Ticket ID"])
        identifier = st.text_input("Identifier")
        comment = st.text_area("Comment")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Submit Request", key="submit_request"):
                if identifier and comment:
                    if add_request(st.session_state.username, request_type, identifier, comment):
                        st.success("Request submitted!")
                        show_notification("New request submitted!")
                    else:
                        st.error("Failed to submit request")
                else:
                    st.warning("Please fill all required fields")
        with col2:
            if st.button("🔄 Refresh Requests", key="refresh_requests"):
                st.rerun()

        st.markdown("""
            </div>
            
            <h2 class="text-2xl font-bold text-gray-800 mb-6">Requests</h2>
            <div class="bg-white rounded-lg shadow overflow-hidden">
        """, unsafe_allow_html=True)
        
        requests = get_requests()
        if requests:
            for req in requests:
                req_id, agent, req_type, identifier, comment, timestamp, completed = req
                
                st.markdown(f"""
                <div class="border-b border-gray-200 p-4 hover:bg-gray-50">
                    <div class="flex items-center">
                        <div class="mr-4">
                            <input type="checkbox" {'checked' if completed else ''} 
                                   onchange="updateRequestStatus({req_id}, this.checked)"
                                   class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded">
                        </div>
                        <div class="flex-1">
                            <div class="flex justify-between items-baseline">
                                <h3 class="text-lg font-medium text-gray-900">
                                    ID: {req_id} | Agent: {agent} | Type: {req_type}
                                </h3>
                                <span class="text-sm text-gray-500">{timestamp}</span>
                            </div>
                            <p class="mt-1 text-sm text-gray-600"><strong>Identifier:</strong> {identifier}</p>
                            <p class="mt-1 text-sm text-gray-600"><strong>Comment:</strong> {comment}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="p-6 text-center text-gray-500">
                No requests found
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    # HOLD Section
    elif st.session_state.current_section == "hold":
        st.markdown("""
        <div class="p-6">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">HOLD Section</h2>
            <div class="bg-white rounded-lg shadow p-6">
        """, unsafe_allow_html=True)
        
        uploaded_image = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
        if uploaded_image:
            st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
            st.success("Image uploaded successfully!")
        
        st.markdown("</div>", unsafe_allow_html=True)

    # Ticket Mistakes Section
    elif st.session_state.current_section == "mistakes":
        st.markdown("""
        <div class="p-6">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">Ticket Mistakes</h2>
            <div class="bg-white rounded-lg shadow p-6 mb-6">
        """, unsafe_allow_html=True)
        
        team_leader = st.text_input("Team Leader Name")
        agent_name = st.text_input("Agent Name")
        ticket_id = st.text_input("Ticket ID")
        error_description = st.text_area("Error Description")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Submit Mistake", key="submit_mistake"):
                if team_leader and agent_name and ticket_id and error_description:
                    add_mistake(team_leader, agent_name, ticket_id, error_description)
                    st.success("Mistake submitted!")
                else:
                    st.warning("Please fill all fields")
        with col2:
            if st.button("🔄 Refresh Mistakes", key="refresh_mistakes"):
                st.rerun()
        
        st.markdown("""
            </div>
            
            <h2 class="text-2xl font-bold text-gray-800 mb-6">Submitted Mistakes</h2>
            <div class="bg-white rounded-lg shadow overflow-hidden">
        """, unsafe_allow_html=True)
        
        mistakes = get_mistakes()
        if mistakes:
            for mistake in mistakes:
                m_id, tl, agent, t_id, desc, ts = mistake
                st.markdown(f"""
                <div class="border-b border-gray-200 p-4 hover:bg-gray-50">
                    <div class="flex justify-between items-baseline">
                        <h3 class="text-lg font-medium text-gray-900">
                            ID: {m_id} | Team Leader: {tl} | Agent: {agent}
                        </h3>
                        <span class="text-sm text-gray-500">{ts}</span>
                    </div>
                    <p class="mt-1 text-sm text-gray-600"><strong>Ticket ID:</strong> {t_id}</p>
                    <p class="mt-1 text-sm text-gray-600"><strong>Description:</strong> {desc}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="p-6 text-center text-gray-500">
                No mistakes found
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    # Group Chat Section
    elif st.session_state.current_section == "chat":
        st.markdown("""
        <div class="p-6">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">Group Chat</h2>
            <div class="bg-white rounded-lg shadow overflow-hidden">
                <div class="message-container p-4">
        """, unsafe_allow_html=True)
        
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
                        f'<span class="mention">@{mention}</span>'
                    )
            
            # Format timestamp
            msg_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            formatted_time = msg_time.strftime("%I:%M %p")
            
            if is_sent:
                st.markdown(f"""
                <div class="flex justify-end mb-4">
                    <div class="max-w-xs lg:max-w-md px-4 py-2 bg-blue-500 text-white rounded-lg">
                        <p>{formatted_message}</p>
                        <p class="text-xs text-blue-100 text-right mt-1">{formatted_time}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="mb-4">
                    <p class="text-sm font-medium text-gray-700">{sender}</p>
                    <div class="max-w-xs lg:max-w-md px-4 py-2 bg-gray-200 rounded-lg">
                        <p>{formatted_message}</p>
                        <p class="text-xs text-gray-500 text-right mt-1">{formatted_time}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("""
                </div>
                
                <div class="border-t border-gray-200 p-4">
        """, unsafe_allow_html=True)
        
        with st.form("group_message_form", clear_on_submit=True):
            new_message = st.text_area("Type your message...", key="group_msg_input")
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
        
        st.markdown("""
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Admin Panel Section
    elif st.session_state.current_section == "admin" and st.session_state.role == "admin":
        st.markdown("""
        <div class="p-6">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">Admin Panel</h2>
        """, unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["User Management", "Clear Data", "System Tools"])
        
        with tab1:
            st.markdown("""
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-xl font-medium text-gray-900 mb-4">User Management</h3>
            """, unsafe_allow_html=True)
            
            # Create new user
            with st.expander("Create New User"):
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
            
            # Manage existing users
            st.markdown("""
            <h4 class="text-lg font-medium text-gray-900 mt-6 mb-4">Existing Users</h4>
            """, unsafe_allow_html=True)
            
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
                            if new_role != role:
                                if st.button("Update Role", key=f"update_role_{user_id}"):
                                    if update_user_role(user_id, new_role):
                                        st.success("Role updated!")
                                        st.rerun()
                        
                        # Reset Password
                        with cols[1]:
                            with st.form(key=f"reset_pass_{user_id}"):
                                new_password = st.text_input("New Password", type="password", key=f"new_pass_{user_id}")
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
                st.markdown("""
                <div class="text-center text-gray-500 py-4">
                    No users found
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with tab2:
            st.markdown("""
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-xl font-medium text-gray-900 mb-4">Clear Data</h3>
            """, unsafe_allow_html=True)
            
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
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with tab3:
            st.markdown("""
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-xl font-medium text-gray-900 mb-4">System Tools</h3>
            """, unsafe_allow_html=True)
            
            if st.button("Refresh Database"):
                init_db()
                st.success("Database refreshed!")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Check for new messages and requests
if st.session_state.get("authenticated", False):
    current_message_count = len(get_group_messages())
    if current_message_count > st.session_state.get("last_message_count", 0):
        st.session_state.last_message_count = current_message_count
        if getattr(st.session_state, 'current_section', '') != "chat":
            show_notification("New message in group chat")
    
    current_request_count = len(get_requests())
    if current_request_count > st.session_state.get("last_request_count", 0):
        st.session_state.last_request_count = current_request_count
        if getattr(st.session_state, 'current_section', '') != "request" and st.session_state.role == "admin":
            show_notification("New request submitted!")

# JavaScript for updating request status
st.markdown("""
<script>
function updateRequestStatus(requestId, completed) {
    fetch('/update_request_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            request_id: requestId,
            completed: completed
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.error('Failed to update request status');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
</script>
""", unsafe_allow_html=True)
