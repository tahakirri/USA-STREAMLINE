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

# [All other database functions remain the same...]

# --------------------------
# Streamlit UI with Modern Messaging
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

# [Rest of your initialization code...]

# Conversation Room Section with Modern UI
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
        st.markdown('<div class="message-container">', unsafe_allow_html=True)
        
        messages = get_group_messages()
        for msg in messages:
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
            st.markdown(f"""
            <div class="message {'sent' if is_sent else 'received'}">
                {'' if is_sent else f'<div class="sender-name">{sender}</div>'}
                {formatted_message}
                <div class="timestamp">{formatted_time}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
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
        st.markdown('<div class="message-container">', unsafe_allow_html=True)
        
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
            st.markdown(f"""
            <div class="message {'sent' if sender == st.session_state.username else 'received'}">
                {'' if sender == st.session_state.username else f'<div class="sender-name">{sender}</div>'}
                {message}
                <div class="timestamp">{formatted_time}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Message input area
        with st.form("private_message_form", clear_on_submit=True):
            private_message = st.text_area("Type your message...", key="private_msg_input")
            col1, col2 = st.columns([10, 1])
            with col2:
                if st.form_submit_button("➤"):
                    if private_message.strip():
                        add_private_message(st.session_state.username, selected_recipient, private_message)
                        st.rerun()

# [Rest of your code...]
