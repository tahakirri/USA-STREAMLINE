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
        (recipient, message, datetime.now().isoformat())
    )

# Initialize database
init_db()

# --- Tailwind CSS Setup ---
def load_tailwind():
    st.markdown("""
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .stApp {
            background-color: #f3f4f6 !important;
        }
        .stTextInput input, .stTextArea textarea, .stSelectbox select {
            border-radius: 0.375rem !important;
            padding: 0.5rem 0.75rem !important;
        }
        .stButton button {
            border-radius: 0.375rem !important;
            padding: 0.5rem 1rem !important;
            font-weight: 500 !important;
        }
        .stDataFrame {
            border-radius: 0.375rem !important;
            box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05) !important;
        }
    </style>
    """, unsafe_allow_html=True)

load_tailwind()

# --- Authentication ---
def authenticate():
    if 'authenticated' not in st.session_state:
        st.markdown("""
        <div class="min-h-screen flex items-center justify-center bg-gray-50">
            <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
                <h2 class="text-2xl font-bold text-center text-gray-800 mb-6">Login</h2>
                <form>
                    <div class="mb-4">
                        <label class="block text-gray-700 text-sm font-bold mb-2" for="username">
                            Username
                        </label>
                        <input class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" id="username" type="text" placeholder="Username">
                    </div>
                    <div class="mb-6">
                        <label class="block text-gray-700 text-sm font-bold mb-2" for="password">
                            Password
                        </label>
                        <input class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline" id="password" type="password" placeholder="Password">
                    </div>
                    <div class="flex items-center justify-between">
                        <button class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline" type="button">
                            Sign In
                        </button>
                    </div>
                </form>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
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

# --- Notification System ---
def show_notifications():
    unread_count = execute_query(
        "SELECT COUNT(*) FROM notifications WHERE recipient = ? AND is_read = 0",
        (st.session_state.user,),
        fetch=True
    )[0][0]
    
    with st.sidebar:
        st.markdown(f"""
        <div class="relative">
            <button class="flex items-center space-x-1 text-gray-700 hover:text-gray-900">
                <span class="relative">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                    </svg>
                    {f'<span class="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-500 rounded-full">{unread_count}</span>' if unread_count > 0 else ''}
                </span>
                <span>Notifications</span>
            </button>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.get('show_notifications'):
            notifs = pd.read_sql(
                '''SELECT message, created_at FROM notifications 
                WHERE recipient = ? ORDER BY created_at DESC LIMIT 10''',
                get_db_connection(),
                params=(st.session_state.user,)
            
            with st.expander("Your Notifications", expanded=True):
                for _, row in notifs.iterrows():
                    st.markdown(f"""
                    <div class="p-3 mb-2 bg-gray-100 rounded-lg">
                        <p class="text-sm text-gray-600">{row['created_at']}</p>
                        <p class="font-medium">{row['message']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                execute_query(
                    "UPDATE notifications SET is_read = 1 WHERE recipient = ?",
                    (st.session_state.user,)
                )

show_notifications()

# --- Navigation ---
with st.sidebar:
    st.markdown("""
    <div class="space-y-4">
        <h3 class="text-lg font-medium text-gray-900">Navigation</h3>
        <div class="space-y-2">
            <a href="#" class="flex items-center space-x-2 text-gray-700 hover:text-blue-600">
                <span>📋</span>
                <span>Request</span>
            </a>
            <a href="#" class="flex items-center space-x-2 text-gray-700 hover:text-blue-600">
                <span>🖼️</span>
                <span>HOLD</span>
            </a>
            <a href="#" class="flex items-center space-x-2 text-gray-700 hover:text-blue-600">
                <span>❌</span>
                <span>Ticket Mistakes</span>
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    section = st.radio("Go to", ["📋 Request", "🖼️ HOLD", "❌ Ticket Mistakes"], label_visibility="collapsed")

# --- Request Section ---
if section == "📋 Request":
    st.markdown("""
    <div class="mb-6">
        <h1 class="text-2xl font-bold text-gray-800">Request Section</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics Dashboard
    request_data = get_requests_df()
    if not request_data.empty:
        st.markdown("""
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div class="bg-white p-4 rounded-lg shadow">
                <p class="text-sm font-medium text-gray-500">Total Requests</p>
                <p class="text-2xl font-semibold">{len(request_data)}</p>
            </div>
            <div class="bg-white p-4 rounded-lg shadow">
                <p class="text-sm font-medium text-gray-500">Completed</p>
                <p class="text-2xl font-semibold">{request_data['completed'].sum()}</p>
            </div>
            <div class="bg-white p-4 rounded-lg shadow">
                <p class="text-sm font-medium text-gray-500">Completion Rate</p>
                <p class="text-2xl font-semibold">{(request_data['completed'].sum()/len(request_data)*100:.1f}%</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Request Form
    with st.form("request_form"):
        st.markdown("""
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
                <h3 class="text-lg font-medium text-gray-900 mb-4">Request Details</h3>
                <div class="space-y-4">
        """, unsafe_allow_html=True)
        
        agent_name = st.text_input("👤 Agent Name", value=st.session_state.user)
        req_type = st.selectbox("🔍 Type", ["Email", "Phone Number", "Ticket ID"])
        identifier = st.text_input("🆔 ID")
        
        st.markdown("""
                </div>
            </div>
            <div>
                <h3 class="text-lg font-medium text-gray-900 mb-4">Comments</h3>
        """, unsafe_allow_html=True)
        
        comment = st.text_area("💬 Comment", height=150)
        
        st.markdown("""
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        submitted = st.form_submit_button("✅ Submit Request", use_container_width=True)
        if submitted:
            if not all([agent_name, req_type, identifier, comment]):
                st.error("Please fill all fields")
            else:
                execute_query(
                    '''INSERT INTO requests (agent_name, type, identifier, comment, timestamp)
                    VALUES (?, ?, ?, ?, ?)''',
                    (agent_name, req_type, identifier, comment, datetime.now().isoformat())
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
        st.markdown("""
        <div class="mt-8">
            <h3 class="text-lg font-medium text-gray-900 mb-4">Request List</h3>
        </div>
        """, unsafe_allow_html=True)
        
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
                (row['completed'], row['id'])
            )

# --- HOLD Section ---
elif section == "🖼️ HOLD":
    st.markdown("""
    <div class="mb-6">
        <h1 class="text-2xl font-bold text-gray-800">HOLD Section</h1>
    </div>
    """, unsafe_allow_html=True)
    
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
    
    if st.button("🔄 View Latest HOLD Image", use_container_width=True):
        if os.path.exists(LATEST_IMAGE_PATH):
            st.image(Image.open(LATEST_IMAGE_PATH), use_column_width=True)
        else:
            st.warning("No HOLD image available")

# --- Mistakes Section ---
elif section == "❌ Ticket Mistakes":
    st.markdown("""
    <div class="mb-6">
        <h1 class="text-2xl font-bold text-gray-800">Ticket Mistakes</h1>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("mistake_form"):
        st.markdown("""
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
                <h3 class="text-lg font-medium text-gray-900 mb-4">Agent Details</h3>
                <div class="space-y-4">
        """, unsafe_allow_html=True)
        
        team_leader = st.text_input("👥 Team Leader")
        agent_name = st.text_input("👤 Agent Name")
        ticket_id = st.text_input("🎫 Ticket ID")
        
        st.markdown("""
                </div>
            </div>
            <div>
                <h3 class="text-lg font-medium text-gray-900 mb-4">Error Details</h3>
        """, unsafe_allow_html=True)
        
        error = st.text_area("⚠️ Error Description", height=150)
        
        st.markdown("""
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        submitted = st.form_submit_button("✅ Submit Mistake", use_container_width=True)
        if submitted:
            if not all([team_leader, agent_name, ticket_id, error]):
                st.error("Please fill all fields")
            else:
                execute_query(
                    '''INSERT INTO mistakes (team_leader, agent_name, ticket_id, error, timestamp)
                    VALUES (?, ?, ?, ?, ?)''',
                    (team_leader, agent_name, ticket_id, error, datetime.now().isoformat())
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
        st.markdown("""
        <div class="mt-8">
            <h3 class="text-lg font-medium text-gray-900 mb-4">Mistakes Log</h3>
        </div>
        """, unsafe_allow_html=True)
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
