import streamlit as st
import requests
import time

API_BASE_URL = "http://localhost:8000/api/v1"

def register_user(role,email, username, password, name):
    """Register a new user."""
    try:
        # The URL path is now just "/register"
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json={
                "role":role,
                "email": email,
                "username": username,
                "password": password,
                "name": name
            }
        )
        return response
    except requests.exceptions.ConnectionError as e:
        st.error(f"Connection error: Could not connect to the server. Details: {e}")
        return None
    

def show_register_page():
    """Displays the user registration page."""
    st.markdown("<h1 class='main-header'>🎯 Create Your Account</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # This block shows the success message AFTER registration
        if st.session_state.get('registration_success'):
            st.success("Registration successful!")
            if st.button("Click here to Login", use_container_width=True):
                st.session_state.page = 'login'
                del st.session_state.registration_success # Clean up the flag
                st.rerun()
            return # Stop here to not show the form again
        with st.form("register_form"):
            st.markdown("### Register New Account")
            role=st.selectbox("Role",['student','admin'],placeholder="select your Role")
            name = st.text_input("Full Name", placeholder="Enter your full name")
            username = st.text_input("Username", placeholder="Choose a username")
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter password (min 6 chars)")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password")

            submitted = st.form_submit_button("Register", use_container_width=True)
            if submitted:
                if not all([role,name, username, email, password, confirm_password]):
                    st.warning("Please fill out all fields.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters long.")
                else:
                    response = register_user(role,email, username, password, name)
                    if response and response.status_code == 201:
                        st.success("Registration successful! Please login.")
                        st.session_state.registration_success=True
                        st.rerun()
                    else:
                        error_detail = response.json().get('detail', 'Registration failed.')
                        st.error(f"Registration failed: {error_detail}")

        if st.button("Back to Login", use_container_width=True):
            st.session_state.page = 'login'
            st.rerun()
