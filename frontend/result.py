import streamlit as st
import requests
from get_assess import submit_assessment_answers

API_BASE_URL = "http://localhost:8000/api/v1"


def get_assessment_result(assessment_id):
    """Get assessment results."""
    if not st.session_state.token:
        return None
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.get(f"{API_BASE_URL}/user-assessments/{assessment_id}/result", headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None


def submit_and_show_results():
    """Helper to handle submission logic and switch to results view."""
    assessment_id = st.session_state.current_assessment['id']
    submit_assessment_answers(assessment_id, st.session_state.user_answers)
    st.session_state.show_results = True # Flag to indicate we should show results now
    st.session_state.page = 'results'

def show_results_page():
    """Displays the final results of the assessment."""
    st.markdown("<h1 class='main-header'>🎯 Assessment Results</h1>", unsafe_allow_html=True)
    assessment_id = st.session_state.current_assessment['id']

    with st.spinner("Calculating your results..."):
        result = get_assessment_result(assessment_id)

    if not result:
        st.error("Could not retrieve your results. Please try again later.")
        if st.button("Back to Dashboard"):
            st.session_state.page = 'dashboard'
            st.rerun()
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Questions", result.get('total_questions', 'N/A'))
    col2.metric("Correct Answers", result.get('correct_answers', 'N/A'))
    col3.metric("Score", f"{result.get('score', 0):.2f}%")

    st.markdown("---")
    st.markdown("### Detailed Review")

    details = result.get('details', [])
    if not details:
        st.info("No detailed results available.")
    else:
        for detail in details:
            with st.expander(f"Question: {detail['question_text']}"):
                st.write(f"**Your Answer:** {detail['user_answer']}")
                st.write(f"**Correct Answer:** {detail['correct_answer']}")
                if detail['is_correct']:
                    st.success("✅ Correct")
                else:
                    st.error("❌ Incorrect")

    if st.button("Back to Dashboard", type="primary", use_container_width=True):
        st.session_state.page = 'dashboard'
        # Reset assessment-specific state
        st.session_state.current_assessment = None
        st.session_state.questions = []
        st.session_state.current_question_index = 0
        st.session_state.user_answers = {}
        st.session_state.start_time = None
        st.session_state.show_results = False
        st.rerun()
