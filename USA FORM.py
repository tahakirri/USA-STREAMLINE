import streamlit as st
import pandas as pd
from datetime import datetime
import os
from PIL import Image

# Custom CSS for dark mode and enhanced styling
st.set_page_config(
    page_title="USA Collab", 
    page_icon="✉️", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Define custom CSS for dark mode and enhanced styling
st.markdown("""
<style>
    /* Dark Mode Theme */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    /* Custom Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #1e2129;
    }
    
    /* Header Styling */
    h1, h2, h3, h4 {
        color: #4db8ff;
    }
    
    /* Input and Select Box Styling */
    .stTextInput > div > div > input, 
    .stSelectbox > div > div > div > select {
        background-color: #2c2f36;
        color: #ffffff;
        border: 1px solid #4a4e57;
    }
    
    /* Data Editor Styling */
    .dataframe {
        background-color: #1e2129;
        color: #ffffff;
    }
    
    /* Button Styling */
    .stButton > button {
        background-color: #4db8ff;
        color: #ffffff;
        border: none;
        transition: background-color 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #3aa0ff;
    }
</style>
""", unsafe_allow_html=True)

# Define separate CSV files for each section
REQUEST_FILE = 'request_data.csv'
MISTAKE_FILE = 'mistake_data.csv'

# Load request data with Completed column
if os.path.exists(REQUEST_FILE):
    request_data = pd.read_csv(REQUEST_FILE)
    if "Completed" not in request_data.columns:
        request_data["Completed"] = False
else:
    request_data = pd.DataFrame(columns=["Completed", "Agent Name", "TYPE", "ID", "COMMENT", "Timestamp"])

# Load mistake data
if os.path.exists(MISTAKE_FILE):
    mistake_data = pd.read_csv(MISTAKE_FILE)
else:
    mistake_data = pd.DataFrame(columns=["Team Leader Name", "Agent Name", "Ticket ID", "Error", "Timestamp"])

# Sidebar for navigation with icons
with st.sidebar:
    st.markdown("### 🧭 Navigation")
    section = st.radio("Choose Section", [
        "📋 Request", 
        "🖼️ HOLD", 
        "❌ Ticket Mistakes"
    ])

# Request Tab
if section == "📋 Request":
    st.header("📋 Request Section")

    col1, col2 = st.columns([3, 2])
    
    with col1:
        agent_name_input = st.text_input("👤 Agent Name", key="agent_name")
        type_input = st.selectbox("🔍 Type", ["Email", "Phone Number", "Ticket ID"], key="type")
        id_input = st.text_input("🆔 ID", key="id")
    
    with col2:
        comment_input = st.text_area("💬 Comment", height=150, key="comment")  
    
    # Side-by-side buttons
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        submit_button = st.button("✅ Submit Data")
    
    with btn_col2:
        refresh_button = st.button("🔄 Refresh Data")
    
    if submit_button:
        if not agent_name_input or not id_input or not comment_input:
            st.error("❗ Please fill out all fields.")
        else:
            new_data = {
                "Completed": False,
                "Agent Name": agent_name_input,
                "TYPE": type_input,
                "ID": id_input,
                "COMMENT": comment_input,
                "Timestamp": datetime.now().strftime("%H:%M:%S")
            }
            new_row = pd.DataFrame([new_data])
            request_data = pd.concat([request_data, new_row], ignore_index=True)
            request_data.to_csv(REQUEST_FILE, index=False)
            st.success("✅ Data Submitted!")

    if not request_data.empty:
        st.write("### 📋 Submitted Requests:")
        
        columns_order = ["Completed", "Agent Name", "TYPE", "ID", "COMMENT", "Timestamp"]
        
        display_data = request_data[columns_order].copy()
        
        edited_df = st.data_editor(
            display_data, 
            column_config={
                "Completed": st.column_config.CheckboxColumn(
                    "✅ Completed",
                    help="Mark request as completed",
                    default=False
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        request_data.loc[:, columns_order] = edited_df
        request_data.to_csv(REQUEST_FILE, index=False)

# HOLD Tab
if section == "🖼️ HOLD":
    st.header("🖼️ HOLD Section")
    uploaded_image = st.file_uploader("📤 Upload Image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    
    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, caption="📸 Uploaded Image", use_column_width=True)

    if st.button("🔍 CHECK HOLD"):
        if uploaded_image:
            st.image(image, caption="📸 Latest Uploaded Image", use_column_width=True)
        else:
            st.write("❌ No image uploaded.")

# Ticket Mistakes Tab
if section == "❌ Ticket Mistakes":
    st.header("❌ Ticket Mistakes Section")

    col1, col2 = st.columns([3, 2])  
    
    with col1:
        team_leader_input = st.text_input("👥 Team Leader Name", key="team_leader")
        agent_name_mistake_input = st.text_input("👤 Agent Name", key="agent_name_mistake")
        ticket_id_input = st.text_input("🆔 Ticket ID", key="ticket_id")
    
    with col2:
        error_input = st.text_area("⚠️ Error", height=150, key="error")
    
    # Side-by-side buttons for Ticket Mistakes
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        submit_mistake_button = st.button("✅ Submit Mistake")
    
    with btn_col2:
        refresh_mistake_button = st.button("🔄 Refresh Mistakes")
    
    if submit_mistake_button:
        if not team_leader_input or not agent_name_mistake_input or not ticket_id_input or not error_input:
            st.error("❗ Please fill out all fields.")
        else:
            new_mistake = {
                "Team Leader Name": team_leader_input,
                "Agent Name": agent_name_mistake_input,
                "Ticket ID": ticket_id_input,
                "Error": error_input,
                "Timestamp": datetime.now().strftime("%H:%M:%S")
            }
            new_row = pd.DataFrame([new_mistake])
            mistake_data = pd.concat([mistake_data, new_row], ignore_index=True)
            mistake_data.to_csv(MISTAKE_FILE, index=False)
            st.success("✅ Mistake Submitted!")

    if refresh_mistake_button or not mistake_data.empty:
        st.write("❌ Mistakes Table:")
        st.dataframe(mistake_data, use_container_width=True)
