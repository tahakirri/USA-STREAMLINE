import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import pandas as pd
import os

# Initialize database with error handling
def init_db():
    conn = None
    try:
        # Create the database directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT CHECK(role IN ('agent', 'admin'))
            )
        """)
        
        # Create requests table
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
        
        # Create mistakes table
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
        
        # Insert admin user if not exists
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, password, role) 
            VALUES (?, ?, ?)
        """, ("TAHA KIRRI", hashlib.sha256("arise@99".encode()).hexdigest(), "admin"))
        
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Authenticate user with error handling
def authenticate(username, password):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role FROM users 
            WHERE username=? AND password=?
        """, (username, hash_password(password)))
        user = cursor.fetchone()
        return user[0] if user else None
    except sqlite3.Error as e:
        st.error(f"Authentication error: {e}")
        return None
    finally:
        if conn:
            conn.close()

# Insert new request with error handling
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
    except sqlite3.Error as e:
        st.error(f"Failed to add request: {e}")
    finally:
        if conn:
            conn.close()

# Insert new mistake with error handling
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
    except sqlite3.Error as e:
        st.error(f"Failed to add mistake: {e}")
    finally:
        if conn:
            conn.close()

# Fetch requests with error handling
def get_requests():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM requests 
            ORDER BY completed, timestamp DESC
        """)
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to fetch requests: {e}")
        return []
    finally:
        if conn:
            conn.close()

# Fetch mistakes with error handling
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

# Update request status with error handling
def update_request_status(request_id, completed):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE requests 
            SET completed=? 
            WHERE id=?
        """, (completed, request_id))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Failed to update request status: {e}")
    finally:
        if conn:
            conn.close()

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
    
    if section == "📋 Request":
        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader("Submit a Request")
        with col2:
            if st.button("🔄 Refresh Requests"):
                st.rerun()
        
        request_type = st.selectbox("Request Type", ["Email", "Phone Number", "Ticket ID"])
        identifier = st.text_input("Identifier")
        comment = st.text_area("Comment")
        
        if st.button("Submit Request"):
            if identifier and comment:
                add_request(st.session_state.username, request_type, identifier, comment)
                st.success("Request submitted!")
            else:
                st.warning("Please fill all required fields")

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

    elif section == "🖼️ HOLD":
        st.subheader("HOLD Section")
        uploaded_image = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
        if uploaded_image:
            st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
            st.success("Image uploaded successfully!")

    elif section == "❌ Ticket Mistakes":
        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader("Ticket Mistakes Section")
        with col2:
            if st.button("🔄 Refresh Mistakes"):
                st.rerun()
        
        team_leader = st.text_input("Team Leader Name")
        agent_name = st.text_input("Agent Name")
        ticket_id = st.text_input("Ticket ID")
        error_description = st.text_area("Error Description")
        
        if st.button("Submit Mistake"):
            if team_leader and agent_name and ticket_id and error_description:
                add_mistake(team_leader, agent_name, ticket_id, error_description)
                st.success("Mistake submitted!")
            else:
                st.warning("Please fill all fields")
        
        # Display submitted mistakes
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

    elif section == "⚙ Admin Panel" and st.session_state.role == "admin":
        st.subheader("Admin Panel")
        
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
