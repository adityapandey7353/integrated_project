# ⟁ AgriTriage — Agriculture Support Intelligence

A unified AI platform for agriculture support combining an **Agentic AI triage pipeline** (LangChain + Groq) with a **GenAI quiz system** (FarmWise). Built with FastAPI on the backend and a dark-themed web frontend.

---

## 📁 Project Structure

```
integrated-project/
│
├── backend/
│   ├── app.py              # FastAPI entry point — mounts all routers
│   ├── config.py           # Centralised env vars + Groq & Supabase clients
│   ├── agent.py            # Agentic AI pipeline (classify → NER → draft → summary)
│   ├── routes.py           # POST /api/triage
│   ├── genai_routes.py     # GET/POST /api/genai/* (quiz, ask, leaderboard)
│   ├── models.py           # Pydantic request/response schemas
│   └── __init__.py
│
├── frontend/
│   ├── index.html          # Main UI shell (Triage + Quiz tabs)
│   ├── app.js              # Triage logic, tab switching, animations
│   ├── style.css           # Dark industrial design system
│   └── genaiindex.html     # FarmWise Quiz UI (loaded in iframe)
│
├── .env                    # API keys (Groq + Supabase) — never commit this
├── pyproject.toml          # Dependencies managed by uv
├── uv.lock                 # Auto-generated lockfile
└── README.md
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- A [Groq](https://console.groq.com/) API key
- A [Supabase](https://supabase.com/) project (for quiz leaderboard)

### 2. Clone & Install

```bash
git clone <your-repo-url>
cd integrated-project

# Install dependencies via uv
uv sync
```

### 3. Configure Environment

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

### 4. Set Up Supabase Table

Run this SQL in your Supabase SQL editor to create the leaderboard table:

```sql
create table quiz_sessions (
  id          uuid primary key default gen_random_uuid(),
  player_name text,
  score       int,
  total       int,
  percentage  int,
  topic       text,
  difficulty  text,
  wrong_topics text[],
  played_at   timestamptz default now()
);
```

### 5. Run the Backend

```bash
uv run uvicorn backend.app:app --reload
```

The API will be available at `http://localhost:8000`.

### 6. Open the Frontend

Open `frontend/index.html` directly in your browser, or serve it with any static file server:

```bash
# Using Python's built-in server from the frontend/ directory
cd frontend
python -m http.server 5500
```

Then visit `http://localhost:5500`.

---

## 🔌 API Reference

### Agentic Triage

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/triage` | Run full triage pipeline on a farmer message |
| `GET`  | `/api/health` | Health check |

**Triage Request Body:**
```json
{
  "message": "My paddy field is flooded near Hoshangabad. Farmer ID: F-1923.",
  "sender_name": "Ramesh Kumar",
  "sender_email": "ramesh@example.com"
}
```

**Triage Response:**
```json
{
  "urgency": "HIGH",
  "urgency_score": 9,
  "intent": "Flood Emergency",
  "entities": {
    "farmer_id": "F-1923",
    "crop_type": "paddy",
    "location": "Hoshangabad",
    "dates": [],
    "issue_keywords": ["flooded", "paddy field"]
  },
  "draft_response": "Dear Ramesh, we have received your urgent report...",
  "summary": "Farmer F-1923 reports flooded paddy field in Hoshangabad.",
  "processing_time_ms": 1842
}
```

### GenAI Quiz

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/genai/questions` | Fetch quiz questions (`?topic=&difficulty=&count=5`) |
| `POST` | `/api/genai/evaluate` | Submit answer, get AI explanation |
| `POST` | `/api/genai/ask` | Ask a free-form farming question |
| `POST` | `/api/genai/session/save` | Save quiz session to Supabase |
| `GET`  | `/api/genai/leaderboard` | Fetch top 10 scores |
| `GET`  | `/api/genai/topics` | List all available quiz topics |
| `GET`  | `/api/genai/tips` | List all farming tips |

---

## 🤖 AI Pipeline (Agentic Triage)

Each message submitted to `/api/triage` runs through 4 sequential LLM calls via LangChain + Groq:

```
Message In
    │
    ▼
[1] Urgency + Intent Classification
    → urgency: HIGH / MEDIUM / LOW
    → urgency_score: 1–10
    → intent: "Pest Report", "Flood Emergency", etc.
    │
    ▼
[2] Named Entity Recognition (NER)
    → farmer_id, crop_type, location, dates, issue_keywords
    │
    ▼
[3] Draft Response Generation
    → Professional, empathetic reply in 3–4 sentences
    │
    ▼
[4] One-Line Summary
    → For internal dashboard display
    │
    ▼
Structured JSON Response
```

**Models used:**
- Triage agent: `llama-3.1-8b-instant` (fast, low-latency)
- GenAI quiz/ask: `llama-3.3-70b-versatile` (higher quality)

---

## 🌾 Frontend Features

### Triage Tab
- Submit farmer messages with sender name/email
- 4-step animated loading pipeline display
- Urgency banner with animated score ring (HIGH / MEDIUM / LOW)
- Extracted entity cards (Farmer ID, Crop, Location, Dates, Keywords)
- AI-generated draft response with copy & send-via-email buttons
- Quick sample messages for demo/testing

### Quiz Tab (FarmWise)
- Topic & difficulty filtering
- Per-question AI explanations via Groq
- Animated score ring on results screen
- Personalized AI feedback summary
- Leaderboard backed by Supabase
- Free-form "Ask AI" farming Q&A

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend framework | FastAPI |
| LLM provider | Groq (Llama 3) |
| Agent orchestration | LangChain |
| Database | Supabase (PostgreSQL) |
| Package manager | uv |
| Frontend | Vanilla HTML/CSS/JS |
| Fonts | Syne, DM Sans, DM Mono, Playfair Display |

---

## 🔧 Development

### Running with auto-reload (recommended)

```bash
uv run uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

### Interactive API docs

FastAPI auto-generates docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### CORS

CORS is currently open (`allow_origins=["*"]`). Before deploying to production, restrict this in `backend/app.py`:

```python
allow_origins=["https://your-frontend-domain.com"]
```

---

## 📝 Notes

- The `.env` file is excluded from version control. Never commit API keys.
- The quiz question pool in `genai_routes.py` is static by default — extend `QUIZ_QUESTIONS` and `FARMING_TIPS` lists to add more content.
- The frontend communicates with the backend at `http://localhost:8000` by default. This is configurable via the **API Endpoint** field in the Triage UI.

---

## 📄 License

MIT
