import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import os
import re
from PIL import Image
import io

# Fancy Number Checker Function
def is_fancy_number(phone_number):
    """
    Determine if a phone number is 'fancy' based on various patterns
    
    Args:
        phone_number (str): The phone number to check
    
    Returns:
        dict: A dictionary with fancy status and reasoning
    """
    # Remove any non-digit characters
    digits = re.sub(r'\D', '', phone_number)
    
    # Check if shorter than 10 digits or not a valid phone number
    if len(digits) < 10:
        return {
            "is_fancy": False,
            "reason": "Invalid phone number length"
        }
    
    # Fancy patterns to check
    fancy_patterns = [
        # Repeating digits
        (r'(\d)\1{2,}', "Has repeating digits"),
        
        # Ascending or descending sequences
        (r'012|123|234|345|456|567|678|789', "Contains ascending sequence"),
        (r'987|876|765|654|543|432|321|210', "Contains descending sequence"),
        
        # Palindrome numbers
        (lambda x: x == x[::-1], "Is a palindrome"),
        
        # Sequential patterns
        (r'(01|12|23|34|45|56|67|78|89)', "Contains sequential digits"),
        
        # Mirror numbers
        (lambda x: len(set(x)) <= 2, "Consists of minimal unique digits"),
        
        # Special number patterns
        (r'8888|6666|9999', "Contains lucky/symbolic numbers"),
    ]
    
    for pattern in fancy_patterns:
        # Handle both regex and lambda pattern checks
        if isinstance(pattern[0], str):
            if re.search(pattern[0], digits):
                return {
                    "is_fancy": True,
                    "reason": pattern[1]
                }
        elif callable(pattern[0]):
            try:
                if pattern[0](digits):
                    return {
                        "is_fancy": True,
                        "reason": pattern[1]
                    }
            except:
                pass
    
    return {
        "is_fancy": False,
        "reason": "Standard phone number"
    }

# [Rest of the previous database and authentication functions remain the same]

# Modify the sidebar navigation and main content sections
else:
    # Sidebar Navigation
    with st.sidebar:
        st.title(f"👋 Welcome, {st.session_state.username}")
        st.markdown("---")
        
        nav_options = [
            ("📋 Requests", "requests"),
            ("📱 Fancy Number", "fancy_number"),  # New navigation option
        ]
        
        if st.session_state.role == "admin":
            nav_options.append(("⚙️ Admin Panel", "admin"))
        
        for option, value in nav_options:
            if st.button(option, key=f"nav_{value}"):
                st.session_state.current_section = value
        
        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.role = None
            st.session_state.username = None
            st.rerun()
    
    # Main Content
    st.title(f"{'📋' if st.session_state.current_section == 'requests' else '📱' if st.session_state.current_section == 'fancy_number' else '⚙️'} {st.session_state.current_section.title()}")

    # Fancy Number Section
    if st.session_state.current_section == "fancy_number":
        st.subheader("📱 Fancy Number Checker")
        
        st.markdown("""
        ### Discover if Your Phone Number is Fancy! 🌟
        
        What makes a phone number "fancy"?
        - Repeating digits (like 8888)
        - Ascending or descending sequences
        - Palindrome numbers
        - Sequential patterns
        - Minimal unique digits
        - Lucky/symbolic number combinations
        """)
        
        with st.form("fancy_number_form"):
            phone_number = st.text_input("Enter Full Phone Number", 
                                         placeholder="e.g., +1 (555) 123-4567")
            
            if st.form_submit_button("Check If Fancy"):
                if phone_number:
                    result = is_fancy_number(phone_number)
                    
                    if result['is_fancy']:
                        st.success(f"🌟 Fancy Number Detected! {result['reason']}")
                        st.balloons()
                        
                        # Additional fancy details
                        st.markdown("""
                        ### 🎉 Congratulations! 
                        Your phone number has a special characteristic that makes it stand out!
                        
                        #### What does this mean?
                        - Your number is unique
                        - It has an interesting mathematical or visual pattern
                        - It could be considered lucky or memorable
                        """)
                    else:
                        st.info(f"📞 {result['reason']}")
                        
                        # Consolation for non-fancy numbers
                        st.markdown("""
                        ### 💡 Tip
                        While your number isn't considered "fancy" right now, 
                        you can always look for interesting patterns when choosing future numbers!
                        """)
                else:
                    st.warning("Please enter a complete phone number")

    # [Rest of the previous code remains the same]
