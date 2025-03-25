# Add a "Clear Data" button
clear_button = st.button("Clear Data")

# Handle the button click for clearing data
if clear_button:
    # Confirmation Dialog
    confirm_clear = st.confirm("Are you sure you want to delete all the data?")
    if confirm_clear:
        # Clear the data if confirmed
        data = pd.DataFrame(columns=["Agent Name", "TYPE", "ID", "COMMENT", "Timestamp"])
        data.to_csv(DATA_FILE, index=False)  # Save the empty data to CSV
        st.success("All data has been cleared!")
    else:
        st.info("Data has not been cleared.")
