import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Define CSV file for storing requests
REQUEST_FILE = "requests_data.csv"

# Load or initialize request data
def load_data():
    if os.path.exists(REQUEST_FILE):
        data = pd.read_csv(REQUEST_FILE)
        if "Completed" not in data.columns:
            data["Completed"] = False  # Ensure 'Completed' column exists
    else:
        data = pd.DataFrame(columns=["Agent Name", "Type", "ID", "Comment", "Timestamp", "Completed"])
    return data

# Save updated request data
def save_data(data):
    data.to_csv(REQUEST_FILE, index=False)

# Load the data
request_data = load_data()

# Streamlit UI setup
st.set_page_config(page_title="USA Collab", layout="wide")
st.title("USA Collab")
st.markdown("<hr>", unsafe_allow_html=True)

# Input fields for a new request
agent_name_input = st.text_input("Agent Name")
type_input = st.selectbox("Type", ["Email", "Phone Number", "Ticket ID"])
id_input = st.text_input("ID")
comment_input = st.text_area("Comment", height=100)

# Buttons
col1, col2 = st.columns([1, 1])
with col1:
    submit_button = st.button("Submit Request")
with col2:
    refresh_button = st.button("Refresh Requests")

# Handle submission
if submit_button:
    if not agent_name_input or not id_input or not comment_input:
        st.error("Please fill out all fields.")
    else:
        new_request = {
            "Agent Name": agent_name_input,
            "Type": type_input,
            "ID": id_input,
            "Comment": comment_input,
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Completed": False
        }
        request_data = pd.concat([pd.DataFrame([new_request]), request_data], ignore_index=True)  # Insert at top
        save_data(request_data)
        st.success("Request Submitted!")

# Display table if data exists
if not request_data.empty:
    st.write("### Submitted Requests:")

    # Rebuild the DataFrame with checkboxes in-line
    edited_data = request_data.copy()
    for index, row in request_data.iterrows():
        checkbox_key = f"chk_{index}"
        edited_data.at[index, "Completed"] = st.checkbox("✔", value=row["Completed"], key=checkbox_key)

    # Display the table
    st.dataframe(edited_data, use_container_width=True)

    # Save the changes back to CSV
    save_data(edited_data)

st.markdown("<hr>", unsafe_allow_html=True)
