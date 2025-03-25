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

# --- Professional CSS Styling ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary: #2563eb;
        --primary-hover: #1d4ed8;
        --sidebar: #1e293b;
        --sidebar-hover: #334155;
        --background: #f8fafc;
        --card: #ffffff;
        --text: #0f172a;
        --text-light: #64748b;
        --border: #e2e8f0;
    }
    
    body {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: var(--background);
    }
    
    [data-testid="stSidebar"] {
        background-color: var(--sidebar) !important;
        border-right: 1px solid var(--sidebar-hover);
    }
    
    .sidebar .nav-item {
        padding: 0.5rem 1rem;
        border-radius: 6px;
        margin-bottom: 4px;
        transition: all 0.2s;
        color: #e2e8f0;
    }
    
    .sidebar .nav-item:hover {
        background-color: var(--sidebar-hover);
    }
    
    .sidebar .nav-item.active {
        background-color: var(--primary);
        color: white;
    }
    
    .sidebar .nav-icon {
        margin-right: 10px;
        font-size: 18px;
    }
    
    .stButton>button {
        background-color: var(--primary);
        color: white;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.2s;
        border: none;
    }
    
    .stButton>button:hover {
        background-color: var(--primary-hover);
        transform: translateY(-1px);
    }
    
    .stTextInput>div>div>input,
    .stSelectbox>div>div>select,
    .stTextArea>div>div>textarea {
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 8px 12px;
    }
    
    .card {
        background-color: var(--card);
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        border: 1px solid var(--border);
    }
    
    h1 {
        color: var(--text);
        font-weight: 600;
        font-size: 1.8rem;
        margin-bottom: 1.5rem;
    }
    
    h2 {
        color: var(--text);
        font-weight: 600;
        font-size: 1.4rem;
        margin-bottom: 1rem;
    }
    
    .stDataFrame {
        border-radius: 8px;
        border: 1px solid var(--border);
    }
    
    .icon-lg {
        font-size: 24px;
        vertical-align: middle;
        margin-right: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- Minimalist Sidebar ---
with st.sidebar:
    st.markdown("""
    <div style="padding: 1rem 0 2rem 0;">
        <h2 style="color: white; font-weight: 600; font-size: 1.2rem; border-bottom: 1px solid #334155; padding-bottom: 1rem; margin-bottom: 1.5rem;">
            <span class="icon-lg">📊</span>Collab Dashboard
        </h2>
        <div class="sidebar">
    """, unsafe_allow_html=True)
    
    nav_options = {
        "📋 Request": "request",
        "🖼️ Media": "hold",
        "⚠️ Mistakes": "mistakes"
    }
    
    for icon, label in nav_options.items():
        active = "active" if section.lower() in label else ""
        st.markdown(f"""
        <div class="nav-item {active}" onclick="window.location.href='?section={label}'" style="cursor: pointer;">
            <span class="nav-icon">{icon}</span>{label.capitalize()}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Minimalist dark mode toggle
    dark_mode = st.checkbox("Dark Mode", value=False, key="dark_mode")
    
    # Add subtle footer
    st.markdown("""
    <div style="position: absolute; bottom: 1rem; left: 1rem; right: 1rem; color: #94a3b8; font-size: 0.8rem; border-top: 1px solid #334155; padding-top: 1rem;">
        USA Collab v1.0
    </div>
    """, unsafe_allow_html=True)

# Apply dark mode if selected
if dark_mode:
    st.markdown("""
    <style>
        :root {
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --sidebar: #0f172a;
            --sidebar-hover: #1e293b;
            --background: #020617;
            --card: #1e293b;
            --text: #f8fafc;
            --text-light: #94a3b8;
            --border: #334155;
        }
        
        .stDataFrame {
            background-color: #1e293b !important;
            color: white !important;
        }
    </style>
    """, unsafe_allow_html=True)

# --- Request Section ---
if "request" in section.lower():
    st.markdown("""
    <div class="card">
        <h1><span class="icon-lg">📋</span>Request Management</h1>
    """, unsafe_allow_html=True)
    
    with st.container():
        col1, col2 = st.columns([3, 2])
        
        with col1:
            agent_name_input = st.text_input("Agent Name", key="agent_name")
            type_input = st.selectbox("Type", ["Email", "Phone Number", "Ticket ID"], key="type")
            id_input = st.text_input("Identifier", key="id")
        
        with col2:
            comment_input = st.text_area("Comments", height=150, key="comment")
    
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    with btn_col1:
        if st.button("Submit Request", use_container_width=True):
            if not agent_name_input or not id_input or not comment_input:
                st.error("Please fill all required fields")
            else:
                execute_query('''
                    INSERT INTO requests (agent_name, type, identifier, comment, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (agent_name_input, type_input, id_input, comment_input, 
                      datetime.now().strftime("%H:%M:%S")))
                st.success("Request submitted successfully")
    
    with btn_col2:
        if st.button("Refresh Data", use_container_width=True):
            st.rerun()
    
    with btn_col3:
        if st.button("Clear Data", use_container_width=True):
            clear_password = st.text_input("Enter admin password:", type="password", key="clear_password")
            if clear_password == "wipe":
                execute_query("DELETE FROM requests")
                st.success("Database cleared")
            elif clear_password:
                st.error("Incorrect password")

    request_data = get_requests_df()
    if not request_data.empty:
        st.markdown("""
        <div class="card" style="margin-top: 1.5rem;">
            <h2><span class="icon-lg">📄</span>Recent Requests</h2>
        """, unsafe_allow_html=True)
        
        edited_df = st.data_editor(
            request_data,
            column_config={
                "id": None,
                "completed": st.column_config.CheckboxColumn(
                    "Completed",
                    help="Mark request as completed",
                    default=False
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        for _, row in edited_df.iterrows():
            execute_query(
                'UPDATE requests SET completed = ? WHERE id = ?',
                (row['completed'], row['id'])
            )
        
        st.markdown("</div>", unsafe_allow_html=True)

# --- HOLD Section ---
elif "hold" in section.lower():
    st.markdown("""
    <div class="card">
        <h1><span class="icon-lg">🖼️</span>Media Management</h1>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown("""
        <div class="card" style="margin-bottom: 1.5rem;">
            <h2>Upload Media</h2>
        """, unsafe_allow_html=True)
        
        uploaded_image = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        
        if uploaded_image:
            try:
                image = Image.open(uploaded_image)
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                os.makedirs(os.path.dirname(LATEST_IMAGE_PATH), exist_ok=True)
                image.save(LATEST_IMAGE_PATH, quality=85)
                
                st.image(image, caption="Uploaded Image", use_container_width=True)
                st.success("Image uploaded successfully")
            except Exception as e:
                st.error(f"Error uploading image: {str(e)}")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("View Latest Upload", use_container_width=True):
            if os.path.exists(LATEST_IMAGE_PATH):
                try:
                    latest_image = Image.open(LATEST_IMAGE_PATH)
                    st.image(latest_image, caption="Latest Upload", use_container_width=True)
                except Exception as e:
                    st.error(f"Error displaying image: {str(e)}")
            else:
                st.warning("No image available")

# --- Mistakes Section ---
elif "mistakes" in section.lower():
    st.markdown("""
    <div class="card">
        <h1><span class="icon-lg">⚠️</span>Error Tracking</h1>
    """, unsafe_allow_html=True)
    
    with st.container():
        col1, col2 = st.columns([3, 2])
        
        with col1:
            team_leader_input = st.text_input("Team Leader", key="team_leader")
            agent_name_mistake_input = st.text_input("Agent Name", key="agent_name_mistake")
            ticket_id_input = st.text_input("Ticket ID", key="ticket_id")
        
        with col2:
            error_input = st.text_area("Error Description", height=150, key="error")
    
    if st.button("Submit Error Report", use_container_width=True):
        if not team_leader_input or not agent_name_mistake_input or not ticket_id_input or not error_input:
            st.error("Please fill all required fields")
        else:
            execute_query('''
                INSERT INTO mistakes (team_leader, agent_name, ticket_id, error, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (team_leader_input, agent_name_mistake_input, ticket_id_input, 
                  error_input, datetime.now().strftime("%H:%M:%S")))
            st.success("Error report submitted")

    mistake_data = get_mistakes_df()
    if not mistake_data.empty:
        st.markdown("""
        <div class="card" style="margin-top: 1.5rem;">
            <h2><span class="icon-lg">📊</span>Recent Errors</h2>
        """, unsafe_allow_html=True)
        
        st.dataframe(
            mistake_data,
            hide_index=True,
            use_container_width=True
        )
        
        st.markdown("</div>", unsafe_allow_html=True)

# --- Hidden Developer Tools ---
with st.sidebar:
    if st.checkbox("Developer Tools", key="dev_tools"):
        st.markdown('<div class="card" style="padding: 1rem; margin-top: 1rem;">', unsafe_allow_html=True)
        
        if st.button("Initialize Database"):
            init_db()
            st.success("Database initialized")
        
        if st.button("Export Data to CSV"):
            df = get_requests_df()
            st.download_button(
                "Download CSV",
                df.to_csv(index=False),
                "requests_export.csv",
                use_container_width=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
