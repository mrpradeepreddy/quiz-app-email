import streamlit as st
import requests
import time

API_BASE_URL = "http://localhost:8000/api/v1"


def get_assessments():
    """Get all available assessments."""
    if not st.session_state.token:
        return []
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        # The URL path is now just "/assessments/"
        response = requests.get(f"{API_BASE_URL}/assessments/", headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            # Handle token expiration or invalid token
            st.error("Your session has expired. Please log out and log back in.")
            return []
        else:
        # Handle other potential errors like 403 Forbidden or 500 Server Error
            st.error(f"Failed to load assessments. Status code: {response.status_code}")
            return []
    except requests.exceptions.RequestException:
        return []



def get_assessment_questions(assessment_id):
    """Get questions for a specific assessment."""
    if not st.session_state.token:
        return []
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.get(f"{API_BASE_URL}/assessments/{assessment_id}/questions", headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException:
        return []



def submit_assessment_answers(assessment_id, answers):
    """Submit all answers at the end of the assessment."""
    if not st.session_state.token:
        return None
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        payload = [
            {"question_id": q_id, "choice_id": c_id}
            for q_id, c_id in answers.items()
        ]
        response = requests.post(
            f"{API_BASE_URL}/user-assessments/{assessment_id}/submit",
            headers=headers,
            json={"answers": payload}
        )
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"Error submitting answers: {e}")
        return None




def show_assessment():
    """Displays the active assessment questions."""
    assessment = st.session_state.current_assessment
    questions = st.session_state.questions

    if not questions:
        st.error("Could not load questions for this assessment.")
        if st.button("Back to Dashboard"):
            st.session_state.page = 'dashboard'
            st.rerun()
        return

    total_questions = len(questions)
    current_idx = st.session_state.current_question_index

    # --- Display Question and Choices (Moved Up) ---
    # It's better to get the user's choice before running timer/navigation logic
    question = questions[current_idx]
    st.markdown(f"<div class='question-card'><h3>{current_idx + 1}. {question['question_text']}</h3></div>", unsafe_allow_html=True)
    
    choices = {choice['choice_text']: choice['id'] for choice in question['choices']}
    
    # Pre-select the user's previous answer if it exists
    previous_answer_id = st.session_state.user_answers.get(question['id'])
    previous_answer_text = None
    if previous_answer_id:
        # Find the text corresponding to the saved answer ID
        for text, choice_id in choices.items():
            if choice_id == previous_answer_id:
                previous_answer_text = text
                break
    
    # Get the index of the previously selected answer for the radio button
    options_list = list(choices.keys())
    try:
        default_index = options_list.index(previous_answer_text) if previous_answer_text else None
    except ValueError:
        default_index = None

    user_choice_text = st.radio(
        "Select your answer:",
        options=options_list,
        key=f"q_{question['id']}",
        index=default_index 
    )

    # --- Timer Logic ---
    time_limit_seconds = assessment.get('duration', 0) * 60 # Use .get for safety
    elapsed_time = int(time.time() - st.session_state.start_time)
    remaining_time = time_limit_seconds - elapsed_time

    if remaining_time <= 0:
        st.warning("Time's up! Submitting your assessment.")
        # --- FIX: Save final answer before submitting ---
        if user_choice_text:
            st.session_state.user_answers[question['id']] = choices[user_choice_text]
        submit_and_show_results()
        st.rerun()

    minutes, seconds = divmod(remaining_time, 60)
    st.sidebar.metric("Time Remaining", f"{minutes:02d}:{seconds:02d}")

    # --- Progress Bar (Corrected) ---
    st.sidebar.progress((current_idx + 1) / total_questions) # FIX: Use +1 to reach 100%
    st.sidebar.markdown(f"**Question {current_idx + 1} of {total_questions}**")

    # --- Navigation Buttons ---
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if current_idx > 0:
            if st.button("⬅️ Previous"):
                # --- FIX: Save current answer before going back ---
                if user_choice_text:
                    st.session_state.user_answers[question['id']] = choices[user_choice_text]
                st.session_state.current_question_index -= 1
                st.rerun()

    with col3:
        if current_idx < total_questions - 1:
            if st.button("Next ➡️"):
                if user_choice_text:
                    st.session_state.user_answers[question['id']] = choices[user_choice_text]
                    st.session_state.current_question_index += 1
                    st.rerun()
                else:
                    st.warning("Please select an answer before proceeding.")
        else: # Last question
            if st.button("Submit Assessment", type="primary"):
                if user_choice_text:
                    st.session_state.user_answers[question['id']] = choices[user_choice_text]
                    submit_and_show_results()
                    st.rerun()
                else:
                    st.warning("Please select an answer before submitting.")

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
