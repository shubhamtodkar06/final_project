# backend/chatbot/tts.py
import base64
import os
from google.cloud import texttospeech

def synthesize_text(text: str):
    """
    Convert text to speech using Google Cloud Text-to-Speech.
    Returns base64-encoded audio data to send to the frontend.
    """

    # Build absolute path to credentials JSON relative to project root
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    credential_path = os.path.join(BASE_DIR, "../big-buttress-457415-v1-2a505cf38889.json")

    if not os.path.exists(credential_path):
        raise FileNotFoundError(f"Google Cloud credential file not found at: {credential_path}")

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credential_path

    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Configure the voice request: use free-tier Standard voice (no billing required)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Standard-B",  # ✅ Free-tier standard voice (no billing required)
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )

    # Audio configuration
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    # Perform the text-to-speech request
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    # Encode audio to base64 for WebSocket transmission
    audio_base64 = base64.b64encode(response.audio_content).decode("utf-8")
    return audio_base64