import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, time, timedelta
import os
import re
from PIL import Image
import io
import pandas as pd
import json
import sys
import traceback

# --------------------------
# Database Functions
# --------------------------

def get_db_connection():
    """Create and return a database connection."""
    try:
        # Ensure the data directory exists
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Create database connection with proper path handling
        db_path = os.path.join(data_dir, "requests.db")
        conn = sqlite3.connect(db_path)
        
        # Enable foreign key support
        conn.execute("PRAGMA foreign_keys = ON")
        
        return conn
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        raise

def hash_password(password):
    """Hash a password using SHA-256."""
    if not isinstance(password, str):
        password = str(password)
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    """Authenticate a user and return their role."""
    if not username or not password:
        return None
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        hashed_password = hash_password(password)
        cursor.execute(
            "SELECT role FROM users WHERE LOWER(username) = LOWER(?) AND password = ?", 
            (username.lower(), hashed_password)
        )
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return None
    finally:
        conn.close()

def init_db():
    """Initialize the database with all necessary tables."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # List of table creation statements
        table_statements = [
            # System settings table
            """CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                killswitch_enabled INTEGER DEFAULT 0,
                chat_killswitch_enabled INTEGER DEFAULT 0
            )""",
            
            # Users table
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT CHECK(role IN ('agent', 'admin')),
                is_vip INTEGER DEFAULT 0
            )""",
            
            # Requests table
            """CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                request_type TEXT,
                identifier TEXT,
                comment TEXT,
                timestamp TEXT,
                completed INTEGER DEFAULT 0
            )""",
            
            # Request comments table
            """CREATE TABLE IF NOT EXISTS request_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER,
                user TEXT,
                comment TEXT,
                timestamp TEXT,
                FOREIGN KEY (request_id) REFERENCES requests (id)
            )""",
            
            # Mistakes table
            """CREATE TABLE IF NOT EXISTS mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_leader TEXT,
                agent_name TEXT,
                ticket_id TEXT,
                error_description TEXT,
                timestamp TEXT
            )""",
            
            # Group messages table
            """CREATE TABLE IF NOT EXISTS group_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                message TEXT,
                timestamp TEXT,
                mentions TEXT
            )""",
            
            # VIP messages table
            """CREATE TABLE IF NOT EXISTS vip_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                message TEXT,
                timestamp TEXT,
                mentions TEXT
            )""",
            
            # Hold images table
            """CREATE TABLE IF NOT EXISTS hold_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uploader TEXT,
                image_data BLOB,
                timestamp TEXT
            )""",
            
            # Late logins table
            """CREATE TABLE IF NOT EXISTS late_logins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                presence_time TEXT,
                login_time TEXT,
                reason TEXT,
                timestamp TEXT
            )""",
            
            # Quality issues table
            """CREATE TABLE IF NOT EXISTS quality_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                issue_type TEXT,
                timing TEXT,
                mobile_number TEXT,
                product TEXT,
                timestamp TEXT
            )""",
            
            # Midshift issues table
            """CREATE TABLE IF NOT EXISTS midshift_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                issue_type TEXT,
                start_time TEXT,
                end_time TEXT,
                timestamp TEXT
            )"""
        ]
        
        # Create all tables
        for statement in table_statements:
            try:
                cursor.execute(statement)
            except sqlite3.Error as e:
                print(f"Error creating table: {str(e)}")
                print(f"Statement: {statement}")
                raise
        
        # Initialize system settings if not exists
        cursor.execute("""
            INSERT OR IGNORE INTO system_settings (id, killswitch_enabled, chat_killswitch_enabled) 
            VALUES (1, 0, 0)
        """)
        
        # Create default admin account
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, password, role, is_vip) 
            VALUES (?, ?, ?, ?)
        """, ("taha kirri", hash_password("arise@99"), "admin", 1))
        
        # Create other admin accounts
        admin_accounts = [
            ("taha kirri", "arise@99"),
            ("Issam Samghini", "admin@2025"),
            ("Loubna Fellah", "admin@99"),
            ("Youssef Kamal", "admin@006"),
            ("Fouad Fathi", "admin@55")
        ]
        
        for username, password in admin_accounts:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO users (username, password, role, is_vip) 
                    VALUES (?, ?, ?, ?)
                """, (username, hash_password(password), "admin", 0))
            except sqlite3.Error as e:
                print(f"Error creating admin account for {username}: {str(e)}")
        
        # Create agent accounts
        agents = [
            ("Karabila Younes", "30866"),
            ("Kaoutar Mzara", "30514"),
            ("Ben Tahar Chahid", "30864"),
            ("Cherbassi Khadija", "30868"),
            ("Lekhmouchi Kamal", "30869"),
            ("Said Kilani", "30626"),
            ("AGLIF Rachid", "30830"),
            ("Yacine Adouha", "30577"),
            ("Manal Elanbi", "30878"),
            ("Jawad Ouassaddine", "30559"),
            ("Kamal Elhaouar", "30844"),
            ("Hoummad Oubella", "30702"),
            ("Zouheir Essafi", "30703"),
            ("Anwar Atifi", "30781"),
            ("Said Elgaouzi", "30782"),
            ("HAMZA SAOUI", "30716"),
            ("Ibtissam Mazhari", "30970"),
            ("Imad Ghazali", "30971"),
            ("Jamila Lahrech", "30972"),
            ("Nassim Ouazzani Touhami", "30973"),
            ("Salaheddine Chaggour", "30974"),
            ("Omar Tajani", "30711"),
            ("Nizar Remz", "30728"),
            ("Abdelouahed Fettah", "30693"),
            ("Amal Bouramdane", "30675"),
            ("Fatima Ezzahrae Oubaalla", "30513"),
            ("Redouane Bertal", "30643"),
            ("Abdelouahab Chenani", "30789"),
            ("Imad El Youbi", "30797"),
            ("Youssef Hammouda", "30791"),
            ("Anas Ouassifi", "30894"),
            ("SALSABIL ELMOUSS", "30723"),
            ("Hicham Khalafa", "30712"),
            ("Ghita Adib", "30710"),
            ("Aymane Msikila", "30722"),
            ("Marouane Boukhadda", "30890"),
            ("Hamid Boulatouan", "30899"),
            ("Bouchaib Chafiqi", "30895"),
            ("Houssam Gouaalla", "30891"),
            ("Abdellah Rguig", "30963"),
            ("Abdellatif Chatir", "30964"),
            ("Abderrahman Oueto", "30965"),
            ("Fatiha Lkamel", "30967"),
            ("Abdelhamid Jaber", "30708"),
            ("Yassine Elkanouni", "30735")
        ]
        
        for agent_name, workspace_id in agents:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO users (username, password, role, is_vip) 
                    VALUES (?, ?, ?, ?)
                """, (agent_name, hash_password(workspace_id), "agent", 0))
            except sqlite3.Error as e:
                print(f"Error creating agent account for {agent_name}: {str(e)}")
        
        # Ensure taha kirri has VIP status
        cursor.execute("""
            UPDATE users SET is_vip = 1 WHERE LOWER(username) = 'taha kirri'
        """)
        
        conn.commit()
        print("Database initialized successfully")
        
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

# Initialize database when the module is loaded
try:
    init_db()
except Exception as e:
    st.error("Failed to initialize database. Please contact the administrator.")
    print(f"Database initialization failed: {str(e)}")

def is_killswitch_enabled():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT killswitch_enabled FROM system_settings WHERE id = 1")
        result = cursor.fetchone()
        return bool(result[0]) if result else False
    finally:
        conn.close()

def is_chat_killswitch_enabled():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT chat_killswitch_enabled FROM system_settings WHERE id = 1")
        result = cursor.fetchone()
        return bool(result[0]) if result else False
    finally:
        conn.close()

def toggle_killswitch(enable):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE system_settings SET killswitch_enabled = ? WHERE id = 1",
                      (1 if enable else 0,))
        conn.commit()
        return True
    finally:
        conn.close()

def toggle_chat_killswitch(enable):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE system_settings SET chat_killswitch_enabled = ? WHERE id = 1",
                      (1 if enable else 0,))
        conn.commit()
        return True
    finally:
        conn.close()

def add_request(agent_name, request_type, identifier, comment):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO requests (agent_name, request_type, identifier, comment, timestamp) 
            VALUES (?, ?, ?, ?, ?)
        """, (agent_name, request_type, identifier, comment, timestamp))
        
        request_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO request_comments (request_id, user, comment, timestamp)
            VALUES (?, ?, ?, ?)
        """, (request_id, agent_name, f"Request created: {comment}", timestamp))
        
        conn.commit()
        return True
    finally:
        conn.close()

def get_requests():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM requests ORDER BY timestamp DESC")
        return cursor.fetchall()
    finally:
        conn.close()

def search_requests(query):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = f"%{query.lower()}%"
        cursor.execute("""
            SELECT * FROM requests 
            WHERE LOWER(agent_name) LIKE ? 
            OR LOWER(request_type) LIKE ? 
            OR LOWER(identifier) LIKE ? 
            OR LOWER(comment) LIKE ?
            ORDER BY timestamp DESC
        """, (query, query, query, query))
        return cursor.fetchall()
    finally:
        conn.close()

def update_request_status(request_id, completed):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE requests SET completed = ? WHERE id = ?",
                      (1 if completed else 0, request_id))
        conn.commit()
        return True
    finally:
        conn.close()

def add_request_comment(request_id, user, comment):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO request_comments (request_id, user, comment, timestamp)
            VALUES (?, ?, ?, ?)
        """, (request_id, user, comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    finally:
        conn.close()

def get_request_comments(request_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM request_comments 
            WHERE request_id = ?
            ORDER BY timestamp ASC
        """, (request_id,))
        return cursor.fetchall()
    finally:
        conn.close()

def add_mistake(team_leader, agent_name, ticket_id, error_description):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO mistakes (team_leader, agent_name, ticket_id, error_description, timestamp) 
            VALUES (?, ?, ?, ?, ?)
        """, (team_leader, agent_name, ticket_id, error_description,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    finally:
        conn.close()

def get_mistakes():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mistakes ORDER BY timestamp DESC")
        return cursor.fetchall()
    finally:
        conn.close()

def search_mistakes(query):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = f"%{query.lower()}%"
        cursor.execute("""
            SELECT * FROM mistakes 
            WHERE LOWER(agent_name) LIKE ? 
            OR LOWER(ticket_id) LIKE ? 
            OR LOWER(error_description) LIKE ?
            ORDER BY timestamp DESC
        """, (query, query, query))
        return cursor.fetchall()
    finally:
        conn.close()

def send_group_message(sender, message):
    if is_killswitch_enabled() or is_chat_killswitch_enabled():
        st.error("Chat is currently locked. Please contact the developer.")
        return False
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        mentions = re.findall(r'@(\w+)', message)
        cursor.execute("""
            INSERT INTO group_messages (sender, message, timestamp, mentions) 
            VALUES (?, ?, ?, ?)
        """, (sender, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
             ','.join(mentions)))
        conn.commit()
        return True
    finally:
        conn.close()

def get_group_messages():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM group_messages ORDER BY timestamp DESC LIMIT 50")
        return cursor.fetchall()
    finally:
        conn.close()

def get_all_users():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM users")
        return cursor.fetchall()
    finally:
        conn.close()

def add_user(username, password, role):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                      (username, hash_password(password), role))
        conn.commit()
        return True
    finally:
        conn.close()

def delete_user(user_id):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True
    finally:
        conn.close()

def add_hold_image(uploader, image_data):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hold_images (uploader, image_data, timestamp) 
            VALUES (?, ?, ?)
        """, (uploader, image_data, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    finally:
        conn.close()

def get_hold_images():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hold_images ORDER BY timestamp DESC")
        return cursor.fetchall()
    finally:
        conn.close()

def clear_hold_images():
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM hold_images")
        conn.commit()
        return True
    finally:
        conn.close()

def clear_all_requests():
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM requests")
        cursor.execute("DELETE FROM request_comments")
        conn.commit()
        return True
    finally:
        conn.close()

def clear_all_mistakes():
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM mistakes")
        conn.commit()
        return True
    finally:
        conn.close()

def clear_all_group_messages():
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM group_messages")
        conn.commit()
        return True
    finally:
        conn.close()

def add_late_login(agent_name, presence_time, login_time, reason):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO late_logins (agent_name, presence_time, login_time, reason, timestamp) 
            VALUES (?, ?, ?, ?, ?)
        """, (agent_name, presence_time, login_time, reason,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    finally:
        conn.close()

def get_late_logins():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM late_logins ORDER BY timestamp DESC")
        return cursor.fetchall()
    finally:
        conn.close()

def add_quality_issue(agent_name, issue_type, timing, mobile_number, product):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO quality_issues (agent_name, issue_type, timing, mobile_number, product, timestamp) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (agent_name, issue_type, timing, mobile_number, product,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    finally:
        conn.close()

def get_quality_issues():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quality_issues ORDER BY timestamp DESC")
        return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching quality issues: {str(e)}")
    finally:
        conn.close()

def add_midshift_issue(agent_name, issue_type, start_time, end_time):
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO midshift_issues (agent_name, issue_type, start_time, end_time, timestamp) 
            VALUES (?, ?, ?, ?, ?)
        """, (agent_name, issue_type, start_time, end_time,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error adding mid-shift issue: {str(e)}")
    finally:
        conn.close()

def get_midshift_issues():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM midshift_issues ORDER BY timestamp DESC")
        return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching mid-shift issues: {str(e)}")
    finally:
        conn.close()

def clear_late_logins():
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM late_logins")
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error clearing late logins: {str(e)}")
    finally:
        conn.close()

def clear_quality_issues():
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM quality_issues")
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error clearing quality issues: {str(e)}")
    finally:
        conn.close()

def clear_midshift_issues():
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM midshift_issues")
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error clearing mid-shift issues: {str(e)}")
    finally:
        conn.close()

def send_vip_message(sender, message):
    """Send a message in the VIP-only chat"""
    if is_killswitch_enabled() or is_chat_killswitch_enabled():
        st.error("Chat is currently locked. Please contact the developer.")
        return False
    
    if not is_vip_user(sender) and sender.lower() != "taha kirri":
        st.error("Only VIP users can send messages in this chat.")
        return False
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        mentions = re.findall(r'@(\w+)', message)
        cursor.execute("""
            INSERT INTO vip_messages (sender, message, timestamp, mentions) 
            VALUES (?, ?, ?, ?)
        """, (sender, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
             ','.join(mentions)))
        conn.commit()
        return True
    finally:
        conn.close()

def get_vip_messages():
    """Get messages from the VIP-only chat"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vip_messages ORDER BY timestamp DESC LIMIT 50")
        return cursor.fetchall()
    finally:
        conn.close()

# --------------------------
# Break Scheduling Functions (from first code)
# --------------------------

def init_break_session_state():
    if 'templates' not in st.session_state:
        st.session_state.templates = {}
    if 'current_template' not in st.session_state:
        st.session_state.current_template = None
    if 'agent_bookings' not in st.session_state:
        st.session_state.agent_bookings = {}
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = datetime.now().strftime('%Y-%m-%d')
    if 'timezone_offset' not in st.session_state:
        st.session_state.timezone_offset = 0  # GMT by default
    if 'break_limits' not in st.session_state:
        st.session_state.break_limits = {}
    if 'active_templates' not in st.session_state:
        st.session_state.active_templates = []
    
    # Load data from files if exists
    if os.path.exists('templates.json'):
        with open('templates.json', 'r') as f:
            st.session_state.templates = json.load(f)
    if os.path.exists('break_limits.json'):
        with open('break_limits.json', 'r') as f:
            st.session_state.break_limits = json.load(f)
    if os.path.exists('all_bookings.json'):
        with open('all_bookings.json', 'r') as f:
            st.session_state.agent_bookings = json.load(f)
    if os.path.exists('active_templates.json'):
        with open('active_templates.json', 'r') as f:
            st.session_state.active_templates = json.load(f)

def adjust_template_time(time_str, hours):
    """Adjust a single time string by adding/subtracting hours"""
    try:
        if not time_str.strip():
            return ""
        time_obj = datetime.strptime(time_str.strip(), "%H:%M")
        adjusted_time = (time_obj + timedelta(hours=hours)).time()
        return adjusted_time.strftime("%H:%M")
    except:
        return time_str

def bulk_update_template_times(hours):
    """Update all template times by adding/subtracting hours"""
    if 'templates' not in st.session_state:
        return False
    
    try:
        for template_name in st.session_state.templates:
            template = st.session_state.templates[template_name]
            
            # Update lunch breaks
            template["lunch_breaks"] = [
                adjust_template_time(t, hours) 
                for t in template["lunch_breaks"]
            ]
            
            # Update early tea breaks
            template["tea_breaks"]["early"] = [
                adjust_template_time(t, hours) 
                for t in template["tea_breaks"]["early"]
            ]
            
            # Update late tea breaks
            template["tea_breaks"]["late"] = [
                adjust_template_time(t, hours) 
                for t in template["tea_breaks"]["late"]
            ]
        
        save_break_data()
        return True
    except Exception as e:
        st.error(f"Error updating template times: {str(e)}")
        return False

def save_break_data():
    with open('templates.json', 'w') as f:
        json.dump(st.session_state.templates, f)
    with open('break_limits.json', 'w') as f:
        json.dump(st.session_state.break_limits, f)
    with open('all_bookings.json', 'w') as f:
        json.dump(st.session_state.agent_bookings, f)
    with open('active_templates.json', 'w') as f:
        json.dump(st.session_state.active_templates, f)

def adjust_time(time_str, offset):
    try:
        if not time_str.strip():
            return ""
        time_obj = datetime.strptime(time_str.strip(), "%H:%M")
        adjusted_time = (time_obj + timedelta(hours=offset)).time()
        return adjusted_time.strftime("%H:%M")
    except:
        return time_str

def adjust_template_times(template, offset):
    """Safely adjust template times with proper error handling"""
    try:
        if not template or not isinstance(template, dict):
            return {
                "lunch_breaks": [],
                "tea_breaks": {"early": [], "late": []}
            }
            
        adjusted_template = {
            "lunch_breaks": [adjust_time(t, offset) for t in template.get("lunch_breaks", [])],
            "tea_breaks": {
                "early": [adjust_time(t, offset) for t in template.get("tea_breaks", {}).get("early", [])],
                "late": [adjust_time(t, offset) for t in template.get("tea_breaks", {}).get("late", [])]
            }
        }
        return adjusted_template
    except Exception as e:
        st.error(f"Error adjusting template times: {str(e)}")
        return {
            "lunch_breaks": [],
            "tea_breaks": {"early": [], "late": []}
        }

def count_bookings(date, break_type, time_slot):
    count = 0
    if date in st.session_state.agent_bookings:
        for agent_id, breaks in st.session_state.agent_bookings[date].items():
            if break_type == "lunch" and "lunch" in breaks and breaks["lunch"] == time_slot:
                count += 1
            elif break_type == "early_tea" and "early_tea" in breaks and breaks["early_tea"] == time_slot:
                count += 1
            elif break_type == "late_tea" and "late_tea" in breaks and breaks["late_tea"] == time_slot:
                count += 1
    return count

def display_schedule(template):
    st.header("LM US ENG 3:00 PM shift")
    
    # Lunch breaks table
    st.markdown("### LUNCH BREAKS")
    lunch_df = pd.DataFrame({
        "DATE": [st.session_state.selected_date],
        **{time: [""] for time in template["lunch_breaks"]}
    })
    st.table(lunch_df)
    
    st.markdown("**KINDLY RESPECT THE RULES BELOW**")
    st.markdown("**Non Respect Of Break Rules = Incident**")
    st.markdown("---")
    
    # Tea breaks table
    st.markdown("### TEA BREAK")
    
    # Create two columns for tea breaks
    max_rows = max(len(template["tea_breaks"]["early"]), len(template["tea_breaks"]["late"]))
    tea_data = {
        "Early Tea Break": template["tea_breaks"]["early"] + [""] * (max_rows - len(template["tea_breaks"]["early"])),
        "Late Tea Break": template["tea_breaks"]["late"] + [""] * (max_rows - len(template["tea_breaks"]["late"]))
    }
    tea_df = pd.DataFrame(tea_data)
    st.table(tea_df)
    
    # Rules section
    st.markdown("""
    **NO BREAK IN THE LAST HOUR WILL BE AUTHORIZED**  
    **PS: ONLY 5 MINUTES BIO IS AUTHORIZED IN THE LAST HHOUR BETWEEN 23:00 TILL 23:30 AND NO BREAK AFTER 23:30 !!!**  
    **BREAKS SHOULD BE TAKEN AT THE NOTED TIME AND NEED TO BE CONFIRMED FROM RTA OR TEAM LEADERS**
    """)

def migrate_booking_data():
    if 'agent_bookings' in st.session_state:
        for date in st.session_state.agent_bookings:
            for agent in st.session_state.agent_bookings[date]:
                bookings = st.session_state.agent_bookings[date][agent]
                if "lunch" in bookings and isinstance(bookings["lunch"], str):
                    bookings["lunch"] = {
                        "time": bookings["lunch"],
                        "template": "Default Template",
                        "booked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                if "early_tea" in bookings and isinstance(bookings["early_tea"], str):
                    bookings["early_tea"] = {
                        "time": bookings["early_tea"],
                        "template": "Default Template",
                        "booked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                if "late_tea" in bookings and isinstance(bookings["late_tea"], str):
                    bookings["late_tea"] = {
                        "time": bookings["late_tea"],
                        "template": "Default Template",
                        "booked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
        
        save_break_data()

def clear_all_bookings():
    if is_killswitch_enabled():
        st.error("System is currently locked. Please contact the developer.")
        return False
    
    try:
        # Clear session state bookings
        st.session_state.agent_bookings = {}
        
        # Clear the bookings file
        if os.path.exists('all_bookings.json'):
            with open('all_bookings.json', 'w') as f:
                json.dump({}, f)
        
        # Save empty state to ensure it's propagated
        save_break_data()
        
        # Force session state refresh
        st.session_state.last_request_count = 0
        st.session_state.last_mistake_count = 0
        st.session_state.last_message_ids = []
        
        return True
    except Exception as e:
        st.error(f"Error clearing bookings: {str(e)}")
        return False

def admin_break_dashboard():
    st.title("Break Schedule Management")
    st.markdown("---")
    
    # Initialize templates if empty
    if 'templates' not in st.session_state:
        st.session_state.templates = {}
    
    # Create default template if no templates exist
    if not st.session_state.templates:
        default_template = {
            "lunch_breaks": ["19:30", "20:00", "20:30", "21:00", "21:30"],
            "tea_breaks": {
                "early": ["16:00", "16:15", "16:30", "16:45", "17:00", "17:15", "17:30"],
                "late": ["21:45", "22:00", "22:15", "22:30"]
            }
        }
        st.session_state.templates["Default Template"] = default_template
        st.session_state.current_template = "Default Template"
        if "Default Template" not in st.session_state.active_templates:
            st.session_state.active_templates.append("Default Template")
        save_break_data()
    
    # Template Activation Management
    st.subheader("🔄 Template Activation")
    st.info("Only activated templates will be available for agents to book breaks from.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("### Active Templates")
        active_templates = st.session_state.active_templates
        template_list = list(st.session_state.templates.keys())
        
        for template in template_list:
            is_active = template in active_templates
            if st.checkbox(f"{template} {'✅' if is_active else ''}", 
                         value=is_active, 
                         key=f"active_{template}"):
                if template not in active_templates:
                    active_templates.append(template)
            else:
                if template in active_templates:
                    active_templates.remove(template)
        
        st.session_state.active_templates = active_templates
        save_break_data()
    
    with col2:
        st.write("### Statistics")
        st.metric("Total Templates", len(template_list))
        st.metric("Active Templates", len(active_templates))
    
    st.markdown("---")
    
    # Template Management
    st.subheader("Template Management")
    
    col1, col2 = st.columns(2)
    with col1:
        template_name = st.text_input("New Template Name:")
    with col2:
        if st.button("Create Template"):
            if template_name and template_name not in st.session_state.templates:
                st.session_state.templates[template_name] = {
                    "lunch_breaks": ["19:30", "20:00", "20:30", "21:00", "21:30"],
                    "tea_breaks": {
                        "early": ["16:00", "16:15", "16:30", "16:45", "17:00", "17:15", "17:30"],
                        "late": ["21:45", "22:00", "22:15", "22:30"]
                    }
                }
                save_break_data()
                st.success(f"Template '{template_name}' created!")
                st.rerun()
    
    # Template Selection and Editing
    selected_template = st.selectbox(
        "Select Template to Edit:",
        list(st.session_state.templates.keys())
    )
    
    if selected_template:
        template = st.session_state.templates[selected_template]
        
        # Time adjustment buttons
        st.subheader("Time Adjustment")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Add 1 Hour to All Times"):
                bulk_update_template_times(1)
                st.success("Added 1 hour to all break times")
                st.rerun()
        with col2:
            if st.button("➖ Subtract 1 Hour from All Times"):
                bulk_update_template_times(-1)
                st.success("Subtracted 1 hour from all break times")
                st.rerun()
        
        # Edit Lunch Breaks
        st.subheader("Edit Lunch Breaks")
        lunch_breaks = st.text_area(
            "Enter lunch break times (one per line):",
            "\n".join(template["lunch_breaks"]),
            height=150
        )
        
        # Edit Tea Breaks
        st.subheader("Edit Tea Breaks")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Early Tea Breaks")
            early_tea = st.text_area(
                "Enter early tea break times (one per line):",
                "\n".join(template["tea_breaks"]["early"]),
                height=200
            )
        
        with col2:
            st.write("Late Tea Breaks")
            late_tea = st.text_area(
                "Enter late tea break times (one per line):",
                "\n".join(template["tea_breaks"]["late"]),
                height=200
            )
        
        # Break Limits
        st.markdown("---")
        st.subheader("Break Limits")
        
        if selected_template not in st.session_state.break_limits:
            st.session_state.break_limits[selected_template] = {
                "lunch": {time: 5 for time in template["lunch_breaks"]},
                "early_tea": {time: 3 for time in template["tea_breaks"]["early"]},
                "late_tea": {time: 3 for time in template["tea_breaks"]["late"]}
            }
        
        limits = st.session_state.break_limits[selected_template]
        
        st.write("Lunch Break Limits")
        cols = st.columns(len(template["lunch_breaks"]))
        for i, time in enumerate(template["lunch_breaks"]):
            with cols[i]:
                limits["lunch"][time] = st.number_input(
                    f"Max at {time}",
                    min_value=1,
                    value=limits["lunch"].get(time, 5),
                    key=f"lunch_limit_{time}"
                )
        
        st.write("Early Tea Break Limits")
        cols = st.columns(len(template["tea_breaks"]["early"]))
        for i, time in enumerate(template["tea_breaks"]["early"]):
            with cols[i]:
                limits["early_tea"][time] = st.number_input(
                    f"Max at {time}",
                    min_value=1,
                    value=limits["early_tea"].get(time, 3),
                    key=f"early_tea_limit_{time}"
                )
        
        st.write("Late Tea Break Limits")
        cols = st.columns(len(template["tea_breaks"]["late"]))
        for i, time in enumerate(template["tea_breaks"]["late"]):
            with cols[i]:
                limits["late_tea"][time] = st.number_input(
                    f"Max at {time}",
                    min_value=1,
                    value=limits["late_tea"].get(time, 3),
                    key=f"late_tea_limit_{time}"
                )
        
        # Consolidated save button
        if st.button("Save All Changes", type="primary"):
            template["lunch_breaks"] = [t.strip() for t in lunch_breaks.split("\n") if t.strip()]
            template["tea_breaks"]["early"] = [t.strip() for t in early_tea.split("\n") if t.strip()]
            template["tea_breaks"]["late"] = [t.strip() for t in late_tea.split("\n") if t.strip()]
            save_break_data()
            st.success("All changes saved successfully!")
            st.rerun()
        
        if st.button("Delete Template") and len(st.session_state.templates) > 1:
            del st.session_state.templates[selected_template]
            if selected_template in st.session_state.active_templates:
                st.session_state.active_templates.remove(selected_template)
            save_break_data()
            st.success(f"Template '{selected_template}' deleted!")
            st.rerun()
    
    # View Bookings with template information
    st.markdown("---")
    st.subheader("View All Bookings")
    
    dates = list(st.session_state.agent_bookings.keys())
    if dates:
        selected_date = st.selectbox("Select Date:", dates, index=len(dates)-1)
        
        # Add clear bookings button with proper confirmation
        if 'confirm_clear' not in st.session_state:
            st.session_state.confirm_clear = False
            
        col1, col2 = st.columns([1, 3])
        with col1:
            if not st.session_state.confirm_clear:
                if st.button("Clear All Bookings"):
                    st.session_state.confirm_clear = True
            
        if st.session_state.confirm_clear:
            st.warning("⚠️ Are you sure you want to clear all bookings? This cannot be undone!")
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Yes, Clear All"):
                    if clear_all_bookings():
                        st.success("All bookings have been cleared!")
                        st.session_state.confirm_clear = False
                        st.rerun()
            with col2:
                if st.button("Cancel"):
                    st.session_state.confirm_clear = False
                    st.rerun()
        
        if selected_date in st.session_state.agent_bookings:
            bookings_data = []
            for agent, breaks in st.session_state.agent_bookings[selected_date].items():
                # Get template name from any break type (they should all be the same)
                template_name = None
                for break_type in ['lunch', 'early_tea', 'late_tea']:
                    if break_type in breaks and isinstance(breaks[break_type], dict):
                        template_name = breaks[break_type].get('template', 'Unknown')
                        break
                
                booking = {
                    "Agent": agent,
                    "Template": template_name or "Unknown",
                    "Lunch": breaks.get("lunch", {}).get("time", "-") if isinstance(breaks.get("lunch"), dict) else breaks.get("lunch", "-"),
                    "Early Tea": breaks.get("early_tea", {}).get("time", "-") if isinstance(breaks.get("early_tea"), dict) else breaks.get("early_tea", "-"),
                    "Late Tea": breaks.get("late_tea", {}).get("time", "-") if isinstance(breaks.get("late_tea"), dict) else breaks.get("late_tea", "-")
                }
                bookings_data.append(booking)
            
            if bookings_data:
                df = pd.DataFrame(bookings_data)
                st.dataframe(df)
                
                # Export option
                if st.button("Export to CSV"):
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Download CSV",
                        csv,
                        f"break_bookings_{selected_date}.csv",
                        "text/csv"
                    )
            else:
                st.info("No bookings found for this date")
    else:
        st.info("No bookings available")

def time_to_minutes(time_str):
    """Convert time string (HH:MM) to minutes since midnight"""
    try:
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    except:
        return None

def times_overlap(time1, time2, duration_minutes=15):
    """Check if two time slots overlap, assuming each break is duration_minutes long"""
    t1 = time_to_minutes(time1)
    t2 = time_to_minutes(time2)
    
    if t1 is None or t2 is None:
        return False
        
    # Check if the breaks overlap
    return abs(t1 - t2) < duration_minutes

def check_break_conflicts(selected_breaks):
    """Check for conflicts between selected breaks"""
    times = []
    
    # Collect all selected break times
    if selected_breaks.get("lunch"):
        times.append(("lunch", selected_breaks["lunch"]))
    if selected_breaks.get("early_tea"):
        times.append(("early_tea", selected_breaks["early_tea"]))
    if selected_breaks.get("late_tea"):
        times.append(("late_tea", selected_breaks["late_tea"]))
    
    # Check each pair of breaks for overlap
    for i in range(len(times)):
        for j in range(i + 1, len(times)):
            break1_type, break1_time = times[i]
            break2_type, break2_time = times[j]
            
            if times_overlap(break1_time, break2_time, 30 if "lunch" in (break1_type, break2_type) else 15):
                return f"Conflict detected between {break1_type.replace('_', ' ')} ({break1_time}) and {break2_type.replace('_', ' ')} ({break2_time})"
    
    return None

def agent_break_dashboard():
    st.title("Break Booking")
    st.markdown("---")
    
    if is_killswitch_enabled():
        st.error("System is currently locked. Break booking is disabled.")
        return
    
    # Initialize session state
    if 'agent_bookings' not in st.session_state:
        st.session_state.agent_bookings = {}
    if 'temp_bookings' not in st.session_state:
        st.session_state.temp_bookings = {}
    if 'booking_confirmed' not in st.session_state:
        st.session_state.booking_confirmed = False
    if 'selected_template_name' not in st.session_state:
        st.session_state.selected_template_name = None
    
    agent_id = st.session_state.username
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Check if agent already has confirmed bookings
    has_confirmed_bookings = (
        current_date in st.session_state.agent_bookings and 
        agent_id in st.session_state.agent_bookings[current_date]
    )
    
    if has_confirmed_bookings:
        st.success("Your breaks have been confirmed for today")
        st.subheader("Your Confirmed Breaks")
        bookings = st.session_state.agent_bookings[current_date][agent_id]
        template_name = None
        for break_type in ['lunch', 'early_tea', 'late_tea']:
            if break_type in bookings and isinstance(bookings[break_type], dict):
                template_name = bookings[break_type].get('template')
                break
        
        if template_name:
            st.info(f"Template: **{template_name}**")
        
        for break_type, display_name in [
            ("lunch", "Lunch Break"),
            ("early_tea", "Early Tea Break"),
            ("late_tea", "Late Tea Break")
        ]:
            if break_type in bookings:
                if isinstance(bookings[break_type], dict):
                    st.write(f"**{display_name}:** {bookings[break_type]['time']}")
                else:
                    st.write(f"**{display_name}:** {bookings[break_type]}")
        return
    
    # Step 1: Template Selection
    if not st.session_state.selected_template_name:
        st.subheader("Step 1: Select Break Schedule")
        available_templates = st.session_state.active_templates
        if not available_templates:
            st.error("No break schedules available. Please contact admin.")
            return
        
        selected_template = st.selectbox(
            "Choose your break schedule:",
            available_templates,
            index=None,
            placeholder="Select a template..."
        )
        
        if selected_template:
            if st.button("Continue to Break Selection"):
                st.session_state.selected_template_name = selected_template
                st.rerun()
        return
    
    # Step 2: Break Selection
    template = st.session_state.templates[st.session_state.selected_template_name]
    
    st.subheader("Step 2: Select Your Breaks")
    st.info(f"Selected Template: **{st.session_state.selected_template_name}**")
    
    if st.button("Change Template"):
        st.session_state.selected_template_name = None
        st.session_state.temp_bookings = {}
        st.rerun()
    
    # Break selection
    with st.form("break_selection_form"):
        st.write("**Lunch Break** (30 minutes)")
        lunch_time = st.selectbox(
            "Select Lunch Break",
            [""] + template["lunch_breaks"],
            format_func=lambda x: "No selection" if x == "" else x
        )
        
        st.write("**Early Tea Break** (15 minutes)")
        early_tea = st.selectbox(
            "Select Early Tea Break",
            [""] + template["tea_breaks"]["early"],
            format_func=lambda x: "No selection" if x == "" else x
        )
        
        st.write("**Late Tea Break** (15 minutes)")
        late_tea = st.selectbox(
            "Select Late Tea Break",
            [""] + template["tea_breaks"]["late"],
            format_func=lambda x: "No selection" if x == "" else x
        )
        
        # Validate and confirm
        if st.form_submit_button("Confirm Breaks"):
            if not (lunch_time or early_tea or late_tea):
                st.error("Please select at least one break.")
                return
            
            # Check for time conflicts
            selected_breaks = {
                "lunch": lunch_time if lunch_time else None,
                "early_tea": early_tea if early_tea else None,
                "late_tea": late_tea if late_tea else None
            }
            
            conflict = check_break_conflicts(selected_breaks)
            if conflict:
                st.error(conflict)
                return
            
            # Check limits for each selected break
            can_book = True
            if lunch_time:
                count = sum(1 for bookings in st.session_state.agent_bookings.get(current_date, {}).values()
                           if isinstance(bookings.get("lunch"), dict) and bookings["lunch"]["time"] == lunch_time)
                limit = st.session_state.break_limits.get(st.session_state.selected_template_name, {}).get("lunch", {}).get(lunch_time, 5)
                if count >= limit:
                    st.error(f"Lunch break at {lunch_time} is full.")
                    can_book = False
            
            if early_tea:
                count = sum(1 for bookings in st.session_state.agent_bookings.get(current_date, {}).values()
                           if isinstance(bookings.get("early_tea"), dict) and bookings["early_tea"]["time"] == early_tea)
                limit = st.session_state.break_limits.get(st.session_state.selected_template_name, {}).get("early_tea", {}).get(early_tea, 3)
                if count >= limit:
                    st.error(f"Early tea break at {early_tea} is full.")
                    can_book = False
            
            if late_tea:
                count = sum(1 for bookings in st.session_state.agent_bookings.get(current_date, {}).values()
                           if isinstance(bookings.get("late_tea"), dict) and bookings["late_tea"]["time"] == late_tea)
                limit = st.session_state.break_limits.get(st.session_state.selected_template_name, {}).get("late_tea", {}).get(late_tea, 3)
                if count >= limit:
                    st.error(f"Late tea break at {late_tea} is full.")
                    can_book = False
            
            if can_book:
                # Save the bookings
                if current_date not in st.session_state.agent_bookings:
                    st.session_state.agent_bookings[current_date] = {}
                
                bookings = {}
                if lunch_time:
                    bookings["lunch"] = {
                        "time": lunch_time,
                        "template": st.session_state.selected_template_name,
                        "booked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                if early_tea:
                    bookings["early_tea"] = {
                        "time": early_tea,
                        "template": st.session_state.selected_template_name,
                        "booked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                if late_tea:
                    bookings["late_tea"] = {
                        "time": late_tea,
                        "template": st.session_state.selected_template_name,
                        "booked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                
                st.session_state.agent_bookings[current_date][agent_id] = bookings
                save_break_data()
                st.success("Your breaks have been confirmed!")
                st.rerun()

def is_vip_user(username):
    """Check if a user has VIP status"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT is_vip FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        return bool(result[0]) if result else False
    finally:
        conn.close()

def set_vip_status(username, is_vip):
    """Set or remove VIP status for a user"""
    if not username:
        return False
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_vip = ? WHERE username = ?", 
                      (1 if is_vip else 0, username))
        conn.commit()
        return True
    finally:
        conn.close()

# --------------------------
# Streamlit Configuration
# --------------------------

st.set_page_config(
    page_title="USA Team Management System",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'is_vip' not in st.session_state:
    st.session_state.is_vip = False

# Custom CSS
st.markdown("""
    <style>
    .stButton button {
        background-color: #1f77b4;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .stButton button:hover {
        background-color: #135c8d;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        color: #155724;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-message {
        padding: 1rem;
        background-color: #f8d7da;
        color: #721c24;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)

def logout():
    """Clear session state and log out user."""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.is_vip = False
    st.experimental_rerun()

def login_page():
    """Display the login page."""
    st.title("USA Team Management System")
    
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        st.markdown("""
            <div style='text-align: center; padding: 2rem;'>
                <h2>Welcome! Please log in</h2>
            </div>
        """, unsafe_allow_html=True)
        
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="login_button"):
            if username and password:
                role = authenticate(username, password)
                if role:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.role = role
                    
                    # Check if user is VIP
                    conn = get_db_connection()
                    try:
                        cursor = conn.cursor()
                        cursor.execute("SELECT is_vip FROM users WHERE username = ?", (username,))
                        result = cursor.fetchone()
                        st.session_state.is_vip = bool(result[0]) if result else False
                    finally:
                        conn.close()
                    
                    st.success("Login successful!")
                    st.experimental_rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter both username and password")

def check_killswitch():
    """Check if the system killswitch is enabled."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT killswitch_enabled FROM system_settings WHERE id = 1")
        result = cursor.fetchone()
        return bool(result[0]) if result else False
    finally:
        conn.close()

def check_chat_killswitch():
    """Check if the chat killswitch is enabled."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT chat_killswitch_enabled FROM system_settings WHERE id = 1")
        result = cursor.fetchone()
        return bool(result[0]) if result else False
    finally:
        conn.close()

# Main application flow
if not st.session_state.authenticated:
    login_page()
else:
    # Check killswitch before proceeding
    if check_killswitch() and st.session_state.role != 'admin':
        st.error("The system is currently under maintenance. Please try again later.")
        if st.button("Logout"):
            logout()
    else:
        # Continue with the main application
        st.sidebar.title(f"Welcome, {st.session_state.username}")
        st.sidebar.text(f"Role: {st.session_state.role.capitalize()}")
        
        if st.sidebar.button("Logout"):
            logout()

# --------------------------
# Streamlit App
# --------------------------

def main():
    """Main application entry point"""
    try:
        # Initialize session state for navigation
        if "page" not in st.session_state:
            st.session_state.page = "requests"
        
        # Initialize database
        init_db()
        
        # Main application logic after authentication
        if st.session_state.authenticated:
            # Sidebar navigation
            st.sidebar.title("Navigation")
            
            # Admin-specific options
            if st.session_state.role == "admin":
                page = st.sidebar.radio(
                    "Select Section",
                    ["Requests", "Mistakes", "Chat", "VIP Chat", "Break Schedule", 
                     "Late Logins", "Quality Issues", "Midshift Issues", "System Settings"]
                )
            else:
                page = st.sidebar.radio(
                    "Select Section",
                    ["Requests", "Chat", "Break Schedule"] + 
                    (["VIP Chat"] if st.session_state.is_vip else [])
                )
            
            st.session_state.page = page.lower()
            
            # Display selected page content
            if st.session_state.page == "requests":
                display_requests_page()
            elif st.session_state.page == "mistakes":
                display_mistakes_page()
            elif st.session_state.page == "chat":
                display_chat_page()
            elif st.session_state.page == "vip chat":
                display_vip_chat_page()
            elif st.session_state.page == "break schedule":
                if st.session_state.role == "admin":
                    admin_break_dashboard()
                else:
                    agent_break_dashboard()
            elif st.session_state.page == "late logins":
                display_late_logins_page()
            elif st.session_state.page == "quality issues":
                display_quality_issues_page()
            elif st.session_state.page == "midshift issues":
                display_midshift_issues_page()
            elif st.session_state.page == "system settings":
                display_system_settings_page()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        print(f"Error details: {str(e)}")
        traceback.print_exc()

def display_requests_page():
    """Display the requests management page"""
    st.title("Request Management")
    
    # Add new request section
    st.subheader("Submit New Request")
    with st.form("new_request_form"):
        request_type = st.selectbox(
            "Request Type",
            ["Technical Issue", "System Access", "Software Installation", 
             "Hardware Problem", "Other"]
        )
        identifier = st.text_input("Ticket/Reference ID")
        comment = st.text_area("Description")
        
        if st.form_submit_button("Submit Request"):
            if identifier and comment:
                if add_request(st.session_state.username, request_type, identifier, comment):
                    st.success("Request submitted successfully!")
                    st.rerun()
            else:
                st.error("Please fill in all fields")
    
    # View requests section
    st.subheader("View Requests")
    search_query = st.text_input("Search requests...", key="request_search")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        show_completed = st.checkbox("Show Completed", value=False)
    
    requests = search_requests(search_query) if search_query else get_requests()
    
    if requests:
        for req in requests:
            if not show_completed and req[5]:  # Skip completed requests if not showing
                continue
                
            with st.expander(
                f"{req[2]} - {req[3]} ({req[1]}) - {'✅' if req[5] else '🔄'}"
            ):
                st.write(f"**Type:** {req[2]}")
                st.write(f"**Agent:** {req[1]}")
                st.write(f"**ID:** {req[3]}")
                st.write(f"**Description:** {req[4]}")
                st.write(f"**Submitted:** {req[5]}")
                
                # Comments section
                st.subheader("Comments")
                comments = get_request_comments(req[0])
                for comment in comments:
                    st.text(f"{comment[2]} ({comment[4]}): {comment[3]}")
                
                # Add comment form
                new_comment = st.text_input("Add comment", key=f"comment_{req[0]}")
                if st.button("Add Comment", key=f"add_comment_{req[0]}"):
                    if new_comment:
                        if add_request_comment(req[0], st.session_state.username, new_comment):
                            st.success("Comment added!")
                            st.rerun()
                
                # Toggle completion status (admin only)
                if st.session_state.role == "admin":
                    if st.button(
                        "Mark as Complete" if not req[5] else "Reopen",
                        key=f"toggle_{req[0]}"
                    ):
                        if update_request_status(req[0], not req[5]):
                            st.success(
                                "Request marked as complete!" if not req[5] 
                                else "Request reopened!"
                            )
                            st.rerun()
    else:
        st.info("No requests found")

def display_mistakes_page():
    """Display the mistakes tracking page"""
    if st.session_state.role != "admin":
        st.error("Access denied")
        return
        
    st.title("Mistake Tracking")
    
    # Add new mistake section
    st.subheader("Record New Mistake")
    with st.form("new_mistake_form"):
        agent_name = st.selectbox(
            "Agent Name",
            [user[1] for user in get_all_users() if user[2] == "agent"]
        )
        ticket_id = st.text_input("Ticket ID")
        error_description = st.text_area("Error Description")
        
        if st.form_submit_button("Record Mistake"):
            if agent_name and ticket_id and error_description:
                if add_mistake(st.session_state.username, agent_name, ticket_id, 
                             error_description):
                    st.success("Mistake recorded successfully!")
                    st.rerun()
            else:
                st.error("Please fill in all fields")
    
    # View mistakes section
    st.subheader("View Mistakes")
    search_query = st.text_input("Search mistakes...", key="mistake_search")
    
    mistakes = search_mistakes(search_query) if search_query else get_mistakes()
    
    if mistakes:
        for mistake in mistakes:
            with st.expander(f"{mistake[2]} - {mistake[3]}"):
                st.write(f"**Team Leader:** {mistake[1]}")
                st.write(f"**Agent:** {mistake[2]}")
                st.write(f"**Ticket ID:** {mistake[3]}")
                st.write(f"**Description:** {mistake[4]}")
                st.write(f"**Recorded:** {mistake[5]}")
    else:
        st.info("No mistakes found")

def display_chat_page():
    """Display the group chat page"""
    st.title("Group Chat")
    
    if check_chat_killswitch():
        st.error("Chat is currently disabled")
        return
    
    # Message input
    with st.form("new_message_form"):
        message = st.text_area("Type your message")
        if st.form_submit_button("Send"):
            if message:
                if send_group_message(st.session_state.username, message):
                    st.success("Message sent!")
                    st.rerun()
            else:
                st.error("Please enter a message")
    
    # Display messages
    st.subheader("Messages")
    messages = get_group_messages()
    
    if messages:
        for msg in messages:
            with st.container():
                st.markdown(f"""
                    <div style='padding: 10px; border-radius: 5px; margin: 5px 0;
                         background-color: {"#1e293b" if msg[1] == st.session_state.username else "#334155"}'>
                        <strong>{msg[1]}</strong> <small>{msg[3]}</small><br>
                        {msg[2]}
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No messages yet")

def display_vip_chat_page():
    """Display the VIP chat page"""
    if not st.session_state.is_vip and st.session_state.username.lower() != "taha kirri":
        st.error("Access denied")
        return
        
    st.title("VIP Chat")
    
    if check_chat_killswitch():
        st.error("Chat is currently disabled")
        return
    
    # Message input
    with st.form("new_vip_message_form"):
        message = st.text_area("Type your message")
        if st.form_submit_button("Send"):
            if message:
                if send_vip_message(st.session_state.username, message):
                    st.success("Message sent!")
                    st.rerun()
            else:
                st.error("Please enter a message")
    
    # Display messages
    st.subheader("Messages")
    messages = get_vip_messages()
    
    if messages:
        for msg in messages:
            with st.container():
                st.markdown(f"""
                    <div style='padding: 10px; border-radius: 5px; margin: 5px 0;
                         background-color: {"#1e293b" if msg[1] == st.session_state.username else "#334155"}'>
                        <strong>{msg[1]}</strong> <small>{msg[3]}</small><br>
                        {msg[2]}
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No messages yet")

def display_late_logins_page():
    """Display the late logins tracking page"""
    if st.session_state.role != "admin":
        st.error("Access denied")
        return
        
    st.title("Late Login Tracking")
    
    # Add new late login
    st.subheader("Record Late Login")
    with st.form("new_late_login_form"):
        agent_name = st.selectbox(
            "Agent Name",
            [user[1] for user in get_all_users() if user[2] == "agent"]
        )
        presence_time = st.time_input("Presence Time")
        login_time = st.time_input("Login Time")
        reason = st.text_area("Reason")
        
        if st.form_submit_button("Record Late Login"):
            if agent_name and reason:
                if add_late_login(agent_name, presence_time.strftime("%H:%M"),
                                login_time.strftime("%H:%M"), reason):
                    st.success("Late login recorded successfully!")
                    st.rerun()
            else:
                st.error("Please fill in all fields")
    
    # View late logins
    st.subheader("View Late Logins")
    late_logins = get_late_logins()
    
    if late_logins:
        for login in late_logins:
            with st.expander(f"{login[1]} - {login[5]}"):
                st.write(f"**Agent:** {login[1]}")
                st.write(f"**Presence Time:** {login[2]}")
                st.write(f"**Login Time:** {login[3]}")
                st.write(f"**Reason:** {login[4]}")
                st.write(f"**Recorded:** {login[5]}")
    else:
        st.info("No late logins recorded")

def display_quality_issues_page():
    """Display the quality issues tracking page"""
    if st.session_state.role != "admin":
        st.error("Access denied")
        return
        
    st.title("Quality Issues Tracking")
    
    # Add new quality issue
    st.subheader("Record Quality Issue")
    with st.form("new_quality_issue_form"):
        agent_name = st.selectbox(
            "Agent Name",
            [user[1] for user in get_all_users() if user[2] == "agent"]
        )
        issue_type = st.selectbox(
            "Issue Type",
            ["Customer Service", "Technical Knowledge", "Communication",
             "Process Adherence", "Other"]
        )
        timing = st.time_input("Time of Issue")
        mobile_number = st.text_input("Customer Mobile Number")
        product = st.text_input("Product/Service")
        
        if st.form_submit_button("Record Issue"):
            if agent_name and issue_type and mobile_number and product:
                if add_quality_issue(agent_name, issue_type, 
                                   timing.strftime("%H:%M"),
                                   mobile_number, product):
                    st.success("Quality issue recorded successfully!")
                    st.rerun()
            else:
                st.error("Please fill in all fields")
    
    # View quality issues
    st.subheader("View Quality Issues")
    quality_issues = get_quality_issues()
    
    if quality_issues:
        for issue in quality_issues:
            with st.expander(f"{issue[1]} - {issue[2]} - {issue[6]}"):
                st.write(f"**Agent:** {issue[1]}")
                st.write(f"**Issue Type:** {issue[2]}")
                st.write(f"**Time:** {issue[3]}")
                st.write(f"**Mobile Number:** {issue[4]}")
                st.write(f"**Product:** {issue[5]}")
                st.write(f"**Recorded:** {issue[6]}")
    else:
        st.info("No quality issues recorded")

def display_midshift_issues_page():
    """Display the midshift issues tracking page"""
    if st.session_state.role != "admin":
        st.error("Access denied")
        return
        
    st.title("Midshift Issues Tracking")
    
    # Add new midshift issue
    st.subheader("Record Midshift Issue")
    with st.form("new_midshift_issue_form"):
        agent_name = st.selectbox(
            "Agent Name",
            [user[1] for user in get_all_users() if user[2] == "agent"]
        )
        issue_type = st.selectbox(
            "Issue Type",
            ["System Down", "Application Error", "Network Issue",
             "Hardware Problem", "Other"]
        )
        start_time = st.time_input("Start Time")
        end_time = st.time_input("End Time")
        
        if st.form_submit_button("Record Issue"):
            if agent_name and issue_type:
                if add_midshift_issue(agent_name, issue_type,
                                    start_time.strftime("%H:%M"),
                                    end_time.strftime("%H:%M")):
                    st.success("Midshift issue recorded successfully!")
                    st.rerun()
            else:
                st.error("Please fill in all fields")
    
    # View midshift issues
    st.subheader("View Midshift Issues")
    midshift_issues = get_midshift_issues()
    
    if midshift_issues:
        for issue in midshift_issues:
            with st.expander(f"{issue[1]} - {issue[2]} - {issue[5]}"):
                st.write(f"**Agent:** {issue[1]}")
                st.write(f"**Issue Type:** {issue[2]}")
                st.write(f"**Start Time:** {issue[3]}")
                st.write(f"**End Time:** {issue[4]}")
                st.write(f"**Recorded:** {issue[5]}")
    else:
        st.info("No midshift issues recorded")

def display_system_settings_page():
    """Display the system settings page"""
    if st.session_state.role != "admin":
        st.error("Access denied")
        return
        
    st.title("System Settings")
    
    # System killswitch
    st.subheader("System Access Control")
    killswitch_enabled = is_killswitch_enabled()
    if st.checkbox("Enable System Maintenance Mode", value=killswitch_enabled):
        if not killswitch_enabled:
            if toggle_killswitch(True):
                st.success("System maintenance mode enabled")
                st.rerun()
    else:
        if killswitch_enabled:
            if toggle_killswitch(False):
                st.success("System maintenance mode disabled")
                st.rerun()
    
    # Chat killswitch
    st.subheader("Chat System Control")
    chat_killswitch_enabled = is_chat_killswitch_enabled()
    if st.checkbox("Disable Chat System", value=chat_killswitch_enabled):
        if not chat_killswitch_enabled:
            if toggle_chat_killswitch(True):
                st.success("Chat system disabled")
                st.rerun()
    else:
        if chat_killswitch_enabled:
            if toggle_chat_killswitch(False):
                st.success("Chat system enabled")
                st.rerun()
    
    # VIP user management
    st.subheader("VIP User Management")
    users = get_all_users()
    
    for user in users:
        is_vip = is_vip_user(user[1])
        if st.checkbox(f"VIP Status - {user[1]}", value=is_vip):
            if not is_vip:
                if set_vip_status(user[1], True):
                    st.success(f"VIP status granted to {user[1]}")
                    st.rerun()
        else:
            if is_vip and user[1].lower() != "taha kirri":
                if set_vip_status(user[1], False):
                    st.success(f"VIP status removed from {user[1]}")
                    st.rerun()
    
    # Data management
    st.subheader("Data Management")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Clear All Requests"):
            if clear_all_requests():
                st.success("All requests cleared")
                st.rerun()
    
    with col2:
        if st.button("Clear All Mistakes"):
            if clear_all_mistakes():
                st.success("All mistakes cleared")
                st.rerun()
    
    with col3:
        if st.button("Clear All Messages"):
            if clear_all_group_messages():
                st.success("All messages cleared")
                st.rerun()
    
    with col4:
        if st.button("Clear All Images"):
            if clear_hold_images():
                st.success("All images cleared")
                st.rerun()

if __name__ == "__main__":
    main()
