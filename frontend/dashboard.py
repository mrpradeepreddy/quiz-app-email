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
    # elif admin_choice == "Stats":
    #     show_stats_page()

def display_all_assessments_for_admin():
    """The default view for the admin, showing a list of all assessments."""
    st.markdown("<h1 class='main-header'>📚 All Assessments</h1>", unsafe_allow_html=True)
    
    # This function call should be in your api_helpers.py or similar
    assessments = get_assessments()

    if not assessments:
        st.info("No assessments found. Create one from the sidebar.")
        return

    # Use 3 columns for a more compact and modern look
    cols = st.columns(3) 
    for idx, assessment in enumerate(assessments):
        with cols[idx % 3]:
            # Use a container with a border for each card
            with st.container(border=True):
                
                # --- Card Header ---
                st.subheader(assessment.get('name', 'Untitled Assessment'))
                
                # Use a colored badge for the status
                status = assessment.get('status', 'N/A').capitalize()
                if status == 'Draft':
                    st.markdown(f"Status: <span style='color:gray; font-weight:bold;'>{status}</span>", unsafe_allow_html=True)
                else: # Assuming 'Published' or other active statuses
                    st.markdown(f"Status: <span style='color:green; font-weight:bold;'>{status}</span>", unsafe_allow_html=True)

                st.markdown("---") # Visual separator

                # --- Card Body with Metrics ---
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="❓ Questions", value=assessment.get('total_questions', 0))
                with col2:
                    st.metric(label="⏱️ Duration", value=f"{assessment.get('duration', 0)} min")

                # --- Card Footer with Button ---
                if st.button("⚙️ Manage", key=f"manage_{assessment['id']}", use_container_width=True):
                    st.info(f"Management page for assessment {assessment['id']} coming soon.")