import os
import cv2
import pytesseract
from PIL import Image
from deep_translator import GoogleTranslator
import google.generativeai as genai
from dotenv import load_dotenv

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
GEMINI_API_KEY_2 = os.getenv("GEMINI_API_KEY_2", GEMINI_API_KEY)  # Second key for more quota

# Model references
MODEL_V3 = None
MODEL_20 = None
MODEL_15 = None
MODEL_LITE = None

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Prioritize Gemini 3 if available, fallback to 2.0 and 1.5
        MODEL_V3 = genai.GenerativeModel('gemini-3-flash-preview')
        MODEL_20 = genai.GenerativeModel('gemini-2.0-flash')
        MODEL_15 = genai.GenerativeModel('gemini-1.5-flash')
        MODEL_LITE = genai.GenerativeModel('gemini-2.0-flash-lite')
        print("[OK] Gemini AI connected! (Models initialized)")
    except Exception as e:
        print(f"[ERROR] Gemini setup failed: {e}")

# Configure second key for quota fallback
if GEMINI_API_KEY_2 and GEMINI_API_KEY_2 != GEMINI_API_KEY:
    try:
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
    """Uses Gemini text-embedding-004 to represent text as a vector."""
    try:
        if not text: return None
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_query"
        )
        return result['embedding']
    except Exception as e:
        print(f"[ERROR] Embedding failed: {e}")
        return None

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
    # Try Gemini 3 or 1.5
    for model in [MODEL_V3, MODEL_15, _FALLBACK_MODEL]:
        if model:
            try:
                response = model.generate_content(prompt)
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

        models_to_try = [MODEL_V3, MODEL_20, MODEL_15, _FALLBACK_MODEL]
        for model in models_to_try:
            if model:
                try:
                    with open("image.jpg", "rb") as f:
                        image_data = f.read()
                    
                    prompt = "Read the text in this image exactly as written. If there is no text, say 'No text detected'. Respond only with the extracted text."
                    response = model.generate_content(
                        contents=[{"text": prompt}, {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}]
                    )
                    return response.text.strip()
                except: continue

        return "OCR service is currently unavailable."
    except Exception as e:
        print(f"[ERROR] OCR failed: {e}")
        return "I encountered an error trying to read the text."

# 6. VISION RESPONSE
def describe_scene(user_input):
    """Sends image.jpg to Gemini Vision for description."""
    if not os.path.exists("image.jpg"):
        return "I can't see anything. Please make sure the camera is working."

    models_to_try = [MODEL_V3, MODEL_20, MODEL_15, _FALLBACK_MODEL]
    for model in models_to_try:
        if model:
            try:
                with open("image.jpg", "rb") as f:
                    image_data = f.read()
                prompt = f"You are the eyes for a visually impaired user. Answer: '{user_input}'. Be descriptive but concise."
                response = model.generate_content(
                    contents=[{"text": prompt}, {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}]
                )
                return response.text.strip()
            except: continue

    return "Vision unavailable right now."

# 7. AI RESPONSE FUNCTION
def generate_response(user_input, memory_context):
    models_to_try = [MODEL_V3, MODEL_20, MODEL_15, _FALLBACK_MODEL]
    for model in models_to_try:
        if model:
            try:
                prompt = f"""
You are Sahayak AI, a helpful voice assistant for visually impaired users.
Context: {memory_context}
User: {user_input}
Keep response short (1-2 sentences). Respond naturally.
"""
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
            except: continue

    return "I'm sorry, I'm having trouble thinking right now."
