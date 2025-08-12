import streamlit as st
import requests

API_BASE_URL = "http://localhost:8000/api/v1"
#
def generate_and_save_questions_api(topic: str, difficulty: str, count: int):
    """Calls the backend to generate and save questions using AI."""
    
    # --- Check 1: Is the user logged in? ---
    # If this is missing, the header will be wrong.
    if not st.session_state.token:
        st.error("Authentication token not found. Please log in.")
        return None

    # --- Check 2: Is the URL correct? ---
    # It must exactly match the one in your API client.
    api_url = f"{API_BASE_URL}/ai/generate-questions-and-save"
    
    # --- Check 3: Is the payload correct? ---
    # The keys 'topic', 'difficulty', and 'count' must match your backend model.
    payload = {
        "topic": topic,
        "difficulty": difficulty.lower(),
        "count": count
    }
    
    # --- Check 4: Is the Authorization header being sent correctly? ---
    headers = {
        "Authorization": f"Bearer {st.session_state.token}"
    }

    try:
        # Give the request a longer timeout as AI generation can be slow
        response = requests.post(api_url, json=payload, headers=headers, timeout=120) 
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"API connection error: {e}")
        return None
    
#
def show_ai_generator_page():
    """Displays a form to generate questions using AI."""
    st.markdown("<h1 class='main-header'>🤖 AI Question Generator</h1>", unsafe_allow_html=True)
    st.markdown("Use this tool to automatically generate and save new questions to the database.")

    with st.form("ai_question_generator_form"):
        st.markdown("### Generation Parameters")
        
        topic = st.text_input(
            "Topic",
            placeholder="e.g., Python Data Types, World War II"
        )
        
        difficulty = st.selectbox(
            "Difficulty",
            ("Easy", "Medium", "Hard"), # These must match your Pydantic enum values
            index=1 # Default to 'Medium'
        )
        
        count = st.number_input(
            "Number of Questions to Generate",
            min_value=1,
            max_value=100, # Set a reasonable max to avoid long waits
            value=5,
            step=1
        )

        submitted = st.form_submit_button("Generate and Save Questions")

        if submitted:
            if not topic:
                st.warning("Please enter a topic.")
            else:
                with st.spinner(f"Generating {count} questions on '{topic}'... This may take a moment."):
                    response = generate_and_save_questions_api(topic, difficulty, count)
                
                if response and response.status_code == 200: # Your endpoint returns 200 OK
                    response_data = response.json()
                    st.success(response_data.get("message", "Questions saved successfully!"))
                    
                    # Optionally, display the questions that were generated
                    generated_questions = response_data.get("questions", [])
                    if generated_questions:
                        st.markdown("---")
                        st.subheader("Generated Questions:")
                        for q in generated_questions:
                            with st.expander(f"**{q.get('question_text')}**"):
                                for choice in q.get('choices', []):
                                    is_correct = choice.get('is_correct', False)
                                    prefix = "✅" if is_correct else "❌"
                                    st.write(f"{prefix} {choice.get('choice_text')}")
                else:
                    error_detail = "An unknown error occurred."
                    if response:
                        try:
                            error_detail = response.json().get('detail', error_detail)
                        except requests.exceptions.JSONDecodeError:
                            error_detail = response.text
                    st.error(f"Error: {error_detail}")