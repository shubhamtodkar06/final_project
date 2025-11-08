

import base64
from django.conf import settings
from google.cloud import texttospeech

def synthesize_text(text: str, voice_name: str = "en-US-Neural2-C", speaking_rate: float = 1.0) -> str:
    """
    Synthesize speech from text using Google Cloud TTS.
    Returns base64-encoded mp3 audio.
    """
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name=voice_name,
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speaking_rate,
    )
    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )
    audio_content = base64.b64encode(response.audio_content).decode("utf-8")
    return audio_content