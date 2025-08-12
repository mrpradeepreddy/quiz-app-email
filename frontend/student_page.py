import requests
import streamlit as st
import time



API_BASE_URL = "http://localhost:8000/api/v1"

# You will need these helper functions
from get_assess import get_assessment_questions # Or wherever you have this

def get_single_assessment(assessment_id,token:str):
    """Fetches a single assessment's details from the backend."""
    # Note: You will need to create a GET /assessments/{id} endpoint in your backend
    # that returns the details for one assessment (like its duration).
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.get(f"{API_BASE_URL}/assessments/{assessment_id}", headers=headers)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return None
def get_assessment_questions(assessment_id: str, token: str): # Add token argument
    """Get questions for a specific assessment."""
    try:
        # Use the token passed into the function
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE_URL}/assessments/{assessment_id}/questions", headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException:
        return []

# In file: student_page.py

def handle_assessment_invite(assessment_id: str, token: str): # Added token argument
    """Prepares the app to start a specific assessment from an invitation link."""
    
    # Pass the token down to the API calls
    assessment_details = get_single_assessment(assessment_id, token)
    questions = get_assessment_questions(assessment_id, token)

    if not assessment_details or not questions:
        st.error("The assessment link is invalid or the assessment could not be found.")
        st.rerun()
        return

    # Set up the session state to start the quiz
    st.session_state.page = "assessment"
    st.session_state.current_assessment = assessment_details
    st.session_state.questions = questions
    st.session_state.current_question_index = 0
    st.session_state.user_answers = {}
    st.session_state.start_time = time.time()
    
    st.rerun()