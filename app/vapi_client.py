import httpx
from app.config import VAPI_API_KEY, ASSISTANT_ID, NGROK_URL

VAPI_BASE = "https://api.vapi.ai"

SYSTEM_PROMPT = """You are Sahayak AI, a helpful voice assistant for visually impaired users.

RULES:
1. ALWAYS use the sahayak_chat tool for EVERY user message
2. NEVER answer directly without using the tool  
3. Keep responses SHORT (1-2 sentences)
4. Respond in Hindi if user speaks Hindi, English otherwise
5. Do NOT try to process any images or clipboard content

When user speaks, call sahayak_chat with their message only."""


def _headers():
    return {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json",
    }


async def create_or_update_assistant() -> dict:
    tool_url = f"{NGROK_URL}/chat"

    payload = {
        "name": "Sahayak AI",
        "model": {
            "provider": "google",
            "model": "gemini-2.0-flash",
            "systemPrompt": SYSTEM_PROMPT,
            "temperature": 0.7,
            "maxTokens": 300,
        },
        "voice": {
            "provider": "11labs",
            "voiceId": "pNInz6obpgDQGcFmaJgB",
            "model": "eleven_multilingual_v2",
        },
        "firstMessage": "Namaste! I'm Sahayak, your voice assistant. How can I help you?",
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "sahayak_chat",
                    "description": "Chat with Sahayak AI. Pass the user's message to get a smart response with memory context.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "The user's voice message"
                            }
                        },
                        "required": ["message"]
                    },
                },
                "server": {
                    "url": tool_url,
                    "method": "POST",
                    "headers": {}
                },
            }
        ],
    }

    async with httpx.AsyncClient() as client:
        if ASSISTANT_ID:
            response = await client.patch(
                f"{VAPI_BASE}/assistant/{ASSISTANT_ID}",
                json=payload,
                headers=_headers(),
            )
        else:
            response = await client.post(
                f"{VAPI_BASE}/assistant",
                json=payload,
                headers=_headers(),
            )
        return response.json()


async def create_web_call(user_id: str) -> dict:
    payload = {
        "assistantId": ASSISTANT_ID,
        "metadata": {"user_id": user_id},
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{VAPI_BASE}/call/web", json=payload, headers=_headers())
        return response.json()


async def create_call(phone_number: str, user_id: str) -> dict:
    payload = {
        "assistantId": ASSISTANT_ID,
        "phoneNumberId": None,
        "customer": {"number": phone_number},
        "metadata": {"user_id": user_id},
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{VAPI_BASE}/call/phone", json=payload, headers=_headers())
        return response.json()
