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
        
        # Create columns for checkbox and data
        for index, row in display_data.iterrows():
            col1, col2 = st.columns([1, 10])
            
            with col1:
                # Checkbox with unique key
                completed = st.checkbox(
                    "✔", 
                    value=row["Completed"], 
                    key=f"completed_{index}"
                )
                updated_completed.append(completed)
            
            with col2:
                # Display row data
                st.write(f"**Agent Name:** {row['Agent Name']}")
                st.write(f"**Type:** {row['TYPE']}")
                st.write(f"**ID:** {row['ID']}")
                st.write(f"**Comment:** {row['COMMENT']}")
                st.write(f"**Timestamp:** {row['Timestamp']}")
                st.markdown("---")
        
        # Update the Completed column in the original dataframe
        request_data.loc[:, "Completed"] = updated_completed
        
        # Save updated data
        request_data.to_csv(REQUEST_FILE, index=False)

    st.markdown("<hr>", unsafe_allow_html=True)

# Rest of the code remains the same (HOLD and Ticket Mistakes sections)
# ... [previous HOLD and Ticket Mistakes sections remain unchanged]
