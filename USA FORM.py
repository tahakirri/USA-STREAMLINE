import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import os
import re
from PIL import Image
import io

# [Previous database functions remain the same]

# Enhanced Streamlit Configuration
st.set_page_config(
    page_title="Request Management System", 
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Custom CSS
st.markdown("""
<style>
    /* Global Styling */
    :root {
        --primary-color: #2c3e50;
        --secondary-color: #3498db;
        --background-color: #f4f6f7;
        --card-background: #ffffff;
        --text-color: #2c3e50;
    }

    .stApp {
        background-color: var(--background-color);
        font-family: 'Inter', 'Roboto', sans-serif;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: var(--primary-color);
        color: white;
        border-right: 1px solid #34495e;
    }

    [data-testid="stSidebar"] .stButton>button {
        background-color: var(--secondary-color);
        color: white;
        width: 100%;
        margin-bottom: 10px;
        border-radius: 6px;
        transition: all 0.3s ease;
    }

    [data-testid="stSidebar"] .stButton>button:hover {
        background-color: #2980b9;
        transform: scale(1.05);
    }

    /* Card Styling */
    .card {
        background-color: var(--card-background);
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin-bottom: 15px;
        transition: all 0.3s ease;
    }

    .card:hover {
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        transform: translateY(-5px);
    }

    /* Button Styling */
    .stButton>button {
        background-color: var(--secondary-color);
        color: white;
        border-radius: 6px;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background-color: #2980b9;
        transform: scale(1.05);
    }

    /* Message Styling */
    .message {
        max-width: 70%;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
        position: relative;
    }

    .sent {
        background-color: var(--secondary-color);
        color: white;
        margin-left: auto;
    }

    .received {
        background-color: #ecf0f1;
        margin-right: auto;
    }

    /* Status Indicators */
    .killswitch-active {
        background-color: #ff6b6b;
        color: white;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        margin-bottom: 20px;
    }

    /* Form Styling */
    .stTextInput>div>div>input, 
    .stSelectbox>div>div>select, 
    .stTextArea>div>div>textarea {
        border-radius: 6px;
        border: 1px solid #bdc3c7;
        padding: 10px;
    }

    /* Responsive Design */
    @media (max-width: 600px) {
        .card {
            padding: 15px;
        }
        .message {
            max-width: 90%;
        }
    }
</style>
""", unsafe_allow_html=True)

# [Rest of the previous code remains the same, with minor UI enhancements]

# Enhanced Login Page Design
def render_login_page():
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; height: 80vh;">
        <div style="background-color: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); width: 400px;">
            <h1 style="text-align: center; color: #2c3e50; margin-bottom: 20px;">Request Management</h1>
            <img src="/api/placeholder/200/200" alt="Company Logo" style="display: block; margin: 0 auto 20px; border-radius: 50%;"/>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Main Application Structure
def main_app():
    # [Previous main application logic remains the same]
    # Consider adding more subtle animations and transitions
    pass

# Application Entry Point
def app():
    # Initialize database
    init_db()

    # Check authentication state
    if not st.session_state.get('authenticated', False):
        render_login_page()
        # [Login form remains the same]
    else:
        main_app()

# Run the application
if __name__ == "__main__":
    app()
