import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from config import settings
from parsers.llm_client import GroqLLMClient
from parsers.resume_parser import extract_text, structure_resume, ResumeParseError
from parsers.jd_parser import structure_jd, JDParseError

router = APIRouter(prefix="/parse", tags=["parsing"])

_llm_client = None


def get_llm_client() -> GroqLLMClient:
    global _llm_client
    if _llm_client is None:
        settings.validate()
        _llm_client = GroqLLMClient(api_key=settings.GROQ_API_KEY)
    return _llm_client


@router.post("/resume")
async def parse_resume(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".pdf", ".docx"):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        raw_text = extract_text(tmp_path)
        structured = structure_resume(raw_text, get_llm_client(), settings.GROQ_MODEL)
    except ResumeParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return {"structured": structured}


@router.post("/jd")
async def parse_jd(jd_text: str = Form(...)):
    try:
        structured = structure_jd(jd_text, get_llm_client(), settings.GROQ_MODEL)
    except JDParseError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"structured": structured}
