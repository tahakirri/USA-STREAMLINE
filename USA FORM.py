import streamlit as st
import sqlite3
from datetime import datetime

# Initialize database
def init_db():
    conn = sqlite3.connect("requests.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT CHECK(role IN ('admin', 'agent'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            status TEXT CHECK(status IN ('open', 'in-progress', 'closed')),
            created_by TEXT,
            assigned_to TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Authentication function
def authenticate_user(username, password):
    conn = sqlite3.connect("requests.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

# Add new request
def add_request(title, description, created_by):
    conn = sqlite3.connect("requests.db")
    c = conn.cursor()
    c.execute("INSERT INTO requests (title, description, status, created_by) VALUES (?, ?, 'open', ?)", 
              (title, description, created_by))
    conn.commit()
    conn.close()

# Fetch requests
def get_requests():
    conn = sqlite3.connect("requests.db")
    c = conn.cursor()
    c.execute("SELECT * FROM requests")
    requests = c.fetchall()
    conn.close()
    return requests

# Update request status
def update_request_status(request_id, status):
    conn = sqlite3.connect("requests.db")
    c = conn.cursor()
    c.execute("UPDATE requests SET status=? WHERE id=?", (status, request_id))
    conn.commit()
    conn.close()

# Streamlit UI
init_db()
st.title("Request Management System")

# Login
authenticated_user = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

if not st.session_state.logged_in:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = authenticate_user(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.username = user[1]
            st.session_state.role = user[3]
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")
else:
    st.sidebar.write(f"Welcome, {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.experimental_rerun()

    # Agent view
    if st.session_state.role == "agent":
        st.subheader("Create New Request")
        title = st.text_input("Title")
        description = st.text_area("Description")
        if st.button("Submit Request"):
            add_request(title, description, st.session_state.username)
            st.success("Request submitted!")

        st.subheader("My Requests")
        requests = get_requests()
        for req in requests:
            if req[4] == st.session_state.username:
                st.write(f"**{req[1]}** - {req[2]} - *{req[3]}*")

    # Admin view
    if st.session_state.role == "admin":
        st.subheader("All Requests")
        requests = get_requests()
        for req in requests:
            st.write(f"**{req[1]}** - {req[2]} - *{req[3]}*")
            new_status = st.selectbox("Update Status", ["open", "in-progress", "closed"], index=["open", "in-progress", "closed"].index(req[3]), key=req[0])
            if st.button(f"Update Request {req[0]}"):
                update_request_status(req[0], new_status)
                st.experimental_rerun()
