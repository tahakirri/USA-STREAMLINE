import streamlit as st
from datetime import datetime
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from streamlit.components.v1 import html
import time

# --- Initialize Session State (for persistence) ---
if "requests" not in st.session_state:
    st.session_state.requests = []

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# --- Helper Functions ---
def format_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def show_notification(message, type="success"):
    if type == "success":
        st.success(message)
    else:
        st.error(message)
    time.sleep(1.5)  # Simulate toast duration

# --- UI Setup ---
st.set_page_config(layout="wide")
st.title("📋 Request Management")

# --- Dark Mode Toggle ---
dark_mode = st.sidebar.toggle("Dark Mode", value=st.session_state.dark_mode)
if dark_mode:
    st.markdown("""
        <style>
            .stApp { background-color: #1e1e1e; color: white; }
            .st-bw { background-color: #333 !important; }
            .st-at { color: white !important; }
            .css-1aumxhk { color: white; }
        </style>
    """, unsafe_allow_html=True)

# --- Request Form ---
with st.form("request_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        agent_name = st.text_input("Agent Name", key="agent_name")
        request_type = st.selectbox(
            "Type", 
            ["Email", "Phone Number", "Ticket ID"], 
            key="request_type"
        )
        identifier = st.text_input("Identifier", key="identifier")
    
    with col2:
        comment = st.text_area("Comment", height=150, key="comment")
    
    submitted = st.form_submit_button("Submit Request")
    if submitted:
        if not agent_name or not identifier or not comment:
            show_notification("Please fill in all required fields", "error")
        else:
            new_request = {
                "id": int(datetime.now().timestamp()),
                "agent_name": agent_name,
                "type": request_type,
                "identifier": identifier,
                "comment": comment,
                "completed": False,
                "timestamp": format_timestamp()
            }
            st.session_state.requests.append(new_request)
            show_notification("Request submitted successfully!")

# --- Action Buttons ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🔄 Refresh Data"):
        show_notification("Data refreshed!")
with col2:
    if st.button("🗑️ Clear All Requests"):
        st.session_state.requests = []
        show_notification("All requests cleared!")
with col4:
    search_term = st.text_input("🔍 Search requests...", key="search")

# --- Filter Requests ---
filtered_requests = [
    req for req in st.session_state.requests
    if search_term.lower() in req["agent_name"].lower() 
    or search_term.lower() in req["identifier"].lower() 
    or search_term.lower() in req["comment"].lower()
]

# --- Display Requests in an Interactive Table ---
if filtered_requests:
    df = pd.DataFrame(filtered_requests)
    
    # Configure AgGrid for checkbox interaction
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_column("completed", header_name="Status", editable=True, cellRenderer="checkbox")
    gb.configure_columns(["agent_name", "type", "identifier", "comment", "timestamp"], editable=False)
    grid_options = gb.build()
    
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        height=400,
        theme="streamlit" if not dark_mode else "dark",
        fit_columns_on_grid_load=True,
        key="requests_grid"
    )
    
    # Update completion status
    updated_df = grid_response["data"]
    for index, row in updated_df.iterrows():
        if row["completed"] != st.session_state.requests[index]["completed"]:
            st.session_state.requests[index]["completed"] = row["completed"]
else:
    st.info("No requests found. Submit a new request above!")
