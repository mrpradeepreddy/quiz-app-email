import streamlit as st
import requests
from student_page import handle_assessment_invite

API_BASE_URL = "http://localhost:8000/api/v1"

# -------------------------------------------------------------------
#  API HELPER
# -------------------------------------------------------------------

def get_student_dashboard_data_api():
    """Fetches personalized assessment data for the logged-in student."""
    if not st.session_state.token:
        return []
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.get(f"{API_BASE_URL}/students/me/assessments", headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException:
        return []

# -------------------------------------------------------------------
#  MAIN STUDENT DASHBOARD ROUTER
# -------------------------------------------------------------------

def show_student_dashboard():
    """Displays the main dashboard and sidebar navigation for a student."""
    user_name = st.session_state.user.get('name', 'Student')
    st.sidebar.title(f"Welcome, {user_name}! 👋")

    # --- Sidebar Navigation ---
    student_choice = st.sidebar.radio(
        "Navigation",
        ["Assessments", "My Progress", "Statistics"],
        label_visibility="collapsed"
    )

    # --- Page Routing based on sidebar selection ---
    if student_choice == "Assessments":
        display_student_assessments_view()
    elif student_choice == "My Progress":
        display_student_progress_view()
    elif student_choice == "Statistics":
        display_student_stats_view()

# -------------------------------------------------------------------
#  DASHBOARD VIEWS (PAGES)
# -------------------------------------------------------------------

def display_student_assessments_view():
    """The default view showing available and completed assessments."""
    st.title("My Assessments")
    st.markdown("Here are your assigned assessments. Good luck!")
    st.markdown("---")

    student_assessments = get_student_dashboard_data_api()
    
    if not student_assessments:
        st.info("You have no assigned assessments at the moment.")
        return

    available = [sa for sa in student_assessments if sa['status'] != 'Completed']
    completed = [sa for sa in student_assessments if sa['status'] == 'Completed']

    tab1, tab2 = st.tabs(["▶️ Available to Take", "✅ Completed"])

    with tab1:
        if not available:
            st.write("You have no new assessments to take. Great job!")
        else:
            for sa in available:
                with st.container(border=True):
                    st.subheader(sa['assessment_name'])
                    if st.button("Start Assessment", key=f"start_{sa['assessment_id']}"):
                        handle_assessment_invite(str(sa['assessment_id']), st.session_state.token)
    with tab2:
        if not completed:
            st.write("You have not completed any assessments yet.")
        else:
            for sa in completed:
                with st.container(border=True):
                    st.subheader(sa['assessment_name'])
                    st.metric(label="Your Score", value=f"{sa['score']:.2f}%")

def display_student_progress_view():
    """A placeholder for the student's progress page."""
    st.title("My Progress 📊")
    st.info("Progress tracking and detailed reports coming soon!")
    # You can add charts and graphs here later

def display_student_stats_view():
    """A placeholder for the student's statistics page."""
    st.title("My Statistics 📈")
    st.info("Personal statistics, such as average score and completion time, coming soon!")
    # You can add more detailed stats here later