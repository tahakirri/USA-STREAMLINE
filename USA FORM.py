# ... [Previous imports and database functions remain the same]

def messaging_section():
    st.header("💬 Messaging Center")
    
    # Tabs for Group and Private Messaging
    tab1, tab2 = st.tabs(["Group Chat", "Private Messages"])
    
    with tab1:
        st.subheader("Group Chat")
        
        # Display Group Messages
        messages = get_group_messages()
        for msg in reversed(messages):
            msg_id, sender, message, timestamp, mentions = msg
            st.markdown(f"**{sender}** at {timestamp}")
            st.write(message)
            st.divider()
        
        # Send Group Message
        with st.form("group_message_form", clear_on_submit=True):
            new_message = st.text_area("Type your message...")
            if st.form_submit_button("Send"):
                if new_message.strip():
                    mentions = extract_mentions(new_message)
                    valid_mentions = []
                    
                    all_users = [user[1] for user in get_all_users()]
                    for mention in mentions:
                        if mention in all_users:
                            valid_mentions.append(mention)
                        else:
                            st.warning(f"User @{mention} not found")
                    
                    add_group_message(st.session_state.username, new_message, valid_mentions)
                    st.success("Message sent!")
    
    with tab2:
        st.subheader("Private Messages")
        
        # Select recipient based on user role
        if st.session_state.role == "agent":
            recipients = get_admins()
        else:
            recipients = get_all_users_except(st.session_state.username)
        
        selected_recipient = st.selectbox("Message to:", recipients)
        
        # Display Conversation History
        conversation = get_conversation_history(st.session_state.username, selected_recipient)
        for msg in conversation:
            msg_id, sender, receiver, message, timestamp, is_read = msg
            st.markdown(f"**{sender}** at {timestamp}")
            st.write(message)
            st.divider()
        
        # Send Private Message
        with st.form("private_message_form", clear_on_submit=True):
            private_message = st.text_area("Type your message...")
            if st.form_submit_button("Send"):
                if private_message.strip():
                    add_private_message(st.session_state.username, selected_recipient, private_message)
                    st.success("Message sent!")

def issue_tracking_section():
    st.header("🚨 Issue Tracking")
    
    # Ticket Mistakes Submission
    st.subheader("Report a Mistake")
    with st.form("mistake_form", clear_on_submit=True):
        team_leader = st.text_input("Team Leader Name")
        agent_name = st.text_input("Agent Name")
        ticket_id = st.text_input("Ticket ID")
        error_description = st.text_area("Error Description")
        
        if st.form_submit_button("Submit Mistake"):
            if team_leader and agent_name and ticket_id and error_description:
                add_mistake(team_leader, agent_name, ticket_id, error_description)
                st.success("Mistake submitted successfully!")
            else:
                st.warning("Please fill all fields")
    
    # Display Submitted Mistakes
    st.subheader("Recorded Mistakes")
    mistakes = get_mistakes()
    
    if mistakes:
        for mistake in mistakes:
            m_id, tl, agent, t_id, desc, ts = mistake
            with st.expander(f"Mistake #{m_id} - {agent}"):
                st.markdown(f"""
                **Team Leader:** {tl}  
                **Ticket ID:** {t_id}  
                **Description:** {desc}  
                **Timestamp:** {ts}
                """)
    else:
        st.info("No mistakes recorded.")

def search_section():
    st.header("🔍 Search")
    
    # Search Requests
    st.subheader("Search Requests")
    search_type = st.selectbox("Search By", ["Agent Name", "Request Type", "Identifier"])
    
    search_query = st.text_input("Search Term")
    
    if st.button("Search Requests"):
        if search_query:
            requests = get_requests()
            
            # Filter requests based on search type
            filtered_requests = []
            for req in requests:
                if search_type == "Agent Name" and search_query.lower() in req[1].lower():
                    filtered_requests.append(req)
                elif search_type == "Request Type" and search_query.lower() in req[2].lower():
                    filtered_requests.append(req)
                elif search_type == "Identifier" and search_query.lower() in req[3].lower():
                    filtered_requests.append(req)
            
            # Display results
            if filtered_requests:
                st.subheader("Search Results")
                for req in filtered_requests:
                    st.markdown(f"""
                    **Request ID:** {req[0]}  
                    **Agent:** {req[1]} | **Type:** {req[2]}  
                    **Identifier:** {req[3]}  
                    **Comments:** {req[4]}  
                    **Timestamp:** {req[5]}
                    """)
                    st.divider()
            else:
                st.info("No matching requests found.")
        else:
            st.warning("Please enter a search term")

def admin_tools_section():
    st.header("⚙️ Admin Tools")
    
    # Tabs for different admin functionalities
    tab1, tab2, tab3 = st.tabs(["User Management", "System Logs", "Data Management"])
    
    with tab1:
        st.subheader("User Management")
        
        # Create New User
        with st.expander("Create New User"):
            with st.form("create_user_form"):
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("Role", ["agent", "admin"])
                
                if st.form_submit_button("Create User"):
                    if new_username and new_password:
                        if create_user(new_username, new_password, new_role):
                            st.success("User created successfully!")
                    else:
                        st.warning("Please enter both username and password")
        
        # Existing Users Management
        st.subheader("Existing Users")
        users = get_all_users()
        
        for user in users:
            user_id, username, role = user
            
            with st.expander(f"{username} ({role})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("Change Role")
                    new_role = st.selectbox(
                        "Select Role", 
                        ["agent", "admin"], 
                        index=0 if role == "agent" else 1,
                        key=f"role_{user_id}"
                    )
                    if st.button(f"Update Role for {username}", key=f"update_role_{user_id}"):
                        if update_user_role(user_id, new_role):
                            st.success("Role updated!")
                
                with col2:
                    st.write("Reset Password")
                    new_password = st.text_input(
                        "New Password", 
                        type="password", 
                        key=f"reset_pass_{user_id}"
                    )
                    if st.button(f"Reset Password for {username}", key=f"reset_btn_{user_id}"):
                        if new_password:
                            if reset_user_password(user_id, new_password):
                                st.success("Password reset successfully!")
                        else:
                            st.warning("Please enter a new password")
                
                with col3:
                    st.write("User Deletion")
                    if st.button(f"Delete {username}", key=f"delete_{user_id}"):
                        if delete_user(user_id):
                            st.success("User deleted!")
    
    with tab2:
        st.subheader("System Logs")
        st.write("Recent Group Messages")
        group_messages = get_group_messages()
        
        for msg in group_messages[-10:]:  # Last 10 messages
            st.markdown(f"**{msg[1]}** at {msg[3]}: {msg[2]}")
    
    with tab3:
        st.subheader("Data Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Clear Requests")
            if st.button("Clear All Requests"):
                conn = sqlite3.connect("data/requests.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM requests")
                conn.commit()
                conn.close()
                st.success("All requests cleared!")
        
        with col2:
            st.write("Clear Mistakes")
            if st.button("Clear All Mistakes"):
                conn = sqlite3.connect("data/requests.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM mistakes")
                conn.commit()
                conn.close()
                st.success("All mistakes cleared!")

# ... [Rest of the previous code remains the same]
