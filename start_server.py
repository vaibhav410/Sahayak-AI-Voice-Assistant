import uvicorn

print("=" * 60)
print("SAHAYAK AI - Voice Accessibility Assistant")
print("=" * 60)
print("Server running at: http://localhost:8000")
print()
print("HACKATHON STACK:")
print("  - Gemini AI     : Smart responses")
print("  - Qdrant       : Memory & context")
print("  - Vapi         : Voice calls")
print("  - Ngrok        : Webhook for Vapi")
print()
print("NEXT STEPS:")
print("  1. Install Qdrant: docker run -p 6333:6333 qdrant/qdrant")
print("  2. Setup Ngrok:   ngrok http 8000")
print("  3. Add NGROK_URL to .env")
print("  4. Setup Vapi:    curl -X POST http://localhost:8000/api/vapi/setup-assistant")
print("=" * 60)
print()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
