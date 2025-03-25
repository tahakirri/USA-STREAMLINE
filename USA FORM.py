import streamlit as st
import pandas as pd
from datetime import datetime
import os
from PIL import Image

# Define CSV files for each section
REQUEST_FILE = 'requests_data.csv'
MISTAKES_FILE = 'mistakes_data.csv'

# Load the data from CSV files or create empty DataFrames
def load_data(file_path, columns):
    if os.path.exists(file_path):
        data = pd.read_csv(file_path)
        if "Completed" not in data.columns:
            data["Completed"] = False  # Ensure 'Completed' column exists
    else:
        data = pd.DataFrame(columns=columns)
    return data

request_columns = ["Agent Name", "TYPE", "ID", "COMMENT", "Timestamp", "Completed"]
mistake_columns = ["Team Leader Name", "Agent Name", "Ticket ID", "Error", "Timestamp"]

request_data = load_data(REQUEST_FILE, request_columns)
mistake_data = load_data(MISTAKES_FILE, mistake_columns)

# Streamlit UI setup
st.set_page_config(page_title="USA Collab", layout="wide")
st.title("USA Collab")
st.markdown("<hr>", unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.markdown("### Navigation")
    section = st.radio("Choose Section", ["Request", "HOLD", "Ticket Mistakes"])

# REQUEST SECTION
if section == "Request":
    st.header("Request Section")
    
    col1, col2 = st.columns([3, 2])
    with col1:
        agent_name_input = st.text_input("Agent Name")
        type_input = st.selectbox("Type", ["Email", "Phone Number", "Ticket ID"])
        id_input = st.text_input("ID")
    
    with col2:
        comment_input = st.text_area("Comment", height=150)

    submit_button = st.button("Submit Request")
    refresh_button = st.button("Refresh Requests")

    if submit_button:
        if not agent_name_input or not id_input or not comment_input:
            st.error("Please fill out all fields.")
        else:
            new_request = {
                "Agent Name": agent_name_input,
                "TYPE": type_input,
                "ID": id_input,
                "COMMENT": comment_input,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Completed": False
            }
            request_data = pd.concat([pd.DataFrame([new_request]), request_data], ignore_index=True)  # Insert at top
            request_data.to_csv(REQUEST_FILE, index=False)
            st.success("Request Submitted!")

    if refresh_button or not request_data.empty:
        st.write("### Submitted Requests:")
        
        table_data = []
        for index, row in request_data.iterrows():
            checkbox_key = f"chk_{index}"
            completed = st.checkbox("✔", value=row["Completed"], key=checkbox_key)
            request_data.at[index, "Completed"] = completed
            table_data.append([row["Agent Name"], row["TYPE"], row["ID"], row["COMMENT"], row["Timestamp"], completed])

        table_df = pd.DataFrame(table_data, columns=["Agent Name", "Type", "ID", "Comment", "Timestamp", "Completed"])
        st.dataframe(table_df, use_container_width=True)
        
        request_data.to_csv(REQUEST_FILE, index=False)

    st.markdown("<hr>", unsafe_allow_html=True)

# HOLD SECTION
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

# TICKET MISTAKES SECTION
if section == "Ticket Mistakes":
    st.header("Ticket Mistakes Section")
    
    col1, col2 = st.columns([3, 2])
    with col1:
        team_leader_input = st.text_input("Team Leader Name")
        agent_name_mistake_input = st.text_input("Agent Name")
        ticket_id_input = st.text_input("Ticket ID")
    
    with col2:
        error_input = st.text_area("Error", height=150)

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
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            mistake_data = pd.concat([pd.DataFrame([new_mistake]), mistake_data], ignore_index=True)  # Insert at top
            mistake_data.to_csv(MISTAKES_FILE, index=False)
            st.success("Mistake Submitted!")

    if refresh_mistake_button or not mistake_data.empty:
        st.write("### Ticket Mistakes:")
        st.dataframe(mistake_data, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)
