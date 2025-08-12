
import re
import streamlit as st
import requests
from get_assess import get_assessments

API_BASE_URL = "http://localhost:8000/api/v1"

def send_invites_api(emails: list[str], assessment_id: int): # Add assessment_id
    """Calls the backend to send invites for a specific assessment."""
    if not st.session_state.token:
        # ... (error handling) ...
        return None

    api_url = f"{API_BASE_URL}/invites/send"
    
    # Payload now includes assessment_id
    payload = { "emails": emails, "assessment_id": assessment_id } 
    
    headers = { "Authorization": f"Bearer {st.session_state.token}" }

    try:
        response = requests.post(api_url, json=payload, headers=headers) 
        return response
    except requests.exceptions.RequestException as e:
        # ... (error handling) ...
        return None
 # Import your function to get assessments

def show_invite_page():
    """Displays a form for sending quiz invitations to students."""
    st.markdown("<h1 class='main-header'>✉️ Invite Students</h1>", unsafe_allow_html=True)
    
    # Fetch assessments to populate the dropdown
    assessments = get_assessments()
    if not assessments:
        st.warning("No assessments found. Please create an assessment first.")
        return

    # Create a mapping of assessment name to ID for the selectbox
    assessment_options = {f"ID {a['id']}: {a['name']}": a['id'] for a in assessments}

    with st.form("invite_students_form"):
        # --- NEW: Dropdown to select an assessment ---
        selected_assessment_label = st.selectbox(
            "Select Assessment to Invite For:",
            options=assessment_options.keys()
        )
        
        emails_input = st.text_area(
            "Student Emails",
            height=200,
            placeholder="student1@example.com, student2@example.com\nstudent3@example.com"
        )
        
        submitted = st.form_submit_button("Send Invitations")

        if submitted:
            if not emails_input or not selected_assessment_label:
                st.warning("Please select an assessment and enter at least one email.")
            else:
                # Get the ID from the selected assessment label
                assessment_id = assessment_options[selected_assessment_label]
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', emails_input)
                
                if not emails:
                    st.error("No valid email addresses found.")
                else:
                    with st.spinner("Sending invitations..."):
                        # Pass the assessment_id to the API call
                        response = send_invites_api(emails, assessment_id)
                    
                    if response and response.status_code == 200:
                        st.success(response.json().get("message", "Invitations sent!"))
                    else:
                        # ... (your existing error handling logic) ...
                        st.error("Failed to send invitations.")