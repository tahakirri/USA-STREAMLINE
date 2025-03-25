import streamlit as st
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Database setup
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT,
                        role TEXT)''')
    conn.commit()
    conn.close()

# Function to add a new user (use this once to create an admin)
def add_user(username, password, role):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    hashed_password = generate_password_hash(password)
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, role))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # User already exists
    conn.close()

# Function to verify user login
def authenticate_user(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password, role FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user[0], password):
        return user[1]  # Return role
    return None

# Initialize database and add default admin
init_db()
add_user("taha kirri", "arise@99", "admin")  # Ensure admin exists

# Streamlit UI
st.title("Request Management System")

# Login form
st.sidebar.header("Login")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")
if st.sidebar.button("Login"):
    role = authenticate_user(username, password)
    if role:
        st.session_state["role"] = role
        st.session_state["username"] = username
        st.sidebar.success(f"Logged in as {role}")
    else:
        st.sidebar.error("Invalid credentials")

# Show dashboard based on role
if "role" in st.session_state:
    st.write(f"Welcome, {st.session_state['username']}! You are logged in as **{st.session_state['role']}**.")

    if st.session_state["role"] == "admin":
        st.subheader("Admin Dashboard")
        st.write("✅ Full access to requests, users, and settings.")
        
        # Example: Add new users
        st.subheader("Add New User")
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")
        new_role = st.selectbox("Role", ["admin", "agent"])
        if st.button("Create User"):
            add_user(new_user, new_pass, new_role)
            st.success(f"User {new_user} added as {new_role}")

    elif st.session_state["role"] == "agent":
        st.subheader("Agent Dashboard")
        st.write("🔒 Limited access to assigned requests only.")

else:
    st.warning("Please log in to access the system.")
