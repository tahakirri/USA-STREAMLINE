import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import pandas as pd
import os

# [Previous functions remain exactly the same until the Streamlit UI section...]

# Streamlit UI
st.set_page_config(
    page_title="Request Management System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None

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
        nav_options = ["📋 Request", "🖼️ HOLD", "❌ Ticket Mistakes"]
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

    # Admin Panel Section
    elif section == "⚙ Admin Panel" and st.session_state.role == "admin":
        st.subheader("Admin Panel")
        
        tab1, tab2, tab3 = st.tabs(["User Management", "Clear Data", "System Tools"])
        
        with tab1:
            st.subheader("User Management")
            
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
            
            st.subheader("Existing Users")
            users = get_all_users()
            if users:
                for user in users:
                    user_id, username, role = user
                    cols = st.columns([3, 2, 2, 2])
                    with cols[0]:
                        st.write(f"**{username}**")
                    with cols[1]:
                        st.write(role)
                    with cols[2]:
                        new_role = st.selectbox(
                            "Change Role",
                            ["agent", "admin"],
                            index=0 if role == "agent" else 1,
                            key=f"role_{user_id}"
                        )
                        if new_role != role:
                            if update_user_role(user_id, new_role):
                                st.success("Role updated!")
                                st.rerun()
                    with cols[3]:
                        if st.button("Delete", key=f"del_{user_id}"):
                            if delete_user(user_id):
                                st.success("User deleted!")
                                st.rerun()
                    st.divider()
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
