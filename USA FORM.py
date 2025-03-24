import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from datetime import datetime

# Path to your Firebase JSON key
key_path = r"C:\Users\Taha\Downloads\usa-form-360ea-firebase-adminsdk-fbsvc-742a7301b4.json"

# Initialize Firebase app (only if not already initialized)
if not firebase_admin._apps:
    cred = credentials.Certificate(key_path)
    firebase_admin.initialize_app(cred)

# Firestore client
db = firestore.client()

# Initialize an empty DataFrame to store the data (for the session)
columns = ["Agent Name", "TYPE", "ID", "COMMENT", "Timestamp"]
data = pd.DataFrame(columns=columns)

# Function to submit data to Firestore
def submit_data(agent_name, type_, id_, comment):
    global data
    
    # Add the new data with timestamp
    new_data = {
        "Agent Name": agent_name,
        "TYPE": type_,
        "ID": id_,
        "COMMENT": comment,
        "Timestamp": datetime.now().strftime("%H:%M:%S")  # Only time (hour:minute:second)
    }

    # Add to Firestore collection
    db.collection('form_data').add(new_data)

    # Add to local DataFrame for display
    new_row = pd.DataFrame([new_data])
    data = pd.concat([data, new_row], ignore_index=True)

    return data

# Function to refresh the data from Firestore
def refresh_data():
    # Get all documents from Firestore
    docs = db.collection('form_data').stream()
    firestore_data = []
    for doc in docs:
        firestore_data.append(doc.to_dict())

    # Convert to DataFrame
    firestore_df = pd.DataFrame(firestore_data)
    return firestore_df

# Function to upload an image
def upload_image(image):
    # This function can be extended to upload images to Firestore or a storage service
    # Currently it just returns the image object
    return image

# Function to check the latest uploaded image
def check_hold():
    return image_storage.get("image", "No image uploaded yet.")

# Initialize image storage (for the hold section)
image_storage = {"image": None}

# Streamlit UI
st.title("USA Collab Form")

# Tabs
tab = st.sidebar.radio("Select Tab", ["Request", "HOLD"])

if tab == "Request":
    st.header("Request Section")

    # Input fields for Agent Name, Type, ID, Comment
    agent_name_input = st.text_input("Agent Name", placeholder="Enter Agent Name")
    type_input = st.selectbox("Type", ["Email", "Phone Number", "Ticket ID"])
    id_input = st.text_input("ID", placeholder="Enter ID")
    comment_input = st.text_area("Comment", placeholder="Enter Comment")

    # Buttons
    submit_button = st.button("Submit Data")
    refresh_button = st.button("Refresh Data")

    # Output Dataframe
    if submit_button:
        data = submit_data(agent_name_input, type_input, id_input, comment_input)
        st.dataframe(data)

    if refresh_button:
        refreshed_data = refresh_data()
        st.dataframe(refreshed_data)

elif tab == "HOLD":
    st.header("HOLD Section")

    # Image upload
    image_input = st.file_uploader("Upload Image (HOLD Section)", type=["png", "jpg", "jpeg"])

    if image_input:
        image_storage["image"] = image_input
        st.image(image_input, caption="Uploaded Image")

    # Check hold button
    if st.button("Check Latest Image"):
        image = check_hold()
        if isinstance(image, str):
            st.write(image)
        else:
            st.image(image, caption="Latest Uploaded Image")

# Firebase Firestore functionality
