import streamlit as st
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# ---------- Utility ----------
def api_post(endpoint, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.post(f"{BASE_URL}{endpoint}", headers=headers, json=data)
    return resp

def api_get(endpoint, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
    return resp

# ---------- Auth ----------
def login():
    st.title("🔐 Login")
    email = st.text_input("Email")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        res = api_post("/auth/login", {"email": email, "username": username, "password": password})
        if res.status_code == 200:
            data = res.json()
            st.session_state.token = data["access_token"]
            st.session_state.username = data["username"]
            st.session_state.role = data["role"]
            st.success("Login successful!")
            try:
                st.rerun()
            except AttributeError:
                st.experimental_rerun()

        else:
            st.error(res.json().get("detail", "Login failed"))

def register():
    st.title("📝 Register")
    name = st.text_input("Full Name")
    role = st.selectbox("Role", ["student", "admin"])
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        res = api_post("/auth/register", {
            "name": name,
            "role": role,
            "username": username,
            "email": email,
            "password": password
        })
        if res.status_code == 200:
            st.success("Registration successful! Please login.")
        else:
            st.error(res.json().get("detail", "Registration failed"))

# ---------- Dashboard ----------
def dashboard():
    st.title(f"📚 Welcome, {st.session_state.username}")
    st.subheader("Available Assessments")
    res = api_get("/assessments", st.session_state.token)
    if res.status_code == 200:
        assessments = res.json()
        for a in assessments:
            with st.expander(f"{a['name']} ({a['duration']} min)"):
                st.write(f"Total Questions: {a.get('total_questions', 'N/A')}")
                if st.button(f"Start {a['name']}", key=f"start_{a['id']}"):
                    start_quiz(a['id'])
    else:
        st.error("Failed to load assessments.")

    if st.session_state.role == "admin":
        st.subheader("Admin Tools")
        if st.button("➕ Create Assessment"):
            create_assessment()
        if st.button("➕ Create Question"):
            create_question()
        if st.button("🤖 AI Question Generation"):
            ai_generate()

# ---------- Quiz ----------
def start_quiz(assessment_id):
    res = api_post("/user-assessments", {"assessment_id": assessment_id}, st.session_state.token)
    if res.status_code == 200:
        user_assessment = res.json()
        st.session_state.user_assessment_id = user_assessment["id"]
        quiz_page(assessment_id)
    else:
        st.error("Failed to start assessment.")

def quiz_page(assessment_id):
    res = api_get(f"/assessments/{assessment_id}/questions", st.session_state.token)
    if res.status_code == 200:
        questions = res.json()
        answers = []
        for q in questions:
            st.write(f"**Q{q['id']}: {q['question_text']}**")
            choice_id = st.radio(
                "Select an answer:",
                [c["id"] for c in q["choices"]],
                format_func=lambda x: next(c["choice_text"] for c in q["choices"] if c["id"] == x),
                key=f"q_{q['id']}"
            )
            answers.append({"question_id": q["id"], "selected_choice_id": choice_id})
        if st.button("Submit Quiz"):
            res_submit = api_post(
                f"/user-assessments/{st.session_state.user_assessment_id}/submit",
                {"answers": answers},
                st.session_state.token
            )
            if res_submit.status_code == 200:
                st.success("Quiz submitted successfully!")
                result_page(st.session_state.user_assessment_id)
            else:
                st.error("Failed to submit answers.")
    else:
        st.error("Failed to load questions.")

# ---------- Result ----------
def result_page(user_assessment_id):
    res = api_get(f"/user-assessments/{user_assessment_id}/result", st.session_state.token)
    if res.status_code == 200:
        r = res.json()
        st.metric("Score", r["score"])
        st.metric("Total Marks", r["total_marks"])
        st.metric("Percentage", f"{r['percentage']}%")
        st.write(f"Completed At: {r['completed_at']}")
    else:
        st.error("Failed to fetch result.")

# ---------- Admin ----------
def create_assessment():
    st.subheader("Create New Assessment")
    name = st.text_input("Assessment Name")
    duration = st.number_input("Duration (minutes)", min_value=1)
    question_ids = st.text_input("Question IDs (comma-separated)")
    if st.button("Create Assessment"):
        ids = [int(x) for x in question_ids.split(",") if x.strip().isdigit()]
        res = api_post("/assessments", {"name": name, "duration": duration, "question_ids": ids}, st.session_state.token)
        if res.status_code == 200:
            st.success("Assessment created successfully!")
        else:
            st.error(res.json().get("detail", "Failed to create assessment."))
            
def create_question():
    st.subheader("Create New Question")
    text = st.text_input("Question Text")
    topic = st.text_input("Topic")
    level = st.selectbox("Level", ["easy", "medium", "hard"])
    num_choices = st.number_input("Number of choices", min_value=2, max_value=6, value=4)
    choices = []
    for i in range(num_choices):
        c_text = st.text_input(f"Choice {i+1} Text", key=f"choice_text_{i}")
        c_correct = st.checkbox(f"Is Correct?", key=f"choice_correct_{i}")
        choices.append({"choice_text": c_text, "is_correct": c_correct})
    if st.button("Create Question"):
        res = api_post("/questions", {"question_text": text, "topic": topic, "level": level, "choices": choices}, st.session_state.token)
        if res.status_code == 200:
            st.success("Question created successfully!")
        else:
            st.error(res.json().get("detail", "Failed to create question."))

def ai_generate():
    st.subheader("AI Question Generation")
    topic = st.text_input("Topic")
    difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
    count = st.number_input("Number of Questions", min_value=1, value=5)
    if st.button("Generate Questions"):
        res = api_post("/ai/generate", {"topic": topic, "difficulty": difficulty, "count": count}, st.session_state.token)
        if res.status_code == 200:
            data = res.json()
            st.write(data)
        else:
            st.error("AI generation failed.")

# ---------- Main App ----------
if "token" not in st.session_state:
    st.session_state.token = None

menu = ["Login", "Register"]
if st.session_state.token:
    menu = ["Dashboard", "Logout"]

choice = st.sidebar.selectbox("Menu", menu)

if choice == "Login":
    login()
elif choice == "Register":
    register()
elif choice == "Dashboard":
    dashboard()
elif choice == "Logout":
    st.session_state.token = None
    st.session_state.username = None
    st.success("Logged out!")
    st.experimental_rerun()
