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

# Function to apply conditional formatting based on the TYPE column
def style_dataframe(df):
    def apply_style(row):
        if row['TYPE'] == 'Phone Number':  # Changed "Phone" to "Phone Number"
            return ['background-color: lightcoral'] * len(row)
        elif row['TYPE'] == 'Email':
            return ['background-color: lightblue'] * len(row)
        elif row['TYPE'] == 'Ticket ID':
            return ['background-color: lightgreen'] * len(row)
        else:
            return [''] * len(row)

    return df.style.apply(apply_style, axis=1)

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
        type_input = st.selectbox("Type", ["Email", "Phone Number", "Ticket ID"])  # Updated option here
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
        styled_data = style_dataframe(data)  # Apply the styling to the dataframe
        st.dataframe(styled_data)  # Display the styled dataframe
    
    # Additional space for better layout
    st.markdown("---")

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
    
    # Additional space for better layout
    st.markdown("---")
