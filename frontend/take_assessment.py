import streamlit as st
import requests
import time

# This should be the base URL of your running FastAPI backend
API_BASE_URL = "http://localhost:8000/api/v1"

def get_public_assessment_api(assessment_id: int):
    """
    Fetches public assessment data for a student by calling the backend API.
    Returns the assessment data dict on success, or None on failure.
    """
    api_url = f"{API_BASE_URL}/assessments/{assessment_id}/take"
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: Could not retrieve assessment (Status: {response.status_code}).")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"API Connection Error: {e}")
        return None

def submit_assessment_api(assessment_id: int, student_email: str, answers: dict):
    """
    Submits the student's answers to the backend.
    Returns the response object.
    """
    api_url = f"{API_BASE_URL}/assessments/{assessment_id}/submit"
    payload = {
        "student_email": student_email,
        "answers": answers
    }
    try:
        response = requests.post(api_url, json=payload)
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"API Connection Error: {e}")
        return None

def show_take_assessment_page():
    """The page a student sees when they click the shareable link."""
    st.title("Welcome to Your Assessment")

    assessment_id = st.query_params.get("id")
    if not assessment_id:
        st.error("Invalid assessment link. No ID found.")
        return

    # Use session state to manage the student's progress
    if 'test_started' not in st.session_state:
        st.session_state.test_started = False

    # 1. Initial screen: Get student's details
    if not st.session_state.test_started:
        assessment_data = get_public_assessment_api(assessment_id)
        if not assessment_data or not assessment_data.get("questions"):
            st.error("This assessment could not be loaded or has no questions.")
            return

        st.header(assessment_data['title'])
        st.write(f"You will have **{assessment_data['duration']} minutes** to complete this assessment.")

        with st.form("student_details_form"):
            student_email = st.text_input("Please enter your email to begin")
            submitted = st.form_submit_button("Start Assessment")

            if submitted and student_email:
                st.session_state.student_email = student_email
                st.session_state.test_started = True
                st.session_state.assessment_data = assessment_data
                st.session_state.start_time = time.time()
                st.session_state.current_question_index = 0
                st.session_state.user_answers = {}
                st.rerun()

    # 2. Main test interface
    else:
        start_time = st.session_state.start_time
        duration_seconds = st.session_state.assessment_data['duration'] * 60
        elapsed_time = time.time() - start_time
        time_left = duration_seconds - elapsed_time

        if time_left <= 0:
            st.warning("Time's up! Your assessment is being submitted.")
            response = submit_assessment_api(assessment_id, st.session_state.student_email, st.session_state.user_answers)
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            if response and response.status_code == 200:
                st.success("Your assessment has been submitted successfully!")
            else:
                st.error("There was an error submitting your assessment.")

            st.info("The page will reload shortly.")
            time.sleep(5)
            st.rerun()
            return

        st.sidebar.metric("Time Remaining", f"{int(time_left // 60)}m {int(time_left % 60)}s")

        questions = st.session_state.assessment_data['questions']
        q_index = st.session_state.current_question_index
        current_question = questions[q_index]

        st.progress((q_index + 1) / len(questions))
        st.subheader(f"Question {q_index + 1}/{len(questions)}")
        st.write(current_question['question_text'])

        option_map = {opt['option_text']: opt['id'] for opt in current_question['options']}
        options_list = list(option_map.keys())
        saved_answer_id = st.session_state.user_answers.get(current_question['id'])
        pre_selected_index = 0
        if saved_answer_id:
            try:
                saved_answer_text = next(text for text, id in option_map.items() if id == saved_answer_id)
                pre_selected_index = options_list.index(saved_answer_text)
            except (StopIteration, ValueError):
                pass

        user_choice = st.radio("Select your answer:", options=options_list, key=f"q_{current_question['id']}", index=pre_selected_index)

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if q_index > 0:
                if st.button("⬅️ Previous"):
                    st.session_state.user_answers[current_question['id']] = option_map[user_choice]
                    st.session_state.current_question_index -= 1
                    st.rerun()
        with col2:
            if q_index < len(questions) - 1:
                if st.button("Next ➡️"):
                    st.session_state.user_answers[current_question['id']] = option_map[user_choice]
                    st.session_state.current_question_index += 1
                    st.rerun()
        with col3:
            if q_index == len(questions) - 1:
                if st.button("✅ Submit Final Answers", type="primary"):
                    st.session_state.user_answers[current_question['id']] = option_map[user_choice]
                    response = submit_assessment_api(assessment_id, st.session_state.student_email, st.session_state.user_answers)
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    
                    if response and response.status_code == 200:
                         st.success("Your assessment has been submitted successfully!")
                         st.balloons()
                    else:
                         st.error("There was an error submitting your assessment.")