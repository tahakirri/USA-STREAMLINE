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

# [Previous database functions remain the same until conversation functions]

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

# --------------------------
# Streamlit UI
# --------------------------

# [Previous UI code remains the same until Conversation Room section]

elif section.startswith("💬 Conversation Room"):
    st.subheader("Conversation Room")
    
    # Show notification badge for unread messages
    unread_msgs = get_unread_messages(st.session_state.username)
    if unread_msgs:
        st.warning(f"You have {len(unread_msgs)} unread messages!")
    
    tab1, tab2 = st.tabs(["Group Chat", "Private Messages"])
    
    with tab1:
        st.markdown("### Group Chat (All users can see these messages)")
        
        # Display full conversation history
        messages = get_group_messages()
        for msg in messages:
            msg_id, sender, message, timestamp, mentions = msg
            
            # Highlight mentions
            if mentions and st.session_state.username in mentions.split(","):
                st.markdown(f"""
                <div style='background-color: #fff8e1; padding: 10px; border-radius: 5px; margin: 5px 0;'>
                    <strong>{sender}</strong> <span style='color: #ff6d00;'>(mentioned you)</span> - {timestamp}<br>
                    {message}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='padding: 10px; border-radius: 5px; margin: 5px 0;'>
                    <strong>{sender}</strong> - {timestamp}<br>
                    {message}
                </div>
                """, unsafe_allow_html=True)
        
        # Message input at bottom
        with st.form("group_message_form"):
            new_message = st.text_area("Message", help="Use @username to mention someone")
            if st.form_submit_button("Send to Group"):
                if new_message:
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
        
        # Display full conversation history with the selected user
        st.markdown(f"#### Conversation with {selected_recipient}")
        conversation = get_conversation_history(st.session_state.username, selected_recipient)
        
        for msg in conversation:
            msg_id, sender, receiver, message, timestamp, is_read = msg
            
            # Mark as read when viewed
            if receiver == st.session_state.username and not is_read:
                mark_as_read(msg_id)
            
            # Different styling for sent vs received messages
            if sender == st.session_state.username:
                st.markdown(f"""
                <div style='background-color: #e3f2fd; padding: 10px; border-radius: 5px; margin: 5px 0; text-align: right;'>
                    <strong>You</strong> - {timestamp}<br>
                    {message}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin: 5px 0;'>
                    <strong>{sender}</strong> - {timestamp}<br>
                    {message}
                </div>
                """, unsafe_allow_html=True)
        
        # Message input at bottom
        with st.form("private_message_form"):
            private_message = st.text_area("Your message")
            if st.form_submit_button(f"Send to {selected_recipient}"):
                if private_message:
                    add_private_message(st.session_state.username, selected_recipient, private_message)
                    st.rerun()

# JavaScript for notifications
def show_notification(message):
    js = f"""
    <script>
        Notification.requestPermission().then(function(permission) {{
            if (permission === "granted") {{
                new Notification("{message}");
            }}
        }});
    </script>
    """
    html(js)

# Check for new messages periodically
if st.session_state.get("authenticated", False):
    unread_count = get_unread_count(st.session_state.username)
    if unread_count > st.session_state.get("last_unread_count", 0):
        show_notification(f"You have {unread_count} new messages")
        st.session_state.last_unread_count = unread_count
        st.rerun()
