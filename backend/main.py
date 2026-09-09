from fastapi import FastAPI
from config import settings

app = FastAPI()


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "groq_key_configured": bool(settings.GROQ_API_KEY),
    }
