from api.parse_routes import router as parse_router
from fastapi import FastAPI
from config import settings

app = FastAPI()
app.include_router(parse_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "groq_key_configured": bool(settings.GROQ_API_KEY),
    }
