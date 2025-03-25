import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

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
        )
    """)
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
    cursor.execute("INSERT INTO requests (agent_name, request_type, identifier, comment, timestamp) VALUES (?, ?, ?, ?, ?)" ,
                   (agent_name, request_type, identifier, comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# Fetch requests
def get_requests():
    conn = sqlite3.connect("requests.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requests")
    requests = cursor.fetchall()
    conn.close()
    return requests

# Streamlit UI
st.title("Request Management System")
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
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")
else:
    st.success(f"Logged in as {st.session_state.username} ({st.session_state.role})")
    if st.session_state.role == "agent":
        st.subheader("Submit a Request")
        request_type = st.selectbox("Request Type", ["Email", "Phone Number", "Ticket ID"])
        identifier = st.text_input("Identifier")
        comment = st.text_area("Comment")
        if st.button("Submit Request"):
            add_request(st.session_state.username, request_type, identifier, comment)
            st.success("Request submitted!")
    
    st.subheader("Requests")
    requests = get_requests()
    for req in requests:
        st.write(req)
    
    if st.session_state.role == "admin":
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
