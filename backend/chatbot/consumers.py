import json
import asyncio
import logging
logging.basicConfig(level=logging.INFO)
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .utils import generate_stream_with_context, get_embedding
from .vector_store import get_student_collection
from .models import ChatHistory
from .tts import synthesize_text
from django.contrib.auth import get_user_model

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.user = self.scope.get("user")
            # Unwrap LazyObject if needed
            if hasattr(self.user, "_wrapped") and hasattr(self.user._wrapped, "id"):
                self.user = self.user._wrapped
            await self.accept()
            logging.info(f"✅ WebSocket connected: {self.user}")
            await self.send(text_data=json.dumps({"message": "Connected to AI Chatbot!"}))
        except Exception as e:
            logging.error(f"❌ Connection error: {e}", exc_info=True)

    async def disconnect(self, close_code):
        try:
            logging.info(f"🔌 Disconnected user: {self.scope.get('user')} | Code: {close_code}")
        except Exception as e:
            logging.error(f"⚠️ Error during disconnect: {e}", exc_info=True)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            if not text_data:
                await self.send(text_data=json.dumps({"error": "Only JSON text messages are supported."}))
                return

            data = json.loads(text_data)
            query = data.get("message", "").strip()
            want_tts = bool(data.get("tts") or data.get("voice"))
            from django.contrib.auth import get_user_model
            User = get_user_model()

            user = self.scope.get("user")
            if hasattr(user, "_wrapped") and hasattr(user._wrapped, "id"):
                user = user._wrapped  # unwrap LazyObject

            student_id = str(user.id) if user and getattr(user, "is_authenticated", False) else "guest"

            if not query:
                await self.send(text_data=json.dumps({"error": "Empty message."}))
                return

            await self.send(text_data=json.dumps({"type": "status", "value": "typing"}))
            logging.info(f"🧠 Generating response for: {query}")

            chunks, full_answer = await sync_to_async(generate_stream_with_context)(student_id, query, user)
            for part in chunks:
                if part.strip():
                    await self.send(text_data=json.dumps({"type": "partial", "text": part}))
                    await asyncio.sleep(0)

            payload = {"type": "final", "reply": full_answer}

            if want_tts and full_answer.strip():
                try:
                    audio_b64 = await sync_to_async(synthesize_text)(full_answer)
                    if audio_b64:
                        payload.update({"audio_b64": audio_b64, "content_type": "audio/wav"})
                except Exception as e:
                    logging.error(f"🎤 TTS generation failed: {e}")
                    payload["tts_error"] = str(e)

            await self.send(text_data=json.dumps(payload))

            if user and getattr(user, "is_authenticated", False):
                await sync_to_async(ChatHistory.objects.create)(user=user, question=query, answer=full_answer)
            student_collection = await sync_to_async(get_student_collection)(student_id)
            emb = await sync_to_async(get_embedding)(query)
            await sync_to_async(student_collection.add)(
                documents=[f"Q: {query}\nA: {full_answer}"],
                embeddings=[emb],
                ids=[f"chat_{student_id}"]
            )

        except Exception as e:
            logging.error(f"❌ WebSocket internal error: {e}", exc_info=True)
            await self.send(text_data=json.dumps({"error": f"Internal server error: {str(e)}"}))