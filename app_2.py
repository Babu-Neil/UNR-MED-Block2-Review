import streamlit as st
import json
import random
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="UNR Med Block 2 Review", layout="wide")

# --- LOAD DATA ---
@st.cache_data
def load_questions():
    try:
        with open('questions.json', 'r') as f:
            data = json.load(f)
            # Ensure every question has a valid session key
            for q in data:
                if 'session' not in q:
                    q['session'] = "Unknown Session"
            return data
    except FileNotFoundError:
        return []

all_questions = load_questions()

# --- SESSION STATE MANAGEMENT ---
# We use session state to store the *shuffled* order of questions so it doesn't reshuffle on every click
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = []
if 'current_q_index' not in st.session_state:
    st.session_state.current_q_index = 0
if 'selected_session_state' not in st.session_state:
    st.session_state.selected_session_state = "All Sessions"
if 'performance' not in st.session_state:
    st.session_state.performance = {}

def update_score(session_name, is_correct):
    if session_name not in st.session_state.performance:
        st.session_state.performance[session_name] = {'correct': 0, 'total': 0}
    st.session_state.performance[session_name]['total'] += 1
    if is_correct:
        st.session_state.performance[session_name]['correct'] += 1

# --- SIDEBAR: FILTERS & SETTINGS ---
st.sidebar.header("Study Configuration")

# Get unique sessions for the dropdown
unique_sessions = sorted(list(set(q['session'] for q in all_questions)))
blueprint_sessions = ["All Sessions"] + unique_sessions

# Dropdown for session selection
selected_session = st.sidebar.selectbox("Select Lecture/Session", blueprint_sessions)

# Check if session filter changed; if so, re-shuffle questions
if selected_session != st.session_state.selected_session_state or not st.session_state.quiz_data:
    st.session_state.selected_session_state = selected_session
    st.session_state.current_q_index = 0
    
    # Filter questions based on selection
    if selected_session == "All Sessions":
        subset = all_questions.copy()
    else:
        subset = [q for q in all_questions if q['session'] == selected_session]
    
    # RANDOMIZE THE QUESTIONS
    random.shuffle(subset)
    st.session_state.quiz_data = subset

# --- PROGRESS REPORT ---
st.sidebar.divider()
st.sidebar.subheader("📊 Progress Report")
if st.sidebar.button("Reset Progress"):
    st.session_state.performance = {}
    st.rerun()

if not st.session_state.performance:
    st.sidebar.info("Start answering to see your stats!")
else:
    for sess, stats in st.session_state.performance.items():
        if stats['total'] > 0:
            accuracy = (stats['correct'] / stats['total']) * 100
            color = "green" if accuracy >= 70 else "red"
            st.sidebar.markdown(f"**{sess}**")
            st.sidebar.markdown(f":{color}[{accuracy:.0f}%] ({stats['correct']}/{stats['total']})")
            st.sidebar.progress(accuracy / 100)

# --- MAIN INTERFACE ---
st.title("Block 2: Cardiovascular, Pulmonary & Renal Review")

if not st.session_state.quiz_data:
    st.warning("No questions available for this selection.")
else:
    # Get current question object
    # Safety check for index out of bounds
    if st.session_state.current_q_index >= len(st.session_state.quiz_data):
        st.success("🎉 You have completed all questions in this set!")
        if st.button("Restart This Set"):
            random.shuffle(st.session_state.quiz_data)
            st.session_state.current_q_index = 0
            st.rerun()
    else:
        q = st.session_state.quiz_data[st.session_state.current_q_index]
        
        # Header info
        st.markdown(f"**Session:** {q['session']} | **Question:** {st.session_state.current_q_index + 1} of {len(st.session_state.quiz_data)}")
        st.progress((st.session_state.current_q_index + 1) / len(st.session_state.quiz_data))
        
        st.divider()
        st.subheader(f"Question {st.session_state.current_q_index + 1}")
        st.markdown(f"#### {q['question']}")
        
        # Display Options
        # We use a unique key per question ID so the radio selection clears when we move to the next question
        option_selected = st.radio("Select your answer:", q['options'], key=f"q_radio_{q['id']}", index=None)
        
        # Check Answer Button
        if st.button("Check Answer"):
            if option_selected:
                is_correct = (option_selected == q['correct_answer'])
                
                # Show Result
                if is_correct:
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Incorrect. The correct answer is: **{q['correct_answer']}**")
                
                # Update Stats
                update_score(q['session'], is_correct)
                
                # Show Explanation
                st.info(f"**Explanation:** {q['explanation']}")
                st.caption(f"Source: {q['session']} ({q['faculty']})")
                
                # AUTO-ADVANCE LOGIC
                # We show a small progress bar to indicate time remaining before next question
                progress_text = "Moving to next question in 5 seconds..."
                my_bar = st.progress(0, text=progress_text)
                
                for percent_complete in range(100):
                    time.sleep(0.08) # Total time = 0.08 * 100 = 8 seconds
                    my_bar.progress(percent_complete + 1, text=progress_text)
                
                # Advance index and rerun
                st.session_state.current_q_index += 1
                st.rerun()
            else:
                st.warning("Please select an option first.")
                
        # Manual Navigation (Optional, in case they want to skip)
        st.divider()
        if st.button("Skip Question"):
            st.session_state.current_q_index += 1
            st.rerun()