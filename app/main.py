from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

from app.assistant import (
    translate_to_english, 
    detect_intent_ai, 
    capture_image, 
    read_text, 
    describe_scene, 
    generate_response,
    warm_up_camera,
    release_camera
)
from app.memory import (
    init_collection,
    store_memory,
    retrieve_memory,
    get_recent_memory
)
from app.config import VAPI_API_KEY, NGROK_URL

try:
    from app.vapi_client import create_web_call, create_or_update_assistant
    VAPI_AVAILABLE = True
except ImportError:
    VAPI_AVAILABLE = False

app = FastAPI(title="Sahayak AI", description="Voice Accessibility Assistant")

app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatRequest(BaseModel):
    user_id: str
    message: str
    camera_index: int = 0

class ChatResponse(BaseModel):
    reply: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Standard API chat logic."""
    reply = process_sahayak_pipeline(req.user_id, req.message, req.camera_index)
    return ChatResponse(reply=reply)

@app.post("/api/read-image-chat")
async def read_image_chat(file: UploadFile = File(...), user_id: str = "web_user"):
    """Handles manual image uploads from the UI."""
    try:
        contents = await file.read()
        with open("image.jpg", "wb") as f:
            f.write(contents)
        
        # Once saved, process with OCR intent
        reply = process_sahayak_pipeline(user_id, "Explain this image")
        return {"reply": reply}
    except Exception as e:
        print(f"[ERROR] Image upload failed: {e}")
        return {"reply": "Sorry, I couldn't process that image. Please try again."}

@app.post("/api/chat-with-image")
async def chat_with_image(req: dict):
    """Handles base64 images pasted into the chat."""
    try:
        import base64
        user_id = req.get("user_id", "web_user")
        message = req.get("message", "Describe this image")
        image_b64 = req.get("image_base64")
        
        if image_b64:
            image_data = base64.b64decode(image_b64)
            with open("image.jpg", "wb") as f:
                f.write(image_data)
        
        reply = process_sahayak_pipeline(user_id, message)
        return {"reply": reply}
    except Exception as e:
        print(f"[ERROR] Base64 image failed: {e}")
        return {"reply": "Sorry, I couldn't process the pasted image."}

def process_sahayak_pipeline(user_id, message_content, camera_index=0):
    """The core intelligence pipeline for Sahayak AI."""
    try:
        print(f"[PIPELINE] Input from {user_id}: {message_content}")
        
        # Step 1: Translate
        translated_text = translate_to_english(message_content)

        # Step 2: Memory (Vector search for relevance)
        relevant_memories = retrieve_memory(user_id, translated_text)
        memory_context = "\n".join([f"{m['role']}: {m['content']}" for m in relevant_memories])

        # Step 3: Brain (AI Intent)
        intent = detect_intent_ai(translated_text, memory_context)
        print(f"[PIPELINE] AI Brain Decided: {intent}")

        # Step 4: Action
        if intent == "ocr":
            capture_image(camera_index)
            ocr_result = read_text()
            reply = f"I read the following text: {ocr_result}"

        elif intent == "vision":
            capture_image(camera_index)
            reply = describe_scene(translated_text)

        elif intent == "help":
            reply = "I can help you read text, describe scenes, or just chat. Try saying 'Read this' or 'What is in front of me?'"

        else:
            reply = generate_response(translated_text, memory_context)

        # Step 5: Store memory (as vector)
        store_memory(user_id, "user", message_content)
        store_memory(user_id, "assistant", reply)
        
        # Safe print for unicode
        try:
            print(f"[PIPELINE] Final Response: {reply}")
        except:
            print(f"[PIPELINE] Final Response: [Unicode Content]")
            
        return reply

    except Exception as e:
        print(f"[ERROR] Pipeline crashed: {e}")
        return "I encountered a technical error while processing your request. Please try again or check your camera/API settings."

@app.get("/api/memory/{user_id}")
async def get_user_memory(user_id: str):
    memories = get_recent_memory(user_id)
    return {"memories": memories}

@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")

# Vapi callback endpoint - receives voice input from Vapi
@app.post("/chat")
async def vapi_chat_tool(request: Request):
    """Endpoint for Vapi custom tool callback."""
    try:
        body = await request.json()
    except:
        body = {}
    
    message_content = ""
    user_id = "vapi_user"
    
    # Handle Vapi function call format
    if "arguments" in body:
        args = body.get("arguments", {})
        if isinstance(args, dict):
            message_content = args.get("message", "")
    
    # Handle standard message format
    if not message_content:
        msg = body.get("message", {})
        if isinstance(msg, dict):
            content = msg.get("content", "")
            if isinstance(content, list):
                message_content = " ".join(
                    c.get("text", "") for c in content if isinstance(c, dict)
                )
            else:
                message_content = str(content)
        else:
            message_content = str(msg)
    
    # Get user_id from metadata
    if "metadata" in body:
        user_id = body["metadata"].get("user_id", "vapi_user")
    
    if not message_content or not message_content.strip():
        return {"result": "I didn't catch that. Please speak again."}
    
    print(f"[VAPI] Input: {message_content}")
    
    # Execute standardized pipeline
    reply = process_sahayak_pipeline(user_id, message_content)
    
    return {"result": reply}

@app.post("/api/vapi/setup-assistant")
async def vapi_setup_assistant():
    """Create or update Vapi assistant with ngrok URL."""
    if not VAPI_AVAILABLE:
        raise HTTPException(status_code=500, detail="Vapi client not available")
    if not VAPI_API_KEY:
        raise HTTPException(status_code=500, detail="VAPI_API_KEY not configured")
    if not NGROK_URL:
        raise HTTPException(status_code=400, detail="NGROK_URL not set in .env")
    result = await create_or_update_assistant()
    return result

@app.post("/api/vapi/web-call")
async def vapi_web_call(user_id: str):
    """Start a Vapi web call."""
    if not VAPI_AVAILABLE:
        raise HTTPException(status_code=500, detail="Vapi client not available")
    if not VAPI_API_KEY:
        raise HTTPException(status_code=500, detail="VAPI_API_KEY not configured")
    result = await create_web_call(user_id)
    return result

@app.get("/api/ngrok-status")
async def ngrok_status():
    """Check ngrok configuration status."""
    return {
        "ngrok_url": NGROK_URL,
        "configured": bool(NGROK_URL and NGROK_URL != "https://your-ngrok-url.ngrok-free.app"),
        "vapi_available": VAPI_AVAILABLE
    }

@app.get("/api/health")
async def health():
    return {"status": "ok", "gemini": "configured"}

@app.on_event("startup")
async def startup_event():
    print("[SERVER] Starting up... Initializing Memory and Camera.")
    init_collection()
    warm_up_camera()

@app.on_event("shutdown")
def shutdown_event():
    print("[SERVER] Shutting down... Releasing camera.")
    release_camera()
