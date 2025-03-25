import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import os

# Define the path to the CSV file where the data will be stored
DATA_FILE = 'shared_data.csv'
TICKET_MISTAKES_FILE = 'ticket_mistakes.csv'

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

# Function to refresh data
def refresh_data():
    return data

def refresh_ticket_mistakes():
    return ticket_mistakes

# Streamlit interface
st.title("USA Collab")

# Tabs
tab = st.radio("Choose a Section", ["Request", "HOLD", "Ticket Mistakes"])

# Request Tab
if tab == "Request":
    st.header("Request Section")
    agent_name_input = st.text_input("Agent Name")
    type_input = st.selectbox("Type", ["Email", "Phone Number", "Ticket ID"])
    id_input = st.text_input("ID")
    comment_input = st.text_area("Comment")
    
    if st.button("Submit Data"):
        data = submit_data(agent_name_input, type_input, id_input, comment_input)
        st.write("Data Submitted!")
        st.write("Latest Submitted Data:")
        st.write(data.tail(1))
    
    if st.button("Refresh Data"):
        st.write("Data Table:")
        st.write(data)  # Display the data as it is

# HOLD Tab
if tab == "HOLD":
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

# Ticket Mistakes Tab
if tab == "Ticket Mistakes":
    st.header("Ticket Mistakes Section")
    team_leader_input = st.text_input("Team Leader Name")
    agent_name_mistake_input = st.text_input("Agent Name")
    ticket_id_input = st.text_input("Ticket ID")
    error_input = st.text_area("Error")
    
    if st.button("Submit Mistake"):
        ticket_mistakes = submit_ticket_mistake(team_leader_input, agent_name_mistake_input, ticket_id_input, error_input)
        st.write("Mistake Submitted!")
        st.write("Latest Submitted Mistake:")
        st.write(ticket_mistakes.tail(1))
    
    if st.button("Refresh Mistakes"):
        st.write("Mistakes Table:")
        st.write(refresh_ticket_mistakes())
