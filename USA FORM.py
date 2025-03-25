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
        
        # Users table - FIXED: Properly closed parenthesis
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

st.set_page_config(
    page_title="Request Management System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern messaging interface
st.markdown("""
<style>
    .message-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 15px;
        max-height: 60vh;
        overflow-y: auto;
        background-color: var(--background-color);
        border-radius: 10px;
        margin-bottom: 15px;
    }
    .message {
        max-width: 70%;
        padding: 12px 16px;
        border-radius: 18px;
        word-wrap: break-word;
        position: relative;
        animation: fadeIn 0.3s ease-in-out;
    }
    .received {
        align-self: flex-start;
        background-color: var(--received-message-bg);
        color: var(--received-message-text);
        border-bottom-left-radius: 5px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .sent {
        align-self: flex-end;
        background-color: var(--sent-message-bg);
        color: var(--sent-message-text);
        border-bottom-right-radius: 5px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .sender-name {
        font-weight: 600;
        font-size: 0.85em;
        margin-bottom: 4px;
        color: var(--sender-name-color);
    }
    .timestamp {
        font-size: 0.7em;
        color: var(--timestamp-color);
        margin-top: 4px;
        text-align: right;
    }
    .mention {
        color: var(--mention-color);
        font-weight: bold;
        background-color: var(--mention-bg);
        padding: 0 2px;
        border-radius: 3px;
    }
    .unread-indicator {
        background-color: var(--unread-indicator-bg);
        color: white;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7em;
        margin-left: 8px;
    }
    .message-input-area {
        position: sticky;
        bottom: 0;
        background: var(--background-color);
        padding: 12px 0;
        border-top: 1px solid var(--border-color);
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Dark mode variables */
    [data-theme="dark"] {
        --background-color: #1e1e1e;
        --received-message-bg: #2d2d2d;
        --received-message-text: #ffffff;
        --sent-message-bg: #0078FF;
        --sent-message-text: #ffffff;
        --sender-name-color: #a0a0a0;
        --timestamp-color: #a0a0a0;
        --mention-color: #64b5f6;
        --mention-bg: rgba(100, 181, 246, 0.1);
        --unread-indicator-bg: #0078FF;
        --border-color: #333333;
    }
    
    /* Light mode variables */
    [data-theme="light"] {
        --background-color: #f8f9fa;
        --received-message-bg: #ffffff;
        --received-message-text: #000000;
        --sent-message-bg: #0078FF;
        --sent-message-text: #ffffff;
        --sender-name-color: #555555;
        --timestamp-color: #777777;
        --mention-color: #1976d2;
        --mention-bg: rgba(25, 118, 210, 0.1);
        --unread-indicator-bg: #0078FF;
        --border-color: #e0e0e0;
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

# Login form
if not st.session_state.authenticated:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
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
else:
    with st.sidebar:
        st.markdown(f"### Welcome, {st.session_state.username}")
        
        # Show unread message count
        unread_count = get_unread_count(st.session_state.username)
        badge = f" ({unread_count})" if unread_count > 0 else ""
        
        nav_options = ["📋 Request", "🖼️ HOLD", "❌ Ticket Mistakes", f"💬 Conversation Room{badge}"]
        if st.session_state.role == "admin":
            nav_options.append("⚙ Admin Panel")
        
        section = st.radio("Navigation", nav_options)
    
    # Request Section
    if section == "📋 Request":
        st.subheader("Submit a Request")
        request_type = st.selectbox("Request Type", ["Email", "Phone Number", "Ticket ID"])
        identifier = st.text_input("Identifier")
        comment = st.text_area("Comment")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Submit Request"):
                if identifier and comment:
                    add_request(st.session_state.username, request_type, identifier, comment)
                    st.success("Request submitted!")
                else:
                    st.warning("Please fill all required fields")
        with col2:
            if st.button("🔄 Refresh Requests"):
                st.rerun()

        st.subheader("Requests")
        requests = get_requests()
        
        if requests:
            for req in requests:
                req_id, agent, req_type, identifier, comment, timestamp, completed = req
                
                cols = st.columns([0.1, 0.9])
                with cols[0]:
                    done = st.checkbox(
                        "Done",
                        value=bool(completed),
                        key=f"check_{req_id}",
                        on_change=update_request_status,
                        args=(req_id, not completed))
                with cols[1]:
                    st.markdown(f"""
                    **ID:** {req_id} | **Agent:** {agent} | **Type:** {req_type}  
                    **Identifier:** {identifier}  
                    **Comment:** {comment}  
                    **Timestamp:** {timestamp}  
                    """)
                st.divider()
        else:
            st.info("No requests found.")

    # HOLD Section
    elif section == "🖼️ HOLD":
        st.subheader("HOLD Section")
        uploaded_image = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
        if uploaded_image:
            st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
            st.success("Image uploaded successfully!")

    # Ticket Mistakes Section
    elif section == "❌ Ticket Mistakes":
        st.subheader("Ticket Mistakes Section")
        team_leader = st.text_input("Team Leader Name")
        agent_name = st.text_input("Agent Name")
        ticket_id = st.text_input("Ticket ID")
        error_description = st.text_area("Error Description")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Submit Mistake"):
                if team_leader and agent_name and ticket_id and error_description:
                    add_mistake(team_leader, agent_name, ticket_id, error_description)
                    st.success("Mistake submitted!")
                else:
                    st.warning("Please fill all fields")
        with col2:
            if st.button("🔄 Refresh Mistakes"):
                st.rerun()
        
        mistakes = get_mistakes()
        if mistakes:
            st.subheader("Submitted Mistakes")
            for mistake in mistakes:
                m_id, tl, agent, t_id, desc, ts = mistake
                st.markdown(f"""
                **ID:** {m_id} | **Team Leader:** {tl} | **Agent:** {agent}  
                **Ticket ID:** {t_id}  
                **Description:** {desc}  
                **Timestamp:** {ts}  
                """)
                st.divider()

    # Conversation Room Section
    elif section.startswith("💬 Conversation Room"):
        st.subheader("Conversation Room")
        
        # Show notification for unread messages
        unread_msgs = get_unread_messages(st.session_state.username)
        if unread_msgs:
            st.warning(f"📬 You have {len(unread_msgs)} unread messages!")
            show_notification(f"You have {len(unread_msgs)} new messages")
        
        tab1, tab2 = st.tabs(["Group Chat", "Private Messages"])
        
        with tab1:
            st.markdown("### Group Chat")
            
            # Container for messages
            messages_container = st.container()
            
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
                
                # Message bubble
                with messages_container:
                    cols = st.columns([1])
                    with cols[0]:
                        if is_sent:
                            st.markdown(f"""
                            <div style="text-align: right; margin-bottom: 10px;">
                                <div style="display: inline-block; background-color: #0078FF; color: white; padding: 8px 12px; border-radius: 15px; max-width: 70%;">
                                    {formatted_message}
                                    <div style="font-size: 0.7em; color: #e0e0e0;">{formatted_time}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="margin-bottom: 10px;">
                                <div style="font-weight: 600; font-size: 0.85em; color: #555;">{sender}</div>
                                <div style="display: inline-block; background-color: #f0f0f0; padding: 8px 12px; border-radius: 15px; max-width: 70%;">
                                    {formatted_message}
                                    <div style="font-size: 0.7em; color: #777;">{formatted_time}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
            
            # Message input area
            with st.form("group_message_form", clear_on_submit=True):
                new_message = st.text_area("Type your message...", key="group_msg_input")
                col1, col2 = st.columns([10, 1])
                with col2:
                    if st.form_submit_button("➤"):
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
        
        with tab2:
            st.markdown("### Private Messages")
            
            # For agents: Select which admin to message
            if st.session_state.role == "agent":
                admins = get_admins()
                if not admins:
                    st.warning("No admin users found")
                else:
                    selected_recipient = st.selectbox("Message to:", admins)
            else:
                # Admins can message anyone
                recipients = get_all_users_except(st.session_state.username)
                selected_recipient = st.selectbox("Message to:", recipients)
            
            # Container for private messages
            private_container = st.container()
            
            conversation = get_conversation_history(st.session_state.username, selected_recipient)
            for msg in conversation:
                msg_id, sender, receiver, message, timestamp, is_read = msg
                
                # Mark as read when viewed
                if receiver == st.session_state.username and not is_read:
                    mark_as_read(msg_id)
                
                # Format timestamp
                msg_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                formatted_time = msg_time.strftime("%I:%M %p")
                
                # Message bubble
                with private_container:
                    cols = st.columns([1])
                    with cols[0]:
                        if sender == st.session_state.username:
                            st.markdown(f"""
                            <div style="text-align: right; margin-bottom: 10px;">
                                <div style="display: inline-block; background-color: #0078FF; color: white; padding: 8px 12px; border-radius: 15px; max-width: 70%;">
                                    {message}
                                    <div style="font-size: 0.7em; color: #e0e0e0;">{formatted_time}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="margin-bottom: 10px;">
                                <div style="font-weight: 600; font-size: 0.85em; color: #555;">{sender}</div>
                                <div style="display: inline-block; background-color: #f0f0f0; padding: 8px 12px; border-radius: 15px; max-width: 70%;">
                                    {message}
                                    <div style="font-size: 0.7em; color: #777;">{formatted_time}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
            
            # Message input area
            with st.form("private_message_form", clear_on_submit=True):
                private_message = st.text_area("Type your message...", key="private_msg_input")
                col1, col2 = st.columns([10, 1])
                with col2:
                    if st.form_submit_button("➤"):
                        if private_message.strip():
                            add_private_message(st.session_state.username, selected_recipient, private_message)
                            st.rerun()

    # Admin Panel Section
    elif section == "⚙ Admin Panel" and st.session_state.role == "admin":
        st.subheader("Admin Panel")
        
        tab1, tab2, tab3 = st.tabs(["User Management", "Clear Data", "System Tools"])
        
        with tab1:
            st.subheader("User Management")
            
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
            st.subheader("Existing Users")
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
                st.info("No users found")
        
        with tab2:
            st.subheader("Clear Data")
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
        
        with tab3:
            st.subheader("System Tools")
            if st.button("Refresh Database"):
                init_db()
                st.success("Database refreshed!")

# Check for new messages and show notifications
if st.session_state.get("authenticated", False):
    current_message_count = len(get_group_messages())
    if current_message_count > st.session_state.get("last_message_count", 0):
        st.session_state.last_message_count = current_message_count
        if section != "💬 Conversation Room":
            show_notification("New message in group chat")
    
    unread_count = get_unread_count(st.session_state.username)
    if unread_count > st.session_state.get("last_unread_count", 0):
        st.session_state.last_unread_count = unread_count
        if not section.startswith("💬 Conversation Room"):
            show_notification(f"You have {unread_count} new messages")
