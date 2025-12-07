import streamlit as st
import json
import random
import time
import copy
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="UNR Med Block 2 Review", layout="wide")

# --- LOAD DATA ---
@st.cache_data
def load_questions():
    combined_data = []
    files_to_load = ['questions_2.json']
    
    for filename in files_to_load:
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                    combined_data.extend(data)
            except Exception as e:
                st.error(f"Error loading {filename}: {e}")
    
    if not combined_data:
        return []
    
    # Re-assign IDs to ensure they are unique across both files
    # (This prevents errors if both files have "Question 1")
    for index, q in enumerate(combined_data):
        q['id'] = index + 1
        if 'session' not in q:
            q['session'] = "Unknown Session"
            
    return combined_data

all_questions = load_questions()

# --- SESSION STATE MANAGEMENT ---
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

# Get unique sessions
if all_questions:
    unique_sessions = sorted(list(set(q['session'] for q in all_questions)))
    blueprint_sessions = ["All Sessions"] + unique_sessions
else:
    blueprint_sessions = ["All Sessions"]

selected_session = st.sidebar.selectbox("Select Lecture/Session", blueprint_sessions)

# Check if session filter changed; if so, re-shuffle questions
if selected_session != st.session_state.selected_session_state or not st.session_state.quiz_data:
    st.session_state.selected_session_state = selected_session
    st.session_state.current_q_index = 0
    
    if all_questions:
        # Filter questions
        if selected_session == "All Sessions":
            subset = copy.deepcopy(all_questions)
        else:
            filtered = [q for q in all_questions if q['session'] == selected_session]
            subset = copy.deepcopy(filtered)
        
        # --- RANDOMIZATION LOGIC ---
        # 1. Shuffle the order of questions
        random.shuffle(subset)
        
        # 2. Shuffle the answer options for EACH question
        for q in subset:
            random.shuffle(q['options'])
            
        st.session_state.quiz_data = subset
    else:
        st.session_state.quiz_data = []

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
    st.warning("No questions found. Please ensure 'questions.json' is in the folder.")
else:
    # Get current question object
    if st.session_state.current_q_index >= len(st.session_state.quiz_data):
        st.success("🎉 You have completed all questions in this set!")
        if st.button("Restart This Set"):
            # Re-shuffle on restart
            random.shuffle(st.session_state.quiz_data)
            for q in st.session_state.quiz_data:
                random.shuffle(q['options'])
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
        # Unique key ensures radio button clears between questions
        option_selected = st.radio("Select your answer:", q['options'], key=f"q_radio_{q['id']}", index=None)
        
        # Check Answer Button
        if st.button("Check Answer"):
            if option_selected:
                is_correct = (option_selected == q['correct_answer'])
                
                if is_correct:
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Incorrect. The correct answer is: **{q['correct_answer']}**")
                
                update_score(q['session'], is_correct)
                
                st.info(f"**Explanation:** {q['explanation']}")
                st.caption(f"Source: {q['session']} ({q['faculty']})")
                
                # Auto-advance timer
                progress_text = "Next question in 5 seconds..."
                my_bar = st.progress(0, text=progress_text)
                for percent_complete in range(100):
                    time.sleep(0.05)
                    my_bar.progress(percent_complete + 1, text=progress_text)
                
                st.session_state.current_q_index += 1
                st.rerun()
            else:
                st.warning("Please select an option first.")
                
        # Skip Button
        st.divider()
        if st.button("Skip Question"):
            st.session_state.current_q_index += 1
            st.rerun()
