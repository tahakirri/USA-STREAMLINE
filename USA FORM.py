import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import os

# Define the path to the CSV file where the data will be stored
DATA_FILE = 'shared_data.csv'
TICKET_MISTAKES_FILE = 'ticket_mistakes.csv'

# Path where images will be saved
IMAGE_SAVE_PATH = 'uploaded_images/'

# Create the directory if it doesn't exist
if not os.path.exists(IMAGE_SAVE_PATH):
    os.makedirs(IMAGE_SAVE_PATH)

# Load the data from the CSV file if it exists
if os.path.exists(DATA_FILE):
    data = pd.read_csv(DATA_FILE)
    data = data.drop(columns=['Completed'], errors='ignore')  # Remove 'Completed' column if exists
else:
    columns = ["Agent Name", "TYPE", "ID", "COMMENT", "Timestamp"]
    data = pd.DataFrame(columns=columns)

if os.path.exists(TICKET_MISTAKES_FILE):
    ticket_mistakes = pd.read_csv(TICKET_MISTAKES_FILE)
else:
    mistake_columns = ["Team Leader Name", "Agent Name", "Ticket ID", "Error", "Timestamp"]
    ticket_mistakes = pd.DataFrame(columns=mistake_columns)

# Function to submit request data
def submit_data(agent_name, type_, id_, comment):
    global data
    new_data = {
        "Agent Name": agent_name,
        "TYPE": type_,
        "ID": id_,
        "COMMENT": comment,
        "Timestamp": datetime.now().strftime("%H:%M:%S")
    }
    new_row = pd.DataFrame([new_data])
    data = pd.concat([data, new_row], ignore_index=True)
    data.to_csv(DATA_FILE, index=False)
    return data

# Function to submit ticket mistakes data
def submit_ticket_mistake(team_leader, agent_name, ticket_id, error):
    global ticket_mistakes
    new_mistake = {
        "Team Leader Name": team_leader,
        "Agent Name": agent_name,
        "Ticket ID": ticket_id,
        "Error": error,
        "Timestamp": datetime.now().strftime("%H:%M:%S")
    }
    new_row = pd.DataFrame([new_mistake])
    ticket_mistakes = pd.concat([ticket_mistakes, new_row], ignore_index=True)
    ticket_mistakes.to_csv(TICKET_MISTAKES_FILE, index=False)
    return ticket_mistakes

# Function to save and return the file path for uploaded images
def save_uploaded_image(uploaded_image):
    image_path = os.path.join(IMAGE_SAVE_PATH, uploaded_image.name)
    with open(image_path, "wb") as f:
        f.write(uploaded_image.getbuffer())
    return image_path

# Function to refresh data
def refresh_data():
    return data

def refresh_ticket_mistakes():
    return ticket_mistakes

# Streamlit interface
st.set_page_config(page_title="USA Collab", layout="wide")  # Set page title and layout

st.title("USA Collab")

# Tabs
tab = st.radio("Choose a Section", ["Request", "HOLD", "Ticket Mistakes"])

# Request Tab
if tab == "Request":
    st.header("Request Section")
    
    # Use columns to structure inputs
    col1, col2 = st.columns([3, 2])  # Wider first column for inputs
    
    with col1:
        agent_name_input = st.text_input("Agent Name")
        type_input = st.selectbox("Type", ["Email", "Phone Number", "Ticket ID"])
        id_input = st.text_input("ID")
    
    with col2:
        comment_input = st.text_area("Comment", height=150)
    
    # Buttons for submission and refresh
    submit_button = st.button("Submit Data")
    refresh_button = st.button("Refresh Data")
    
    if submit_button:
        # Ensure fields are filled out before submission
        if not agent_name_input or not id_input or not comment_input:
            st.error("Please fill out all fields.")
        else:
            data = submit_data(agent_name_input, type_input, id_input, comment_input)
            st.success("Data Submitted!")
            st.write("Latest Submitted Data:")
            st.write(data)  # Automatically display the refreshed data
    
    if refresh_button:
        st.write("Latest Submitted Data:")
        st.write(data)  # Show the data when refresh is clicked
    
    # Additional space for better layout
    st.markdown("---")

# HOLD Tab
if tab == "HOLD":
    st.header("HOLD Section")
    uploaded_image = st.file_uploader("Upload Image (HOLD Section)", type=["jpg", "jpeg", "png"])

    if uploaded_image:
        # Save the uploaded image
        image_path = save_uploaded_image(uploaded_image)
        st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
    
    # Check if the uploaded image exists and show it
    if st.button("CHECK HOLD"):
        # List all uploaded images in the folder
        uploaded_images = os.listdir(IMAGE_SAVE_PATH)
        
        if uploaded_images:
            # Display the images
            for img_file in uploaded_images:
                img_path = os.path.join(IMAGE_SAVE_PATH, img_file)
                img = Image.open(img_path)
                st.image(img, caption=f"Uploaded Image: {img_file}", use_column_width=True)
        else:
            st.write("No image uploaded.")
    
    # Additional space for better layout
    st.markdown("---")

# Ticket Mistakes Tab
if tab == "Ticket Mistakes":
    st.header("Ticket Mistakes Section")
    
    # Use columns for input fields
    col1, col2 = st.columns([3, 2])  # Wider first column for inputs
    
    with col1:
        team_leader_input = st.text_input("Team Leader Name")
        agent_name_mistake_input = st.text_input("Agent Name")
        ticket_id_input = st.text_input("Ticket ID")
    
    with col2:
        error_input = st.text_area("Error", height=150)
    
    # Buttons for submission and refresh
    submit_button = st.button("Submit Mistake")
    refresh_button = st.button("Refresh Mistakes")
    
    if submit_button:
        # Ensure fields are filled out before submission
        if not team_leader_input or not agent_name_mistake_input or not ticket_id_input or not error_input:
            st.error("Please fill out all fields.")
        else:
            ticket_mistakes = submit_ticket_mistake(team_leader_input, agent_name_mistake_input, ticket_id_input, error_input)
            st.success("Mistake Submitted!")
            st.write("Mistakes Table:")
            st.write(ticket_mistakes)  # Automatically display the refreshed data
    
    if refresh_button:
        st.write("Mistakes Table:")
        st.write(ticket_mistakes)  # Show the ticket mistakes data when refresh is clicked
    
    # Additional space for better layout
    st.markdown("---")
