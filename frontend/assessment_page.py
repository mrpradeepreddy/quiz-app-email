import streamlit as st
import requests
import time

API_BASE_URL = "http://localhost:8000/api/v1"

# You will need this helper function to get questions for the dropdown
def get_all_questions_api():
    """Fetches all questions from the API to display in the multiselect."""
    if not st.session_state.token:
        return []
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        # You must create a GET /questions/ endpoint in your backend
        response = requests.get(f"{API_BASE_URL}/questions/", headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException:
        return []

def create_assessment_api(title: str, duration: int, question_ids: list[int]):
    """
    Calls the backend API to create a new assessment with a list of questions.
    """
    # Ensure the user is logged in and has a token
    if not st.session_state.token:
        st.error("Authentication token not found. Please log in.")
        return None

    # The backend endpoint URL
    api_url = f"{API_BASE_URL}/assessments/create"

    # This payload must exactly match your backend's Pydantic model
    payload = {
        "name": title,          # Make sure your backend expects "name" or "title"
        "duration": duration,
        "question_ids": question_ids # This is now sending a list of integers
    }

    # Creating an assessment is a protected action, so we must send the auth token
    headers = {
        "Authorization": f"Bearer {st.session_state.token}"
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"API connection error: {e}")
        return None

# Replace your existing function with this one
def show_create_assessment_page():
    """Displays a form for admins to create a new assessment."""
    st.markdown("<h1 class='main-header'>📝 Create New Assessment</h1>", unsafe_allow_html=True)

    # 1. Fetch all questions to show as options
    all_questions = get_all_questions_api()
    if not all_questions:
        st.error("No questions found. Please create questions in the database first.")
        if st.button("Back to Dashboard"):
            st.session_state.page = 'dashboard' # Or handle navigation differently
            st.rerun()
        return

    # 2. Create a user-friendly mapping of question text to question ID
    question_options = {f"ID: {q['id']} - {q['question_text']}": q['id'] for q in all_questions}

    with st.form("create_assessment_form"):
        st.markdown("### New Assessment")
        title = st.text_input("Title", placeholder="e.g., Basic Python Quiz")
        duration = st.number_input("Time Limit (minutes)", min_value=5, max_value=180, value=30, step=1)
        
        # 3. Use a multiselect box to select multiple questions
        selected_question_labels = st.multiselect(
            "Select Questions for this Assessment",
            options=question_options.keys()
        )

        # for label, question_id in question_options.items():
        # st.checkbox(label, key=f"q_{question_id}") # The key must be unique!

        for question in all_questions:
            label = f"**ID: {question['id']}** - {question['question_text']}"
            st.checkbox(label, key=f"q_{question['id']}") # e.g., key='q_101', 'q_102'
        submitted = st.form_submit_button("Create Assessment")
        # if submitted:
        #     # 4. Get the list of integer IDs from the user's selection
        #     selected_question_ids = [question_options[label] for label in selected_question_labels]
        
        
        if submitted:
            # 3. On submission, collect the IDs of all checked boxes.
            #    Streamlit stores the state of each widget in st.session_state using its key.
            selected_question_ids = [
                question['id'] for question in all_questions if st.session_state[f"q_{question['id']}"]
            ]

            if not all([title, duration]) or not selected_question_ids:
                st.warning("Please fill out all fields and select at least one question.")
            else:
                # 5. Send the list of IDs to your API
                response = create_assessment_api(title, duration, selected_question_ids)
                
                if response and response.status_code == 201:
                    st.success("Assessment created successfully!")
                    # Since we are already on the dashboard page, no need to rerun
                else:
                    error_detail = response.json().get('detail', 'Failed to create assessment.')
                    st.error(f"Error: {error_detail}")



# this is my new assessment page

# --- Mock API Functions (for demonstration purposes) ---
# In your real application, these would make actual HTTP requests to your backend.
