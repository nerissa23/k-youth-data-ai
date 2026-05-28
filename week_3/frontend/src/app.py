import os
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")

app = FastAPI()
app.mount("/assets", StaticFiles(directory="src/assets"), name="assets")
app.mount("/styles", StaticFiles(directory="src/styles"), name="styles")

# config jinja2 templates directory
templates = Jinja2Templates(directory="src/templates")


# html-rendering routes
@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    context = {"name": "Resume Helper", "backend_url": os.getenv("BACKEND_URL")}
    return templates.TemplateResponse(request, "chat_page.html", context)
