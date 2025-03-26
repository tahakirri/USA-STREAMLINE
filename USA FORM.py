import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import os
import re
from PIL import Image
import io

# New function to check if a phone number is fancy
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

# Rest of the previous code remains the same (database functions, authentication, etc.)
# ... [include all previous code before the main Streamlit app] ...

# Modify the main Streamlit app to include Fancy Number Check section
elif st.session_state.current_section == "requests":
    # Existing request section code...
    
    # Add Fancy Number Checker
    st.markdown("---")
    st.subheader("📱 Fancy Number Checker")
    with st.form("fancy_number_form"):
        phone_number = st.text_input("Enter Phone Number")
        
        if st.form_submit_button("Check Number"):
            if phone_number:
                result = is_fancy_number(phone_number)
                
                if result['is_fancy']:
                    st.success(f"🌟 Fancy Number Detected! {result['reason']}")
                    st.balloons()
                else:
                    st.info(f"📞 {result['reason']}")
            else:
                st.warning("Please enter a phone number")

# Rest of the code remains the same
# ... [include the rest of the previous code]
