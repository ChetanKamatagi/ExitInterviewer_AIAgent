import streamlit as st
import json
import os
import base64
import speech_recognition as sr
from gtts import gTTS
from config import config
from llm.conversation import GroqConversationService
from llm.summarizer import GroqSummaryService

# ─── Page Config ───
st.set_page_config(
    page_title="AI Exit Interviewer",
    page_icon="🎤",
    layout="centered"
)

# ─── Custom CSS ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    
    /* Landing page card */
    .landing-card {
        background: rgba(255,255,255,0.06);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 3rem 2.5rem;
        margin: 2rem auto;
        max-width: 500px;
        text-align: center;
    }
    
    .landing-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    
    .landing-subtitle {
        color: rgba(255,255,255,0.55);
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }
    
    /* Chat bubbles */
    .agent-bubble {
        background: linear-gradient(135deg, rgba(102,126,234,0.25), rgba(118,75,162,0.25));
        border: 1px solid rgba(102,126,234,0.3);
        border-radius: 18px 18px 18px 4px;
        padding: 1rem 1.3rem;
        margin: 0.8rem 0;
        color: #e0e0e0;
        max-width: 85%;
        animation: fadeIn 0.3s ease-in;
    }
    
    .user-bubble {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 18px 18px 4px 18px;
        padding: 1rem 1.3rem;
        margin: 0.8rem 0 0.8rem auto;
        color: #e0e0e0;
        max-width: 85%;
        text-align: right;
        animation: fadeIn 0.3s ease-in;
    }
    
    .system-msg {
        text-align: center;
        color: rgba(255,255,255,0.35);
        font-size: 0.8rem;
        margin: 0.5rem 0;
        font-style: italic;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Progress bar */
    .progress-container {
        background: rgba(255,255,255,0.08);
        border-radius: 10px;
        height: 8px;
        margin: 1rem 0 1.5rem 0;
        overflow: hidden;
    }
    .progress-fill {
        background: linear-gradient(90deg, #667eea, #764ba2);
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease;
    }
    
    /* Status badge */
    .status-badge {
        display: inline-block;
        background: rgba(102,126,234,0.2);
        border: 1px solid rgba(102,126,234,0.4);
        border-radius: 20px;
        padding: 0.3rem 1rem;
        color: #667eea;
        font-size: 0.8rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }

    /* Summary card */
    .summary-card {
        background: rgba(255,255,255,0.06);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #e0e0e0;
    }
    .summary-card h4 {
        color: #667eea;
        margin-bottom: 0.5rem;
    }

    /* Hide streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    div[data-testid="stStatusWidget"] { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─── Session State Initialization ───
def init_session():
    defaults = {
        "page": "landing",
        "emp_name": "",
        "emp_id": "",
        "chat_history": [],
        "interview_data": {},
        "current_question_index": 0,
        "last_user_response": "",
        "follow_ups": [],
        "follow_up_count": 0,
        "current_context": "",
        "phase": "ask_question",  # ask_question | waiting_response | follow_up | done
        "conversation_service": None,
        "summary_service": None,
        "base_questions": [
            "What is the primary reason for leaving the organization?",
            "How would you describe your overall experience with the company?",
            "What did you like most about working here?",
            "What could the company improve?",
            "How was your relationship with your manager and team?",
            "Would you recommend this company to others? Why or why not?"
        ],
        "audio_autoplay": None,
        "interview_complete": False,
        "summary_json": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ─── Helper: TTS to autoplay HTML ───
def generate_tts_autoplay(text):
    """Generate gTTS audio and return an autoplay HTML audio element."""
    tts = gTTS(text=text, lang=config.TTS_LANG, tld=config.TTS_TLD)
    tts.save("speech.mp3")
    with open("speech.mp3", "rb") as f:
        audio_bytes = f.read()
    b64 = base64.b64encode(audio_bytes).decode()
    return f'<audio autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'


# ─── Helper: Record from mic (STT) ───
def record_from_mic():
    """Record audio from the local microphone and transcribe via Google STT."""
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = config.STT_PAUSE_THRESHOLD
    mic = sr.Microphone()
    
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=config.STT_TIMEOUT, phrase_time_limit=config.STT_PHRASE_TIME_LIMIT)
        except sr.WaitTimeoutError:
            return None
    
    try:
        text = recognizer.recognize_google(audio)
        return text
    except (sr.UnknownValueError, sr.RequestError):
        return None


# ─── Helper: Save JSON files ───
def save_interview_data(interview_data, emp_name, emp_id):
    json_dir = os.path.join(os.path.dirname(__file__), "Json")
    os.makedirs(json_dir, exist_ok=True)
    
    data_with_meta = {
        "employee_name": emp_name,
        "employee_id": emp_id,
        "responses": interview_data
    }
    
    filepath = os.path.join(json_dir, "exit_interview_data.json")
    with open(filepath, "w") as f:
        json.dump(data_with_meta, f, indent=4)
    return filepath

def save_summary(summary_json, emp_name, emp_id):
    json_dir = os.path.join(os.path.dirname(__file__), "Json")
    os.makedirs(json_dir, exist_ok=True)
    
    summary_with_meta = {
        "employee_name": emp_name,
        "employee_id": emp_id,
        "summary": summary_json
    }
    
    filepath = os.path.join(json_dir, "interview_summary.json")
    with open(filepath, "w") as f:
        json.dump(summary_with_meta, f, indent=4)
    return filepath


# ═══════════════════════════════════════════
#              PAGE 1: LANDING
# ═══════════════════════════════════════════
def landing_page():
    st.markdown("<div style='height: 4rem'></div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="landing-card">
        <div class="landing-title">🎤 AI Exit Interviewer</div>
        <div class="landing-subtitle">A safe, confidential space to share your experience</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        emp_name = st.text_input("👤 Employee Name", placeholder="Enter your full name")
        emp_id = st.text_input("🆔 Employee ID", placeholder="Enter your employee ID")
        
        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
        
        if st.button("🚀 Begin Interview", use_container_width=True, type="primary"):
            if emp_name.strip() and emp_id.strip():
                st.session_state.emp_name = emp_name.strip()
                st.session_state.emp_id = emp_id.strip()
                st.session_state.page = "interview"
                
                # Initialize LLM services
                st.session_state.conversation_service = GroqConversationService()
                st.session_state.summary_service = GroqSummaryService()
                
                # Add intro message
                intro = "Hello! Thank you for taking the time for this exit interview. I want this to be a safe space to share your thoughts."
                st.session_state.chat_history.append({"role": "agent", "content": intro})
                st.session_state.audio_autoplay = generate_tts_autoplay(intro)
                
                st.rerun()
            else:
                st.error("Please fill in both fields to continue.")


# ═══════════════════════════════════════════
#           PAGE 2: INTERVIEW
# ═══════════════════════════════════════════
def interview_page():
    ss = st.session_state
    conv = ss.conversation_service
    total_q = len(ss.base_questions)
    
    # ─── Header ───
    st.markdown(f"""
    <div style="text-align:center; margin-bottom:0.5rem;">
        <div class="status-badge">Interview in Progress</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<p style='color:rgba(255,255,255,0.5); font-size:0.85rem;'>👤 {ss.emp_name}</p>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<p style='color:rgba(255,255,255,0.5); font-size:0.85rem; text-align:right;'>🆔 {ss.emp_id}</p>", unsafe_allow_html=True)
    
    # Progress
    progress = min(ss.current_question_index / total_q, 1.0)
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-fill" style="width: {progress * 100}%"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # ─── Chat History ───
    for msg in ss.chat_history:
        if msg["role"] == "agent":
            st.markdown(f'<div class="agent-bubble">🤖 {msg["content"]}</div>', unsafe_allow_html=True)
        elif msg["role"] == "user":
            st.markdown(f'<div class="user-bubble">{msg["content"]} 🗣️</div>', unsafe_allow_html=True)
        elif msg["role"] == "system":
            st.markdown(f'<div class="system-msg">{msg["content"]}</div>', unsafe_allow_html=True)
    
    # ─── Autoplay audio ───
    if ss.audio_autoplay:
        st.markdown(ss.audio_autoplay, unsafe_allow_html=True)
        ss.audio_autoplay = None
    
    # ─── Interview complete → show summary ───
    if ss.interview_complete:
        show_summary_page()
        return
    
    # ─── Ask the current question if phase is ask_question ───
    if ss.phase == "ask_question":
        if ss.current_question_index >= total_q:
            # All questions done → generate sign-off
            with st.spinner("Agent is wrapping up..."):
                final_msg = conv.generate_sign_off()
            ss.chat_history.append({"role": "agent", "content": final_msg})
            ss.audio_autoplay = generate_tts_autoplay(final_msg)
            
            # Save data
            save_interview_data(ss.interview_data, ss.emp_name, ss.emp_id)
            
            # Generate summary
            with st.spinner("Compiling HR Report..."):
                ss.summary_json = ss.summary_service.generate_summary(ss.interview_data)
            if ss.summary_json:
                save_summary(ss.summary_json, ss.emp_name, ss.emp_id)
            
            ss.interview_complete = True
            ss.phase = "done"
            st.rerun()
            return
        
        current_q = ss.base_questions[ss.current_question_index]
        
        # Skip logic
        if ss.interview_data:
            try:
                if conv.should_skip_question(ss.interview_data, current_q):
                    ss.interview_data[current_q] = {"status": "Answered previously in conversation"}
                    ss.current_question_index += 1
                    st.rerun()
                    return
            except Exception:
                pass
        
        # Generate agent speech
        if ss.current_question_index == 0:
            agent_speech = current_q
        else:
            with st.spinner("Agent is thinking..."):
                agent_speech = conv.generate_transition(ss.last_user_response, current_q)
        
        ss.chat_history.append({"role": "agent", "content": agent_speech})
        ss.audio_autoplay = generate_tts_autoplay(agent_speech)
        ss.phase = "waiting_response"
        ss.follow_ups = []
        ss.follow_up_count = 0
        st.rerun()
        return
    
    # ─── Waiting for user response ───
    if ss.phase in ["waiting_response", "follow_up"]:
        # Dual input: text box + mic button
        input_col, mic_col = st.columns([5, 1])
        
        with input_col:
            user_input = st.chat_input("Type your response or click 🎤 to speak...")
        
        with mic_col:
            st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
            mic_clicked = st.button("🎤", key="mic_btn", use_container_width=True, help="Click to speak")
        
        # Handle mic input
        if mic_clicked:
            with st.spinner("🎤 Listening... Speak now!"):
                voice_text = record_from_mic()
            if voice_text:
                user_input = voice_text
            else:
                st.warning("Could not understand. Please try again or type your response.")
                user_input = None
        
        if user_input:
            ss.chat_history.append({"role": "user", "content": user_input})
            
            if ss.phase == "waiting_response":
                ss.current_context = user_input
                ss.last_user_response = user_input
                
                # Check for follow-up
                if ss.follow_up_count < 2:
                    with st.spinner("Agent is thinking..."):
                        follow_up = conv.generate_follow_up(
                            ss.base_questions[ss.current_question_index],
                            user_input
                        )
                    
                    if "NONE" not in follow_up.upper():
                        ss.chat_history.append({"role": "agent", "content": follow_up})
                        ss.audio_autoplay = generate_tts_autoplay(follow_up)
                        ss.follow_ups.append({"ai_question": follow_up, "user_answer": ""})
                        ss.follow_up_count += 1
                        ss.phase = "follow_up"
                        st.rerun()
                        return
                
                # No follow-up needed → store and move on
                current_q = ss.base_questions[ss.current_question_index]
                ss.interview_data[current_q] = {
                    "primary_response": user_input,
                    "follow_up_qa": ss.follow_ups
                }
                ss.current_question_index += 1
                ss.phase = "ask_question"
                st.rerun()
                
            elif ss.phase == "follow_up":
                # Record the follow-up answer
                if ss.follow_ups:
                    ss.follow_ups[-1]["user_answer"] = user_input
                ss.last_user_response = user_input
                
                # Check for another follow-up
                if ss.follow_up_count < 2:
                    with st.spinner("Agent is thinking..."):
                        follow_up = conv.generate_follow_up(
                            ss.base_questions[ss.current_question_index],
                            user_input
                        )
                    
                    if "NONE" not in follow_up.upper():
                        ss.chat_history.append({"role": "agent", "content": follow_up})
                        ss.audio_autoplay = generate_tts_autoplay(follow_up)
                        ss.follow_ups.append({"ai_question": follow_up, "user_answer": ""})
                        ss.follow_up_count += 1
                        st.rerun()
                        return
                
                # Done with follow-ups → store and move on
                current_q = ss.base_questions[ss.current_question_index]
                ss.interview_data[current_q] = {
                    "primary_response": ss.current_context,
                    "follow_up_qa": ss.follow_ups
                }
                ss.current_question_index += 1
                ss.phase = "ask_question"
                st.rerun()


# ═══════════════════════════════════════════
#           SUMMARY PAGE
# ═══════════════════════════════════════════
def show_summary_page():
    ss = st.session_state
    
    st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 2rem 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;">
        <div class="landing-title" style="font-size:1.6rem;">✅ Interview Complete</div>
        <div class="landing-subtitle">Thank you for your valuable feedback</div>
    </div>
    """, unsafe_allow_html=True)
    
    if ss.summary_json:
        st.markdown('<div class="summary-card">', unsafe_allow_html=True)
        st.markdown("#### 📊 HR Executive Summary")
        
        summary = ss.summary_json
        if isinstance(summary, dict):
            if "primary_reason_for_leaving" in summary:
                st.markdown(f"**Primary Reason for Leaving:** {summary['primary_reason_for_leaving']}")
            if "key_positives" in summary:
                positives = summary["key_positives"]
                if isinstance(positives, list):
                    st.markdown("**Key Positives:**")
                    for p in positives:
                        st.markdown(f"- {p}")
                else:
                    st.markdown(f"**Key Positives:** {positives}")
            if "areas_for_improvement" in summary:
                areas = summary["areas_for_improvement"]
                if isinstance(areas, list):
                    st.markdown("**Areas for Improvement:**")
                    for a in areas:
                        st.markdown(f"- {a}")
                else:
                    st.markdown(f"**Areas for Improvement:** {areas}")
            if "overall_sentiment" in summary:
                st.markdown(f"**Overall Sentiment:** {summary['overall_sentiment']}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Download buttons
    col1, col2 = st.columns(2)
    json_dir = os.path.join(os.path.dirname(__file__), "Json")
    
    data_path = os.path.join(json_dir, "exit_interview_data.json")
    if os.path.exists(data_path):
        with open(data_path, "r") as f:
            with col1:
                st.download_button(
                    "📥 Download Interview Data",
                    f.read(),
                    file_name="exit_interview_data.json",
                    mime="application/json",
                    use_container_width=True
                )
    
    summary_path = os.path.join(json_dir, "interview_summary.json")
    if os.path.exists(summary_path):
        with open(summary_path, "r") as f:
            with col2:
                st.download_button(
                    "📥 Download Summary",
                    f.read(),
                    file_name="interview_summary.json",
                    mime="application/json",
                    use_container_width=True
                )
    
    st.markdown("<div style='height: 2rem'></div>", unsafe_allow_html=True)
    if st.button("🔄 Start New Interview", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ═══════════════════════════════════════════
#              ROUTER
# ═══════════════════════════════════════════
if st.session_state.page == "landing":
    landing_page()
elif st.session_state.page == "interview":
    interview_page()
