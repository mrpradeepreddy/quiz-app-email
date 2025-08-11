import streamlit as st
import requests
import time

API_BASE_URL = "http://localhost:8000/api/v1"

def authenticate_user(email, username, password):
    """Authenticate user and get JWT token."""
    try:
        # CORRECTED: Changed `data` to `json` to match the FastAPI endpoint which expects a JSON body.
        # The URL path is now just "/login" because the base URL already contains "/api/v1".
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"email":email,"username": username, "password": password}
        )
        if response.status_code == 200:
            # Assuming the response contains user info under a 'user' key
            # If not, you might need to adjust this based on your actual API response
            response_data = response.json()
            user_info = {
                "email":response_data.get("email"),
                "username": response_data.get("username"),
                "full_name": response_data.get("username"), # Placeholder, adjust if full name is available
                "role": response_data.get("role")
            }
            return {"access_token": response_data["access_token"], "user": user_info}

        st.error(f"Login failed: {response.json().get('detail', 'Invalid credentials')}")
        return None
    except requests.exceptions.ConnectionError as e:
        st.error(f"Connection error: Could not connect to the server. Please ensure it's running. Details: {e}")
        return None


def show_login_page():
    """Displays the login and registration forms."""
    st.markdown("<h1 class='main-header'>🎯 Quiz Application</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("### Login")
            email = st.text_input("Email", placeholder="Enter your email")
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.warning("Please enter your username and password.")
                else:
                    auth_data = authenticate_user(email, username, password)
                    if auth_data:
                        st.session_state.token = auth_data["access_token"]
                        st.session_state.user = auth_data["user"]
                        st.session_state.page = 'dashboard'
                        st.success("Login successful!")
                        st.rerun()

        st.markdown("---")
        st.markdown("Don't have an account?")
        if st.button("Create Account", use_container_width=True):
            st.session_state.page = 'register'
            st.rerun()