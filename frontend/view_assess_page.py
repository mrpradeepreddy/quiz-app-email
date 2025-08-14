import streamlit as st
import requests

# This should be the base URL of your running FastAPI backend
API_BASE_URL = "http://localhost:8000/api/v1"

# --- API Helper Functions ---
# In a real app, these would be in your api_helpers.py file

def get_admin_assessment_details_api(assessment_id: int, token: str):
    """
    Fetches the full details of a single assessment for an admin.
    This is a protected endpoint.
    """
    # MOCK IMPLEMENTATION
    print(f"API CALL: Fetching details for assessment {assessment_id} with token.")
    if assessment_id: # Assuming ID is passed as string from session state
        return {
            "id": assessment_id,
            "title": f"Details for assessment #{assessment_id}",
            "duration": 30 
        }
    return None

def get_assessment_questions_api(assessment_id: int, token: str):
    """
    Fetches the list of questions for a specific assessment.
    This would be a separate endpoint in a real application.
    """
    # MOCK IMPLEMENTATION
    api_url = f"{API_BASE_URL}/assessments/{assessment_id}/questions"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            # On success, return the list of questions from the JSON response.
            return response.json()
        
        # UPDATE: Added specific checks for common HTTP error codes.
        elif response.status_code == 401:
            st.error("Authentication failed. Please log out and log back in.")
            return []
        elif response.status_code == 404:
            st.error("Error: The questions endpoint for this assessment was not found (404).")
            return []
        else:
            # Generic error for other failed statuses.
            st.error(f"Failed to load questions (Status: {response.status_code}). Details: {response.text}")
            return []
            
    except requests.exceptions.RequestException as e:
        # If there's a network error, show an error and return an empty list.
        st.error(f"API Connection Error: Could not connect to the backend at {api_url}.")
        return []


def delete_assessment_api(assessment_id: int, token: str):
    """
    Calls the backend to delete an assessment.
    This is a protected endpoint.
    """
    # MOCK IMPLEMENTATION
    print(f"API CALL: Deleting assessment {assessment_id} with token.")
    # In a real app:
    # headers = {"Authorization": f"Bearer {token}"}
    # response = requests.delete(f"{API_BASE_URL}/assessments/{assessment_id}", headers=headers)
    # return response.status_code == 204 # 204 No Content is a common success status for DELETE
    return True # Mock success

# --- Main Page Function ---

def show_view_assessment_page():
    """
    Displays the details for a single assessment for an admin.
    Shows the shareable link and allows deletion.
    """
    st.header("📄 Assessment Details")
    
    # This ID must be set in the session state before navigating to this page.
    assessment_id = st.session_state.get("current_assessment_id")
    token = st.session_state.get("token")

    if not assessment_id or not token:
        st.error("Could not load assessment. Please go back to the dashboard and try again.")
        if st.button("⬅️ Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        return

    # Fetch the assessment details from the API
    assessment_data = get_admin_assessment_details_api(assessment_id, token)

    if not assessment_data:
        st.error(f"Could not find details for Assessment ID: {assessment_id}")
        if st.button("⬅️ Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        return
    
    questions = get_assessment_questions_api(assessment_id, token)
    # --- Display Page Content ---
    
    st.title(assessment_data['title'])
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

    st.markdown("---")

    # Display Key Details & Shareable Link
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Time Limit", f"{assessment_data['duration']} minutes")
    with col2:
        st.metric("Number of Questions", len(questions))
    
    st.markdown("### ✉️ Shareable Link for Students")
    st.info("Copy the link below and send it to students to take the assessment.")
    # NOTE: Replace 'http://localhost:8501' with your actual app's URL when deployed.
    shareable_link = f"http://localhost:8501/?id={assessment_id}"
    st.code(shareable_link, language="text")

    st.markdown("---")

    # Display the list of questions
    st.markdown("### ❓ Questions in this Assessment")
    # questions = assessment_data.get('questions', [])
    if not questions:
        st.warning("This assessment currently has no questions.")
    else:
        for i, question in enumerate(questions):
            st.text(f"{i+1}. {question['question_text']}")

    st.markdown("---")

    # Add a Delete button with a confirmation step
    st.markdown("### 🗑️ Danger Zone")
    
    if 'confirm_delete' not in st.session_state:
        st.session_state.confirm_delete = False

    if st.button("Delete this Assessment", type="primary"):
        st.session_state.confirm_delete = True

    if st.session_state.get("confirm_delete"):
        st.warning("**Are you sure you want to permanently delete this assessment? This action cannot be undone.**")
        
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            if st.button("✅ Yes, Delete", type="primary"):
                if delete_assessment_api(assessment_id, token):
                    st.success("Assessment deleted successfully.")
                    st.session_state.confirm_delete = False
                    st.session_state.page = "dashboard"
                    time.sleep(2) # Give user time to read message
                    st.rerun()
                else:
                    st.error("Failed to delete the assessment.")
        with c2:
            if st.button("❌ No, Cancel"):
                st.session_state.confirm_delete = False
                st.rerun()
