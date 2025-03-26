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

# [Keep all database functions exactly the same as original]

# --------------------------
# Streamlit App Configuration
# --------------------------

st.set_page_config(
    page_title="Request Management System", 
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional design
st.markdown("""
<style>
    :root {
        --primary: #2C3E50;
        --secondary: #3498DB;
        --background: #F5F6FA;
        --card-bg: #FFFFFF;
    }
    
    .stApp { background-color: var(--background); }
    
    [data-testid="stSidebar"] { 
        background-color: var(--card-bg) !important;
        box-shadow: 2px 0 10px rgba(0,0,0,0.1);
    }
    
    .stButton>button {
        background-color: var(--secondary) !important;
        border-radius: 8px !important;
        padding: 8px 24px !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover {
        opacity: 0.9;
        transform: translateY(-1px);
    }
    
    .card {
        background: var(--card-bg);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid var(--secondary);
    }
    
    .timestamp {
        font-size: 0.85rem;
        color: #7F8C8D;
        margin-top: 0.5rem;
    }
    
    .warning-banner {
        background: #FFF3E0;
        border-left: 4px solid #FFA726;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    
    .system-alert {
        background: #FFEBEE;
        border-left: 4px solid #EF5350;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    
    .user-badge {
        background: #ECEFF1;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.9rem;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    
    .mention-badge {
        background: #E3F2FD;
        color: #1976D2;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.current_section = "requests"
    st.session_state.last_message_count = 0

# Initialize database
init_db()

# --------------------------
# Authentication Page
# --------------------------

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; margin-bottom: 2rem;'>🔒 Request Management System</h1>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("""
            <div style='background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1)'>
                <h2 style='margin-bottom: 1.5rem;'>System Login</h2>
            """, unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                if st.form_submit_button("Sign In", use_container_width=True):
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
            
            st.markdown("</div>", unsafe_allow_html=True)

# --------------------------
# Main Application
# --------------------------

else:
    # System status banner
    if is_killswitch_enabled():
        st.markdown("""
        <div class='system-alert'>
            <h3>⚠️ System Locked</h3>
            <p>All modification features are disabled. Contact system administrator.</p>
        </div>
        """, unsafe_allow_html=True)

    # Sidebar Navigation
    with st.sidebar:
        st.markdown(f"""
        <div class='user-badge'>
            <span>👤</span>
            <div>
                <strong>{st.session_state.username}</strong><br>
                <small>{st.session_state.role.capitalize()}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        nav_items = {
            "requests": ("📥 Requests", "Submit and track requests"),
            "hold": ("🖼️ Media Hold", "Manage held media files"),
            "mistakes": ("⚠️ Quality Issues", "Report and review errors"),
            "chat": ("📢 Team Comms", "Group communications"),
            "admin": ("⚙️ Administration", "System management")
        }
        
        if st.session_state.role != "admin":
            del nav_items["admin"]
            
        for section, (icon, desc) in nav_items.items():
            if st.button(
                f"{icon} {section.capitalize()}",
                help=desc,
                use_container_width=True,
                key=f"nav_{section}"
            ):
                st.session_state.current_section = section
        
        st.markdown("---")
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.role = None
            st.session_state.username = None
            st.rerun()

    # --------------------------
    # Main Content Sections
    # --------------------------

    st.markdown(f"<h1>{nav_items[st.session_state.current_section][0]} {st.session_state.current_section.capitalize()}</h1>", unsafe_allow_html=True)

    # Requests Section
    if st.session_state.current_section == "requests":
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if not is_killswitch_enabled():
                with st.container():
                    st.markdown("### 🆕 New Request")
                    with st.form("request_form"):
                        request_type = st.selectbox("Type", ["Email", "Phone", "Ticket ID"])
                        identifier = st.text_input("Identifier")
                        comment = st.text_area("Details")
                        
                        if st.form_submit_button("Submit Request"):
                            if identifier and comment:
                                if add_request(st.session_state.username, request_type, identifier, comment):
                                    st.success("Request submitted!")
            else:
                st.markdown("<div class='warning-banner'>⚠️ Submission disabled while system is locked</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("### 📋 Active Requests")
            requests = get_requests()
            
            if not requests:
                st.markdown("<div class='card'>No active requests found</div>", unsafe_allow_html=True)
            
            for req in requests:
                req_id, agent, req_type, identifier, comment, timestamp, completed = req
                status = "✅ Completed" if completed else "🟡 Pending"
                
                st.markdown(f"""
                <div class='card'>
                    <div style="display: flex; justify-content: space-between; align-items: center">
                        <h3>#{req_id} - {req_type}</h3>
                        <div style="display: flex; align-items: center; gap: 1rem">
                            <span>{status}</span>
                            {'' if is_killswitch_enabled() else st.checkbox("", value=completed, key=f"check_{req_id}", label_visibility="hidden")}
                        </div>
                    </div>
                    <p><strong>Identifier:</strong> {identifier}</p>
                    <p><strong>Details:</strong> {comment}</p>
                    <div class='timestamp'>
                        Submitted by {agent} at {timestamp.split()[1]}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # [Other sections follow similar structure with updated styling...]

    # --------------------------
    # Admin Panel Section
    # --------------------------

    elif st.session_state.current_section == "admin" and st.session_state.role == "admin":
        tab1, tab2, tab3 = st.tabs(["👥 User Management", "⚡ System Controls", "🗑️ Data Management"])
        
        with tab1:
            st.markdown("### User Accounts")
            
            if not is_killswitch_enabled():
                with st.expander("➕ Add New User", expanded=True):
                    with st.form("add_user_form"):
                        new_username = st.text_input("Username")
                        new_password = st.text_input("Password", type="password")
                        new_role = st.selectbox("Role", ["agent", "admin"])
                        
                        if st.form_submit_button("Create Account"):
                            if new_username and new_password:
                                if add_user(new_username, new_password, new_role):
                                    st.success("User created successfully!")
            
            st.markdown("### Active Users")
            users = get_all_users()
            for user in users:
                cols = st.columns([3, 2, 1])
                cols[0].markdown(f"**{user[1]}**")
                cols[1].markdown(f"`{user[2]}`")
                if cols[2].button("Delete", key=f"del_{user[0]}"):
                    delete_user(user[0])
                    st.rerun()
        
        with tab2:
            if st.session_state.username.lower() == "taha kirri":
                st.markdown("### System Killswitch")
                current_status = is_killswitch_enabled()
                
                col1, col2 = st.columns(2)
                col1.metric("System Status", 
                          value="🔴 Locked" if current_status else "🟢 Operational",
                          delta="Lock Active" if current_status else "All Systems Normal")
                
                if current_status:
                    if col2.button("🟢 Restore System", type="primary"):
                        toggle_killswitch(False)
                        st.rerun()
                else:
                    if col2.button("🔴 Activate Lock", type="secondary"):
                        toggle_killswitch(True)
                        st.rerun()
        
        with tab3:
            st.markdown("### Data Management")
            st.markdown("<div class='warning-banner'>⚠️ These actions are irreversible</div>", unsafe_allow_html=True)
            
            cols = st.columns(3)
            with cols[0]:
                if st.button("Clear All Requests"):
                    clear_all_requests()
            with cols[1]:
                if st.button("Clear Quality Issues"):
                    clear_all_mistakes()
            with cols[2]:
                if st.button("Clear Team Comms"):
                    clear_all_group_messages()

# [Remaining sections maintain similar structure with updated styling elements]

if __name__ == "__main__":
    st.write("System Initialized")
