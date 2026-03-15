# 🎤 AI Exit Interviewer — Agentic AI System

An autonomous AI-powered exit interview agent that conducts structured conversations with departing employees, asks intelligent follow-up questions, and generates HR executive summaries, all powered by lightning-fast LLMs with voice I/O.

---

### Demo - https://exitintervieweraiagent.streamlit.app/

---

## 📐 Architecture

```
AIInterviewer/
├── config.py                  # Centralized configuration (API keys, models, STT/TTS params, temperatures)
├── main.py                    # CLI orchestrator — runs the full interview in the terminal
├── app.py                     # Streamlit UI — web-based chat interface
├── audio/
│   ├── stt.py                 # Speech-to-Text using Google Speech Recognition
│   └── tts.py                 # Text-to-Speech using gTTS
├── llm/
│   ├── conversation.py        # Groq LLM service for real-time conversation (with integrated prompts)
│   └── summarizer.py          # Groq LLM service for post-interview HR summarization
├── Json/
│   ├── exit_interview_data.json   # Raw interview transcript (auto-generated)
│   └── interview_summary.json     # AI-generated HR executive summary (auto-generated)
├── .env                       # API keys and model configuration
└── pyproject.toml             # Project dependencies (managed via uv)
```

### Design Decisions

- I decided to build the agent using the Groq API directly instead of relying on heavy frameworks like LangChain or CrewAI. Doing this gave me absolute control over the conversation logic, kept the codebase lightweight, and minimized latency which is absolutely critical for a seamless voice AI experience.
- I designed the architecture to be clean and modular. I completely separated the audio processing (STT/TTS), the AI brain (conversation and summarization), and the main application loop into their own independent files. This makes the project much easier to debug, maintain, and scale.
- To ensure the interview never crashes mid-conversation, I built an automatic fallback system. If the primary AI model hits a rate limit or fails to respond, my code instantly switches to a list of backup models so the user's experience is never interrupted.

---

## 🧠 Agentic Capabilities

| Feature | Implementation |
|---|---|
| **Autonomous Workflow** | The agent completely drives the interview: greeting → asks the 6 base questions → handles follow-ups → signs off → saves data → generates the summary. |
| **Context Awareness** | Analyzes the full interview history before every question to "connect the dots" and automatically skip topics the employee has already covered. |
| **Dynamic Follow-ups** | The LLM decides in real-time if critical context is missing and generates exactly 1 follow-up question. It defaults to accepting valid answers to prevent user fatigue. |
| **Empathetic Transitions** | The LLM generates human-like, non-repetitive transitions between questions, reacting directly and naturally to the employee's previous emotional state. |
| **Conversational Interceptor** | The agent instantly detects if the user asks to repeat the question (e.g., "Come again?", "I didn't hear you") and automatically replays the audio without breaking the interview loop. |
| **Robust Error Recovery** | Built-in retry limits trap empty audio (e.g., background noise). Instant, graceful shutdowns trigger on hardware disconnects or network failures. |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (highly recommended for dependency management)
- A working microphone and speakers
- A Groq API key — [Get one for free here](https://console.groq.com/)

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/ChetanKamatagi/ExitInterviewer_AIAgent.git
   cd AIInterviewer
   ```

2. **Install dependencies using uv:**

   ```bash
   uv sync
   ```

### Configuration

Create a `.env` file in the root directory of your project and add your specific configurations:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
PRIMARY_MODEL=llama-3.3-70b-versatile
FALLBACK_MODELS=llama-3.1-8b-instant,mixtral-8x7b-32768,gemma2-9b-it
```

---

## 💻 Running the Application

This project supports two completely different deployment modes that share the same powerful backend.

### Option 1: CLI Mode (Voice-based Terminal)

Runs the full, hands-free interview directly in your terminal with microphone input and speaker output.

```bash
uv run python main.py
```

- 🎤 Speak your responses naturally into the microphone.
- 🔊 The agent speaks back to you using Text-to-Speech.
- 💾 JSON files are automatically saved to the `Json/` folder upon completion.

### Option 2: Streamlit UI (Web-based)

Launches a modern web interface with a familiar chat-style layout.

```bash
uv run streamlit run app.py
```

- 📝 Type your responses in the chat input, or...
- 🎤 Click the microphone button to speak your answers.
- 🔊 The agent auto-plays its audio responses in the browser.
- 📥 Download the final interview data and summary as JSON files directly from the UI.

---

## 📊 Sample Data Output

### Executive Summary (`interview_summary.json`)

The system automatically compiles the raw transcript into a structured, actionable HR report:

```json
{
    "primary_reason_for_leaving": "Toxic behavior of the manager, including lack of support and partiality",
    "key_positives": [
        "awesome work culture",
        "good pay scale",
        "supportive teammates"
    ],
    "areas_for_improvement": [
        "manager's behavior",
        "transparency in promotions",
        "workload distribution"
    ],
    "overall_sentiment": "Mixed — positive about culture and pay, negative about management"
}
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **LLM (Conversation)** | Groq API — `llama-3.3-70b-versatile` |
| **LLM (Summarization)** | Groq API — `llama-3.3-70b-versatile` (Temperature: 0) |
| **Speech-to-Text** | Google Speech Recognition (`SpeechRecognition`) |
| **Text-to-Speech** | Google TTS (`gTTS`) |
| **Audio Playback** | PyGame |
| **Web Interface** | Streamlit & `audio-recorder-streamlit` |
| **Environment Control** | `uv` and `python-dotenv` |
