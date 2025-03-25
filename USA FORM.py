import sqlite3
import streamlit as st
from werkzeug.security import generate_password_hash, check_password_hash

db = "requests.db"

def init_db():
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    role TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT,
                    description TEXT,
                    status TEXT DEFAULT 'Pending'
                )''')
    
    # Ensure admin user exists
    c.execute("SELECT * FROM users WHERE username=?", ("taha kirri",))
    if not c.fetchone():
        hashed_password = generate_password_hash("arise@99", method='pbkdf2:sha256')
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("taha kirri", hashed_password, "admin"))
    
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("SELECT password, role FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    if user and check_password_hash(user[0], password):
        return user[1]  # Return role
    return None

def add_request(user, description):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("INSERT INTO requests (user, description) VALUES (?, ?)", (user, description))
    conn.commit()
    conn.close()

def get_requests():
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("SELECT * FROM requests")
    data = c.fetchall()
    conn.close()
    return data

def update_request_status(request_id, status):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("UPDATE requests SET status=? WHERE id=?", (status, request_id))
    conn.commit()
    conn.close()

# Streamlit UI
init_db()
st.title("Request Management System")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = ""

if not st.session_state.logged_in:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        role = login_user(username, password)
        if role:
            st.session_state.logged_in = True
            st.session_state.role = role
            st.session_state.username = username
            st.success(f"Welcome, {username} ({role})")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")
else:
    st.write(f"Logged in as: {st.session_state.username} ({st.session_state.role})")
    if st.session_state.role == "agent":
        description = st.text_area("Describe your request")
        if st.button("Submit Request"):
            add_request(st.session_state.username, description)
            st.success("Request submitted")
    elif st.session_state.role == "admin":
        requests = get_requests()
        for r in requests:
            st.write(f"ID: {r[0]}, User: {r[1]}, Description: {r[2]}, Status: {r[3]}")
            new_status = st.selectbox("Update Status", ["Pending", "In Progress", "Completed"], key=f"status_{r[0]}")
            if st.button(f"Update {r[0]}"):
                update_request_status(r[0], new_status)
                st.success("Status updated")
                st.experimental_rerun()
    
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.experimental_rerun()
