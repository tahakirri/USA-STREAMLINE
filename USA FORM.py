import streamlit as st
import pandas as pd
from datetime import datetime
import os
from PIL import Image

# Ensure a directory exists for storing uploaded images
UPLOAD_DIRECTORY = 'uploaded_images'
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
LATEST_IMAGE_PATH = os.path.join(UPLOAD_DIRECTORY, 'latest_hold_image.jpg')

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

# Request Tab remains the same as in previous version

# HOLD Tab
if section == "🖼️ HOLD":
    st.header("🖼️ HOLD Section")
    uploaded_image = st.file_uploader("📤 Upload Image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    
    if uploaded_image:
        # Open and save the uploaded image
        image = Image.open(uploaded_image)
        
        # Save the image to the latest image path
        image.save(LATEST_IMAGE_PATH)
        
        # Display the uploaded image
        st.image(image, caption="📸 Uploaded Image", use_container_width=True)
        st.success("✅ Image uploaded successfully!")

    if st.button("🔍 CHECK HOLD"):
        # Check if the latest image exists
        if os.path.exists(LATEST_IMAGE_PATH):
            # Open and display the latest image
            latest_image = Image.open(LATEST_IMAGE_PATH)
            st.image(latest_image, caption="📸 Latest Uploaded Image", use_container_width=True)
        else:
            st.write("❌ No image uploaded.")

# Ticket Mistakes Tab remains the same as in previous version
