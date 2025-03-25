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
        
        # [All table creation code...]
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

# [All other database functions...]

# --------------------------
# Streamlit UI
# --------------------------

st.set_page_config(
    page_title="Request Management System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.last_unread_count = 0

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
        # [Request section code...]
        pass
    
    # HOLD Section
    elif section == "🖼️ HOLD":
        # [HOLD section code...]
        pass
    
    # Ticket Mistakes Section
    elif section == "❌ Ticket Mistakes":
        # [Ticket mistakes section code...]
        pass
    
    # Conversation Room Section
    elif section.startswith("💬 Conversation Room"):
        # [Modern messaging UI code...]
        pass
    
    # Admin Panel Section
    elif section == "⚙ Admin Panel" and st.session_state.role == "admin":
        # [Admin panel code...]
        pass

# Check for new messages and show notifications
if st.session_state.get("authenticated", False):
    unread_count = get_unread_count(st.session_state.username)
    if unread_count > st.session_state.get("last_unread_count", 0):
        st.session_state.last_unread_count = unread_count
        st.rerun()
