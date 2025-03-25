# Ticket Mistakes Tab
if section == "Ticket Mistakes":
    st.header("Ticket Mistakes Section")

    col1, col2 = st.columns([3, 2])  
    
    with col1:
        team_leader_input = st.text_input("Team Leader Name", key="team_leader")
        agent_name_mistake_input = st.text_input("Agent Name", key="agent_name_mistake")
        ticket_id_input = st.text_input("Ticket ID", key="ticket_id")
    
    with col2:
        error_type = st.selectbox("Error Type", [
            "Communication Error", 
            "Technical Error", 
            "Process Error", 
            "Quality Error", 
            "Other"
        ], key="error_type")
        error_input = st.text_area("Error Description", height=150, key="error")
    
    # Additional context for mistake
    severity = st.slider("Severity of Mistake", min_value=1, max_value=5, value=3, key="severity")
    
    col_submit, col_refresh = st.columns(2)
    with col_submit:
        submit_mistake_button = st.button("Submit Mistake")
    with col_refresh:
        refresh_mistake_button = st.button("Refresh Mistakes")
    
    if submit_mistake_button:
        if not team_leader_input or not agent_name_mistake_input or not ticket_id_input or not error_input:
            st.error("Please fill out all fields.")
        else:
            new_mistake = {
                "Team Leader Name": team_leader_input,
                "Agent Name": agent_name_mistake_input,
                "Ticket ID": ticket_id_input,
                "Error Type": error_type,
                "Error Description": error_input,
                "Severity": severity,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            new_row = pd.DataFrame([new_mistake])
            mistake_data = pd.concat([mistake_data, new_row], ignore_index=True)
            mistake_data.to_csv(MISTAKE_FILE, index=False)
            st.success("Mistake Submitted Successfully! 🚨")

    # Display and filter mistakes
    if not mistake_data.empty:
        st.write("### Mistakes Overview")
        
        # Filter options
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            filter_agent = st.multiselect(
                "Filter by Agent", 
                options=mistake_data["Agent Name"].unique(),
                default=[]
            )
        
        with col_filter2:
            filter_error_type = st.multiselect(
                "Filter by Error Type", 
                options=mistake_data["Error Type"].unique(),
                default=[]
            )
        
        # Apply filters
        filtered_data = mistake_data.copy()
        
        if filter_agent:
            filtered_data = filtered_data[filtered_data["Agent Name"].isin(filter_agent)]
        
        if filter_error_type:
            filtered_data = filtered_data[filtered_data["Error Type"].isin(filter_error_type)]
        
        # Display filtered data
        st.dataframe(filtered_data, use_container_width=True)
        
        # Basic statistics
        st.write("### Mistake Statistics")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Mistakes", len(mistake_data))
            st.metric("Unique Agents", mistake_data["Agent Name"].nunique())
        
        with col2:
            st.metric("Average Mistake Severity", f"{mistake_data['Severity'].mean():.2f}/5")
            most_common_error = mistake_data["Error Type"].mode().values[0]
            st.metric("Most Common Error Type", most_common_error)

    st.markdown("<hr>", unsafe_allow_html=True)
