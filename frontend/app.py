import streamlit as st
import requests
import time

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

# --- API Helper Functions ---

def authenticate_user(email, username, password):
    """Authenticate user and get JWT token."""
    try:
        # CORRECTED: Changed `data` to `json` to match the FastAPI endpoint which expects a JSON body.
        # The URL path is now just "/login" because the base URL already contains "/api/v1".
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"email":email,"username": username, "password": password}
        )
        if response.status_code == 200:
            # Assuming the response contains user info under a 'user' key
            # If not, you might need to adjust this based on your actual API response
            response_data = response.json()
            user_info = {
                "email":response_data.get("email"),
                "username": response_data.get("username"),
                "full_name": response_data.get("username"), # Placeholder, adjust if full name is available
                "role": response_data.get("role")
            }
            return {"access_token": response_data["access_token"], "user": user_info}

        st.error(f"Login failed: {response.json().get('detail', 'Invalid credentials')}")
        return None
    except requests.exceptions.ConnectionError as e:
        st.error(f"Connection error: Could not connect to the server. Please ensure it's running. Details: {e}")
        return None

def register_user(role,email, username, password, name):
    """Register a new user."""
    try:
        # The URL path is now just "/register"
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json={
                "role":role,
                "email": email,
                "username": username,
                "password": password,
                "name": name
            }
        )
        return response
    except requests.exceptions.ConnectionError as e:
        st.error(f"Connection error: Could not connect to the server. Details: {e}")
        return None

def create_assessment_api(name:str,question_id:int,duration:int):
    try:
        response=requests.post(
            f"{API_BASE_URL}/assessments/create",
            json= {
                "name": name,
                "duration": duration,
                "question_id":question_id
            }
        )
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"API connection error: {e}")
        return None


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

# --- Page Rendering Functions ---

def show_login_page():
    """Displays the login and registration forms."""
    st.markdown("<h1 class='main-header'>🎯 Quiz Application</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("### Login")
            email = st.text_input("Email", placeholder="Enter your email")
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.warning("Please enter your username and password.")
                else:
                    auth_data = authenticate_user(email, username, password)
                    if auth_data:
                        st.session_state.token = auth_data["access_token"]
                        st.session_state.user = auth_data["user"]
                        st.session_state.page = 'dashboard'
                        st.success("Login successful!")
                        st.rerun()

        st.markdown("---")
        st.markdown("Don't have an account?")
        if st.button("Create Account", use_container_width=True):
            st.session_state.page = 'register'
            st.rerun()

def show_register_page():
    """Displays the user registration page."""
    st.markdown("<h1 class='main-header'>🎯 Create Your Account</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # This block shows the success message AFTER registration
        if st.session_state.get('registration_success'):
            st.success("Registration successful!")
            if st.button("Click here to Login", use_container_width=True):
                st.session_state.page = 'login'
                del st.session_state.registration_success # Clean up the flag
                st.rerun()
            return # Stop here to not show the form again
        with st.form("register_form"):
            st.markdown("### Register New Account")
            role=st.selectbox("Role",['student','admin'],placeholder="select your Role")
            name = st.text_input("Full Name", placeholder="Enter your full name")
            username = st.text_input("Username", placeholder="Choose a username")
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter password (min 6 chars)")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password")

            submitted = st.form_submit_button("Register", use_container_width=True)
            if submitted:
                if not all([role,name, username, email, password, confirm_password]):
                    st.warning("Please fill out all fields.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters long.")
                else:
                    response = register_user(role,email, username, password, name)
                    if response and response.status_code == 201:
                        st.success("Registration successful! Please login.")
                        st.session_state.registration_success=True
                        st.rerun()
                    else:
                        error_detail = response.json().get('detail', 'Registration failed.')
                        st.error(f"Registration failed: {error_detail}")

        if st.button("Back to Login", use_container_width=True):
            st.session_state.page = 'login'
            st.rerun()

def show_dashboard():
    """Displays the main dashboard with available assessments."""
    # A check to ensure user object is not None before accessing its keys
    is_admin=False
    if st.session_state.user and st.session_state.user.get('role')=='admin':
        is_admin=True
        st.sidebar.markdown(f"### Welcome, {st.session_state.user.get('name','Admin')}!")
    elif st.session_state.user:
        st.sidebar.markdown(f"### Welcome!, {st.session_state.user.get('name','User')}!")
    
    if is_admin:
        st.sidebar.subheader("Admin Actions")
        if st.sidebar.button("Create New Asssessment"):
            st.session_state.page='create_assessment'
            st.rerun()
    if st.sidebar.button("Logout"):
        # Use the built-in clear() method for a safe and clean logout
        st.session_state.clear()
        st.rerun()

    st.markdown("<h1 class='main-header'>📚 Quiz Dashboard</h1>", unsafe_allow_html=True)
    assessments = get_assessments()

    if not assessments:
        st.info("No assessments available at the moment.")
        return

    st.markdown("### Available Assessments")
    cols = st.columns(2)
    for idx, assessment in enumerate(assessments):
        with cols[idx % 2]:
            with st.container(border=True):
                # ... inside with st.container(border=True):
                st.markdown(f"#### {assessment.get('title', 'Untitled Assessment')}")
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

def show_create_assessment_page():
    """Displays a form for admins to create a new assessment."""
    st.markdown("<h1 class='main-header'>📝 Create New Assessment</h1>", unsafe_allow_html=True)

    with st.form("create_assessment_form"):
        st.markdown("### Assessment Details")
        title = st.text_input("Title", placeholder="e.g., Basic Python Quiz")
        question_id = st.number_input("question_ids", placeholder="")
        duration = st.number_input("Time Limit (minutes)", min_value=5, max_value=180, value=30)
        
        
        submitted = st.form_submit_button("Create Assessment")
        if submitted:
            if not all([title, duration, question_id]):
                st.warning("Please fill out all fields.")
            else:
                # This will be your API call function
                response = create_assessment_api(title, duration,question_id)
                
                if response and response.status_code == 201:
                    st.success("Assessment created successfully!")
                    # Optional: Go back to dashboard after creation
                    st.session_state.page = 'dashboard'
                    st.rerun()
                else:
                    error_detail = response.json().get('detail', 'Failed to create assessment.')
                    st.error(f"Error: {error_detail}")

    if st.button("Back to Dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()

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

    # --- Timer Logic ---
    time_limit_seconds = assessment['time_limit'] * 60
    elapsed_time = int(time.time() - st.session_state.start_time)
    remaining_time = time_limit_seconds - elapsed_time

    if remaining_time <= 0:
        st.warning("Time's up! Submitting your assessment.")
        time.sleep(2) # Give user a moment to see the message
        submit_and_show_results()
        st.rerun()

    minutes, seconds = divmod(remaining_time, 60)
    st.sidebar.metric("Time Remaining", f"{minutes:02d}:{seconds:02d}")

    # --- Progress Bar ---
    st.sidebar.progress((current_idx) / total_questions)
    st.sidebar.markdown(f"**Question {current_idx + 1} of {total_questions}**")


    # --- Display Question and Choices ---
    question = questions[current_idx]
    st.markdown(f"<div class='question-card'><h3>{current_idx + 1}. {question['question_text']}</h3></div>", unsafe_allow_html=True)

    # Use a radio button for choices, which is more intuitive for single-choice questions
    choices = {choice['choice_text']: choice['id'] for choice in question['choices']}
    user_choice_text = st.radio(
        "Select your answer:",
        options=choices.keys(),
        key=f"q_{question['id']}",
        index=None # No default selection
    )

    # --- Navigation Buttons ---
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if current_idx > 0:
            if st.button("⬅️ Previous"):
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


# --- Main App Logic ---
def main():
    """Main function to control page navigation."""
    if st.session_state.page == 'login':
        show_login_page()
    elif st.session_state.page == 'register':
        show_register_page()
    elif st.session_state.page == 'dashboard':
        show_dashboard()
    elif st.session_state.page == 'create_assessment':
        show_create_assessment_page()
    elif st.session_state.page == 'assessment':
        show_assessment()
    elif st.session_state.page == 'results':
        show_results_page()
    else:
        st.session_state.page = 'login'
        st.rerun()


if __name__ == "__main__":
    main()
