# [Previous imports and other functions remain the same...]

# Add these new functions for user management
def create_user(username, password, role):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, role) 
            VALUES (?, ?, ?)
        """, (username, hash_password(password), role))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to create user: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_all_users():
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM users ORDER BY username")
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to fetch users: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_user_role(user_id, new_role):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET role=? 
            WHERE id=?
        """, (new_role, user_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to update user role: {e}")
        return False
    finally:
        if conn:
            conn.close()

def delete_user(user_id):
    conn = None
    try:
        conn = sqlite3.connect("data/requests.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Failed to delete user: {e}")
        return False
    finally:
        if conn:
            conn.close()

# [Previous code remains the same until the Admin Panel section...]

    elif section == "⚙ Admin Panel" and st.session_state.role == "admin":
        st.subheader("Admin Panel")
        
        tab1, tab2, tab3 = st.tabs(["User Management", "Clear Data", "System Tools"])
        
        with tab1:
            st.subheader("User Management")
            
            # Create new user
            with st.expander("Create New User"):
                with st.form("create_user_form"):
                    new_username = st.text_input("Username")
                    new_password = st.text_input("Password", type="password")
                    new_role = st.selectbox("Role", ["agent", "admin"])
                    if st.form_submit_button("Create User"):
                        if new_username and new_password:
                            if create_user(new_username, new_password, new_role):
                                st.success("User created successfully!")
                                st.rerun()
                        else:
                            st.warning("Please enter both username and password")
            
            # View and manage existing users
            st.subheader("Existing Users")
            users = get_all_users()
            if users:
                for user in users:
                    user_id, username, role = user
                    cols = st.columns([3, 2, 2, 2])
                    with cols[0]:
                        st.write(f"**{username}**")
                    with cols[1]:
                        st.write(role)
                    with cols[2]:
                        new_role = st.selectbox(
                            "Change Role",
                            ["agent", "admin"],
                            index=0 if role == "agent" else 1,
                            key=f"role_{user_id}"
                        )
                        if new_role != role:
                            if update_user_role(user_id, new_role):
                                st.success("Role updated!")
                                st.rerun()
                    with cols[3]:
                        if st.button("Delete", key=f"del_{user_id}"):
                            if delete_user(user_id):
                                st.success("User deleted!")
                                st.rerun()
                    st.divider()
            else:
                st.info("No users found")
        
        with tab2:
            st.subheader("Clear Data")
            if st.button("Clear All Requests"):
                conn = None
                try:
                    conn = sqlite3.connect("data/requests.db")
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM requests")
                    conn.commit()
                    st.success("All requests cleared!")
                except sqlite3.Error as e:
                    st.error(f"Failed to clear requests: {e}")
                finally:
                    if conn:
                        conn.close()
            
            if st.button("Clear All Mistakes"):
                conn = None
                try:
                    conn = sqlite3.connect("data/requests.db")
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM mistakes")
                    conn.commit()
                    st.success("All mistakes cleared!")
                except sqlite3.Error as e:
                    st.error(f"Failed to clear mistakes: {e}")
                finally:
                    if conn:
                        conn.close()
        
        with tab3:
            st.subheader("System Tools")
            if st.button("Refresh Database"):
                init_db()
                st.success("Database refreshed!")
