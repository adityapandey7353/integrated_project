# backend/genai_routes.py

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import random
import os
from datetime import datetime

from groq import Groq
from supabase import create_client, Client
from dotenv import load_dotenv

from backend.config import get_groq_client, get_supabase, MODEL_GENAI

load_dotenv()

router = APIRouter()

# ─── Clients ───────────────────────────────────────────
groq_client = get_groq_client()
supabase = get_supabase()
GROQ_MODEL = MODEL_GENAI

# ─── Data Models ───────────────────────────────────────

class AnswerRequest(BaseModel):
    question_id: str
    answer: str

class SaveSessionRequest(BaseModel):
    player_name: Optional[str] = "Anonymous"
    score: int
    total: int
    topic: Optional[str] = "Mixed"
    difficulty: Optional[str] = "Mixed"
    wrong_topics: List[str] = []

class AskRequest(BaseModel):
    question: str


# ─── Static Data (same as your Flask) ───────────────────

FARMING_TIPS = [
    {"id": "tip_001", "topic": "Soil Health", "content": "Crop rotation prevents nutrient depletion and reduces pest buildup."},
    {"id": "tip_002", "topic": "Irrigation", "content": "Drip irrigation delivers water directly to plant roots, saving water."},
]

QUIZ_QUESTIONS = [
    {
        "id": "q001",
        "topic": "Soil Health",
        "question": "What is the benefit of rotating legumes?",
        "options": {"A": "Water saving", "B": "Nitrogen fixing", "C": "Pest removal", "D": "pH control"},
        "correct_answer": "B",
        "tip_id": "tip_001",
        "difficulty": "medium"
    }
]

# ─── Helper ────────────────────────────────────────────

def get_tip_for_question(tip_id: str) -> str:
    for tip in FARMING_TIPS:
        if tip["id"] == tip_id:
            return tip["content"]
    return ""


# ─── Routes ────────────────────────────────────────────

@router.get("/questions")
def get_questions(
    topic: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    count: int = 5
):
    pool = QUIZ_QUESTIONS.copy()

    if topic:
        pool = [q for q in pool if q["topic"] == topic]

    if difficulty:
        pool = [q for q in pool if q["difficulty"] == difficulty]

    selected = random.sample(pool, min(count, len(pool)))

    safe = [{k: v for k, v in q.items() if k != "correct_answer"} for q in selected]

    return {"questions": safe, "total": len(selected)}


@router.post("/evaluate")
def evaluate_answer(data: AnswerRequest):
    question = next((q for q in QUIZ_QUESTIONS if q["id"] == data.question_id), None)

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    user_answer = data.answer.strip().upper()
    is_correct = user_answer == question["correct_answer"]

    tip_content = get_tip_for_question(question["tip_id"])

    prompt = f"""
    Question: {question['question']}
    Correct Answer: {question['correct_answer']}
    User Answer: {user_answer}
    Tip: {tip_content}

    Explain briefly.
    """

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )

    return {
        "is_correct": is_correct,
        "correct_answer": question["correct_answer"],
        "explanation": response.choices[0].message.content
    }


@router.post("/ask")
def ask_question(data: AskRequest):
    if not data.question:
        raise HTTPException(status_code=400, detail="No question provided")

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{
            "role": "user",
            "content": data.question
        }],
        max_tokens=200
    )

    return {"answer": response.choices[0].message.content}


@router.post("/session/save")
def save_session(data: SaveSessionRequest):
    pct = round((data.score / data.total) * 100) if data.total > 0 else 0

    record = {
        "player_name": data.player_name,
        "score": data.score,
        "total": data.total,
        "percentage": pct,
        "topic": data.topic,
        "difficulty": data.difficulty,
        "wrong_topics": data.wrong_topics,
        "played_at": datetime.utcnow().isoformat()
    }

    result = supabase.table("quiz_sessions").insert(record).execute()

    return {"saved": True, "id": result.data[0]["id"] if result.data else None}


@router.get("/leaderboard")
def get_leaderboard():
    result = supabase.table("quiz_sessions")\
        .select("*")\
        .order("percentage", desc=True)\
        .limit(10)\
        .execute()

    return {"leaderboard": result.data}


@router.get("/topics")
def get_topics():
    topics = sorted(list(set(q["topic"] for q in QUIZ_QUESTIONS)))
    return {"topics": topics}


@router.get("/tips")
def get_tips():
    return {"tips": FARMING_TIPS}