import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
NGROK_URL = os.getenv("NGROK_URL", "")

GEMINI_MODEL = "gemini-3-flash-preview"
EMBEDDING_MODEL = "models/text-embedding-004"
COLLECTION_NAME = "sahayak_memory"
