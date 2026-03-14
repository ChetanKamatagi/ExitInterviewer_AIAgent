import pygame
from gtts import gTTS
from config import config

# Initialize audio playback system once
pygame.mixer.init()

def text_to_speech(text):
    """Converts text to human-like speech using gTTS and local configuration."""
    output_file = "speech.mp3"
    
    # Generate the audio using gTTS
    tts = gTTS(text=text, lang=config.TTS_LANG, tld=config.TTS_TLD)
    tts.save(output_file)
    
    # Play the audio
    pygame.mixer.music.load(output_file)
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    
    # Unload the file so it can be overwritten on the next call
    pygame.mixer.music.unload()
