import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sqlite3
from contextlib import closing
from PIL import Image

# --- Database Setup ---
DB_NAME = 'collab_app.db'
UPLOAD_DIRECTORY = 'uploaded_images'
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
LATEST_IMAGE_PATH = os.path.join(UPLOAD_DIRECTORY, 'latest_hold_image.jpg')

def init_db():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cursor = conn.cursor()
        # Requests table
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
        # Mistakes table
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
        conn.commit()

def get_db_connection():
    return sqlite3.connect(DB_NAME)

def execute_query(query, params=(), fetch=False):
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetch:
            return cursor.fetchall()
        conn.commit()

def get_requests_df():
    return pd.read_sql('SELECT * FROM requests', get_db_connection())

def get_mistakes_df():
    return pd.read_sql('SELECT * FROM mistakes', get_db_connection())

# Initialize database
init_db()

# --- UI Configuration ---
st.set_page_config(
    page_title="USA Collab", 
    page_icon="✉️", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Inject Tailwind CSS
st.markdown("""
<script src="https://cdn.tailwindcss.com"></script>
<style>
    .stApp {
        background-color: #f3f4f6;
    }
    [data-testid="stSidebar"] {
        background-color: #1f2937;
    }
    .stTextInput > div > div > input, 
    .stSelectbox > div > div > div > select,
    .stTextArea > div > div > textarea {
        background-color: #ffffff;
        border: 1px solid #d1d5db;
        border-radius: 0.375rem;
        padding: 0.5rem;
    }
    .stButton > button {
        background-color: #3b82f6;
        color: white;
        border-radius: 0.375rem;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton > button:hover {
        background-color: #2563eb;
    }
    .stDataFrame {
        border-radius: 0.375rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar Navigation ---
with st.sidebar:
    st.markdown("""
    <div class="mb-6">
        <h3 class="text-xl font-semibold text-white mb-4">🧭 Navigation</h3>
        <div class="space-y-2">
    """, unsafe_allow_html=True)
    
    section = st.radio(
        "Choose Section",
        ["📋 Request", "🖼️ HOLD", "❌ Ticket Mistakes"],
        label_visibility="collapsed"
    )
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Theme toggle
    dark_mode = st.toggle("🌙 Dark Mode", value=True)
    
    # Developer options
    if st.checkbox("Show Developer Options"):
        st.markdown('<div class="mt-6 p-4 bg-gray-800 rounded-lg">', unsafe_allow_html=True)
        if st.button("⚠️ Initialize Database"):
            init_db()
            st.success("Database initialized!")
        
        if st.button("🔄 Export Requests to CSV"):
            df = get_requests_df()
            st.download_button(
                "Download Requests",
                df.to_csv(index=False),
                "requests_export.csv"
            )
        st.markdown('</div>', unsafe_allow_html=True)

# Apply dark mode if selected
if dark_mode:
    st.markdown("""
    <style>
        .stApp {
            background-color: #111827;
            color: #f3f4f6;
        }
        [data-testid="stSidebar"] {
            background-color: #1f2937;
        }
        .stTextInput > div > div > input, 
        .stSelectbox > div > div > div > select,
        .stTextArea > div > div > textarea {
            background-color: #1f2937;
            color: #f3f4f6;
            border-color: #374151;
        }
        .stButton > button {
            background-color: #2563eb;
        }
        .stButton > button:hover {
            background-color: #1d4ed8;
        }
        .stCheckbox label, .stRadio label, 
        .stTextInput label, .stTextArea label {
            color: #f3f4f6 !important;
        }
    </style>
    """, unsafe_allow_html=True)

# --- Request Section ---
if section == "📋 Request":
    st.markdown("""
    <div class="mb-6">
        <h1 class="text-2xl font-bold text-blue-600 mb-4">📋 Request Section</h1>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown('<div class="mb-4">', unsafe_allow_html=True)
        agent_name_input = st.text_input("👤 Agent Name", key="agent_name")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="mb-4">', unsafe_allow_html=True)
        type_input = st.selectbox("🔍 Type", ["Email", "Phone Number", "Ticket ID"], key="type")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="mb-4">', unsafe_allow_html=True)
        id_input = st.text_input("🆔 ID", key="id")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="mb-4 h-full">', unsafe_allow_html=True)
        comment_input = st.text_area("💬 Comment", height=150, key="comment")
        st.markdown('</div>', unsafe_allow_html=True)
    
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    with btn_col1:
        submit_button = st.button("✅ Submit Data", use_container_width=True)
    
    with btn_col2:
        refresh_button = st.button("🔄 Refresh Data", use_container_width=True)
    
    with btn_col3:
        clear_button = st.button("🗑️ Clear Data", use_container_width=True)
    
    if clear_button:
        clear_password = st.text_input("🔐 Enter password to clear data:", type="password", key="clear_password")
        if clear_password == "wipe":
            execute_query("DELETE FROM requests")
            st.success("✅ Request data has been cleared!")
        elif clear_password:
            st.error("❌ Incorrect password")
    
    if submit_button:
        if not agent_name_input or not id_input or not comment_input:
            st.error("❗ Please fill out all fields.")
        else:
            execute_query('''
                INSERT INTO requests (agent_name, type, identifier, comment, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (agent_name_input, type_input, id_input, comment_input, 
                  datetime.now().strftime("%H:%M:%S")))
            st.success("✅ Data Submitted!")

    request_data = get_requests_df()
    if not request_data.empty:
        st.markdown("""
        <div class="mb-4">
            <h2 class="text-xl font-semibold text-blue-600 mb-2">📋 Submitted Requests:</h2>
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
        
        # Update completed status
        for _, row in edited_df.iterrows():
            execute_query(
                'UPDATE requests SET completed = ? WHERE id = ?',
                (row['completed'], row['id'])
            )

# --- HOLD Section ---
elif section == "🖼️ HOLD":
    st.markdown("""
    <div class="mb-6">
        <h1 class="text-2xl font-bold text-blue-600 mb-4">🖼️ HOLD Section</h1>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="mb-4 p-4 bg-white rounded-lg shadow">', unsafe_allow_html=True)
    uploaded_image = st.file_uploader("📤 Upload Image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_image:
        try:
            image = Image.open(uploaded_image)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            os.makedirs(os.path.dirname(LATEST_IMAGE_PATH), exist_ok=True)
            image.save(LATEST_IMAGE_PATH, quality=85)
            
            st.markdown('<div class="mb-4 p-4 bg-white rounded-lg shadow">', unsafe_allow_html=True)
            st.image(image, caption="📸 Uploaded Image", use_container_width=True)
            st.success("✅ Image uploaded successfully!")
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ Error uploading image: {str(e)}")

    if st.button("🔍 CHECK HOLD", use_container_width=True):
        if os.path.exists(LATEST_IMAGE_PATH):
            try:
                latest_image = Image.open(LATEST_IMAGE_PATH)
                st.markdown('<div class="mb-4 p-4 bg-white rounded-lg shadow">', unsafe_allow_html=True)
                st.image(latest_image, caption="📸 Latest Uploaded Image", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ Error displaying image: {str(e)}")
        else:
            st.write("❌ No image uploaded.")

# --- Mistakes Section ---
elif section == "❌ Ticket Mistakes":
    st.markdown("""
    <div class="mb-6">
        <h1 class="text-2xl font-bold text-blue-600 mb-4">❌ Ticket Mistakes Section</h1>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])  
    
    with col1:
        st.markdown('<div class="mb-4">', unsafe_allow_html=True)
        team_leader_input = st.text_input("👥 Team Leader Name", key="team_leader")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="mb-4">', unsafe_allow_html=True)
        agent_name_mistake_input = st.text_input("👤 Agent Name", key="agent_name_mistake")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="mb-4">', unsafe_allow_html=True)
        ticket_id_input = st.text_input("🆔 Ticket ID", key="ticket_id")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="mb-4 h-full">', unsafe_allow_html=True)
        error_input = st.text_area("⚠️ Error", height=150, key="error")
        st.markdown('</div>', unsafe_allow_html=True)
    
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        submit_mistake_button = st.button("✅ Submit Mistake", use_container_width=True)
    
    with btn_col2:
        refresh_mistake_button = st.button("🔄 Refresh Mistakes", use_container_width=True)
    
    if submit_mistake_button:
        if not team_leader_input or not agent_name_mistake_input or not ticket_id_input or not error_input:
            st.error("❗ Please fill out all fields.")
        else:
            execute_query('''
                INSERT INTO mistakes (team_leader, agent_name, ticket_id, error, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (team_leader_input, agent_name_mistake_input, ticket_id_input, 
                  error_input, datetime.now().strftime("%H:%M:%S")))
            st.success("✅ Mistake Submitted!")

    if refresh_mistake_button:
        st.rerun()

    mistake_data = get_mistakes_df()
    if not mistake_data.empty:
        st.markdown("""
        <div class="mb-4">
            <h2 class="text-xl font-semibold text-blue-600 mb-2">❌ Mistakes Table:</h2>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(mistake_data, use_container_width=True)
