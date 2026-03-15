import pygame
import os
from gtts import gTTS
from config import config

try:
    pygame.mixer.init()
except pygame.error as e:
    print(f"[Critical Error: Audio Hardware] Could not initialize audio player: {e}")

def text_to_speech(text):
    if not text or not text.strip():
        print("[Error: TTS] No text provided to speak.")
        return

    output_file = "speech.mp3"
    
    try:
        tts = gTTS(text=text, lang=config.TTS_LANG, tld=config.TTS_TLD)
        tts.save(output_file)
    except Exception as e:
        print(f"[Error: Network/gTTS] Failed to generate speech. Check your internet connection. (Details: {e})")
        return
        
    try:
        pygame.mixer.music.load(output_file)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        pygame.mixer.music.unload()
        
    except pygame.error as e:
        print(f"[Error: Audio Playback] Failed to play the audio file: {e}")
    except Exception as e:
        print(f"[Error: Unexpected Playback Issue] {e}")
    finally:
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except OSError:
                pass