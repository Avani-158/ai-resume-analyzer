"""
main.py — FastAPI application entry point.
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import google.generativeai as genai
from dotenv import load_dotenv

from ml_service import analyze_resume, get_available_roles

load_dotenv()

app = FastAPI(
    title="AI Resume Analyzer API",
    version="1.0.0",
    description="Production-level resume analysis powered by ML",
)

# ─── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", os.getenv("FRONTEND_URL", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-resume-analyzer"}


@app.post("/analyze-resume")
async def analyze_resume_endpoint(
    file: UploadFile = File(...),
    target_role: str = Form(...),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        result = analyze_resume(pdf_bytes, target_role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    return JSONResponse(content=result)


@app.get("/roles")
async def roles():
    try:
        return {"roles": get_available_roles()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load roles: {str(e)}")


# ─── Chat ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
class ChatRequest(BaseModel):
    query: str
    resume_context: dict = {}


@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """
    Rule-based career assistant. Replace with an LLM call (OpenAI / Gemini)
    by swapping the body of `generate_reply` below.
    """
    reply = generate_reply(req.query, req.resume_context)
    return {"reply": reply}


def generate_reply(query: str, ctx: dict) -> str:
    if not GEMINI_API_KEY:
        return _fallback_chat_reply(query, ctx)

    skills = ctx.get("skills", [])
    missing = ctx.get("missing_skills", [])
    target_role = ctx.get("target_role", "your target role")
    ats = ctx.get("ats_score", 0)
    predicted_roles = ctx.get("predicted_roles", [])
    suggestions = ctx.get("suggestions", [])

    system_prompt = (
        "You are an AI career assistant for resume analysis. "
        "Be concise, practical, and specific. "
        "Use the provided resume context only; do not invent facts. "
        "Give actionable next steps in bullet points when helpful."
    )

    user_prompt = f"""
User question:
{query}

Resume context:
- target_role: {target_role}
- ats_score: {ats}
- skills: {skills}
- missing_skills: {missing}
- predicted_roles: {predicted_roles}
- suggestions: {suggestions}
"""

    try:
        model = genai.GenerativeModel("gemini-flash-latest")
        response = model.generate_content(
            [system_prompt, user_prompt],
            generation_config={
                "temperature": 0.4,
                "max_output_tokens": 500,
            },
        )
        text = (response.text or "").strip()
        return text if text else "I could not generate a response right now."
    except Exception as e:
        return _fallback_chat_reply(query, ctx, error=f"Chat service error: {str(e)}")


def _fallback_chat_reply(query: str, ctx: dict, error: str | None = None) -> str:
    """
    Deterministic assistant fallback so chat remains useful without Gemini.
    """
    q = query.lower()
    skills = [str(s) for s in ctx.get("skills", [])]
    missing = [str(s) for s in ctx.get("missing_skills", [])]
    target_role = str(ctx.get("target_role", "your target role"))
    ats = ctx.get("ats_score", 0)
    predicted_roles = ctx.get("predicted_roles", [])[:3]

    if "missing" in q or "skill" in q:
        if missing:
            return (
                f"For {target_role}, your biggest gaps are: {', '.join(missing[:6])}. "
                "Prioritize 1-2 skills first, then add a project that demonstrates each one."
            )
        return (
            f"You are covering the key listed skills for {target_role}. "
            "Next step is to strengthen impact bullets with measurable outcomes."
        )

    if "ats" in q or "score" in q or "improve" in q:
        return (
            f"Your ATS score is {ats}/100. Improve it by: "
            "1) adding exact target-role keywords, "
            "2) quantifying project/work outcomes, "
            "3) keeping clear section headers (Projects, Experience, Skills, Education)."
        )

    top_roles = ", ".join(
        f"{r.get('role', 'Role')} ({r.get('score', 0)}%)"
        for r in predicted_roles
    ) or "No role predictions available yet"
    skill_preview = ", ".join(skills[:8]) if skills else "No skills extracted yet"
    prefix = f"{error}. " if error else ""
    return (
        f"{prefix}Here is your current snapshot for {target_role}: "
        f"ATS {ats}/100, top roles: {top_roles}. "
        f"Detected skills: {skill_preview}. "
        "Ask me about missing skills, ATS improvement, or project ideas."
    )