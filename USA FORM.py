import streamlit as st
import pandas as pd
from datetime import datetime
import os
from PIL import Image

# Define separate CSV files for each section
REQUEST_FILE = 'request_data.csv'
MISTAKE_FILE = 'mistake_data.csv'

# Load request data with Completed column
if os.path.exists(REQUEST_FILE):
    request_data = pd.read_csv(REQUEST_FILE)
    if "Completed" not in request_data.columns:
        request_data["Completed"] = False
else:
    request_data = pd.DataFrame(columns=["Agent Name", "TYPE", "ID", "COMMENT", "Timestamp", "Completed"])

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

    col1, col2 = st.columns([3, 2])
    
    with col1:
        agent_name_input = st.text_input("Agent Name", key="agent_name")
        type_input = st.selectbox("Type", ["Email", "Phone Number", "Ticket ID"], key="type")
        id_input = st.text_input("ID", key="id")
    
    with col2:
        comment_input = st.text_area("Comment", height=150, key="comment")  
    
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
                "Completed": False
            }
            new_row = pd.DataFrame([new_data])
            request_data = pd.concat([request_data, new_row], ignore_index=True)
            request_data.to_csv(REQUEST_FILE, index=False)
            st.success("Data Submitted!")

    if not request_data.empty:
        st.write("### Submitted Requests:")
        
        # Create a copy of the dataframe to modify for display
        display_data = request_data.copy()
        
        # Create a list to store updated completed status
        updated_completed = []
        
        # Create a list to hold display rows
        display_rows = []
        
        for index, row in display_data.iterrows():
            # Create checkbox
            completed = st.checkbox(
                "✔", 
                value=row["Completed"], 
                key=f"completed_{index}"
            )
            updated_completed.append(completed)
            display_rows.append({
                "Completed": completed,
                "Agent Name": row["Agent Name"],
                "Type": row["TYPE"],
                "ID": row["ID"],
                "Comment": row["COMMENT"],
                "Timestamp": row["Timestamp"]
            })
        
        # Create display DataFrame
        display_df = pd.DataFrame(display_rows)
        
        # Reorder columns
        display_df = display_df[["Completed", "Agent Name", "Type", "ID", "Comment", "Timestamp"]]
        
        # Display as dataframe
        st.dataframe(display_df, use_container_width=True)
        
        # Update the Completed column in the original dataframe
        request_data.loc[:, "Completed"] = updated_completed
        
        # Save updated data
        request_data.to_csv(REQUEST_FILE, index=False)

    st.markdown("<hr>", unsafe_allow_html=True)

# HOLD Tab
if section == "HOLD":
    st.header("HOLD Section")
    uploaded_image = st.file_uploader("Upload Image (HOLD Section)", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    
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

    col1, col2 = st.columns([3, 2])  
    
    with col1:
        team_leader_input = st.text_input("Team Leader Name", key="team_leader")
        agent_name_mistake_input = st.text_input("Agent Name", key="agent_name_mistake")
        ticket_id_input = st.text_input("Ticket ID", key="ticket_id")
    
    with col2:
        error_input = st.text_area("Error", height=150, key="error")
    
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

    if refresh_mistake_button or not mistake_data.empty:
        st.write("Mistakes Table:")
        st.dataframe(mistake_data, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)
