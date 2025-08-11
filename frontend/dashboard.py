import streamlit as st
import requests
import time
from assessment_page import show_create_assessment_page
from get_assess import get_assessments,get_assessment_questions


API_BASE_URL = "http://localhost:8000/api/v1"

def show_dashboard():
    """Displays the main dashboard with available assessments."""
    # A check to ensure user object is not None before accessing its keys
    is_admin=False
    if st.session_state.user and st.session_state.user.get('role')=='admin':
        is_admin=True
        st.sidebar.markdown(f"### Welcome, {st.session_state.user.get('name','Admin')}!")
    elif st.session_state.user:
        st.sidebar.markdown(f"### Welcome!, {st.session_state.user.get('name','User')}!")
    
    admin_choice = "View Assessments"
    if is_admin:
        st.sidebar.subheader("Admin Actions")
        admin_choice = st.sidebar.radio(
            "Mode",
            ("View Assessments", "Create New Assessment","Generate-Questions-AI","Invite Students","Stats"),
            label_visibility="collapsed" # Hides the "Mode" label for a cleaner look
        )
    
    # This code block determines what to display based on the radio button selection
    if admin_choice == "Create New Assessment":
    # Call the function to display the creation form
        show_create_assessment_page()

    elif admin_choice == "Generate-Questions-AI":
    # You would call a function for your AI page here
        st.info("AI Question Generator page coming soon!")

    elif admin_choice == "Invite Students":
    # You would call a function for your Invite page here
        st.info("Invite Students page coming soon!")

    elif admin_choice == "Stats":
        st.info("Stats page coming soon!")

    else: # This handles the "View Assessments" case
    # Show the default dashboard view
        st.markdown("<h1 class='main-header'>📚 Quiz Dashboard</h1>", unsafe_allow_html=True)
        assessments = get_assessments()

        if not assessments:
            st.info("No assessments available at the moment.")
        else:
            st.markdown("### Available Assessments")
            cols = st.columns(2)
            for idx, assessment in enumerate(assessments):
                with cols[idx % 2]:
                    with st.container(border=True):
                # ... inside with st.container(border=True):
                        st.markdown(f"#### {assessment.get('name', 'Untitled Assessment')}")
                        st.markdown(f"_{assessment.get('description', 'No description available.')}_")
                        st.markdown(f"**Duration:** {assessment.get('time_limit', 0)} minutes")
                        st.markdown(f"**Questions:** {assessment.get('total_questions', 0)}")
                        if st.button(f"Start Assessment", key=f"start_{assessment['id']}", use_container_width=True):
                            st.session_state.current_assessment = assessment
                            st.session_state.questions = get_assessment_questions(assessment['id'])
                            st.session_state.current_question_index = 0
                            st.session_state.user_answers = {}
                            st.session_state.start_time = time.time()
                            st.session_state.show_results = False
                            st.session_state.page = 'assessment'
                            st.rerun()