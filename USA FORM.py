import os
import pandas as pd
from datetime import datetime
from PIL import Image

import streamlit as st

# Page config MUST be the first Streamlit command
st.set_page_config(
    page_title="USA Collab", 
    layout="wide", 
    page_icon=":clipboard:"
)  

# Custom CSS for enhanced styling
def set_custom_styling():
    st.markdown("""
    <style>
    /* Custom color scheme */
    :root {
        --primary-color: #2c3e50;
        --secondary-color: #3498db;
        --background-color: #f4f6f7;
        --text-color: #2c3e50;
    }

    /* Main page styling */
    .main {
        background-color: var(--background-color);
        color: var(--text-color);
    }

    /* Title styling */
    .title {
        color: var(--primary-color);
        font-weight: bold;
        text-align: center;
        padding: 20px 0;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 2px solid #e0e0e0;
    }

    /* Navigation radio button styling */
    .stRadio > div {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 10px;
    }

    /* Input and selectbox styling */
    .stTextInput > div > div > input, 
    .stSelectbox > div > div > div {
        border: 1px solid var(--secondary-color);
        border-radius: 5px;
        padding: 8px;
    }

    /* Button styling */
    .stButton > button {
        background-color: var(--secondary-color);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        transition: background-color 0.3s ease;
    }

    .stButton > button:hover {
        background-color: #2980b9;
    }

    /* Dataframe styling */
    .dataframe {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        overflow: hidden;
    }

    /* Success and error message styling */
    .stAlert {
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# File paths
REQUEST_FILE = 'request_data.csv'
MISTAKE_FILE = 'mistake_data.csv'

# Load request data with Completed column
def load_request_data():
    if os.path.exists(REQUEST_FILE):
        request_data = pd.read_csv(REQUEST_FILE)
        if "Completed" not in request_data.columns:
            request_data["Completed"] = False
    else:
        request_data = pd.DataFrame(columns=["Completed", "Agent Name", "TYPE", "ID", "COMMENT", "Timestamp"])
    return request_data

# Load mistake data
def load_mistake_data():
    if os.path.exists(MISTAKE_FILE):
        mistake_data = pd.read_csv(MISTAKE_FILE)
    else:
        mistake_data = pd.DataFrame(columns=["Team Leader Name", "Agent Name", "Ticket ID", "Error", "Timestamp"])
    return mistake_data

# Main application
def main():
    # Set custom styling
    set_custom_styling()

    # Custom title with icon
    st.markdown(
        "<h1 class='title'>🔍 USA Collab Management System</h1>", 
        unsafe_allow_html=True
    )

    # Load data
    request_data = load_request_data()
    mistake_data = load_mistake_data()

    # Sidebar for navigation with icons
    with st.sidebar:
        st.markdown("### 📋 Navigation")
        section = st.radio("Choose Section", [
            "🔬 Request", 
            "🖼️ HOLD", 
            "❌ Ticket Mistakes"
        ])

    # Remove the "section =" prefix from the selection
    section = section.split()[-1]

    # Request Tab
    if section == "Request":
        st.header("📝 Request Section")

        # Create columns for input
        col1, col2 = st.columns([3, 2])
        
        with col1:
            agent_name_input = st.text_input("Agent Name", key="agent_name")
            type_input = st.selectbox("Type", ["Email", "Phone Number", "Ticket ID"], key="type")
            id_input = st.text_input("ID", key="id")
        
        with col2:
            comment_input = st.text_area("Comment", height=150, key="comment")  
        
        # Buttons with columns for spacing
        col_submit, col_refresh = st.columns(2)
        with col_submit:
            submit_button = st.button("Submit Data")
        with col_refresh:
            refresh_button = st.button("Refresh Data")
        
        # Submission logic
        if submit_button:
            if not agent_name_input or not id_input or not comment_input:
                st.error("Please fill out all fields.")
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
                st.success("Data Submitted Successfully! 🎉")

        # Display data
        if not request_data.empty:
            st.write("### 📋 Submitted Requests:")
            
            # Reorder columns
            columns_order = ["Completed", "Agent Name", "TYPE", "ID", "COMMENT", "Timestamp"]
            
            # Use data editor for inline editing
            edited_df = st.data_editor(
                request_data[columns_order], 
                column_config={
                    "Completed": st.column_config.CheckboxColumn(
                        "Completed",
                        help="Mark request as completed",
                        default=False
                    )
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Save changes
            request_data.loc[:, columns_order] = edited_df
            request_data.to_csv(REQUEST_FILE, index=False)

    # HOLD Tab
    elif section == "HOLD":
        st.header("🖼️ HOLD Section")
        uploaded_image = st.file_uploader(
            "Upload Image", 
            type=["jpg", "jpeg", "png"], 
            label_visibility="collapsed"
        )
        
        if uploaded_image:
            image = Image.open(uploaded_image)
            col1, col2 = st.columns(2)
            with col1:
                st.image(image, caption="Uploaded Image", use_column_width=True)
            with col2:
                st.write("Image Details:")
                st.write(f"**Filename:** {uploaded_image.name}")
                st.write(f"**Size:** {uploaded_image.size} bytes")

        if st.button("Check Hold"):
            if uploaded_image:
                st.image(image, caption="Latest Uploaded Image", use_column_width=True)
            else:
                st.warning("No image uploaded.")

    # Ticket Mistakes Tab
    elif section == "Ticket Mistakes":
        st.header("❌ Ticket Mistakes Section")

        # Input columns
        col1, col2 = st.columns([3, 2])  
        
        with col1:
            team_leader_input = st.text_input("Team Leader Name", key="team_leader")
            agent_name_mistake_input = st.text_input("Agent Name", key="agent_name_mistake")
            ticket_id_input = st.text_input("Ticket ID", key="ticket_id")
        
        with col2:
            error_input = st.text_area("Error", height=150, key="error")
        
        # Buttons with columns for spacing
        col_submit, col_refresh = st.columns(2)
        with col_submit:
            submit_mistake_button = st.button("Submit Mistake")
        with col_refresh:
            refresh_mistake_button = st.button("Refresh Mistakes")
        
        # Submission logic
        if submit_mistake_button:
            if not team_leader_input or not agent_name_mistake_input or not ticket_id_input or not error_input:
                st.error("Please fill out all fields.")
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
                st.success("Mistake Submitted Successfully! 🚨")

        # Display mistakes
        if refresh_mistake_button or not mistake_data.empty:
            st.write("### 📋 Mistakes Table:")
            st.dataframe(mistake_data, use_container_width=True)

# Run the main application
if __name__ == "__main__":
    main()
