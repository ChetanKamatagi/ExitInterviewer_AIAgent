# 🎤 AI Exit Interviewer — Agentic AI System

An autonomous AI-powered exit interview agent that conducts structured conversations with departing employees, asks intelligent follow-up questions, and generates HR executive summaries — all powered by LLMs with voice I/O.

---

## 📐 Architecture

```
AIInterviewer/
├── config.py                  # Centralized configuration (API keys, model settings, STT/TTS params)
├── main.py                    # CLI orchestrator — runs the full interview in the terminal
├── app.py                     # Streamlit UI — web-based chat interface
├── audio/
│   ├── stt.py                 # Speech-to-Text using Google Speech Recognition
│   └── tts.py                 # Text-to-Speech using gTTS (South African accent)
├── llm/
│   ├── conversation.py        # Groq LLM service for real-time conversation (with fallback models)
│   └── summarizer.py          # Groq LLM service for post-interview summarization
├── Json/
│   ├── exit_interview_data.json   # Raw interview transcript (auto-generated)
│   └── interview_summary.json     # AI-generated HR executive summary (auto-generated)
├── .env                       # API keys and model configuration
└── pyproject.toml             # Project dependencies
```

### Design Decisions

- **No framework overhead**: Instead of LangChain or CrewAI, the agent is built with a clean, modular architecture using direct Groq API calls. This gives full control over the conversation flow, reduces latency, and avoids unnecessary abstraction layers.
- **Separation of concerns**: Audio (STT/TTS), LLM services (conversation/summarization), and orchestration (main.py/app.py) are fully decoupled into independent modules.
- **Model fallback system**: If the primary model hits a rate limit or token exhaustion, the system automatically falls back through a configurable list of backup models.

---

## 🧠 Agentic Capabilities

| Capability | Implementation |
|---|---|
| **Autonomous Workflow** | Agent drives the entire interview: greeting → 6 questions → follow-ups → sign-off → save → summarize |
| **Context Awareness** | Analyzes full interview history before each question to skip already-covered topics |
| **Dynamic Follow-ups** | LLM decides in real-time whether a follow-up is needed (up to 2 per question) |
| **Empathetic Transitions** | LLM generates human-like transitions between questions, acknowledging the employee's previous response |
| **Conversation Summarization** | Dedicated summarizer extracts key insights into a structured JSON report |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A microphone (for voice input in CLI mode)
- Groq API key ([get one free](https://console.groq.com/keys))

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/AIInterviewer.git
cd AIInterviewer

# Install dependencies
uv sync
```

### Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
PRIMARY_MODEL=llama-3.3-70b-versatile
FALLBACK_MODELS=llama-3.1-8b-instant,mixtral-8x7b-32768,gemma2-9b-it
```

---

## 💻 Running the App

### Option 1: CLI Mode (Voice-based)

Runs the full interview in your terminal with microphone input and speaker output.

```bash
uv run python main.py
```

- 🎤 Speak your responses into the microphone
- 🔊 Agent speaks back using gTTS
- JSON files saved to `Json/` folder on completion

### Option 2: Streamlit UI (Web-based)

A modern web interface with a chat-style layout.

```bash
uv run streamlit run app.py
```

- 📝 Type responses in the chat input, or
- 🎤 Click the mic button to speak
- 🔊 Agent auto-plays audio responses
- Download interview data and summary as JSON files

---

## 📊 Sample Output

### Interview Transcript (`exit_interview_data.json`)

```json
{
    "employee_name": "John Doe",
    "employee_id": "EMP-1234",
    "responses": {
        "What is the primary reason for leaving the organization?": {
            "primary_response": "due to my manager is very toxic so I need to move",
            "follow_up_qa": [
                {
                    "ai_question": "Can you elaborate on what you mean by 'toxic'?",
                    "user_answer": "non supportive, partial, doing partiality between teammates"
                }
            ]
        }
    }
}
```

### Executive Summary (`interview_summary.json`)

```json
{
    "employee_name": "John Doe",
    "employee_id": "EMP-1234",
    "summary": {
        "primary_reason_for_leaving": "Toxic behavior of the manager, including lack of support and partiality",
        "key_positives": ["awesome work culture", "good pay scale", "supportive teammates"],
        "areas_for_improvement": ["manager's behavior", "transparency in promotions", "workload distribution"],
        "overall_sentiment": "Mixed — positive about culture and pay, negative about management"
    }
}
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **LLM (Conversation)** | Groq API — `llama-3.3-70b-versatile` |
| **LLM (Summarization)** | Groq API — same model with fallbacks |
| **Speech-to-Text** | Google Speech Recognition (`SpeechRecognition` library) |
| **Text-to-Speech** | Google TTS (`gTTS`) with South African accent |
| **Audio Playback** | PyGame |
| **Web UI** | Streamlit |
| **Configuration** | python-dotenv |

---

## 📁 Two Deployment Modes

| Mode | Entry Point | Input | Output |
|---|---|---|---|
| **CLI** | `main.py` | Voice via microphone | Terminal + JSON files |
| **Streamlit** | `app.py` | Text + Voice (mic button) | Web chat UI + downloadable JSON |

Both modes share the same modular backend (`config.py`, `audio/`, `llm/`) and produce identical `Json/` output files.
