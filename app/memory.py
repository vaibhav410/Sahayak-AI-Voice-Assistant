import os
import uuid
import time
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.assistant import get_gemini_embedding

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "sahayak_memory"
VECTOR_SIZE = 768 # text-embedding-004 size

client = None

if QDRANT_URL and QDRANT_API_KEY:
    try:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        print(f"[OK] Qdrant client connected to {QDRANT_URL}")
    except Exception as e:
        print(f"[ERROR] Qdrant connection failed: {e}")
else:
    print("[WARN] QDRANT_URL or QDRANT_API_KEY missing. Using limited memory.")

def init_collection():
    if not client: return
    try:
        collections = client.get_collections().collections
        exists = any(c.name == COLLECTION_NAME for c in collections)
        if not exists:
            print(f"[DEBUG] Creating collection {COLLECTION_NAME}...")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE),
            )
            print(f"[OK] Collection {COLLECTION_NAME} created.")
        else:
            print(f"[OK] Collection {COLLECTION_NAME} already exists.")
        
        # Ensure payload index exists for user_id filtering
        try:
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="user_id",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            print("[OK] Payload index for 'user_id' created.")
        except Exception:
            pass  # Index may already exist, that's fine
            
    except Exception as e:
        print(f"[ERROR] Qdrant init failed: {e}")

def store_memory(user_id: str, role: str, content: str):
    """Store context in Qdrant with user filter."""
    if not client or not content: return
    
    vec = get_gemini_embedding(content)
    if not vec: return

    try:
        point_id = str(uuid.uuid4())
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vec,
                    payload={
                        "user_id": user_id,
                        "role": role,
                        "content": content,
                        "timestamp": time.time()
                    }
                )
            ]
        )
        return point_id
    except Exception as e:
        print(f"[ERROR] Failed to store memory in Qdrant: {e}")
        return None

def retrieve_memory(user_id: str, query: str, limit: int = 5) -> list:
    """Retrieve relevant memories using vector search."""
    if not client or not query: return []
    
    vec = get_gemini_embedding(query)
    if not vec: return []

    try:
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vec,
            query_filter=models.Filter(
                must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
            ),
            limit=limit,
            with_payload=True
        )
        # Format as list of dicts for assistant context
        memories = [
            {"role": r.payload["role"], "content": r.payload["content"]} 
            for r in results if r.payload
        ]
        return memories
    except Exception as e:
        print(f"[ERROR] Qdrant search failed: {e}")
        return []

def get_recent_memory(user_id: str, limit: int = 10) -> list:
    """Fallback: get absolute recent messages for this user."""
    if not client: return []
    try:
        results = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=models.Filter(
                must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
            ),
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        points = results[0]
        # Sort by timestamp (scrolling isn't always sorted)
        sorted_points = sorted(points, key=lambda x: x.payload.get("timestamp", 0))
        return [
            {"role": p.payload["role"], "content": p.payload["content"]} 
            for p in sorted_points
        ]
    except Exception as e:
        print(f"[ERROR] Qdrant scroll failed: {e}")
        return []
