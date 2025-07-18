import streamlit as st

# Hardcoded credentials 
CREDENTIALS = {
    "Ajay": "Ajay123",
    "Ramya P": "RamyaP123",
    "Agasteen": "Agasteen123",
    "Deepika": "Deepika123"
}

def login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h4 style='text-align:center; color:#ccc;'>Welcome to the Analytics Dashboard</h4>", unsafe_allow_html=True)
        st.title("🔐 Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if username in CREDENTIALS and CREDENTIALS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login successful")
                st.stop()
            else:
                st.error("Invalid Username or Password")


