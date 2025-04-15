import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, time
import os
import re
from PIL import Image
import io
import pandas as pd
import json

# --------------------------
# Database Functions
# --------------------------

def get_db_connection():
    """Create and return a database connection."""
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect("data/requests.db")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        hashed_password = hash_password(password)
        cursor.execute("SELECT role FROM users WHERE LOWER(username) = LOWER(?) AND password = ?", 
                      (username, hashed_password))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def init_db():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT CHECK(role IN ('agent', 'admin')))
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                request_type TEXT,
                identifier TEXT,
                comment TEXT,
                timestamp TEXT,
                completed INTEGER DEFAULT 0)
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_leader TEXT,
                agent_name TEXT,
                ticket_id TEXT,
                error_description TEXT,
                timestamp TEXT)
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                message TEXT,
                timestamp TEXT,
                mentions TEXT)
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hold_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uploader TEXT,
                image_data BLOB,
                timestamp TEXT)
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS request_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER,
                user TEXT,
                comment TEXT,
                timestamp TEXT,
                FOREIGN KEY(request_id) REFERENCES requests(id))
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS late_logins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                presence_time TEXT,
                login_time TEXT,
                reason TEXT,
                timestamp TEXT)
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                issue_type TEXT,
                timing TEXT,
                mobile_number TEXT,
                product TEXT,
                timestamp TEXT)
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS midshift_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                issue_type TEXT,
                start_time TEXT,
                end_time TEXT,
                timestamp TEXT)
        """)
        
        # Handle system_settings table schema migration
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_settings'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE system_settings (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    killswitch_enabled INTEGER DEFAULT 0,
                    chat_killswitch_enabled INTEGER DEFAULT 0)
            """)
            cursor.execute("INSERT INTO system_settings (id, killswitch_enabled, chat_killswitch_enabled) VALUES (1, 0, 0)")
        else:
            cursor.execute("PRAGMA table_info(system_settings)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'chat_killswitch_enabled' not in columns:
                cursor.execute("ALTER TABLE system_settings ADD COLUMN chat_killswitch_enabled INTEGER DEFAULT 0")
                cursor.execute("UPDATE system_settings SET chat_killswitch_enabled = 0 WHERE id = 1")
        
        # Create default admin account
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, password, role) 
            VALUES (?, ?, ?)
        """, ("taha kirri", hash_password("arise@99"), "admin"))
        admin_accounts = [
            ("taha kirri", "arise@99"),
            ("Issam Samghini", "admin@2025"),
            ("Loubna Fellah", "admin@99"),
            ("Youssef Kamal", "admin@006"),
            ("Fouad Fathi", "admin@55")
        ]
        
        for username, password in admin_accounts:
            cursor.execute("""
                INSERT OR IGNORE INTO users (username, password, role) 
                VALUES (?, ?, ?)
            """, (username, hash_password(password), "admin"))
        
        # Create agent accounts (agent name as username, workspace ID as password)
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
            cursor.execute("""
                INSERT OR IGNORE INTO users (username, password, role) 
                VALUES (?, ?, ?)
            """, (agent_name, hash_password(workspace_id), "agent"))
        
        conn.commit()
    finally:
        conn.close()

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

# --------------------------
# Break Booking System Functions
# --------------------------

def init_break_booking_db():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS break_bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                shift TEXT,
                break_type TEXT,
                slot TEXT,
                booking_date TEXT,
                timestamp TEXT)
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS break_settings (
                id INTEGER PRIMARY KEY DEFAULT 1,
                max_per_slot INTEGER DEFAULT 3,
                current_template TEXT DEFAULT 'default')
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS break_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                template_data TEXT)
        """)
        
        # Insert default template if not exists
        cursor.execute("SELECT COUNT(*) FROM break_templates WHERE name = 'default'")
        if cursor.fetchone()[0] == 0:
            default_template = {
                "description": "Default break schedule",
                "shifts": {
                    "2pm": {
                        "early_tea": {"start": "15:00", "end": "16:30", "slots": ["15:00", "15:15", "15:30", "15:45", "16:00", "16:15", "16:30"]},
                        "lunch": {"start": "18:30", "end": "20:30", "slots": ["18:30", "19:00", "19:30", "20:00", "20:30"]},
                        "late_tea": {"start": "20:45", "end": "21:30", "slots": ["20:45", "21:00", "21:15", "21:30"]}
                    },
                    "6pm": {
                        "early_tea": {"start": "19:00", "end": "20:45", "slots": ["19:00", "19:15", "19:30", "19:45", "20:00", "20:15", "20:30", "20:45"]},
                        "lunch": {"start": "21:00", "end": "22:30", "slots": ["21:00", "21:30", "22:00", "22:30"]},
                        "late_tea": {"start": "00:00", "end": "01:30", "slots": ["00:00", "00:15", "00:30", "00:45", "01:00", "01:15", "01:30"]}
                    }
                }
            }
            
            cursor.execute("""
                INSERT INTO break_templates (name, description, template_data)
                VALUES (?, ?, ?)
            """, ("default", "Default break schedule", json.dumps(default_template)))
        
        # Ensure settings exist
        cursor.execute("SELECT COUNT(*) FROM break_settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO break_settings (id, max_per_slot, current_template)
                VALUES (1, 3, 'default')
            """)
        
        conn.commit()
    finally:
        conn.close()

def get_break_settings():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT max_per_slot, current_template FROM break_settings WHERE id = 1")
        result = cursor.fetchone()
        return {"max_per_slot": result[0], "current_template": result[1]} if result else {"max_per_slot": 3, "current_template": "default"}
    finally:
        conn.close()

def update_break_settings(max_per_slot=None, current_template=None):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if max_per_slot is not None:
            cursor.execute("UPDATE break_settings SET max_per_slot = ? WHERE id = 1", (max_per_slot,))
        if current_template is not None:
            cursor.execute("UPDATE break_settings SET current_template = ? WHERE id = 1", (current_template,))
        conn.commit()
        return True
    finally:
        conn.close()

def get_break_template(template_name=None):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if template_name is None:
            settings = get_break_settings()
            template_name = settings["current_template"]
        
        cursor.execute("SELECT template_data FROM break_templates WHERE name = ?", (template_name,))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else None
    finally:
        conn.close()

def get_all_break_templates():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name, description, template_data FROM break_templates")
        return {row[0]: {"description": row[1], **json.loads(row[2])} for row in cursor.fetchall()}
    finally:
        conn.close()

def save_break_template(name, description, template_data):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO break_templates (name, description, template_data)
            VALUES (?, ?, ?)
        """, (name, description, json.dumps(template_data)))
        conn.commit()
        return True
    finally:
        conn.close()

def delete_break_template(name):
    if name == "default":
        return False
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM break_templates WHERE name = ?", (name,))
        conn.commit()
        return True
    finally:
        conn.close()

def add_break_booking(agent_name, shift, break_type, slot, booking_date):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if booking already exists
        cursor.execute("""
            SELECT COUNT(*) FROM break_bookings 
            WHERE agent_name = ? AND shift = ? AND break_type = ? AND booking_date = ?
        """, (agent_name, shift, break_type, booking_date))
        
        if cursor.fetchone()[0] > 0:
            return False
        
        # Check if slot is full
        settings = get_break_settings()
        cursor.execute("""
            SELECT COUNT(*) FROM break_bookings 
            WHERE shift = ? AND break_type = ? AND slot = ? AND booking_date = ?
        """, (shift, break_type, slot, booking_date))
        
        if cursor.fetchone()[0] >= settings["max_per_slot"]:
            return False
        
        # Add booking
        cursor.execute("""
            INSERT INTO break_bookings (agent_name, shift, break_type, slot, booking_date, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (agent_name, shift, break_type, slot, booking_date, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        conn.commit()
        return True
    finally:
        conn.close()

def remove_break_booking(agent_name, shift, break_type, slot, booking_date):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM break_bookings 
            WHERE agent_name = ? AND shift = ? AND break_type = ? AND slot = ? AND booking_date = ?
        """, (agent_name, shift, break_type, slot, booking_date))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def get_break_bookings(booking_date):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT agent_name, shift, break_type, slot 
            FROM break_bookings 
            WHERE booking_date = ?
            ORDER BY slot
        """, (booking_date,))
        return cursor.fetchall()
    finally:
        conn.close()

def get_agent_break_bookings(agent_name, booking_date):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT shift, break_type, slot 
            FROM break_bookings 
            WHERE agent_name = ? AND booking_date = ?
        """, (agent_name, booking_date))
        return cursor.fetchall()
    finally:
        conn.close()

def clear_break_bookings(booking_date):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM break_bookings WHERE booking_date = ?", (booking_date,))
        conn.commit()
        return True
    finally:
        conn.close()

# --------------------------
# Streamlit App
# --------------------------

st.set_page_config(
    page_title="Request Management System",
    page_icon=":office:",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #121212; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #1E1E1E; }
    .stButton>button { background-color: #2563EB; color: white; }
    .card { background-color: #1F1F1F; border-radius: 12px; padding: 1.5rem; }
    .metric-card { background-color: #1F2937; border-radius: 10px; padding: 20px; }
    .killswitch-active {
        background-color: #4A1E1E;
        border-left: 5px solid #D32F2F;
        padding: 1rem;
        margin-bottom: 1rem;
        color: #FFCDD2;
    }
    .chat-killswitch-active {
        background-color: #1E3A4A;
        border-left: 5px solid #1E88E5;
        padding: 1rem;
        margin-bottom: 1rem;
        color: #B3E5FC;
    }
    .comment-box {
        margin: 0.5rem 0;
        padding: 0.5rem;
        background: #2D2D2D;
        border-radius: 8px;
    }
    .comment-user {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.25rem;
    }
    .comment-text {
        margin-top: 0.5rem;
    }
    .editable-break {
        background-color: #2D3748;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .stTimeInput > div > div > input {
        padding: 0.5rem;
    }
    .time-input {
        font-family: monospace;
    }
    /* Fancy number checker styles */
    .fancy-number { color: #00ff00; font-weight: bold; }
    .normal-number { color: #ffffff; }
    .result-box { padding: 15px; border-radius: 5px; margin: 10px 0; }
    .fancy-result { background-color: #1e3d1e; border: 1px solid #00ff00; }
    .normal-result { background-color: #3d1e1e; border: 1px solid #ff0000; }
</style>
""", unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state.update({
        "authenticated": False,
        "role": None,
        "username": None,
        "current_section": "requests",
        "last_request_count": 0,
        "last_mistake_count": 0,
        "last_message_ids": []
    })

init_db()

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏢 Request Management System")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if username and password:
                    role = authenticate(username, password)
                    if role:
                        st.session_state.update({
                            "authenticated": True,
                            "role": role,
                            "username": username,
                            "last_request_count": len(get_requests()),
                            "last_mistake_count": len(get_mistakes()),
                            "last_message_ids": [msg[0] for msg in get_group_messages()]
                        })
                        st.rerun()
                    else:
                        st.error("Invalid credentials")

else:
    if is_killswitch_enabled():
        st.markdown("""
        <div class="killswitch-active">
            <h3>⚠️ SYSTEM LOCKED ⚠️</h3>
            <p>The system is currently in read-only mode.</p>
        </div>
        """, unsafe_allow_html=True)
    elif is_chat_killswitch_enabled():
        st.markdown("""
        <div class="chat-killswitch-active">
            <h3>⚠️ CHAT LOCKED ⚠️</h3>
            <p>The chat functionality is currently disabled.</p>
        </div>
        """, unsafe_allow_html=True)

    def show_notifications():
        current_requests = get_requests()
        current_mistakes = get_mistakes()
        current_messages = get_group_messages()
        
        new_requests = len(current_requests) - st.session_state.last_request_count
        if new_requests > 0 and st.session_state.last_request_count > 0:
            st.toast(f"📋 {new_requests} new request(s) submitted!")
        st.session_state.last_request_count = len(current_requests)
        
        new_mistakes = len(current_mistakes) - st.session_state.last_mistake_count
        if new_mistakes > 0 and st.session_state.last_mistake_count > 0:
            st.toast(f"❌ {new_mistakes} new mistake(s) reported!")
        st.session_state.last_mistake_count = len(current_mistakes)
        
        current_message_ids = [msg[0] for msg in current_messages]
        new_messages = [msg for msg in current_messages if msg[0] not in st.session_state.last_message_ids]
        for msg in new_messages:
            if msg[1] != st.session_state.username:
                mentions = msg[4].split(',') if msg[4] else []
                if st.session_state.username in mentions:
                    st.toast(f"💬 You were mentioned by {msg[1]}!")
                else:
                    st.toast(f"💬 New message from {msg[1]}!")
        st.session_state.last_message_ids = current_message_ids

    show_notifications()

    with st.sidebar:
        st.title(f"👋 Welcome, {st.session_state.username}")
        st.markdown("---")
        
        nav_options = [
            ("📋 Requests", "requests"),
            ("🖼️ HOLD", "hold"),
            ("❌ Mistakes", "mistakes"),
            ("💬 Chat", "chat"),
            ("📱 Fancy Number", "fancy_number"),
            ("⏰ Late Login", "late_login"),
            ("📞 Quality Issues", "quality_issues"),
            ("🔄 Mid-shift Issues", "midshift_issues"),
            ("☕ Break Booking", "breaks")
        ]
        if st.session_state.role == "admin":
            nav_options.append(("⚙️ Admin", "admin"))
        
        for option, value in nav_options:
            if st.button(option, key=f"nav_{value}"):
                st.session_state.current_section = value
                
        st.markdown("---")
        pending_requests = len([r for r in get_requests() if not r[6]])
        new_mistakes = len(get_mistakes())
        unread_messages = len([m for m in get_group_messages() 
                             if m[0] not in st.session_state.last_message_ids 
                             and m[1] != st.session_state.username])
        
        st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <h4>🔔 Notifications</h4>
            <p>📋 Pending requests: {pending_requests}</p>
            <p>❌ Recent mistakes: {new_mistakes}</p>
            <p>💬 Unread messages: {unread_messages}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.rerun()

    st.title(st.session_state.current_section.title())

    if st.session_state.current_section == "requests":
        if not is_killswitch_enabled():
            with st.expander("➕ Submit New Request"):
                with st.form("request_form"):
                    cols = st.columns([1, 3])
                    request_type = cols[0].selectbox("Type", ["Email", "Phone", "Ticket"])
                    identifier = cols[1].text_input("Identifier")
                    comment = st.text_area("Comment")
                    if st.form_submit_button("Submit"):
                        if identifier and comment:
                            if add_request(st.session_state.username, request_type, identifier, comment):
                                st.success("Request submitted successfully!")
                                st.rerun()
        
        st.subheader("🔍 Search Requests")
        search_query = st.text_input("Search requests...")
        requests = search_requests(search_query) if search_query else get_requests()
        
        st.subheader("All Requests")
        for req in requests:
            req_id, agent, req_type, identifier, comment, timestamp, completed = req
            with st.container():
                cols = st.columns([0.1, 0.9])
                with cols[0]:
                    if not is_killswitch_enabled():
                        st.checkbox("Done", value=bool(completed), 
                                   key=f"check_{req_id}", 
                                   on_change=update_request_status,
                                   args=(req_id, not completed))
                    else:
                        st.checkbox("Done", value=bool(completed), disabled=True)
                with cols[1]:
                    st.markdown(f"""
                    <div class="card">
                        <div style="display: flex; justify-content: space-between;">
                            <h4>#{req_id} - {req_type}</h4>
                            <small>{timestamp}</small>
                        </div>
                        <p>Agent: {agent}</p>
                        <p>Identifier: {identifier}</p>
                        <div style="margin-top: 1rem;">
                            <h5>Status Updates:</h5>
                    """, unsafe_allow_html=True)
                    
                    comments = get_request_comments(req_id)
                    for comment in comments:
                        cmt_id, _, user, cmt_text, cmt_time = comment
                        st.markdown(f"""
                            <div class="comment-box">
                                <div class="comment-user">
                                    <small><strong>{user}</strong></small>
                                    <small>{cmt_time}</small>
                                </div>
                                <div class="comment-text">{cmt_text}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    if st.session_state.role == "admin" and not is_killswitch_enabled():
                        with st.form(key=f"comment_form_{req_id}"):
                            new_comment = st.text_input("Add status update/comment")
                            if st.form_submit_button("Add Comment"):
                                if new_comment:
                                    add_request_comment(req_id, st.session_state.username, new_comment)
                                    st.rerun()

    elif st.session_state.current_section == "mistakes":
        if not is_killswitch_enabled():
            with st.expander("➕ Report New Mistake"):
                with st.form("mistake_form"):
                    cols = st.columns(3)
                    agent_name = cols[0].text_input("Agent Name")
                    ticket_id = cols[1].text_input("Ticket ID")
                    error_description = st.text_area("Error Description")
                    if st.form_submit_button("Submit"):
                        if agent_name and ticket_id and error_description:
                            add_mistake(st.session_state.username, agent_name, ticket_id, error_description)
        
        st.subheader("🔍 Search Mistakes")
        search_query = st.text_input("Search mistakes...")
        mistakes = search_mistakes(search_query) if search_query else get_mistakes()
        
        st.subheader("Mistakes Log")
        for mistake in mistakes:
            m_id, tl, agent, ticket, error, ts = mistake
            st.markdown(f"""
            <div class="card">
                <div style="display: flex; justify-content: space-between;">
                    <h4>#{m_id}</h4>
                    <small>{ts}</small>
                </div>
                <p>Agent: {agent}</p>
                <p>Ticket: {ticket}</p>
                <p>Error: {error}</p>
            </div>
            """, unsafe_allow_html=True)

    elif st.session_state.current_section == "chat":
        if is_chat_killswitch_enabled():
            st.warning("Chat functionality is currently disabled by the administrator.")
        else:
            messages = get_group_messages()
            for msg in reversed(messages):
                msg_id, sender, message, ts, mentions = msg
                is_mentioned = st.session_state.username in (mentions.split(',') if mentions else [])
                st.markdown(f"""
                <div style="background-color: {'#3b82f6' if is_mentioned else '#1F1F1F'};
                            padding: 1rem;
                            border-radius: 8px;
                            margin-bottom: 1rem;">
                    <strong>{sender}</strong>: {message}<br>
                    <small>{ts}</small>
                </div>
                """, unsafe_allow_html=True)
            
            if not is_killswitch_enabled():
                with st.form("chat_form"):
                    message = st.text_input("Type your message...")
                    if st.form_submit_button("Send"):
                        if message:
                            send_group_message(st.session_state.username, message)
                            st.rerun()

    elif st.session_state.current_section == "hold":
        if st.session_state.role == "admin" and not is_killswitch_enabled():
            with st.expander("📤 Upload Image"):
                img = st.file_uploader("Choose image", type=["jpg", "png", "jpeg"])
                if img:
                    add_hold_image(st.session_state.username, img.read())
        
        images = get_hold_images()
        if images:
            for img in images:
                iid, uploader, data, ts = img
                st.markdown(f"""
                <div class="card">
                    <div style="display: flex; justify-content: space-between;">
                        <h4>Image #{iid}</h4>
                        <small>{ts}</small>
                    </div>
                    <p>Uploaded by: {uploader}</p>
                </div>
                """, unsafe_allow_html=True)
                st.image(Image.open(io.BytesIO(data)), use_container_width=True)
        else:
            st.info("No images in HOLD")

    elif st.session_state.current_section == "fancy_number":
        st.header("📱 Lycamobile Fancy Number Checker")
        st.subheader("Official Policy: Analyzes last 6 digits only for qualifying patterns")

        phone_input = st.text_input("Enter Phone Number", 
                                  placeholder="e.g., 1555123456 or 44207123456")

        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("🔍 Check Number"):
                if not phone_input:
                    st.warning("Please enter a phone number")
                else:
                    is_fancy, pattern = is_fancy_number(phone_input)
                    clean_number = re.sub(r'\D', '', phone_input)
                    
                    # Extract last 6 digits for display
                    last_six = clean_number[-6:] if len(clean_number) >= 6 else clean_number
                    formatted_num = f"{last_six[:3]}-{last_six[3:]}" if len(last_six) == 6 else last_six

                    if is_fancy:
                        st.markdown(f"""
                        <div class="result-box fancy-result">
                            <h3><span class="fancy-number">✨ {formatted_num} ✨</span></h3>
                            <p>FANCY NUMBER DETECTED!</p>
                            <p><strong>Pattern:</strong> {pattern}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="result-box normal-result">
                            <h3><span class="normal-number">{formatted_num}</span></h3>
                            <p>Standard phone number</p>
                            <p><strong>Reason:</strong> {pattern}</p>
                        </div>
                        """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            ### Lycamobile Fancy Number Policy
            **Qualifying Patterns (last 6 digits only):**
            
            #### 6-Digit Patterns
            - 123456 (ascending)
            - 987654 (descending)
            - 666666 (repeating)
            - 100001 (palindrome)
            
            #### 3-Digit Patterns  
            - 444 555 (double triplets)
            - 121 122 (similar triplets)
            - 786 786 (repeating triplets)
            - 457 456 (nearly sequential)
            
            #### 2-Digit Patterns
            - 11 12 13 (incremental)
            - 20 20 20 (repeating)
            - 01 01 01 (alternating)
            - 32 42 52 (stepping)
            
            #### Exceptional Cases
            - Ending with 123/555/777/999
            """)

        # Test cases
        debug_mode = st.checkbox("Show test cases", False)
        if debug_mode:
            test_numbers = [
                ("16109055580", False),  # 055580 → No pattern ✗
                ("123456", True),       # 6-digit ascending ✓
                ("444555", True),       # Double triplets ✓
                ("121122", True),       # Similar triplets ✓ 
                ("111213", True),       # Incremental pairs ✓
                ("202020", True),       # Repeating pairs ✓
                ("010101", True),       # Alternating pairs ✓
                ("324252", True),       # Stepping pairs ✓
                ("7900000123", True),   # Ends with 123 ✓
                ("123458", False),      # No pattern ✗
                ("112233", False),      # Not in our strict rules ✗
                ("555555", True)        # 6 identical digits ✓
            ]
            
            st.markdown("### Strict Policy Validation")
            for number, expected in test_numbers:
                is_fancy, pattern = is_fancy_number(number)
                result = "PASS" if is_fancy == expected else "FAIL"
                color = "green" if result == "PASS" else "red"
                st.write(f"<span style='color:{color}'>{number[-6:]}: {result} ({pattern})</span>", unsafe_allow_html=True)

    elif st.session_state.current_section == "late_login":
        st.subheader("⏰ Late Login Report")
        
        if not is_killswitch_enabled():
            with st.form("late_login_form"):
                cols = st.columns(3)
                presence_time = cols[0].text_input("Time of presence (HH:MM)", placeholder="08:30")
                login_time = cols[1].text_input("Time of log in (HH:MM)", placeholder="09:15")
                reason = cols[2].selectbox("Reason", [
                    "Workspace Issue",
                    "Avaya Issue",
                    "Aaad Tool",
                    "Windows Issue",
                    "Reset Password"
                ])
                
                if st.form_submit_button("Submit"):
                    # Validate time formats
                    try:
                        datetime.strptime(presence_time, "%H:%M")
                        datetime.strptime(login_time, "%H:%M")
                        add_late_login(
                            st.session_state.username,
                            presence_time,
                            login_time,
                            reason
                        )
                        st.success("Late login reported successfully!")
                    except ValueError:
                        st.error("Invalid time format. Please use HH:MM format (e.g., 08:30)")
        
        st.subheader("Late Login Records")
        late_logins = get_late_logins()
        
        if st.session_state.role == "admin":
            if late_logins:
                # Prepare data for download
                data = []
                for login in late_logins:
                    _, agent, presence, login_time, reason, ts = login
                    data.append({
                        "Agent's Name": agent,
                        "Time of presence": presence,
                        "Time of log in": login_time,
                        "Reason": reason
                    })
                
                df = pd.DataFrame(data)
                st.dataframe(df)
                
                # Download button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download as CSV",
                    data=csv,
                    file_name="late_logins.csv",
                    mime="text/csv"
                )
                
                if st.button("Clear All Records"):
                    clear_late_logins()
                    st.rerun()
            else:
                st.info("No late login records found")
        else:
            # For agents, only show their own records
            user_logins = [login for login in late_logins if login[1] == st.session_state.username]
            if user_logins:
                data = []
                for login in user_logins:
                    _, agent, presence, login_time, reason, ts = login
                    data.append({
                        "Agent's Name": agent,
                        "Time of presence": presence,
                        "Time of log in": login_time,
                        "Reason": reason
                    })
                
                df = pd.DataFrame(data)
                st.dataframe(df)
            else:
                st.info("You have no late login records")

    elif st.session_state.current_section == "quality_issues":
        st.subheader("📞 Quality Related Technical Issue")
        
        if not is_killswitch_enabled():
            with st.form("quality_issue_form"):
                cols = st.columns(4)
                issue_type = cols[0].selectbox("Type of issue", [
                    "Blocage Physical Avaya",
                    "Hold Than Call Drop",
                    "Call Drop From Workspace",
                    "Wrong Space Frozen"
                ])
                timing = cols[1].text_input("Timing (HH:MM)", placeholder="14:30")
                mobile_number = cols[2].text_input("Mobile number")
                product = cols[3].selectbox("Product", [
                    "LM_CS_LMUSA_EN",
                    "LM_CS_LMUSA_ES"
                ])
                
                if st.form_submit_button("Submit"):
                    try:
                        datetime.strptime(timing, "%H:%M")
                        add_quality_issue(
                            st.session_state.username,
                            issue_type,
                            timing,
                            mobile_number,
                            product
                        )
                        st.success("Quality issue reported successfully!")
                    except ValueError:
                        st.error("Invalid time format. Please use HH:MM format (e.g., 14:30)")
        
        st.subheader("Quality Issue Records")
        quality_issues = get_quality_issues()
        
        if st.session_state.role == "admin":
            if quality_issues:
                # Prepare data for download
                data = []
                for issue in quality_issues:
                    _, agent, issue_type, timing, mobile, product, ts = issue
                    data.append({
                        "Agent's Name": agent,
                        "Type of issue": issue_type,
                        "Timing": timing,
                        "Mobile number": mobile,
                        "Product": product
                    })
                
                df = pd.DataFrame(data)
                st.dataframe(df)
                
                # Download button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download as CSV",
                    data=csv,
                    file_name="quality_issues.csv",
                    mime="text/csv"
                )
                
                if st.button("Clear All Records"):
                    clear_quality_issues()
                    st.rerun()
            else:
                st.info("No quality issue records found")
        else:
            # For agents, only show their own records
            user_issues = [issue for issue in quality_issues if issue[1] == st.session_state.username]
            if user_issues:
                data = []
                for issue in user_issues:
                    _, agent, issue_type, timing, mobile, product, ts = issue
                    data.append({
                        "Agent's Name": agent,
                        "Type of issue": issue_type,
                        "Timing": timing,
                        "Mobile number": mobile,
                        "Product": product
                    })
                
                df = pd.DataFrame(data)
                st.dataframe(df)
            else:
                st.info("You have no quality issue records")

    elif st.session_state.current_section == "midshift_issues":
        st.subheader("🔄 Mid-shift Technical Issue")
        
        if not is_killswitch_enabled():
            with st.form("midshift_issue_form"):
                cols = st.columns(3)
                issue_type = cols[0].selectbox("Issue Type", [
                    "Default Not Ready",
                    "Frozen Workspace",
                    "Physical Avaya",
                    "Pc Issue",
                    "Aaad Tool",
                    "Disconnected Avaya"
                ])
                start_time = cols[1].text_input("Start time (HH:MM)", placeholder="10:00")
                end_time = cols[2].text_input("End time (HH:MM)", placeholder="10:30")
                
                if st.form_submit_button("Submit"):
                    try:
                        datetime.strptime(start_time, "%H:%M")
                        datetime.strptime(end_time, "%H:%M")
                        add_midshift_issue(
                            st.session_state.username,
                            issue_type,
                            start_time,
                            end_time
                        )
                        st.success("Mid-shift issue reported successfully!")
                    except ValueError:
                        st.error("Invalid time format. Please use HH:MM format (e.g., 10:00)")
        
        st.subheader("Mid-shift Issue Records")
        midshift_issues = get_midshift_issues()
        
        if st.session_state.role == "admin":
            if midshift_issues:
                # Prepare data for download
                data = []
                for issue in midshift_issues:
                    _, agent, issue_type, start_time, end_time, ts = issue
                    data.append({
                        "Agent's Name": agent,
                        "Issue Type": issue_type,
                        "Start time": start_time,
                        "End Time": end_time
                    })
                
                df = pd.DataFrame(data)
                st.dataframe(df)
                
                # Download button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download as CSV",
                    data=csv,
                    file_name="midshift_issues.csv",
                    mime="text/csv"
                )
                
                if st.button("Clear All Records"):
                    clear_midshift_issues()
                    st.rerun()
            else:
                st.info("No mid-shift issue records found")
        else:
            # For agents, only show their own records
            user_issues = [issue for issue in midshift_issues if issue[1] == st.session_state.username]
            if user_issues:
                data = []
                for issue in user_issues:
                    _, agent, issue_type, start_time, end_time, ts = issue
                    data.append({
                        "Agent's Name": agent,
                        "Issue Type": issue_type,
                        "Start time": start_time,
                        "End Time": end_time
                    })
                
                df = pd.DataFrame(data)
                st.dataframe(df)
            else:
                st.info("You have no mid-shift issue records")

    elif st.session_state.current_section == "admin" and st.session_state.role == "admin":
        if st.session_state.username.lower() == "taha kirri":
            st.subheader("🚨 System Killswitch")
            current = is_killswitch_enabled()
            status = "🔴 ACTIVE" if current else "🟢 INACTIVE"
            st.write(f"Current Status: {status}")
            
            col1, col2 = st.columns(2)
            if current:
                if col1.button("Deactivate Killswitch"):
                    toggle_killswitch(False)
                    st.rerun()
            else:
                if col1.button("Activate Killswitch"):
                    toggle_killswitch(True)
                    st.rerun()
            
            st.markdown("---")
            
            st.subheader("💬 Chat Killswitch")
            current_chat = is_chat_killswitch_enabled()
            chat_status = "🔴 ACTIVE" if current_chat else "🟢 INACTIVE"
            st.write(f"Current Status: {chat_status}")
            
            col1, col2 = st.columns(2)
            if current_chat:
                if col1.button("Deactivate Chat Killswitch"):
                    toggle_chat_killswitch(False)
                    st.rerun()
            else:
                if col1.button("Activate Chat Killswitch"):
                    toggle_chat_killswitch(True)
                    st.rerun()
            
            st.markdown("---")
        
        st.subheader("🧹 Data Management")
        
        with st.expander("❌ Clear All Requests"):
            with st.form("clear_requests_form"):
                st.warning("This will permanently delete ALL requests and their comments!")
                if st.form_submit_button("Clear All Requests"):
                    if clear_all_requests():
                        st.success("All requests deleted!")
                        st.rerun()

        with st.expander("❌ Clear All Mistakes"):
            with st.form("clear_mistakes_form"):
                st.warning("This will permanently delete ALL mistakes!")
                if st.form_submit_button("Clear All Mistakes"):
                    if clear_all_mistakes():
                        st.success("All mistakes deleted!")
                        st.rerun()

        with st.expander("❌ Clear All Chat Messages"):
            with st.form("clear_chat_form"):
                st.warning("This will permanently delete ALL chat messages!")
                if st.form_submit_button("Clear All Chat"):
                    if clear_all_group_messages():
                        st.success("All chat messages deleted!")
                        st.rerun()

        with st.expander("❌ Clear All HOLD Images"):
            with st.form("clear_hold_form"):
                st.warning("This will permanently delete ALL HOLD images!")
                if st.form_submit_button("Clear All HOLD Images"):
                    if clear_hold_images():
                        st.success("All HOLD images deleted!")
                        st.rerun()

        with st.expander("❌ Clear All Late Logins"):
            with st.form("clear_late_logins_form"):
                st.warning("This will permanently delete ALL late login records!")
                if st.form_submit_button("Clear All Late Logins"):
                    if clear_late_logins():
                        st.success("All late login records deleted!")
                        st.rerun()

        with st.expander("❌ Clear All Quality Issues"):
            with st.form("clear_quality_issues_form"):
                st.warning("This will permanently delete ALL quality issue records!")
                if st.form_submit_button("Clear All Quality Issues"):
                    if clear_quality_issues():
                        st.success("All quality issue records deleted!")
                        st.rerun()

        with st.expander("❌ Clear All Mid-shift Issues"):
            with st.form("clear_midshift_issues_form"):
                st.warning("This will permanently delete ALL mid-shift issue records!")
                if st.form_submit_button("Clear All Mid-shift Issues"):
                    if clear_midshift_issues():
                        st.success("All mid-shift issue records deleted!")
                        st.rerun()

        with st.expander("💣 Clear ALL Data"):
            with st.form("nuclear_form"):
                st.error("THIS WILL DELETE EVERYTHING IN THE SYSTEM!")
                if st.form_submit_button("🚨 Execute Full System Wipe"):
                    try:
                        clear_all_requests()
                        clear_all_mistakes()
                        clear_all_group_messages()
                        clear_hold_images()
                        clear_late_logins()
                        clear_quality_issues()
                        clear_midshift_issues()
                        st.success("All system data deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error during deletion: {str(e)}")
        
        st.markdown("---")
        st.subheader("User Management")
        if not is_killswitch_enabled():
            with st.form("add_user"):
                user = st.text_input("Username")
                pwd = st.text_input("Password", type="password")
                role = st.selectbox("Role", ["agent", "admin"])
                if st.form_submit_button("Add User"):
                    if user and pwd:
                        add_user(user, pwd, role)
                        st.rerun()
        
        st.subheader("Existing Users")
        users = get_all_users()
        for uid, uname, urole in users:
            cols = st.columns([3, 1, 1])
            cols[0].write(uname)
            cols[1].write(urole)
            if cols[2].button("Delete", key=f"del_{uid}") and not is_killswitch_enabled():
                delete_user(uid)
                st.rerun()

    elif st.session_state.current_section == "breaks":
        show_break_booking_section()

def show_break_booking_section():
    st.title("Break Booking System")
    
    if not st.session_state.authenticated:
        st.warning("Please log in to access the break booking system.")
        return
    
    # Initialize break booking database
    init_break_booking_db()
    
    if st.session_state.role == "admin":
        show_break_admin_interface()
    else:
        show_break_agent_interface()

def show_break_agent_interface():
    st.header("Break Booking - Agent View")
    
    # Date selector
    date = st.date_input("Select Date")
    date_str = date.strftime("%Y-%m-%d")
    
    # Get current template and settings
    template = get_break_template()
    if not template:
        st.error("No break template found. Please contact an administrator.")
        return
        
    settings = get_break_settings()
    max_per_slot = settings["max_per_slot"]
    
    # Get agent's current bookings
    agent_bookings = get_agent_break_bookings(st.session_state.username, date_str)
    booked_breaks = {(b[0], b[1]): b[2] for b in agent_bookings}
    
    # Create tabs for the two shifts
    tab1, tab2 = st.tabs(["2:00 PM Shift", "6:00 PM Shift"])
    
    # 2 PM Shift
    with tab1:
        st.subheader("2:00 PM Shift")
        col1, col2, col3 = st.columns(3)
        
        # Early Tea Break
        with col1:
            st.markdown("### Early Tea Break")
            early_tea_booked = ("2pm", "early_tea") in booked_breaks
            
            if early_tea_booked:
                st.success(f"Booked: {booked_breaks[('2pm', 'early_tea')]}")
                if st.button("Cancel Early Tea Booking (2PM)"):
                    if remove_break_booking(st.session_state.username, "2pm", "early_tea", 
                                         booked_breaks[("2pm", "early_tea")], date_str):
                        st.success("Booking cancelled!")
                        st.rerun()
            else:
                # Show available slots
                available_slots = []
                all_bookings = get_break_bookings(date_str)
                slot_counts = {}
                for booking in all_bookings:
                    if booking[1] == "2pm" and booking[2] == "early_tea":
                        slot_counts[booking[3]] = slot_counts.get(booking[3], 0) + 1
                
                for slot in template["shifts"]["2pm"]["early_tea"]["slots"]:
                    count = slot_counts.get(slot, 0)
                    if count < max_per_slot:
                        available_slots.append(f"{slot} ({count}/{max_per_slot})")
                
                if available_slots:
                    selected_slot = st.selectbox("Select Early Tea Time (2PM)", available_slots)
                    if st.button("Book Early Tea Break (2PM)"):
                        slot_time = selected_slot.split(" ")[0]
                        if add_break_booking(st.session_state.username, "2pm", "early_tea", 
                                          slot_time, date_str):
                            st.success(f"Booked Early Tea Break at {slot_time}")
                            st.rerun()
                else:
                    st.info("No available slots for Early Tea Break")
        
        # Lunch Break
        with col2:
            st.markdown("### Lunch Break")
            lunch_booked = ("2pm", "lunch") in booked_breaks
            
            if lunch_booked:
                st.success(f"Booked: {booked_breaks[('2pm', 'lunch')]}")
                if st.button("Cancel Lunch Booking (2PM)"):
                    if remove_break_booking(st.session_state.username, "2pm", "lunch", 
                                         booked_breaks[("2pm", "lunch")], date_str):
                        st.success("Booking cancelled!")
                        st.rerun()
            else:
                # Show available slots
                available_slots = []
                all_bookings = get_break_bookings(date_str)
                slot_counts = {}
                for booking in all_bookings:
                    if booking[1] == "2pm" and booking[2] == "lunch":
                        slot_counts[booking[3]] = slot_counts.get(booking[3], 0) + 1
                
                for slot in template["shifts"]["2pm"]["lunch"]["slots"]:
                    count = slot_counts.get(slot, 0)
                    if count < max_per_slot:
                        available_slots.append(f"{slot} ({count}/{max_per_slot})")
                
                if available_slots:
                    selected_slot = st.selectbox("Select Lunch Time (2PM)", available_slots)
                    if st.button("Book Lunch Break (2PM)"):
                        slot_time = selected_slot.split(" ")[0]
                        if add_break_booking(st.session_state.username, "2pm", "lunch", 
                                          slot_time, date_str):
                            st.success(f"Booked Lunch Break at {slot_time}")
                            st.rerun()
                else:
                    st.info("No available slots for Lunch Break")
        
        # Late Tea Break
        with col3:
            st.markdown("### Late Tea Break")
            late_tea_booked = ("2pm", "late_tea") in booked_breaks
            
            if late_tea_booked:
                st.success(f"Booked: {booked_breaks[('2pm', 'late_tea')]}")
                if st.button("Cancel Late Tea Booking (2PM)"):
                    if remove_break_booking(st.session_state.username, "2pm", "late_tea", 
                                         booked_breaks[("2pm", "late_tea")], date_str):
                        st.success("Booking cancelled!")
                        st.rerun()
            else:
                # Show available slots
                available_slots = []
                all_bookings = get_break_bookings(date_str)
                slot_counts = {}
                for booking in all_bookings:
                    if booking[1] == "2pm" and booking[2] == "late_tea":
                        slot_counts[booking[3]] = slot_counts.get(booking[3], 0) + 1
                
                for slot in template["shifts"]["2pm"]["late_tea"]["slots"]:
                    count = slot_counts.get(slot, 0)
                    if count < max_per_slot:
                        available_slots.append(f"{slot} ({count}/{max_per_slot})")
                
                if available_slots:
                    selected_slot = st.selectbox("Select Late Tea Time (2PM)", available_slots)
                    if st.button("Book Late Tea Break (2PM)"):
                        slot_time = selected_slot.split(" ")[0]
                        if add_break_booking(st.session_state.username, "2pm", "late_tea", 
                                          slot_time, date_str):
                            st.success(f"Booked Late Tea Break at {slot_time}")
                            st.rerun()
                else:
                    st.info("No available slots for Late Tea Break")
    
    # 6 PM Shift
    with tab2:
        st.subheader("6:00 PM Shift")
        col1, col2, col3 = st.columns(3)
        
        # Early Tea Break
        with col1:
            st.markdown("### Early Tea Break")
            early_tea_booked = ("6pm", "early_tea") in booked_breaks
            
            if early_tea_booked:
                st.success(f"Booked: {booked_breaks[('6pm', 'early_tea')]}")
                if st.button("Cancel Early Tea Booking (6PM)"):
                    if remove_break_booking(st.session_state.username, "6pm", "early_tea", 
                                         booked_breaks[("6pm", "early_tea")], date_str):
                        st.success("Booking cancelled!")
                        st.rerun()
            else:
                # Show available slots
                available_slots = []
                all_bookings = get_break_bookings(date_str)
                slot_counts = {}
                for booking in all_bookings:
                    if booking[1] == "6pm" and booking[2] == "early_tea":
                        slot_counts[booking[3]] = slot_counts.get(booking[3], 0) + 1
                
                for slot in template["shifts"]["6pm"]["early_tea"]["slots"]:
                    count = slot_counts.get(slot, 0)
                    if count < max_per_slot:
                        available_slots.append(f"{slot} ({count}/{max_per_slot})")
                
                if available_slots:
                    selected_slot = st.selectbox("Select Early Tea Time (6PM)", available_slots)
                    if st.button("Book Early Tea Break (6PM)"):
                        slot_time = selected_slot.split(" ")[0]
                        if add_break_booking(st.session_state.username, "6pm", "early_tea", 
                                          slot_time, date_str):
                            st.success(f"Booked Early Tea Break at {slot_time}")
                            st.rerun()
                else:
                    st.info("No available slots for Early Tea Break")
        
        # Lunch Break
        with col2:
            st.markdown("### Lunch Break")
            lunch_booked = ("6pm", "lunch") in booked_breaks
            
            if lunch_booked:
                st.success(f"Booked: {booked_breaks[('6pm', 'lunch')]}")
                if st.button("Cancel Lunch Booking (6PM)"):
                    if remove_break_booking(st.session_state.username, "6pm", "lunch", 
                                         booked_breaks[("6pm", "lunch")], date_str):
                        st.success("Booking cancelled!")
                        st.rerun()
            else:
                # Show available slots
                available_slots = []
                all_bookings = get_break_bookings(date_str)
                slot_counts = {}
                for booking in all_bookings:
                    if booking[1] == "6pm" and booking[2] == "lunch":
                        slot_counts[booking[3]] = slot_counts.get(booking[3], 0) + 1
                
                for slot in template["shifts"]["6pm"]["lunch"]["slots"]:
                    count = slot_counts.get(slot, 0)
                    if count < max_per_slot:
                        available_slots.append(f"{slot} ({count}/{max_per_slot})")
                
                if available_slots:
                    selected_slot = st.selectbox("Select Lunch Time (6PM)", available_slots)
                    if st.button("Book Lunch Break (6PM)"):
                        slot_time = selected_slot.split(" ")[0]
                        if add_break_booking(st.session_state.username, "6pm", "lunch", 
                                          slot_time, date_str):
                            st.success(f"Booked Lunch Break at {slot_time}")
                            st.rerun()
                else:
                    st.info("No available slots for Lunch Break")
        
        # Late Tea Break
        with col3:
            st.markdown("### Late Tea Break")
            late_tea_booked = ("6pm", "late_tea") in booked_breaks
            
            if late_tea_booked:
                st.success(f"Booked: {booked_breaks[('6pm', 'late_tea')]}")
                if st.button("Cancel Late Tea Booking (6PM)"):
                    if remove_break_booking(st.session_state.username, "6pm", "late_tea", 
                                         booked_breaks[("6pm", "late_tea")], date_str):
                        st.success("Booking cancelled!")
                        st.rerun()
            else:
                # Show available slots
                available_slots = []
                all_bookings = get_break_bookings(date_str)
                slot_counts = {}
                for booking in all_bookings:
                    if booking[1] == "6pm" and booking[2] == "late_tea":
                        slot_counts[booking[3]] = slot_counts.get(booking[3], 0) + 1
                
                for slot in template["shifts"]["6pm"]["late_tea"]["slots"]:
                    count = slot_counts.get(slot, 0)
                    if count < max_per_slot:
                        available_slots.append(f"{slot} ({count}/{max_per_slot})")
                
                if available_slots:
                    selected_slot = st.selectbox("Select Late Tea Time (6PM)", available_slots)
                    if st.button("Book Late Tea Break (6PM)"):
                        slot_time = selected_slot.split(" ")[0]
                        if add_break_booking(st.session_state.username, "6pm", "late_tea", 
                                          slot_time, date_str):
                            st.success(f"Booked Late Tea Break at {slot_time}")
                            st.rerun()
                else:
                    st.info("No available slots for Late Tea Break")

def show_break_admin_interface():
    st.header("Break Booking - Admin View")
    
    # Create tabs for different admin functions
    tab1, tab2, tab3 = st.tabs(["View Bookings", "Manage Templates", "Settings"])
    
    # Tab 1: View Bookings
    with tab1:
        st.subheader("View All Bookings")
        
        # Date selector
        date = st.date_input("Select Date to View")
        date_str = date.strftime("%Y-%m-%d")
        
        # Get all bookings for the date
        bookings = get_break_bookings(date_str)
        
        if bookings:
            # Prepare data for display
            df_data = []
            for booking in bookings:
                df_data.append({
                    "Agent": booking[0],
                    "Shift": booking[1],
                    "Break Type": booking[2],
                    "Time": booking[3]
                })
            
            df = pd.DataFrame(df_data)
            
            # Display bookings by shift and break type
            for shift in ["2pm", "6pm"]:
                st.markdown(f"### {shift.upper()} Shift")
                shift_data = df[df["Shift"] == shift]
                
                if not shift_data.empty:
                    for break_type in ["early_tea", "lunch", "late_tea"]:
                        break_data = shift_data[shift_data["Break Type"] == break_type]
                        if not break_data.empty:
                            st.markdown(f"#### {break_type.replace('_', ' ').title()}")
                            st.dataframe(break_data[["Agent", "Time"]])
                else:
                    st.info(f"No bookings for {shift.upper()} shift")
            
            # Export option
            if st.button("Export to CSV"):
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Download CSV",
                    csv,
                    f"break_bookings_{date_str}.csv",
                    "text/csv",
                    key='download-csv'
                )
            
            # Clear bookings option
            if st.button("Clear All Bookings for This Date"):
                if clear_break_bookings(date_str):
                    st.success(f"All bookings for {date_str} have been cleared!")
                    st.rerun()
        else:
            st.info(f"No bookings found for {date_str}")
    
    # Tab 2: Manage Templates
    with tab2:
        st.subheader("Break Schedule Templates")
        
        # Get current settings and templates
        settings = get_break_settings()
        templates = get_all_break_templates()
        
        # Display current template
        st.markdown(f"**Current Template:** {settings['current_template']}")
        
        # Template selector
        template_names = list(templates.keys())
        selected_template = st.selectbox("Select Template", template_names,
                                       index=template_names.index(settings["current_template"]))
        
        if st.button("Set as Active Template"):
            update_break_settings(current_template=selected_template)
            st.success(f"Template '{selected_template}' is now active!")
            st.rerun()
        
        # Create new template
        st.markdown("### Create New Template")
        new_template_name = st.text_input("New Template Name")
        new_template_desc = st.text_input("Description")
        
        # Copy from existing template
        copy_from = st.selectbox("Copy settings from", template_names)
        
        if st.button("Create Template"):
            if new_template_name and new_template_desc:
                template_data = templates[copy_from]
                if save_break_template(new_template_name, new_template_desc, template_data):
                    st.success(f"Template '{new_template_name}' created!")
                    st.rerun()
            else:
                st.error("Please fill in all fields")
        
        # Delete template
        st.markdown("### Delete Template")
        if len(templates) > 1:
            template_to_delete = st.selectbox("Select template to delete",
                                            [t for t in template_names if t != "default"])
            
            if st.button("Delete Template"):
                if template_to_delete == settings["current_template"]:
                    st.error("Cannot delete the active template")
                else:
                    if delete_break_template(template_to_delete):
                        st.success(f"Template '{template_to_delete}' deleted!")
                        st.rerun()
        else:
            st.info("Cannot delete the only remaining template")
    
    # Tab 3: Settings
    with tab3:
        st.subheader("Break System Settings")
        
        settings = get_break_settings()
        
        # Max bookings per slot
        max_per_slot = st.number_input("Maximum Bookings Per Slot",
                                      min_value=1,
                                      max_value=10,
                                      value=settings["max_per_slot"])
        
        if st.button("Update Settings"):
            update_break_settings(max_per_slot=max_per_slot)
            st.success("Settings updated successfully!")
            st.rerun()

if __name__ == "__main__":
    st.write("Request Management System")
