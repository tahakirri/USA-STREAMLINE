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

# --- Theme Management ---
with st.sidebar:
    st.markdown("### 🧭 Navigation")
    section = st.radio("Choose Section", [
        "📋 Request", 
        "🖼️ HOLD", 
        "❌ Ticket Mistakes"
    ])
    
    # Theme toggle
    dark_mode = st.toggle("🌙 Dark Mode", value=True)

# Theme CSS
if dark_mode:
    theme_css = """
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
            --button-text: #ffffff;
            --table-bg: #1e2129;
            --table-text: #ffffff;
        }
    </style>
    """
else:
    theme_css = """
    <style>
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
    </style>
    """

common_css = """
<style>
    .stApp {
        background-color: var(--background);
        color: var(--primary-text);
    }
    [data-testid="stSidebar"] {
        background-color: var(--sidebar);
    }
    h1, h2, h3, h4 {
        color: var(--header);
    }
    .stTextInput > div > div > input, 
    .stSelectbox > div > div > div > select,
    .stTextArea > div > div > textarea {
        background-color: var(--input-bg);
        color: var(--input-text);
        border: 1px solid var(--input-border);
    }
    .dataframe {
        background-color: var(--table-bg);
        color: var(--table-text);
    }
    .stButton > button {
        background-color: var(--button-bg);
        color: var(--button-text);
        border: none;
    }
    .stButton > button:hover {
        background-color: var(--button-hover);
    }
    .stCheckbox label, .stRadio label, 
    .stTextInput label, .stTextArea label {
        color: var(--primary-text) !important;
    }
</style>
"""

st.markdown(theme_css + common_css, unsafe_allow_html=True)

# --- Request Section ---
if section == "📋 Request":
    st.header("📋 Request Section")

    col1, col2 = st.columns([3, 2])
    
    with col1:
        agent_name_input = st.text_input("👤 Agent Name", key="agent_name")
        type_input = st.selectbox("🔍 Type", ["Email", "Phone Number", "Ticket ID"], key="type")
        id_input = st.text_input("🆔 ID", key="id")
    
    with col2:
        comment_input = st.text_area("💬 Comment", height=150, key="comment")  
    
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    with btn_col1:
        submit_button = st.button("✅ Submit Data")
    
    with btn_col2:
        refresh_button = st.button("🔄 Refresh Data")
    
    with btn_col3:
        clear_button = st.button("🗑️ Clear Data")
    
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
        st.write("### 📋 Submitted Requests:")
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
    st.header("🖼️ HOLD Section")
    uploaded_image = st.file_uploader("📤 Upload Image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    
    if uploaded_image:
        try:
            image = Image.open(uploaded_image)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            os.makedirs(os.path.dirname(LATEST_IMAGE_PATH), exist_ok=True)
            image.save(LATEST_IMAGE_PATH, quality=85)
            st.image(image, caption="📸 Uploaded Image", use_container_width=True)
            st.success("✅ Image uploaded successfully!")
        except Exception as e:
            st.error(f"❌ Error uploading image: {str(e)}")

    if st.button("🔍 CHECK HOLD"):
        if os.path.exists(LATEST_IMAGE_PATH):
            try:
                latest_image = Image.open(LATEST_IMAGE_PATH)
                st.image(latest_image, caption="📸 Latest Uploaded Image", use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error displaying image: {str(e)}")
        else:
            st.write("❌ No image uploaded.")

# --- Mistakes Section ---
elif section == "❌ Ticket Mistakes":
    st.header("❌ Ticket Mistakes Section")

    col1, col2 = st.columns([3, 2])  
    
    with col1:
        team_leader_input = st.text_input("👥 Team Leader Name", key="team_leader")
        agent_name_mistake_input = st.text_input("👤 Agent Name", key="agent_name_mistake")
        ticket_id_input = st.text_input("🆔 Ticket ID", key="ticket_id")
    
    with col2:
        error_input = st.text_area("⚠️ Error", height=150, key="error")
    
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        submit_mistake_button = st.button("✅ Submit Mistake")
    
    with btn_col2:
        refresh_mistake_button = st.button("🔄 Refresh Mistakes")
    
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
        st.write("❌ Mistakes Table:")
        st.dataframe(mistake_data, use_container_width=True)

# --- Migration Utility (One-time use) ---
with st.sidebar:
    if st.checkbox("Show Developer Options"):
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
