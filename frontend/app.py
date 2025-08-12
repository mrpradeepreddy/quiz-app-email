import streamlit as st
import requests
import time
from register import show_register_page
from login_page import show_login_page
from dashboard import show_dashboard
from assessment_page import show_create_assessment_page
from get_assess import show_assessment,show_results_page,get_assessment_questions
from student_page import handle_assessment_invite

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

# --- Main App Logic (Merged and Corrected) ---
def main():
    """Main function to control page navigation."""
    
    # --- Priority 1: Check for an invitation link in the URL ---
    query_params = st.query_params
    if "page" in query_params and query_params.page == "take_assessment" and "id" in query_params:
        # Save the intended destination to the session state
        st.session_state.invite_assessment_id = query_params.id
        
        # Clear the URL so it doesn't get stuck in a loop
        st.query_params.clear()
        st.rerun() # Rerun to proceed to the login page with the invite saved
    # --- Priority 2: Standard page navigation using session state ---
    # This part runs if there's no special invitation link.
     # This check now happens AFTER we've saved any potential invite link info.
    if not st.session_state.user:
        show_login_page()
        return # Stop execution to prevent showing other pages

    # page = st.session_state.get('page', 'login')
    # # page = st.session_state.get('page', 'dashboard')

    # This code only runs if the user IS logged in
    page = st.session_state.get('page', 'dashboard')
    if page == 'dashboard':
       show_dashboard()
    elif page == 'login':
        show_login_page()
    elif page == 'register':
        show_register_page()
    # elif page == 'dashboard':
    #     show_dashboard()
    elif page == 'assessment':
        show_assessment()
    elif page == 'results':
        show_results_page()
    else:
        st.session_state.page = 'login'
        # st.session_state.page = 'dashboard'

        st.rerun()


if __name__ == "__main__":
    main()