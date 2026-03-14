import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

    # Models
    PRIMARY_MODEL = os.environ.get("PRIMARY_MODEL", "llama-3.3-70b-versatile")
    
    fallback_str = os.environ.get("FALLBACK_MODELS", "")
    FALLBACK_MODELS = [m.strip() for m in fallback_str.split(",") if m.strip()]

    # STT Config
    STT_PAUSE_THRESHOLD = 2.5
    STT_TIMEOUT = 10
    STT_PHRASE_TIME_LIMIT = 90

    # TTS Config
    TTS_LANG = 'en'
    TTS_TLD = 'co.za'

config = Config()
