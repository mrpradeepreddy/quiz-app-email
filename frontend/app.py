import streamlit as st
import requests
import time
from register import show_register_page
from login_page import show_login_page
from dashboard import show_dashboard
from assessment_page import show_create_assessment_page
from get_assess import show_assessment, show_results_page
from student_page import handle_assessment_invite
from take_assessment import show_take_assessment_page
from view_assess_page import show_view_assessment_page

# --- Page Configuration ---
st.set_page_config(
    page_title="Quiz Application",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- API Configuration ---
API_BASE_URL = "http://localhost:8000/api/v1"

# --- Initialize Session State ---
# This ensures that the keys exist in the session state from the beginning
# if 'token' not in st.session_state:
#     st.session_state.token = None
# if 'user' not in st.session_state:
#     st.session_state.user = None
# if 'page' not in st.session_state:
#     st.session_state.page = 'login'
# if 'current_assessment' not in st.session_state:
#     st.session_state.current_assessment = None
# if 'questions' not in st.session_state:
#     st.session_state.questions = []
# if 'current_question_index' not in st.session_state:
#     st.session_state.current_question_index = 0
# if 'user_answers' not in st.session_state:
#     st.session_state.user_answers = {}
# if 'start_time' not in st.session_state:
#     st.session_state.start_time = None
# if 'show_results' not in st.session_state:
#     st.session_state.show_results = False


def initialize_session_state():
    """Initializes all necessary keys in the session state."""
    defaults = {
        'token': None,
        'user': None,
        'page': 'login',
        'current_assessment_id': None,
        'test_started': False, # For student page
        'user_answers': {},   # For student page
        'start_time': None    # For student page
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Call the initialization function once at the start
initialize_session_state()


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

# --- Main App Logic ---
def main():
    """Main function to control page navigation."""
    
    # This logic correctly detects a student link and sets the page state.
    if "id" in st.query_params and st.session_state.page != "take_assessment":
        st.session_state.page = "take_assessment"
        # Clear the URL to prevent loops and keep it clean.
        st.query_params.clear()
        st.rerun()

    
    page = st.session_state.get('page', 'login')

    if page == "take_assessment":
        # This route is accessible to anyone with the link, no login required.
        show_take_assessment_page()

    
    # --- Priority 2: The Main Authentication Gate ---
    elif not st.session_state.get('user'):
        # --- Unauthenticated User Routing (Login and Register) ---
        if page == 'register':
            show_register_page()
        else: # Default to login for any other page state
            show_login_page()
        
        return # Stop here for unauthenticated users

    else:
    
        if page == 'dashboard':
            show_dashboard()
        elif page == 'assessment':
            show_assessment()
        elif page == 'results':
            show_results_page()
        elif page == 'create_assessment':
            show_create_assessment_page()
        elif page == 'view_assessment':
            show_view_assessment_page()
        else:
        # If the page state is invalid for a logged-in user, reset to the dashboard.
            st.session_state.page = 'dashboard'
            st.rerun()


if __name__ == "__main__":
    main()