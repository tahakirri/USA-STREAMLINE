import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Define the path to the CSV file where the data will be stored
DATA_FILE = 'shared_data.csv'
TICKET_MISTAKES_FILE = 'ticket_mistakes.csv'

# Load the data from the CSV file if it exists
if os.path.exists(DATA_FILE):
    data = pd.read_csv(DATA_FILE)
else:
    columns = ["Agent Name", "TYPE", "ID", "COMMENT", "Timestamp", "Completed"]
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
        "Timestamp": datetime.now().strftime("%H:%M:%S"),
        "Completed": "Not Completed"  # Default to "Not Completed"
    }
    new_row = pd.DataFrame([new_data])
    data = pd.concat([data, new_row], ignore_index=True)
    data.to_csv(DATA_FILE, index=False)
    return data

# Function to update the completed status
def update_completion(index, completed_status):
    global data
    data.at[index, "Completed"] = completed_status
    data.to_csv(DATA_FILE, index=False)

# Function to refresh data
def refresh_data():
    return data

# Streamlit interface
st.title("USA Collab")

# Tabs
tab = st.radio("Choose a Section", ["Request", "Ticket Mistakes"])

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
        for index, row in data.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 3, 2, 1])
            col1.write(row["Agent Name"])
            col2.write(row["TYPE"])
            col3.write(row["ID"])
            col4.write(row["COMMENT"])
            col5.write(row["Timestamp"])
            
            # Using a toggle button for "Completed" status
            completed_status = st.session_state.get(f"status_{index}", row["Completed"])  # Retrieve current status from session_state
            
            # Toggle button for the status change
            if st.button(f"Toggle {row['ID']}", key=f"toggle_{index}"):
                # Toggle between "Not Completed" and "Completed"
                new_status = "Completed" if completed_status == "Not Completed" else "Not Completed"
                update_completion(index, new_status)
                st.session_state[f"status_{index}"] = new_status  # Save the new status in session_state
                st.experimental_rerun()  # Trigger a rerun to update the display

            col6.write(completed_status)  # Display the current status

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
