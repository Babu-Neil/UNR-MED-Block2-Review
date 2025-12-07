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
    # List all your JSON files here
    files_to_load = ['questions.json']
    
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
    
    # Ensure unique IDs and session keys
    for index, q in enumerate(combined_data):
        q['id'] = index  # Use simple integer ID based on load order
        if 'session' not in q:
            q['session'] = "Unknown Session"
            
    return combined_data

all_questions = load_questions()

# --- SESSION STATE INITIALIZATION ---
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = []
if 'current_q_index' not in st.session_state:
    st.session_state.current_q_index = 0
if 'selected_session_state' not in st.session_state:
    st.session_state.selected_session_state = "All Sessions"
if 'performance' not in st.session_state:
    st.session_state.performance = {}

# NEW: Track user answers { question_index: selected_option_string }
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}

def update_score(session_name, is_correct):
    if session_name not in st.session_state.performance:
        st.session_state.performance[session_name] = {'correct': 0, 'total': 0}
    st.session_state.performance[session_name]['total'] += 1
    if is_correct:
        st.session_state.performance[session_name]['correct'] += 1

# --- SIDEBAR ---
st.sidebar.header("Study Configuration")

# 1. Session Selection
if all_questions:
    unique_sessions = sorted(list(set(q['session'] for q in all_questions)))
    blueprint_sessions = ["All Sessions"] + unique_sessions
else:
    blueprint_sessions = ["All Sessions"]

selected_session = st.sidebar.selectbox("Select Lecture/Session", blueprint_sessions)

# 2. Reset / Shuffle Logic
if selected_session != st.session_state.selected_session_state or not st.session_state.quiz_data:
    st.session_state.selected_session_state = selected_session
    st.session_state.current_q_index = 0
    st.session_state.user_answers = {} # Clear history on new topic selection
    
    if all_questions:
        if selected_session == "All Sessions":
            subset = copy.deepcopy(all_questions)
        else:
            filtered = [q for q in all_questions if q['session'] == selected_session]
            subset = copy.deepcopy(filtered)
        
        # Randomize order and options
        random.shuffle(subset)
        for q in subset:
            random.shuffle(q['options'])
            
        st.session_state.quiz_data = subset
    else:
        st.session_state.quiz_data = []

# 3. Progress Report
st.sidebar.divider()
st.sidebar.subheader("📊 Progress Report")
if st.sidebar.button("Reset All Progress"):
    st.session_state.performance = {}
    st.session_state.user_answers = {}
    st.rerun()

if st.session_state.performance:
    for sess, stats in st.session_state.performance.items():
        if stats['total'] > 0:
            accuracy = (stats['correct'] / stats['total']) * 100
            color = "green" if accuracy >= 70 else "red"
            st.sidebar.markdown(f"**{sess}**")
            st.sidebar.markdown(f":{color}[{accuracy:.0f}%] ({stats['correct']}/{stats['total']})")
            st.sidebar.progress(accuracy / 100)
else:
    st.sidebar.info("Start answering to see stats!")

# --- MAIN INTERFACE ---
st.title("Block 2: Cardiovascular, Pulmonary & Renal Review")

if not st.session_state.quiz_data:
    st.warning("No questions found.")
else:
    # 1. Navigation Header
    col_nav1, col_nav2, col_nav3 = st.columns([1, 4, 1])
    
    with col_nav1:
        if st.button("⬅️ Previous"):
            st.session_state.current_q_index = max(0, st.session_state.current_q_index - 1)
            st.rerun()
            
    with col_nav2:
        # Progress Bar
        total_q = len(st.session_state.quiz_data)
        current = st.session_state.current_q_index + 1
        st.progress(current / total_q)
        st.caption(f"Question {current} of {total_q}")

    with col_nav3:
        if st.button("Next ➡️"):
            st.session_state.current_q_index = min(total_q - 1, st.session_state.current_q_index + 1)
            st.rerun()

    st.divider()

    # 2. Get Current Question Data
    # Safety check
    if st.session_state.current_q_index >= len(st.session_state.quiz_data):
        st.session_state.current_q_index = 0 
        
    q = st.session_state.quiz_data[st.session_state.current_q_index]
    
    # 3. Check if we have already answered this question
    # We track answers by the INDEX in the shuffled list (0, 1, 2...), not the Question ID
    # This keeps it simple for the current session.
    has_answered = st.session_state.current_q_index in st.session_state.user_answers
    previous_choice = st.session_state.user_answers.get(st.session_state.current_q_index)

    # 4. Display Question
    st.markdown(f"### {q['question']}")
    
    # Determine the index for the radio button if previously answered
    radio_index = None
    if has_answered and previous_choice in q['options']:
        radio_index = q['options'].index(previous_choice)

    # 5. Render Options (Disabled if already answered)
    option_selected = st.radio(
        "Select your answer:", 
        q['options'], 
        key=f"q_{q['id']}", 
        index=radio_index,
        disabled=has_answered  # <--- THIS LOCKS THE ANSWER
    )

    # 6. Action Logic
    if has_answered:
        # --- REVIEW MODE (Already Answered) ---
        is_correct = (previous_choice == q['correct_answer'])
        
        if is_correct:
            st.success(f"✅ You answered: {previous_choice}")
        else:
            st.error(f"❌ You answered: {previous_choice}")
            st.success(f"Correct Answer: {q['correct_answer']}")
            
        st.info(f"**Explanation:** {q['explanation']}")
        st.caption(f"Source: {q['session']} ({q['faculty']})")

    else:
        # --- ACTIVE MODE (Not yet answered) ---
        if st.button("Check Answer"):
            if option_selected:
                # 1. Save answer to history (Lock it)
                st.session_state.user_answers[st.session_state.current_q_index] = option_selected
                
                # 2. Check correctness
                is_correct = (option_selected == q['correct_answer'])
                
                # 3. Update stats
                update_score(q['session'], is_correct)
                
                # 4. Show immediate feedback before auto-advancing
                if is_correct:
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Incorrect. The correct answer was: {q['correct_answer']}")
                
                st.info(f"**Explanation:** {q['explanation']}")
                
                # 5. Auto-Advance Timer
                progress_text = "Saving and moving to next question..."
                my_bar = st.progress(0, text=progress_text)
                for percent_complete in range(100):
                    time.sleep(0.03) # 3 seconds total wait
                    my_bar.progress(percent_complete + 1, text=progress_text)
                
                # 6. Move to next
                if st.session_state.current_q_index < len(st.session_state.quiz_data) - 1:
                    st.session_state.current_q_index += 1
                    st.rerun()
                else:
                    st.balloons()
                    st.success("You've reached the end of this set!")
            else:
                st.warning("Please select an option first.")
