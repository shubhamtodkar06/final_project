# backend/chatbot/tts.py
import base64
import os
from google.cloud import texttospeech

def synthesize_text(text: str):
    """
    Convert text to speech using Google Cloud Text-to-Speech.
    Works both locally and on Render by using the environment variable 
    GOOGLE_APPLICATION_CREDENTIALS if available.
    Returns base64-encoded audio data.
    """

    # Prefer credentials from environment (Render)
    credential_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    # Fallback to local file for development
    if not credential_path:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        credential_path = os.path.join(BASE_DIR, "../big-buttress-457415-v1-2a505cf38889.json")

    if not os.path.exists(credential_path):
        raise FileNotFoundError(f"Google Cloud credential file not found at: {credential_path}")

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credential_path

    # Initialize client
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Configure free-tier voice
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Standard-B",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )

    # Configure output
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    # Perform request
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    # Return base64 encoded audio
    return base64.b64encode(response.audio_content).decode("utf-8")