import os
import cv2
import pytesseract
from PIL import Image
from deep_translator import GoogleTranslator
import warnings
warnings.filterwarnings("ignore")

# Try new google.genai package, fallback to deprecated
try:
    import google.genai as genai_client
    USE_NEW_GENAI = True
    print("[INFO] Using google.genai package")
except ImportError:
    import google.generativeai as genai_client
    USE_NEW_GENAI = False
    print("[INFO] Using deprecated google.generativeai package")

from dotenv import load_dotenv

# Import configuration
from app.config import GEMINI_MODEL, EMBEDDING_MODEL

load_dotenv()

# Tesseract Configuration (Flexible Path Detection)
def get_tesseract_path():
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.join(os.getenv("LOCALAPPDATA", ""), r"Tesseract-OCR\tesseract.exe"),
        "tesseract" # If in PATH
    ]
    for path in common_paths:
        if path == "tesseract": return path # Assume it works if in PATH
        if os.path.exists(path): return path
    return None

pytesseract.pytesseract.tesseract_cmd = get_tesseract_path() or r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Initialize Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_KEY_2 = os.getenv("GEMINI_API_KEY_2", GEMINI_API_KEY)

# Model references - store (client, model_name) tuples
MODEL_20 = None
MODEL_15 = None
MODEL_LITE = None

# Shared client for new API
_genai_client = None

def _call_generate(model_ref, prompt, contents=None):
    """Helper to generate content with either old or new API."""
    if USE_NEW_GENAI:
        client, model_name = model_ref
        return client.models.generate_content(model=model_name, contents=contents or [prompt])
    else:
        return model_ref.generate_content(prompt)

def _call_generate_with_image(model_ref, prompt, image_data):
    """Helper to generate content with image using either old or new API."""
    if USE_NEW_GENAI:
        client, model_name = model_ref
        from google.genai import types
        contents = [
            types.Content(
                parts=[types.Part(text=prompt)]
            ),
            types.Content(
                parts=[types.Part(inline_data=types.Blob(data=image_data, mime_type='image/jpeg'))]
            )
        ]
        return client.models.generate_content(model=model_name, contents=contents)
    else:
        return model_ref.generate_content(
            contents=[{"text": prompt}, {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}]
        )

def init_model(model_name):
    """Initialize a single model with error handling"""
    global _genai_client
    try:
        if USE_NEW_GENAI:
            if _genai_client is None:
                _genai_client = genai_client.Client(api_key=GEMINI_API_KEY)
            model_ref = (_genai_client, model_name)
        else:
            genai_client.configure(api_key=GEMINI_API_KEY)
            model_ref = genai_client.GenerativeModel(model_name)
        print(f"[OK] {model_name} ready")
        return model_ref
    except Exception as e:
        print(f"[WARN] {model_name} failed: {e}")
        return None

if GEMINI_API_KEY:
    try:
        # Initialize each model independently
        MODEL_20 = init_model('gemini-2.5-flash')
        MODEL_15 = init_model('gemini-2.5-flash')
        MODEL_LITE = init_model('gemini-2.5-flash')
        
        if MODEL_20 or MODEL_15 or MODEL_LITE:
            print("[OK] Gemini AI connected!")
        else:
            print("[ERROR] No Gemini models available")
    except Exception as e:
        print(f"[ERROR] Gemini setup failed: {e}")

# Configure second key for quota fallback
_genai_client_2 = None

if GEMINI_API_KEY_2 and GEMINI_API_KEY_2 != GEMINI_API_KEY:
    try:
        if USE_NEW_GENAI:
            import google.genai as genai2
            _genai_client_2 = genai2.Client(api_key=GEMINI_API_KEY_2)
            _FALLBACK_MODEL = (_genai_client_2, 'gemini-2.5-flash')
        else:
            import google.generativeai as genai2
            genai2.configure(api_key=GEMINI_API_KEY_2)
            _FALLBACK_MODEL = genai2.GenerativeModel('gemini-1.5-flash')
        print("[OK] Fallback API key configured!")
    except Exception as e:
        print(f"[WARN] Fallback key failed: {e}")
        _FALLBACK_MODEL = None
else:
    _FALLBACK_MODEL = None

# ── EMBEDDING FUNCTION ──────────────────
def get_gemini_embedding(text):
    """Uses Gemini embedding model to represent text as a vector."""
    if not text: return None
    
    # Try embedding model from config
    embedding_models = [EMBEDDING_MODEL]
    
    for model_name in embedding_models:
        try:
            if USE_NEW_GENAI:
                result = _genai_client.embed_content(
                    model=model_name,
                    contents=[text],
                    config={"task_type": "retrieval_query"}
                )
                return result.embedding[0].values
            else:
                result = genai_client.embed_content(
                    model=model_name,
                    content=text,
                    task_type="retrieval_query"
                )
                return result['embedding']
        except Exception as e:
            print(f"[WARN] Embedding API failed: {e}")
            break  # Don't retry, use fallback
    
    # Fallback: Simple hash-based embedding (768-dim for Qdrant compatibility)
    print("[INFO] Using fallback embedding")
    import hashlib
    
    # Create deterministic embedding from text hash
    hash_bytes = hashlib.sha256(text.encode()).digest()
    # Expand to 768 dimensions using repeated hashing
    embedding = []
    for i in range(24):  # 24 * 32 = 768
        chunk = hashlib.sha256(hash_bytes + str(i).encode()).digest()
        embedding.extend([b / 255.0 for b in chunk])
    
    return embedding[:768]  # Ensure exactly 768 dimensions

# 0. PERSISTENT CAMERA MANAGER
class CameraManager:
    def __init__(self):
        self.caps = {} # Store camera instances by index

    def initialize(self, index=0):
        try:
            if index not in self.caps or not self.caps[index].isOpened():
                print(f"[DEBUG] Initializing camera {index}...")
                self.caps[index] = cv2.VideoCapture(index)
                if not self.caps[index].isOpened():
                    print(f"[WARN] Camera {index} could not be opened.")
                self.caps[index].set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception as e:
            print(f"[ERROR] Camera initialize error: {e}")

    def get_frame(self, index=0):
        self.initialize(index)
        cap = self.caps[index]
        if cap.isOpened():
            for _ in range(2): cap.grab()
            ret, frame = cap.read()
            return ret, frame
        return False, None

    def release(self):
        for index in list(self.caps.keys()):
            if self.caps[index].isOpened():
                self.caps[index].release()
                print(f"[DEBUG] Camera {index} released.")
            del self.caps[index]

camera_manager = CameraManager()

def warm_up_camera(index=0):
    camera_manager.initialize(index)

def release_camera():
    camera_manager.release()

# 1. TRANSLATION FUNCTION
def translate_to_english(text):
    try:
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        return translated
    except Exception as e:
        print(f"[WARN] Translation failed: {e}")
        return text

# 1. BRAIN: AI INTENT DETECTION
def detect_intent_ai(user_input, memory_context):
    """Uses Gemini to intelligently decide the next action."""
    prompt = f"""
You are the brain of Sahayak AI, a voice assistant for visually impaired users.
User Input: "{user_input}"
Recent History: {memory_context}

Your job is to decide the best action. Prioritize VISION if the user asks about their surroundings.
Respond with EXACTLY one of these tags:
- ACTION: OCR (If user wants to read text, scan documents, or see what is written)
- ACTION: VISION (If user wants to know what's in front of them, describe a scene, or identify objects)
- ACTION: HELP (If user wants help, instructions, or to know what you can do)
- ACTION: CHAT (If it's a general question, greeting, or request for information)

Only respond with the tag. No explanation.
"""
    # Try available models
    for model in [MODEL_20, MODEL_15, MODEL_LITE, _FALLBACK_MODEL]:
        if model:
            try:
                response = _call_generate(model, prompt)
                tag = response.text.strip().upper()
                if "OCR" in tag: return "ocr"
                if "VISION" in tag: return "vision"
                if "HELP" in tag: return "help"
                return "chat"
            except: continue

    return "chat"

# 4. CAMERA FUNCTION (Dual Support)
def capture_image(camera_index=0):
    print(f"[DEBUG] Capturing real-time image from camera {camera_index}...")
    ret, frame = camera_manager.get_frame(camera_index)
    if ret:
        cv2.imwrite("image.jpg", frame)
        print(f"[OK] Image saved from camera {camera_index}")
        return True
    return False

# 5. OCR FUNCTION (Powered by Gemini Vision)
def read_text():
    """Uses Gemini Vision to read text from image.jpg."""
    try:
        if not os.path.exists("image.jpg"):
            return "I couldn't find an image to read. Please check the camera."

        models_to_try = [MODEL_20, MODEL_15, MODEL_LITE, _FALLBACK_MODEL]
        for model in models_to_try:
            if model:
                try:
                    with open("image.jpg", "rb") as f:
                        image_data = f.read()
                    
                    prompt = "Read the text in this image exactly as written. If there is no text, say 'No text detected'. Respond only with the extracted text."
                    response = _call_generate_with_image(model, prompt, image_data)
                    return response.text.strip()
                except Exception as e:
                    print(f"[WARN] OCR model failed: {e}")
                    continue

        return "OCR service is currently unavailable."
    except Exception as e:
        print(f"[ERROR] OCR failed: {e}")
        return "I encountered an error trying to read the text."

# 6. VISION RESPONSE
def describe_scene(user_input):
    """Sends image.jpg to Gemini Vision for description."""
    if not os.path.exists("image.jpg"):
        return "I can't see anything. Please make sure the camera is working."

    models_to_try = [MODEL_20, MODEL_15, MODEL_LITE, _FALLBACK_MODEL]
    for model in models_to_try:
        if model:
            try:
                with open("image.jpg", "rb") as f:
                    image_data = f.read()
                prompt = f"You are the eyes for a visually impaired user. Answer: '{user_input}'. Be descriptive but concise."
                response = _call_generate_with_image(model, prompt, image_data)
                return response.text.strip()
            except Exception as e:
                print(f"[WARN] Vision model failed: {e}")
                continue

    return "Vision unavailable right now."

# 7. AI RESPONSE FUNCTION
def generate_response(user_input, memory_context):
    models_to_try = [MODEL_20, MODEL_15, MODEL_LITE, _FALLBACK_MODEL]
    for model in models_to_try:
        if model:
            try:
                prompt = f"""
You are Sahayak AI, a helpful voice assistant for visually impaired users.
Context: {memory_context}
User: {user_input}
Keep response short (1-2 sentences). Respond naturally.
"""
                response = _call_generate(model, prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                print(f"[WARN] Chat model failed: {e}")
                continue

    return "I'm sorry, I'm having trouble thinking right now."
