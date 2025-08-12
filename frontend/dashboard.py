import streamlit as st
import requests
import time
from assessment_page import show_create_assessment_page
from get_assess import get_assessments,get_assessment_questions
from ai_generator import show_ai_generator_page
from invite import show_invite_page
from student_dashboard import show_student_dashboard 
# from stats_page import show_stats_page

API_BASE_URL = "http://localhost:8000/api/v1"

# -------------------------------------------------------------------
#  THE MAIN DASHBOARD ROUTER
# -------------------------------------------------------------------

def show_dashboard():
    """
    Acts as a router to show the correct dashboard based on user role.
    This is the only function that should be imported into your main app.py.
    """
    if 'user' not in st.session_state or not st.session_state.user:
        st.error("You must be logged in to view the dashboard.")
        st.session_state.page = 'login'
        st.rerun()
        return

    # Check the user's role and call the appropriate dashboard function
    if st.session_state.user.get('role') == 'admin':
        show_admin_dashboard()
    else:
        show_student_dashboard()

# -------------------------------------------------------------------
#  THE ADMIN DASHBOARD
# -------------------------------------------------------------------

def show_admin_dashboard():
    """
    Displays the dashboard with all controls for an admin user.
    """
    st.sidebar.title("Admin Dashboard")
    st.sidebar.markdown(f"### Welcome, {st.session_state.user.get('name', 'Admin')}!")
    
    admin_choice = st.sidebar.radio(
        "Admin Actions",
        ("View Assessments", "Create New Assessment", "Generate-Questions-AI", "Invite Students", "Stats"),
        label_visibility="collapsed"
    )
    
    # Page routing based on the admin's choice
    if admin_choice == "View Assessments":
        display_all_assessments_for_admin()
    elif admin_choice == "Create New Assessment":
        show_create_assessment_page()
    elif admin_choice == "Generate-Questions-AI":
        show_ai_generator_page()
    elif admin_choice == "Invite Students":
        show_invite_page()
    elif admin_choice == "Stats":
        show_stats_page()

def display_all_assessments_for_admin():
    """The default view for the admin, showing a list of all assessments."""
    st.markdown("<h1 class='main-header'>📚 All Assessments</h1>", unsafe_allow_html=True)
    
    assessments = get_assessments()

    if not assessments:
        st.info("No assessments found. Create one from the sidebar.")
        return

    cols = st.columns(2)
    for idx, assessment in enumerate(assessments):
        with cols[idx % 2]:
            with st.container(border=True):
                st.markdown(f"#### {assessment.get('name', 'Untitled Assessment')}")
                st.markdown(f"**Status:** {assessment.get('status', 'N/A').capitalize()}")
                st.markdown(f"**Questions:** {assessment.get('total_questions', 0)}")
                if st.button("Manage", key=f"manage_{assessment['id']}"):
                    st.info(f"Management page for assessment {assessment['id']} coming soon.")