# backend/config.py

import os
from dotenv import load_dotenv
from groq import Groq
from supabase import create_client, Client

load_dotenv()

# ─── ENV ───────────────────────────────────────────────

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")


# ─── LLM ───────────────────────────────────────────────

def get_groq_client() -> Groq:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set")
    return Groq(api_key=GROQ_API_KEY)


# ─── SUPABASE (ONLY FOR GENAI) ─────────────────────────

def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase config missing")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ─── MODELS ────────────────────────────────────────────

MODEL_AGENT = "llama-3.1-8b-instant"
MODEL_GENAI = "llama-3.3-70b-versatile"