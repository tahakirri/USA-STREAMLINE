import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import os
import re
from PIL import Image
import io

# --------------------------
# Database Functions
# --------------------------

# ... [Keep all previous database functions the same] ...

# --------------------------
# Improved Fancy Number Checker Functions (Last 6 Digits Focus)
# --------------------------

def get_last_six_digits(number):
    """Extract and return the last 6 digits of a phone number."""
    clean_number = re.sub(r'\D', '', number)
    return clean_number[-6:] if len(clean_number) >= 6 else None

def is_consecutive(digits, ascending=True):
    """Check if digits form a consecutive sequence."""
    for i in range(1, len(digits)):
        diff = digits[i] - digits[i-1]
        if ascending and diff != 1:
            return False
        if not ascending and diff != -1:
            return False
    return True

def has_repeating_pattern(digits):
    """Check for repeating patterns in the last 6 digits."""
    # Check for pair patterns (e.g., 1212, 123123)
    if digits[:3] == digits[3:]:
        return "Repeating 3-digit pattern"
    if digits[:2] == digits[2:4] == digits[4:]:
        return "Repeating 2-digit pattern"
    return None

def is_fancy_number(number):
    """Check if last 6 digits of a number contain fancy patterns."""
    last_six = get_last_six_digits(number)
    if not last_six or len(last_six) != 6:
        return False, "Invalid number length"
    
    digits = [int(d) for d in last_six]
    
    # 1. All digits same
    if len(set(digits)) == 1:
        return True, "All last 6 digits identical"
    
    # 2. Consecutive sequences
    if is_consecutive(digits):
        return True, "Last 6 digits sequential ascending"
    if is_consecutive(digits, ascending=False):
        return True, "Last 6 digits sequential descending"
    
    # 3. Palindrome check
    if digits == digits[::-1]:
        return True, "Last 6 digits palindrome"
    
    # 4. Repeating patterns
    if pattern := has_repeating_pattern(digits):
        return True, pattern
    
    # 5. Bookend patterns (e.g., 1xxxx1, 12xx21)
    if digits[0] == digits[-1] and digits[1] == digits[-2]:
        return True, "Last 6 digits bookend pattern"
    
    # 6. Triple same digits
    for i in range(4):
        if len(set(digits[i:i+3])) == 1:
            return True, "Triple repeating digits in last 6"
    
    # 7. Multiple pairs (e.g., 112233)
    if all(digits[i] == digits[i+1] for i in range(0, 6, 2)):
        return True, "Multiple pairs in last 6 digits"
    
    # 8. Mixed sequence with repeated start (e.g., 112345)
    if digits[0] == digits[1] and is_consecutive(digits[2:]):
        return True, "Repeated start with sequence in last 6"
    
    # 9. Mirror pattern (e.g., 123321)
    if digits[:3] == digits[:2:-1]:
        return True, "Mirror pattern in last 6 digits"
    
    # 10. Special combination check
    special_cases = {
        '123456': 'Perfect ascending sequence',
        '654321': 'Perfect descending sequence',
        '112233': 'Multiple pairs',
        '121212': 'Repeating 12 pattern',
        '111222': 'Triple pairs'
    }
    
    if last_six in special_cases:
        return True, special_cases[last_six]
    
    return False, "No fancy pattern in last 6 digits"

# ... [Keep all other functions the same] ...

# --------------------------
# Streamlit UI Configuration
# --------------------------

# ... [Keep previous UI configuration the same] ...

# Fancy Number Checker Section
elif st.session_state.current_section == "fancy_number":
    st.subheader("🔢 Fancy Number Checker (Last 6 Digits)")
    
    with st.form("fancy_number_form"):
        phone_number = st.text_input("Enter phone number to check")
        
        if st.form_submit_button("Check Number"):
            if phone_number:
                is_fancy, pattern = is_fancy_number(phone_number)
                save_fancy_number(phone_number, is_fancy, pattern)
                
                if is_fancy:
                    st.success(f"✅ FANCY NUMBER! Pattern: {pattern}")
                else:
                    st.error(f"❌ Not fancy. {pattern}")
    
    st.subheader("Detection Rules for Last 6 Digits")
    with st.expander("What makes a number fancy?"):
        st.markdown("""
        - **Sequential numbers**: 123456, 654321  
        - **Repeating patterns**: 121212, 123123  
        - **Palindrome numbers**: 123321, 122221  
        - **Special combinations**: 112233, 111222  
        - **Repeated digits**: 999999, 888888  
        - **Bookend patterns**: 123451, 135791  
        - **Mirror patterns**: 123321, 456654  
        - **Triple digits**: 111234, 123444  
        """)
    
    st.subheader("Number Check History")
    fancy_numbers = get_fancy_numbers_history()
    
    if fancy_numbers:
        for num in fancy_numbers:
            num_id, number, is_fancy, pattern, timestamp = num
            st.markdown(f"""
            <div class="card {'fancy-true' if is_fancy else 'fancy-false'}">
                <div style="display: flex; justify-content: space-between;">
                    <h4>{number}</h4>
                    <small>{timestamp}</small>
                </div>
                <p><strong>Last 6 digits:</strong> {get_last_six_digits(number) or 'N/A'}</p>
                <p><strong>Pattern:</strong> {pattern}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No numbers checked yet.")
    
    if st.session_state.role == "admin" and st.button("🗑️ Clear History"):
        if clear_fancy_numbers_history():
            st.success("Fancy numbers history cleared!")
            st.rerun()

# ... [Rest of the code remains unchanged] ...
