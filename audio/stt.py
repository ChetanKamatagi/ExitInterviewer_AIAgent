import sys
import speech_recognition as sr
from config import config

recognizer = sr.Recognizer()
recognizer.pause_threshold = config.STT_PAUSE_THRESHOLD
microphone = sr.Microphone()

print("\n[System: Calibrating microphone for ambient noise...]")
try:
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
    print("[System: Microphone calibrated successfully!]")
except OSError:
    print("[Critical Error: Microphone not found or currently in use by another app.]")

def speech_to_text():
    try:
        with microphone as source:
            print(f"\n[System: Listening! Please speak now...)]")
            try:
                audio = recognizer.listen(source, timeout=config.STT_TIMEOUT, phrase_time_limit=config.STT_PHRASE_TIME_LIMIT)
            except sr.WaitTimeoutError:
                print("[Error: Timeout] No speech was detected within the time limit.")
                return None

        print("[System: Transcribing...]")
        
        text = recognizer.recognize_google(audio)
        text = text.strip()
        
        if len(text) < 2:
            print(f"[Error: Gibberish/Noise] The audio was too short to be a real answer. (Heard: '{text}')")
            return None
            
        print(f"You said: {text}")
        return text

    except sr.UnknownValueError:
        print("[Error: Unclear Audio] I heard something, but it sounded like background noise or gibberish.")
        return None
        
    except sr.RequestError as e:
        print(f"[Error: Network] Could not reach Google's servers. Check your internet connection. (Details: {e})")
        sys.exit(1)

        
    except OSError:
        print("[Error: Hardware] The microphone was disconnected or is inaccessible.")
        return None
        
    except Exception as e:
        print(f"[Error: Unexpected Crash] Something completely unexpected went wrong: {e}")
        return None