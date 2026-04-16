# PRODUCT REQUIREMENT DOCUMENT (PRD)

## 1. Product Overview

**Product Name:** Sahayak AI - Voice Accessibility Assistant

**Vision:** To enable visually impaired and low-literacy users to interact with digital systems using natural voice, making technology more inclusive and accessible.

**Problem Statement:**
Millions of users struggle with:
- Reading text on screens
- Navigating digital interfaces
- Accessing information independently

---

## 2. Solution

Sahayak AI is a voice-first intelligent assistant that:
- Understands user voice input
- Responds with natural speech
- Remembers user context
- Assists in real-world tasks

---

## 3. Target Users

- Visually impaired individuals
- Low literacy users
- Elderly users
- Rural users with limited digital exposure

---

## 4. Core Features

### Voice Interaction (MANDATORY)
- Speak -> AI responds
- Powered by Vapi (with browser Speech Recognition fallback)

### Context Memory
- Remembers previous conversations
- Personalized responses
- Powered by Qdrant vector database

### Text Reading (OCR)
- Capture image -> Read text aloud
- Helps users read documents
- Powered by pytesseract

### AI Assistance
- Answer questions
- Provide step-by-step guidance
- Help with daily tasks
- Powered by Gemini AI (FREE tier)

### Image Understanding
- Analyzes images and describes content
- Powered by Gemini Vision

### Multilingual Support
- English + Hindi
- Smart language detection
- Responds in user's language

---

## 5. System Architecture

```
User Voice
   |
   v
Vapi / Browser Speech API (Speech-to-Text)
   |
   v
ngrok (Public URL tunnel -> localhost:8000)
   |
   v
Backend (FastAPI - Python)
   |
   v
Qdrant (Memory Retrieval via semantic search)
   |
   v
Gemini AI (Response Generation)
   |
   v
Vapi / Web Speech API (Text-to-Speech)
   |
   v
User hears answer

Vapi Tool Flow:
User speaks -> Vapi STT -> Vapi calls ngrok_url/chat -> FastAPI processes -> Returns result -> Vapi TTS -> User hears
```

---

## 6. Tech Stack (ALL FREE)

| Layer | Technology |
|-------|-----------|
| Voice | Vapi SDK + Browser Web Speech API |
| Backend | Python (FastAPI) |
| AI Model | Gemini (Free tier) |
| Memory | Qdrant Cloud (Free tier) |
| OCR | pytesseract + Pillow |
| Frontend | HTML, CSS, JavaScript |
| Embeddings | OpenAI text-embedding-3-small |
| Tunnel | ngrok (MANDATORY for Vapi callback) |

---

## 7. User Flow

1. User clicks mic or speaks
2. Voice -> Text (Vapi / Web Speech API)
3. Vapi calls `/chat` via ngrok public URL
4. Context fetched from Qdrant (semantic search)
5. AI generates response via Gemini
6. Response -> Voice (TTS)
7. User hears answer

**ngrok is MANDATORY** - Vapi cannot reach `localhost`. You must:
1. Run `ngrok http 8000`
2. Copy the public URL
3. Set `NGROK_URL` in `.env`
4. Call `/api/vapi/setup-assistant` to configure the tool URL

---

## 8. Key Use Cases

### Use Case 1: General Help
> User: "Aaj kaunsa din hai?" (Hindi)
> AI: "Aaj Budhvar hai, 15 April 2026"

### Use Case 2: Follow-up (Memory)
> User: "What about tomorrow?"
> AI remembers context from previous question via Qdrant

### Use Case 3: Reading Text
> User: Uploads image -> "Isme kya likha hai?"
> AI reads document/image text aloud via OCR

### Use Case 4: Image Understanding
> User: Shares image
> AI describes what's in the image via Gemini Vision

### Use Case 5: Guidance
> User: "Form kaise bhare?"
> AI provides step-by-step instructions in Hindi/English

---

## 9. Success Metrics

- Voice response accuracy
- Response time (< 3 sec ideal)
- Context retention quality (via Qdrant)
- User satisfaction (demo feedback)

---

## 10. Constraints

- Requires internet connection
- Depends on API latency
- Tesseract OCR accuracy depends on image quality

---

## 11. Future Scope

- Real-time object detection (YOLO integration)
- Emergency voice alerts
- Offline mode
- Emotion detection
- Mobile app version
- Full multilingual support (10+ languages)

---

## 12. Unique Selling Points (USP)

- Voice-first (not text-first)
- Context-aware (memory powered by vector search)
- Accessibility-focused design
- Real-world impact
- Dual voice pipeline (Vapi + browser fallback)
- Multilingual (Hindi + English)

---

## 13. Demo Plan

1. User speaks in Hindi -> AI responds in Hindi
2. Ask follow-up -> shows memory retention via Qdrant
3. Use OCR -> reads text from image
4. Share image -> Gemini Vision describes it
5. Text input fallback -> shows accessibility

---

## 14. Conclusion

Sahayak AI bridges the gap between humans and technology by enabling natural, voice-based interaction, making digital systems more inclusive and empowering users with independence.

> **"We built a voice-first intelligent accessibility system with contextual memory using FREE tools."**
