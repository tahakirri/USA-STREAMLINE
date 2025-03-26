import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import os
import re
from streamlit.components.v1 import html
from PIL import Image
import io

# --------------------------
# Database Functions
# --------------------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()

        # Hash the provided password
        hashed_password = hash_password(password)

        # Check credentials against users table
        cursor.execute("""
            SELECT role FROM users 
            WHERE username = ? AND password = ?
        """, (username, hashed_password))

        result = cursor.fetchone()

        # Return role if credentials are valid, otherwise return None
        return result[0] if result else None

    except sqlite3.Error as e:
        st.error(f"Authentication error: {e}")
        return None
    finally:
        if conn:
            conn.close()

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

        # HOLD images table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hold_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uploader TEXT,
                image_data BLOB,
                timestamp TEXT
            )
        """)

        # Default admin accounts
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, password, role) 
            VALUES (?, ?, ?)
        """, ("admin", hash_password("admin123"), "admin"))

        cursor.execute("""
            INSERT OR IGNORE INTO users (username, password, role) 
            VALUES (?, ?, ?)
        """, ("taha kirri", hash_password("arise@99"), "admin"))

        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

# Mistakes Section Functions
def add_mistake(team_leader, agent_name, ticket_id, error_description):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO mistakes (team_leader, agent_name, ticket_id, error_description, timestamp) 
            VALUES (?, ?, ?, ?, ?)
        """, (team_leader, agent_name, ticket_id, error_description, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to add mistake: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_mistakes():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM mistakes 
            ORDER BY timestamp DESC
        """)
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to fetch mistakes: {e}")
        return []
    finally:
        if conn:
            conn.close()

# Group Chat Functions
def send_group_message(sender, message):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()

        # Extract mentions
        mentions = re.findall(r'@(\w+)', message)

        cursor.execute("""
            INSERT INTO group_messages (sender, message, timestamp, mentions) 
            VALUES (?, ?, ?, ?)
        """, (sender, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ','.join(mentions)))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to send message: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_group_messages():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM group_messages 
            ORDER BY timestamp DESC
            LIMIT 50
        """)
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to fetch group messages: {e}")
        return []
    finally:
        if conn:
            conn.close()

# Admin Panel Functions
def get_all_users():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM users")
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to fetch users: {e}")
        return []
    finally:
        if conn:
            conn.close()

def add_user(username, password, role):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, role) 
            VALUES (?, ?, ?)
        """, (username, hash_password(password), role))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to add user: {e}")
        return False
    finally:
        if conn:
            conn.close()

def delete_user(user_id):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to delete user: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Existing functions from previous implementation...
def add_request(agent_name, request_type, identifier, comment):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO requests (agent_name, request_type, identifier, comment, timestamp) 
            VALUES (?, ?, ?, ?, ?)
        """, (agent_name, request_type, identifier, comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to add request: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_requests():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM requests 
            ORDER BY timestamp DESC
        """)
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to fetch requests: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_request_status(request_id, completed):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE requests 
            SET completed = ? 
            WHERE id = ?
        """, (1 if completed else 0, request_id))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Failed to update request status: {e}")
    finally:
        if conn:
            conn.close()

def add_hold_image(uploader, image_data):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hold_images (uploader, image_data, timestamp) 
            VALUES (?, ?, ?)
        """, (uploader, image_data, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Failed to add HOLD image: {e}")
    finally:
        if conn:
            conn.close()

def get_hold_images():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM hold_images 
            ORDER BY timestamp DESC
        """)
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to fetch HOLD images: {e}")
        return []
    finally:
        if conn:
            conn.close()

def clear_hold_images():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM hold_images")
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to clear HOLD images: {e}")
        return False
    finally:
        if conn:
            conn.close()

# ------------------------
# Streamlit Interface
# ------------------------

def show_login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        role = authenticate(username, password)
        if role:
            st.session_state.username = username
            st.session_state.role = role
            st.success(f"Welcome, {role}")
            show_dashboard()
        else:
            st.error("Invalid username or password")

def show_dashboard():
    st.title("Dashboard")
    role = st.session_state.role

    # Admin panel
    if role == "admin":
        st.header("Admin Panel")
        action = st.selectbox("Choose an action", ["Manage Users", "View Requests", "View Mistakes", "View Group Messages", "Manage HOLD Images"])

        if action == "Manage Users":
            manage_users()
        elif action == "View Requests":
            view_requests()
        elif action == "View Mistakes":
            view_mistakes()
        elif action == "View Group Messages":
            view_group_messages()
        elif action == "Manage HOLD Images":
            manage_hold_images()

    # Agent panel
    elif role == "agent":
        st.header("Agent Panel")
        action = st.selectbox("Choose an action", ["Submit Request", "View Requests", "View Mistakes", "View Group Messages", "Upload HOLD Image"])

        if action == "Submit Request":
            submit_request()
        elif action == "View Requests":
            view_requests()
        elif action == "View Mistakes":
            view_mistakes()
        elif action == "View Group Messages":
            view_group_messages()
        elif action == "Upload HOLD Image":
            upload_hold_image()

def submit_request():
    agent_name = st.session_state.username
    request_type = st.text_input("Request Type")
    identifier = st.text_input("Identifier")
    comment = st.text_area("Comment")

    if st.button("Submit"):
        if add_request(agent_name, request_type, identifier, comment):
            st.success("Request submitted successfully.")
        else:
            st.error("Failed to submit request.")

def view_requests():
    requests = get_requests()
    if requests:
        for req in requests:
            st.write(f"Request ID: {req[0]} | Agent: {req[1]} | Type: {req[2]} | Comment: {req[4]} | Completed: {'Yes' if req[5] else 'No'}")
            if req[5] == 0:
                if st.button(f"Mark Request {req[0]} as Completed"):
                    update_request_status(req[0], True)
                    st.success(f"Request {req[0]} marked as completed.")
            st.write("---")
    else:
        st.write("No requests found.")

def view_mistakes():
    mistakes = get_mistakes()
    if mistakes:
        for mistake in mistakes:
            st.write(f"Ticket ID: {mistake[3]} | Agent: {mistake[2]} | Error: {mistake[4]} | Timestamp: {mistake[5]}")
            st.write("---")
    else:
        st.write("No mistakes found.")

def view_group_messages():
    messages = get_group_messages()
    if messages:
        for msg in messages:
            st.write(f"{msg[1]}: {msg[2]} | {msg[3]}")
            st.write("---")
    else:
        st.write("No messages found.")

def manage_users():
    users = get_all_users()
    if users:
        for user in users:
            st.write(f"User ID: {user[0]} | Username: {user[1]} | Role: {user[2]}")
            if user[2] != 'admin':  # Only allow deleting non-admin users
                if st.button(f"Delete User {user[1]}"):
                    if delete_user(user[0]):
                        st.success(f"User {user[1]} deleted.")
                    else:
                        st.error(f"Failed to delete user {user[1]}.")
            st.write("---")
    else:
        st.write("No users found.")

def manage_hold_images():
    images = get_hold_images()
    if images:
        for img in images:
            img_data = io.BytesIO(img[2])
            img_pil = Image.open(img_data)
            st.image(img_pil)
            if st.button(f"Clear Image {img[0]}"):
                if clear_hold_images():
                    st.success(f"Image {img[0]} cleared.")
                else:
                    st.error(f"Failed to clear image {img[0]}.")
    else:
        st.write("No HOLD images found.")

def upload_hold_image():
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        if st.button("Upload Image"):
            add_hold_image(st.session_state.username, uploaded_file.read())
            st.success("Image uploaded successfully.")

if __name__ == "__main__":
    init_db()
    if 'username' not in st.session_state:
        show_login()
    else:
        show_dashboard()
