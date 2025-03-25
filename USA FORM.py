import streamlit as st
import pandas as pd
from datetime import datetime
import os
from PIL import Image

# Define the path to the CSV file where the data will be stored
DATA_FILE = 'shared_data.csv'

# Load the data from the CSV file if it exists
if os.path.exists(DATA_FILE):
    data = pd.read_csv(DATA_FILE)
    data = data.drop(columns=['Completed'], errors='ignore')  # Remove 'Completed' column if exists
else:
    columns = ["Agent Name", "TYPE", "ID", "COMMENT", "Timestamp"]
    data = pd.DataFrame(columns=columns)

# Streamlit interface settings
st.set_page_config(page_title="USA Collab", layout="wide")  # Set page title and layout
st.title("USA Collab")
st.markdown("<hr>", unsafe_allow_html=True)

# Sidebar for navigation
with st.sidebar:
    st.image('https://www.example.com/logo.png', width=100)  # Optionally add a logo
    st.markdown("### Navigation")
    section = st.radio("Choose Section", ["Request", "HOLD", "Ticket Mistakes"])

    # Dark Mode / Light Mode Toggle
    dark_mode = st.checkbox("Dark Mode", value=False)
    if dark_mode:
        st.markdown("""
            <style>
                body { background-color: #1e1e1e; color: white; }
                .stButton>button { background-color: #333; color: white; }
                .stDataFrame { background-color: #333; color: white; }
                .stTextInput, .stSelectbox, .stTextArea { background-color: #444; color: white; }
                .css-1j7c2tb { color: white; }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
                body { background-color: #f0f0f0; color: black; }
                .stButton>button { background-color: #0073e6; color: white; }
                .stDataFrame { background-color: white; color: black; }
                .stTextInput, .stSelectbox, .stTextArea { background-color: white; color: black; }
                .css-1j7c2tb { color: black; }
            </style>
        """, unsafe_allow_html=True)

# Request Tab
if section == "Request":
    st.header("Request Section")
    
    # Layout with columns for better alignment
    col1, col2 = st.columns([3, 2])  # Wider first column for inputs
    
    with col1:
        agent_name_input = st.text_input("Agent Name", key="agent_name")
        type_input = st.selectbox("Type", ["Email", "Phone Number", "Ticket ID"], key="type")
        id_input = st.text_input("ID", key="id")
    
    with col2:
        comment_input = st.text_area("Comment", height=150, key="comment")
    
    # Buttons for submission and refresh with icons
    submit_button = st.button("Submit Data", icon="check_circle")
    refresh_button = st.button("Refresh Data", icon="refresh")
    
    if submit_button:
        # Ensure fields are filled out before submission
        if not agent_name_input or not id_input or not comment_input:
            st.error("Please fill out all fields.")
        else:
            new_data = {
                "Agent Name": agent_name_input,
                "TYPE": type_input,
                "ID": id_input,
                "COMMENT": comment_input,
                "Timestamp": datetime.now().strftime("%H:%M:%S")
            }
            new_row = pd.DataFrame([new_data])
            data = pd.concat([data, new_row], ignore_index=True)
            data.to_csv(DATA_FILE, index=False)
            st.success("Data Submitted!")

    if refresh_button:
        st.write("Latest Submitted Data:")
        st.dataframe(data)  # Display the data without the additional styling (removing color formatting)

    st.markdown("<hr>", unsafe_allow_html=True)

# HOLD Tab
if section == "HOLD":
    st.header("HOLD Section")
    uploaded_image = st.file_uploader("Upload Image (HOLD Section)", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    
    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, caption="Uploaded Image", use_column_width=True)

    if st.button("CHECK HOLD", icon="search"):
        if uploaded_image:
            st.image(image, caption="Latest Uploaded Image", use_column_width=True)
        else:
            st.write("No image uploaded.")
    st.markdown("<hr>", unsafe_allow_html=True)

# Ticket Mistakes Tab
if section == "Ticket Mistakes":
    st.header("Ticket Mistakes Section")
    
    # Layout with columns for better alignment
    col1, col2 = st.columns([3, 2])  # Wider first column for inputs
    
    with col1:
        team_leader_input = st.text_input("Team Leader Name", key="team_leader")
        agent_name_mistake_input = st.text_input("Agent Name", key="agent_name_mistake")
        ticket_id_input = st.text_input("Ticket ID", key="ticket_id")
    
    with col2:
        error_input = st.text_area("Error", height=150, key="error")
    
    # Buttons for submission and refresh with icons
    submit_mistake_button = st.button("Submit Mistake", icon="check_circle")
    refresh_mistake_button = st.button("Refresh Mistakes", icon="refresh")
    
    if submit_mistake_button:
        # Ensure fields are filled out before submission
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
            data = pd.concat([data, new_row], ignore_index=True)
            data.to_csv(DATA_FILE, index=False)
            st.success("Mistake Submitted!")

    if refresh_mistake_button:
        st.write("Mistakes Table:")
        st.dataframe(data)  # Display the mistakes table

    st.markdown("<hr>", unsafe_allow_html=True)
