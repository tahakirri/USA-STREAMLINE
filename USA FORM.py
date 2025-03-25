import streamlit as st
import pandas as pd
from datetime import datetime
import os
from PIL import Image

# Define file paths for different sections
REQUEST_FILE = 'requests.csv'
MISTAKE_FILE = 'mistakes.csv'

# Load request data
if os.path.exists(REQUEST_FILE):
    request_data = pd.read_csv(REQUEST_FILE)
else:
    request_data = pd.DataFrame(columns=["Agent Name", "TYPE", "ID", "COMMENT", "Timestamp", "Completed"])

# Ensure 'Completed' column exists
if "Completed" not in request_data.columns:
    request_data["Completed"] = False

# Load mistake data
if os.path.exists(MISTAKE_FILE):
    mistake_data = pd.read_csv(MISTAKE_FILE)
else:
    mistake_data = pd.DataFrame(columns=["Team Leader Name", "Agent Name", "Ticket ID", "Error", "Timestamp"])

# Streamlit interface settings
st.set_page_config(page_title="USA Collab", layout="wide")  
st.title("USA Collab")
st.markdown("<hr>", unsafe_allow_html=True)

# Sidebar for navigation
with st.sidebar:
    st.markdown("### Navigation")
    section = st.radio("Choose Section", ["Request", "HOLD", "Ticket Mistakes"])

# Request Tab
if section == "Request":
    st.header("Request Section")
    
    # Layout with columns for better alignment
    col1, col2 = st.columns([3, 2])  
    
    with col1:
        agent_name_input = st.text_input("Agent Name")
        type_input = st.selectbox("Type", ["Email", "Phone Number", "Ticket ID"])
        id_input = st.text_input("ID")
    
    with col2:
        comment_input = st.text_area("Comment", height=150)
    
    # Buttons
    submit_button = st.button("Submit Data")
    refresh_button = st.button("Refresh Data")
    
    if submit_button:
        if not agent_name_input or not id_input or not comment_input:
            st.error("Please fill out all fields.")
        else:
            new_data = {
                "Agent Name": agent_name_input,
                "TYPE": type_input,
                "ID": id_input,
                "COMMENT": comment_input,
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                "Completed": False  # Default to not completed
            }
            new_row = pd.DataFrame([new_data])
            request_data = pd.concat([request_data, new_row], ignore_index=True)
            request_data.to_csv(REQUEST_FILE, index=False)
            st.success("Data Submitted!")
            st.rerun()  # Refresh the app

    if refresh_button:
        st.rerun()

    # Display stored requests with checkboxes for completion
    if not request_data.empty:
        st.write("### Submitted Requests:")
        for index, row in request_data.iterrows():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{row['Agent Name']}** - {row['TYPE']} - {row['ID']} - {row['COMMENT']} ({row['Timestamp']})")
            with col2:
                checked = st.checkbox("Completed", value=row["Completed"], key=f"chk_{index}")
                request_data.at[index, "Completed"] = checked
        
        # Save the updated checkbox states
        request_data.to_csv(REQUEST_FILE, index=False)

    st.markdown("<hr>", unsafe_allow_html=True)

# HOLD Tab
if section == "HOLD":
    st.header("HOLD Section")
    uploaded_image = st.file_uploader("Upload Image (HOLD Section)", type=["jpg", "jpeg", "png"])
    
    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, caption="Uploaded Image", use_column_width=True)

    if st.button("CHECK HOLD"):
        if uploaded_image:
            st.image(image, caption="Latest Uploaded Image", use_column_width=True)
        else:
            st.write("No image uploaded.")
    st.markdown("<hr>", unsafe_allow_html=True)

# Ticket Mistakes Tab
if section == "Ticket Mistakes":
    st.header("Ticket Mistakes Section")
    
    # Layout with columns for better alignment
    col1, col2 = st.columns([3, 2])  
    
    with col1:
        team_leader_input = st.text_input("Team Leader Name")
        agent_name_mistake_input = st.text_input("Agent Name")
        ticket_id_input = st.text_input("Ticket ID")
    
    with col2:
        error_input = st.text_area("Error", height=150)
    
    # Buttons
    submit_mistake_button = st.button("Submit Mistake")
    refresh_mistake_button = st.button("Refresh Mistakes")
    
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
            st.success("Mistake Submitted!")
            st.rerun()  

    if refresh_mistake_button:
        st.rerun()

    # Display mistakes
    if not mistake_data.empty:
        st.write("### Mistakes Table:")
        st.dataframe(mistake_data)

    st.markdown("<hr>", unsafe_allow_html=True)
