import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import pandas as pd

# Initialize database
def init_db():
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT CHECK(role IN ('agent', 'admin'))
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
        INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)
    """, ("TAHA KIRRI", hashlib.sha256("arise@99".encode()).hexdigest(), "admin"))
    conn.commit()
    conn.close()

# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Authenticate user
def authenticate(username, password):
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, hash_password(password)))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

# Insert new request
def add_request(agent_name, request_type, identifier, comment):
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO requests (agent_name, request_type, identifier, comment, timestamp) 
        VALUES (?, ?, ?, ?, ?)
    """, (agent_name, request_type, identifier, comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# Fetch requests
def get_requests():
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requests ORDER BY completed, timestamp DESC")
    requests = cursor.fetchall()
    conn.close()
    return requests

# Update request completion status
def update_request_status(request_id, completed):
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE requests SET completed=? WHERE id=?", (completed, request_id))
    conn.commit()
    conn.close()

# Streamlit UI
st.set_page_config(page_title="Request Management System", layout="wide", initial_sidebar_state="expanded")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None

# Login form
if not st.session_state.authenticated:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        role = authenticate(username, password)
        if role:
            st.session_state.authenticated = True
            st.session_state.role = role
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Invalid credentials")
else:
    with st.sidebar:
        st.markdown(f"### Welcome, {st.session_state.username}")
        section = st.radio("Navigation", ["📋 Request", "🖼️ HOLD", "❌ Ticket Mistakes", "⚙ Admin Panel" if st.session_state.role == "admin" else ""])
    
    if section == "📋 Request":
        st.subheader("Submit a Request")
        request_type = st.selectbox("Request Type", ["Email", "Phone Number", "Ticket ID"])
        identifier = st.text_input("Identifier")
        comment = st.text_area("Comment")
        if st.button("Submit Request"):
            add_request(st.session_state.username, request_type, identifier, comment)
            st.success("Request submitted!")

        st.subheader("Requests")
        requests = get_requests()
        if requests:
            # Create a DataFrame for better display
            df = pd.DataFrame(requests, columns=["ID", "Agent", "Type", "Identifier", "Comment", "Timestamp", "Completed"])
            
            # Display each request with a checkbox
            for index, row in df.iterrows():
                col1, col2 = st.columns([0.9, 0.1])
                with col1:
                    st.markdown(f"""
                    **Request ID:** {row['ID']}  
                    **Agent:** {row['Agent']}  
                    **Type:** {row['Type']}  
                    **Identifier:** {row['Identifier']}  
                    **Comment:** {row['Comment']}  
                    **Timestamp:** {row['Timestamp']}  
                    """)
                with col2:
                    completed = st.checkbox("Done", value=bool(row['Completed']), key=f"check_{row['ID']}")
                    if completed != bool(row['Completed']):
                        update_request_status(row['ID'], int(completed))
                        st.rerun()
                st.divider()
        else:
            st.write("No requests found.")

    elif section == "🖼️ HOLD":
        st.subheader("HOLD Section")
        uploaded_image = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
        if uploaded_image:
            st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
            st.success("Image uploaded successfully!")

    elif section == "❌ Ticket Mistakes":
        st.subheader("Ticket Mistakes Section")
        team_leader = st.text_input("Team Leader Name")
        agent_name = st.text_input("Agent Name")
        ticket_id = st.text_input("Ticket ID")
        error_description = st.text_area("Error Description")
        if st.button("Submit Mistake"):
            st.success("Mistake submitted!")

    elif section == "⚙ Admin Panel" and st.session_state.role == "admin":
        st.subheader("Admin Panel")
        if st.button("Clear All Requests"):
            conn = sqlite3.connect("requests.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM requests")
            conn.commit()
            conn.close()
            st.success("All requests cleared!")

# Initialize database
init_db()
