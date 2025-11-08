

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .utils import rag_query

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        await self.accept()
        await self.send(text_data=json.dumps({"message": "Connected to AI Chatbot!"}))

    async def disconnect(self, close_code):
        print(f"Disconnected: {self.user}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        query = data.get("message", "")
        student_id = str(self.user.id) if self.user.is_authenticated else "guest"
        response = await sync_to_async(rag_query)(student_id, query)
        await self.send(text_data=json.dumps({"reply": response}))
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.conf import settings
from .utils import rag_query
from .tts import synthesize_text

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        await self.accept()
        await self.send(text_data=json.dumps({"message": "Connected to AI Chatbot!"}))

    async def disconnect(self, close_code):
        print(f"Disconnected: {self.user}")

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handles both text and voice messages.
        If text_data: expects JSON with 'message' and optional 'voice' (bool) for TTS.
        If bytes_data: expects raw audio (not implemented here).
        """
        if text_data:
            data = json.loads(text_data)
            query = data.get("message", "")
            want_voice = data.get("voice", False)
            student_id = str(self.user.id) if self.user.is_authenticated else "guest"
            response = await sync_to_async(rag_query)(student_id, query)
            if want_voice:
                # Synthesize TTS audio (base64-encoded)
                audio_content = await sync_to_async(synthesize_text)(response)
                await self.send(text_data=json.dumps({"reply": response, "audio": audio_content}))
            else:
                await self.send(text_data=json.dumps({"reply": response}))
        elif bytes_data:
            # (Optional) Handle incoming voice message (ASR not implemented)
            await self.send(text_data=json.dumps({"error": "Voice input not supported in this demo."}))