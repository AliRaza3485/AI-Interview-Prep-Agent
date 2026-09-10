from api.analyze_routes import router as analyze_router
from api.parse_routes import router as parse_router
from api.interview_routes import router as interview_router
from fastapi import FastAPI
from config import settings
from session_store import init_db

app = FastAPI()

# App start hote hi sessions.db aur uska table ban jaye, agar pehle se nahi hai
init_db()

app.include_router(parse_router)
app.include_router(analyze_router)
app.include_router(interview_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "groq_key_configured": bool(settings.GROQ_API_KEY),
    }
