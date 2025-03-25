import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sqlite3
from contextlib import closing
from PIL import Image
import time
import zipfile
import plotly.express as px

# --- Constants ---
DB_NAME = 'collab_app.db'
UPLOAD_DIRECTORY = 'uploaded_images'
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
LATEST_IMAGE_PATH = os.path.join(UPLOAD_DIRECTORY, 'latest_hold_image.jpg')
AUTO_REFRESH_INTERVAL = 300  # 5 minutes
USER_CREDENTIALS = {"admin": "admin123", "agent1": "pass123"}

# --- Database Setup ---
def init_db():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                completed BOOLEAN DEFAULT 0,
                agent_name TEXT NOT NULL,
                type TEXT NOT NULL,
                identifier TEXT NOT NULL,
                comment TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_leader TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                ticket_id TEXT NOT NULL,
                error TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY,
                recipient TEXT,
                message TEXT,
                is_read BOOLEAN DEFAULT 0,
                created_at TEXT
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_requests_agent ON requests(agent_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON notifications(recipient)')
        conn.commit()

def get_db_connection():
    return sqlite3.connect(DB_NAME)

@st.cache_data(ttl=60)
def execute_query(query, params=(), fetch=False):
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetch:
            return cursor.fetchall()
        conn.commit()

@st.cache_data(ttl=30)
def get_requests_df():
    return pd.read_sql('SELECT * FROM requests', get_db_connection())

@st.cache_data(ttl=30)
def get_mistakes_df():
    return pd.read_sql('SELECT * FROM mistakes', get_db_connection())

def create_notification(recipient, message):
    execute_query(
        '''INSERT INTO notifications (recipient, message, created_at)
        VALUES (?, ?, ?)''',
        params=(recipient, message, datetime.now().isoformat())
    )

# Initialize database
init_db()

# --- Authentication ---
def authenticate():
    if 'authenticated' not in st.session_state:
        with st.sidebar:
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                if USER_CREDENTIALS.get(username) == password:
                    st.session_state.authenticated = True
                    st.session_state.user = username
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        st.stop()

authenticate()

# --- UI Configuration ---
st.set_page_config(
    page_title="USA Collab", 
    page_icon="✉️", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- Responsive Design CSS ---
st.markdown("""
<style>
    @media screen and (max-width: 768px) {
        .stColumns > div {
            flex-direction: column !important;
        }
        .stTextInput input, .stTextArea textarea, .stSelectbox select {
            font-size: 14px !important;
        }
        .stButton button {
            padding: 8px 12px !important;
            font-size: 14px !important;
        }
    }
    
    :root {
        --primary-text: #000000;
        --secondary-text: #333333;
        --background: #ffffff;
        --sidebar: #f0f2f6;
        --header: #0068c9;
        --input-bg: #ffffff;
        --input-border: #d1d5db;
        --input-text: #000000;
        --button-bg: #0068c9;
        --button-hover: #0055a5;
        --button-text: #ffffff;
        --table-bg: #ffffff;
        --table-text: #000000;
    }
    
    [data-testid="stSidebar"] {
        background-color: var(--sidebar) !important;
    }
    .stApp {
        background-color: var(--background) !important;
        color: var(--primary-text) !important;
    }
    h1, h2, h3, h4 {
        color: var(--header) !important;
    }
    .stTextInput > div > div > input, 
    .stSelectbox > div > div > div > select,
    .stTextArea > div > div > textarea {
        background-color: var(--input-bg) !important;
        color: var(--input-text) !important;
        border: 1px solid var(--input-border) !important;
    }
    .stDataFrame {
        background-color: var(--table-bg) !important;
        color: var(--table-text) !important;
    }
    .stButton > button {
        background-color: var(--button-bg) !important;
        color: var(--button-text) !important;
    }
    .stButton > button:hover {
        background-color: var(--button-hover) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Theme Toggle ---
with st.sidebar:
    dark_mode = st.toggle("🌙 Dark Mode", value=False)
    if dark_mode:
        st.markdown("""
        <style>
            :root {
                --primary-text: #ffffff;
                --secondary-text: #f0f0f0;
                --background: #0e1117;
                --sidebar: #1e2129;
                --header: #4db8ff;
                --input-bg: #2c2f36;
                --input-border: #4a4e57;
                --input-text: #ffffff;
                --button-bg: #4db8ff;
                --button-hover: #3aa0ff;
                --table-bg: #1e2129;
                --table-text: #ffffff;
            }
        </style>
        """, unsafe_allow_html=True)

# --- Auto-Refresh ---
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > AUTO_REFRESH_INTERVAL:
    st.session_state.last_refresh = time.time()
    st.rerun()

# --- Notification System ---
def show_notifications():
    unread_count = execute_query(
        "SELECT COUNT(*) FROM notifications WHERE recipient = ? AND is_read = 0",
        params=(st.session_state.user,),
        fetch=True
    )[0][0]
    
    with st.sidebar:
        if st.button(f"🔔 Notifications ({unread_count})"):
            st.session_state.show_notifications = not st.session_state.get('show_notifications', False)
        
        if st.session_state.get('show_notifications'):
            with st.expander("Your Notifications", expanded=True):
                notifs = pd.read_sql(
                    '''SELECT message, created_at FROM notifications 
                    WHERE recipient = ? ORDER BY created_at DESC LIMIT 10''',
                    get_db_connection(),
                    params=(st.session_state.user,)
                
                for _, row in notifs.iterrows():
                    st.write(f"{row['created_at']}: {row['message']}")
                
                execute_query(
                    "UPDATE notifications SET is_read = 1 WHERE recipient = ?",
                    params=(st.session_state.user,)
                )

show_notifications()

# --- Backup System ---
with st.sidebar.expander("💾 Backup Tools"):
    if st.button("Create Backup"):
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        with open(DB_NAME, 'rb') as f_src, open(backup_name, 'wb') as f_dst:
            f_dst.write(f_src.read())
        st.success(f"Backup created: {backup_name}")
    
    backups = [f for f in os.listdir() if f.startswith('backup_') and f.endswith('.db')]
    selected_backup = st.selectbox("Select Backup", backups)
    
    if st.button("Restore Backup"):
        with open(selected_backup, 'rb') as f_src, open(DB_NAME, 'wb') as f_dst:
            f_dst.write(f_src.read())
        st.cache_data.clear()
        st.success("Database restored! Please refresh the page.")

# --- Navigation ---
with st.sidebar:
    st.markdown("### 🧭 Navigation")
    section = st.radio("Go to", ["📋 Request", "🖼️ HOLD", "❌ Ticket Mistakes"])

# --- Request Section ---
if section == "📋 Request":
    st.header("📋 Request Section")
    
    # Metrics Dashboard
    request_data = get_requests_df()
    if not request_data.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Requests", len(request_data))
        with col2:
            st.metric("Completed", request_data['completed'].sum())
        with col3:
            st.metric("Completion Rate", 
                     f"{(request_data['completed'].sum()/len(request_data)*100):.1f}%")
    
    # Request Form
    with st.form("request_form"):
        col1, col2 = st.columns([1, 1])
        with col1:
            agent_name = st.text_input("👤 Agent Name", value=st.session_state.user)
            req_type = st.selectbox("🔍 Type", ["Email", "Phone Number", "Ticket ID"])
            identifier = st.text_input("🆔 ID")
        with col2:
            comment = st.text_area("💬 Comment", height=150)
        
        submitted = st.form_submit_button("✅ Submit Request")
        if submitted:
            if not all([agent_name, req_type, identifier, comment]):
                st.error("Please fill all fields")
            else:
                execute_query(
                    '''INSERT INTO requests (agent_name, type, identifier, comment, timestamp)
                    VALUES (?, ?, ?, ?, ?)''',
                    params=(agent_name, req_type, identifier, comment, datetime.now().isoformat())
                )
                
                create_notification(
                    "admin",
                    f"New request submitted by {agent_name}: {req_type} - {identifier}"
                )
                
                st.success("Request submitted!")
                time.sleep(1)
                st.rerun()
    
    # Request List
    if not request_data.empty:
        st.subheader("📋 Request List")
        edited_df = st.data_editor(
            request_data,
            column_config={
                "id": None,
                "completed": st.column_config.CheckboxColumn(
                    "✅ Completed",
                    help="Mark request as completed",
                    default=False
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Save changes
        for _, row in edited_df.iterrows():
            execute_query(
                'UPDATE requests SET completed = ? WHERE id = ?',
                params=(row['completed'], row['id'])
            )

# --- HOLD Section ---
elif section == "🖼️ HOLD":
    st.header("🖼️ HOLD Section")
    
    uploaded_image = st.file_uploader("📤 Upload Image", type=["jpg", "jpeg", "png"])
    
    if uploaded_image:
        try:
            img = Image.open(uploaded_image)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(LATEST_IMAGE_PATH, quality=85)
            st.image(img, caption="Uploaded Image", use_column_width=True)
            st.success("Image saved successfully!")
            
            create_notification(
                "admin",
                f"New HOLD image uploaded by {st.session_state.user}"
            )
        except Exception as e:
            st.error(f"Error saving image: {str(e)}")
    
    if st.button("🔄 View Latest HOLD Image"):
        if os.path.exists(LATEST_IMAGE_PATH):
            st.image(Image.open(LATEST_IMAGE_PATH), use_column_width=True)
        else:
            st.warning("No HOLD image available")

# --- Mistakes Section ---
elif section == "❌ Ticket Mistakes":
    st.header("❌ Ticket Mistakes")
    
    with st.form("mistake_form"):
        col1, col2 = st.columns([1, 1])
        with col1:
            team_leader = st.text_input("👥 Team Leader")
            agent_name = st.text_input("👤 Agent Name")
            ticket_id = st.text_input("🎫 Ticket ID")
        with col2:
            error = st.text_area("⚠️ Error Description", height=150)
        
        submitted = st.form_submit_button("✅ Submit Mistake")
        if submitted:
            if not all([team_leader, agent_name, ticket_id, error]):
                st.error("Please fill all fields")
            else:
                execute_query(
                    '''INSERT INTO mistakes (team_leader, agent_name, ticket_id, error, timestamp)
                    VALUES (?, ?, ?, ?, ?)''',
                    params=(team_leader, agent_name, ticket_id, error, datetime.now().isoformat())
                )
                
                create_notification(
                    team_leader,
                    f"New mistake reported for {agent_name} on ticket {ticket_id}"
                )
                
                st.success("Mistake reported!")
                time.sleep(1)
                st.rerun()
    
    # Mistakes List
    mistakes = get_mistakes_df()
    if not mistakes.empty:
        st.subheader("❌ Mistakes Log")
        st.dataframe(mistakes, use_container_width=True)

# --- Auto-Refresh Controls ---
with st.sidebar.expander("⚙️ Settings"):
    auto_refresh = st.checkbox("Enable Auto-Refresh", value=True)
    if auto_refresh:
        refresh_rate = st.slider("Refresh Rate (seconds)", 30, 600, AUTO_REFRESH_INTERVAL)
        st.session_state.auto_refresh = True
        st.session_state.refresh_rate = refresh_rate
    else:
        st.session_state.auto_refresh = False

# --- Performance Info ---
with st.sidebar.expander("📊 Performance"):
    db_size = os.path.getsize(DB_NAME) / (1024 * 1024)  # in MB
    st.write(f"Database size: {db_size:.2f} MB")
    st.write(f"Requests count: {len(get_requests_df())}")
    st.write(f"Mistakes count: {len(get_mistakes_df())}")
    
    if st.button("Clear Cache"):
        st.cache_data.clear()
        st.success("Cache cleared!")
