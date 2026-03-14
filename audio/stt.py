import speech_recognition as sr
from config import config

# Initialize standard STT components globally so it only calibrates noise once
recognizer = sr.Recognizer()
recognizer.pause_threshold = config.STT_PAUSE_THRESHOLD
microphone = sr.Microphone()

print("\n[System: Calibrating microphone for ambient noise... This only happens once.]")
with microphone as source:
    recognizer.adjust_for_ambient_noise(source, duration=1)
print("[System: Microphone calibrated successfully!]")

def speech_to_text():
    """Records audio from the mic and uses Google's free API for STT."""
    with microphone as source:
        print(f"\n[System: Listening! Please speak now... (Will stop after a {config.STT_PAUSE_THRESHOLD}s pause or {config.STT_PHRASE_TIME_LIMIT}s max)]")
        try:
            audio = recognizer.listen(source, timeout=config.STT_TIMEOUT, phrase_time_limit=config.STT_PHRASE_TIME_LIMIT)
        except sr.WaitTimeoutError:
            print("[System: No speech detected.]")
            return None

    print("[System: Transcribing...]")
    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("[System: Sorry, I could not understand the audio.]")
        return None
    except sr.RequestError:
        print("[System: Could not request results. Please check your internet connection.]")
        return None
