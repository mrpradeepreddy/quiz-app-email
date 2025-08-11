import streamlit as st
import requests
import time
from register import show_register_page
from login_page import show_login_page
from dashboard import show_dashboard
from assessment_page import show_create_assessment_page
from get_assess import show_assessment,show_results_page

# --- Page Configuration ---
st.set_page_config(
    page_title="Quiz Application",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- API Configuration ---
# CORRECTED: The base URL now includes the /api/v1 prefix from your FastAPI router setup.
API_BASE_URL = "http://localhost:8000/api/v1"

# --- Initialize Session State ---
# This ensures that the keys exist in the session state from the beginning
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'current_assessment' not in st.session_state:
    st.session_state.current_assessment = None
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'show_results' not in st.session_state:
    st.session_state.show_results = False


# --- Custom CSS ---
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .question-card {
        background-color: #f0f2f6;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #e0e0e0;
    }
    .stButton>button {
        width: 100%;
        margin: 0.5rem 0;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- API Helper Functions ---



# --- Page Rendering Functions ---




# --- Main App Logic ---
def main():
    """Main function to control page navigation."""
    if st.session_state.page == 'login':
        show_login_page()
    elif st.session_state.page == 'register':
        show_register_page()
    elif st.session_state.page == 'dashboard':
        show_dashboard()
    elif st.session_state.page == 'create_assessment':
        show_create_assessment_page()
    elif st.session_state.page == 'assessment':
        show_assessment()
    elif st.session_state.page == 'results':
        show_results_page()
    else:
        st.session_state.page = 'login'
        st.rerun()


if __name__ == "__main__":
    main()
