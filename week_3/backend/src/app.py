import os
import sys
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

sys.path.append(os.path.join(os.path.dirname(__file__), "week_2"))
from find_skill_gaps import find_skill_gaps
from prompt_model import prompt_model, ModelConfig

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")

app = FastAPI()

# allow requests from any origin * (diff port = diff origins)
# allows frontend (8000) communicate w backend (8001)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = os.getenv("DB_NAME")
DB_PATH = os.path.join(os.path.dirname(__file__), "week_2", "data", DB_NAME)
MODEL = os.getenv("MODEL")

MODEL_USAGE = """Hi! I'm a resume assistant analyser. Here's how to use me:

    1. Upload your resume file (.pdf, .docx, or .txt)
    2. Optionally type a message and hit send

    Things I can do:
    - Find skill gaps based on job market data
    - Summarise your resume
    - Answer general questions
"""


class ChatRequest(BaseModel):
    message: str = ""
    file_text: str = ""


def detect_task(message: str) -> str:
    """Detect what the user wants based on their input message"""

    prompt = f"""
        Classify the following user message into exactly one of these categories:
        - "skill_gap": user wants to find skill gaps, missing skills, or skills to improve
        - "summary": user wants a summary or overview of their resume
        - "general": anything else

        User message: "{message}"

        Reply with ONLY one word: skill_gap, summary, or general
    """

    result = prompt_model(MODEL, prompt).strip().lower()

    if "skill_gap" in result:
        return "skill_gap"
    elif "summary" in result:
        return "summary"
    else:
        return "general"
    

def summarise_resume(file_text: str, message: str) -> str:
    """Generate a resume summary using the model"""

    prompt = f"""
        You are a professional resume reviewer.
        The user has uploaded their resume and asked: "{message}"

        Please provide a clear, concise summary of the resume below.
        Cover: key skills, experience, and notable achievements.

        ## RESUME
        {file_text}
    """
    return prompt_model(MODEL, prompt, ModelConfig(temperature=0.7))


@app.post("/chat")
async def chat(req: ChatRequest):
    # no file attached (general chat)
    if not req.file_text.strip():
        reply = prompt_model(MODEL, req.message, ModelConfig(temperature=0.7))
        return JSONResponse(content={"reply": reply})

    # file attached --> we detect what task the user wants    
    task = detect_task(req.message) if req.message.strip() else "skill_gap"

    if task == "summary":
        reply = summarise_resume(req.file_text, req.message)
        return JSONResponse(content={"reply": reply})
    
    elif task == "skill_gap":
        # write file_text to temp file so find_skill_gaps can read it
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".txt", mode="w", encoding="utf-8"
        ) as tmp:
            tmp.write(req.file_text)
            tmp_resume_path = tmp.name

        try:
            result = find_skill_gaps(tmp_resume_path, DB_PATH, req.message)

            if result is None or not result.gaps:
                reply = "No skill gaps found, or the resume could not be processed."
            else:
                gaps_list = "\n".join(f"• {gap}" for gap in result.gaps)
                reply = f"Based on your resume, here are your skill gaps:\n\n{gaps_list}"
        finally:
            os.unlink(tmp_resume_path)
        return JSONResponse(content={"reply": reply})
    
    else:
        # general question but with file context
        prompt = f"""
            The user has uploaded a resume and asked: "{req.message}"
            Use the resume below as context to answer.

            ## RESUME
            {req.file_text}
        """
        reply = prompt_model(MODEL, prompt, ModelConfig(temperature=0.7))
        return JSONResponse(content={"reply": reply})