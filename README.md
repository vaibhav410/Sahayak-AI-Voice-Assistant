<div align="center">

![Sahayak AI Banner](static/assets/sahayak_banner.png)

# 🎙️ Sahayak AI
### Empowering Accessibility through AI Sight and Memory

[![Python](https://img.shields.io/badge/Python-3.9+-yellow.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688.svg)](https://fastapi.tiangolo.com/)
[![Gemini](https://img.shields.io/badge/Google-Gemini_3_Flash-blue.svg)](https://deepmind.google/technologies/gemini/)
[![Vapi](https://img.shields.io/badge/Voice-Vapi_API-orange.svg)](https://vapi.ai/)
[![Qdrant](https://img.shields.io/badge/Memory-Qdrant_Vector_DB-red.svg)](https://qdrant.tech/)

**Sahayak AI** is a cutting-edge voice assistant designed to bridge the digital divide for the visually impaired. It acts as a digital companion that can **see**, **read**, and **remember**, providing real-time assistance through natural voice interaction.

</div>

---

## ✨ Core Capabilities

- **🗣️ Natural Voice Interaction**: Ultra-low latency voice-to-voice communication.
- **👁️ Intelligent Vision**: Real-time scene description and object identification using Gemini Vision.
- **📖 Robust OCR**: Instant extraction and reading of text from documents, labels, and signs.
- **🧠 Personalized Memory**: Persistent context retention—it remembers your preferences and past interactions.
- **🇮🇳 Multilingual Support**: Seamlessly communicates in both English and Hindi.

## 📺 Video Demo

> [!TIP]
> **Check out Sahayak AI in action!**
> 
> *Add your video demo link here or upload a GIF to the `static/assets/` folder to showcase the assistant's real-time interaction.*

## 🚀 Deployment (Free)

Sahayak AI is optimized for deployment on **Render.com**. Follow these steps to get your assistant live:

### 1. Push to GitHub
Ensure all your latest changes are pushed to your repository.

### 2. Setup on Render
- Create a **New > Web Service** on [Render](https://dashboard.render.com).
- Connect your GitHub repository.
- **Runtime**: Python
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python start_server.py` (or let the `Procfile` handle it).

### 3. Environment Variables
Add all keys from your local `.env` to the Render **Environment** dashboard:
- `GEMINI_API_KEY`
- `QDRANT_URL` & `QDRANT_API_KEY`
- `VAPI_API_KEY` & `ASSISTANT_ID`
- `NGROK_URL`: Set this to your new Render URL (e.g., `https://sahayak-ai.onrender.com`).

### 4. Final Activation
Once the build is successful, trigger the Vapi update by calling:
`https://your-app.onrender.com/api/vapi/setup-assistant` (via browser or CURL).

## 🛠️ Tech Stack

| Component | Technical Details |
| :--- | :--- |
| **LLM Brain** | Gemini 3 Flash Preview |
| **Vision Engine** | Gemini 1.5/2.0 Vision Pipeline |
| **Vector Memory** | Qdrant (Semantic Search) |
| **Voice API** | Vapi (Public API) |
| **Backend** | Python & FastAPI |
| **Tunnelling** | ngrok (Callback processing) |

## 🏗️ How It Works

1. **Audio Capture**: User speech is captured and streamed to Vapi.
2. **Contextual Retrieval**: The system searches **Qdrant** for relevant past memories and personal context.
3. **Cognitive Processing**: **Gemini 3** synthesizes the speech, context, and any visual data (OCR/Scene description).
4. **Natural Response**: A context-aware response is generated and delivered back via high-quality TTS.

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+
- API Keys for: Gemini, Vapi, and Qdrant.
- `ngrok` for local development.

### 2. Installation
```bash
git clone <YOUR_NEW_REPO_URL>
cd voice-ai-agent
pip install -r requirements.txt
```

### 3. Execution
1. **Start Backend**:
   ```bash
   python start_server.py
   ```
2. **Launch ngrok**:
   ```bash
   ngrok http 8000
   ```
3. **Configure Environment**: Update `.env` with your API keys and the ngrok URL.
4. **Final Sync**: 
   `curl -X POST http://localhost:8000/api/vapi/setup-assistant`

---

<div align="center">
Built with ❤️ for a more inclusive world.
</div>
