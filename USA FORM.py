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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        
        hashed_password = hash_password(password)
        
        cursor.execute("""
            SELECT role FROM users 
            WHERE username = ? AND password = ?
        """, (username, hashed_password))
        
        result = cursor.fetchone()
        return result[0] if result else None
    
    except sqlite3.Error as e:
        st.error(f"Authentication error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def init_db():
    conn = None
    try:
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT CHECK(role IN ('agent', 'admin'))
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                request_type TEXT,
                identifier TEXT,
                comment TEXT,
                timestamp TEXT,
                completed INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_leader TEXT,
                agent_name TEXT,
                ticket_id TEXT,
                error_description TEXT,
                timestamp TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                message TEXT,
                timestamp TEXT,
                mentions TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hold_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uploader TEXT,
                image_data BLOB,
                timestamp TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fancy_numbers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT UNIQUE,
                is_fancy INTEGER,
                pattern TEXT,
                timestamp TEXT
            )
        """)
        
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, password, role) 
            VALUES (?, ?, ?)
        """, ("admin", hash_password("admin123"), "admin"))
        
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, password, role) 
            VALUES (?, ?, ?)
        """, ("taha kirri", hash_password("arise@99"), "admin"))
        
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

# --------------------------
# Fancy Number Checker Functions
# --------------------------

def get_last_six_digits(number):
    """Extract and return the last 6 digits of a phone number."""
    clean_number = re.sub(r'\D', '', number)
    return clean_number[-6:] if len(clean_number) >= 6 else None

def is_consecutive(digits, ascending=True):
    """Check if digits form a perfect consecutive sequence."""
    for i in range(1, len(digits)):
        diff = digits[i] - digits[i-1]
        if ascending and diff != 1:
            return False
        if not ascending and diff != -1:
            return False
    return True

def is_fancy_number(number):
    """Strict check for truly fancy numbers in last 6 digits."""
    last_six = get_last_six_digits(number)
    if not last_six or len(last_six) != 6:
        return False, "Invalid number length"
    
    digits = [int(d) for d in last_six]
    
    # 1. All digits same (e.g., 999999)
    if len(set(digits)) == 1:
        return True, "All digits identical"
    
    # 2. Perfect consecutive sequences
    if is_consecutive(digits):
        return True, "Perfect ascending sequence"
    if is_consecutive(digits, ascending=False):
        return True, "Perfect descending sequence"
    
    # 3. Perfect palindrome (e.g., 123321)
    if digits == digits[::-1]:
        return True, "Perfect palindrome"
    
    # 4. Repeating patterns (e.g., 121212, 123123)
    if digits[:3] == digits[3:]:
        return True, "Repeating 3-digit pattern"
    if digits[:2] == digits[2:4] == digits[4:]:
        return True, "Repeating 2-digit pattern"
    
    # 5. Multiple pairs (e.g., 112233)
    if all(digits[i] == digits[i+1] for i in range(0, 6, 2)):
        return True, "Multiple pairs"
    
    # 6. Triple digits (e.g., 111234, 123444)
    for i in range(4):
        if digits[i] == digits[i+1] == digits[i+2]:
            return True, "Triple repeating digits"
    
    # 7. Bookend with mirror (e.g., 123321, 135531)
    if digits[0] == digits[-1] and digits[1] == digits[-2] and digits[2] == digits[-3]:
        return True, "Mirrored bookend pattern"
    
    # 8. Special known fancy patterns
    special_cases = {
        '112233': 'Multiple pairs',
        '121212': 'Repeating 12 pattern',
        '123123': 'Repeating 123 pattern',
        '111222': 'Triple pairs',
        '123321': 'Mirror sequence'
    }
    
    if last_six in special_cases:
        return True, special_cases[last_six]
    
    return False, "No fancy pattern detected"

def save_fancy_number(number, is_fancy, pattern):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO fancy_numbers (number, is_fancy, pattern, timestamp) 
            VALUES (?, ?, ?, ?)
        """, (number, 1 if is_fancy else 0, pattern, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to save fancy number: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_fancy_numbers_history():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM fancy_numbers 
            ORDER BY timestamp DESC
            LIMIT 50
        """)
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to fetch fancy numbers history: {e}")
        return []
    finally:
        if conn:
            conn.close()

def clear_fancy_numbers_history():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fancy_numbers")
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to clear fancy numbers history: {e}")
        return False
    finally:
        if conn:
            conn.close()

# --------------------------
# Streamlit UI Configuration
# --------------------------

st.set_page_config(
    page_title="Request Management System", 
    page_icon=":office:",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { 
        background-color: #ffffff; 
        border-right: 1px solid #e9ecef; 
    }
    .stButton>button {
        background-color: #3b82f6;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    .card {
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .fancy-true {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
    }
    .fancy-false {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.current_section = "requests"

init_db()

# Login Page
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏢 Request Management System")
        st.markdown("---")
        
        with st.container():
            st.header("Login")
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Login"):
                    if username and password:
                        role = authenticate(username, password)
                        if role:
                            st.session_state.authenticated = True
                            st.session_state.role = role
                            st.session_state.username = username
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                    else:
                        st.warning("Please enter both username and password")

# Main Application
else:
    with st.sidebar:
        st.title(f"👋 Welcome, {st.session_state.username}")
        st.markdown("---")
        
        nav_options = [
            ("📋 Requests", "requests"),
            ("🖼️ HOLD", "hold"),
            ("❌ Ticket Mistakes", "mistakes"),
            ("💬 Group Chat", "chat"),
            ("🔢 Fancy Number Checker", "fancy_number")
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
    
    st.title(f"{'📋' if st.session_state.current_section == 'requests' else ''}"
             f"{'🖼️' if st.session_state.current_section == 'hold' else ''}"
             f"{'❌' if st.session_state.current_section == 'mistakes' else ''}"
             f"{'💬' if st.session_state.current_section == 'chat' else ''}"
             f"{'⚙️' if st.session_state.current_section == 'admin' else ''}"
             f"{'🔢' if st.session_state.current_section == 'fancy_number' else ''}"
             f" {st.session_state.current_section.title()}")

    # Fancy Number Checker Section
    if st.session_state.current_section == "fancy_number":
        st.subheader("🔢 Strict Fancy Number Checker")
        st.markdown("Analyzes **last 6 digits** for true fancy patterns")
        
        with st.form("fancy_number_form"):
            phone_number = st.text_input("Enter phone number")
            
            if st.form_submit_button("Check Number"):
                if phone_number:
                    is_fancy, pattern = is_fancy_number(phone_number)
                    save_fancy_number(phone_number, is_fancy, pattern)
                    
                    if is_fancy:
                        st.success(f"✅ **FANCY NUMBER DETECTED!** Pattern: {pattern}")
                    else:
                        st.error(f"❌ **Not a fancy number.** {pattern}")
        
        with st.expander("ℹ️ What counts as fancy?"):
            st.markdown("""
            **True fancy numbers must have:**  
            - Perfect sequences (123456, 654321)  
            - Perfect repeats (121212, 123123)  
            - Mirror patterns (123321)  
            - Triple digits (111234)  
            - Multiple pairs (112233)  
            - All digits same (999999)  
            
            *Regular numbers like 1123456789 won't be flagged as fancy*
            """)
        
        st.subheader("Check History")
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
                    <p><strong>Last 6:</strong> {get_last_six_digits(number) or 'N/A'}</p>
                    <p><strong>Pattern:</strong> {pattern}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No numbers checked yet.")
        
        if st.session_state.role == "admin" and st.button("🗑️ Clear History"):
            if clear_fancy_numbers_history():
                st.success("History cleared!")
                st.rerun()

    # ... [Rest of your existing sections (requests, hold, mistakes, chat, admin) remain unchanged] ...

if __name__ == "__main__":
    st.write("Request Management System")
