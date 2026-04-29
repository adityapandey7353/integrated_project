# backend/app.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
# Existing agentic AI routes
from backend.routes import router as triage_router

# NEW: GenAI routes
from backend.genai_routes import router as genai_router


app = FastAPI(
    title="Agri AI Unified Backend",
    description="Combined Agentic AI + GenAI system",
    version="2.0.0",
)
# ─── Serve Frontend ─────────────────────────────

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend')

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ─── CORS (important for frontend) ──────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # later restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ───────────────────────────────────────────

# Agentic AI (existing)
app.include_router(triage_router, prefix="/api")

# GenAI (NEW)
app.include_router(genai_router, prefix="/api/genai")


# ─── Root Check ────────────────────────────────────────
@app.get("/")
async def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# ─── Health Check ──────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}