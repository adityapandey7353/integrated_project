import os
import json
import re
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from backend.models import ExtractedEntities
from backend.config import GROQ_API_KEY, MODEL_AGENT
def get_llm():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in config")

    return ChatGroq(
        model=MODEL_AGENT,
        api_key=GROQ_API_KEY,
        temperature=0.2,
    )


# ── 1. Urgency + Intent Classification ──────────────────────────────────────
CLASSIFY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an agriculture support triage specialist.
Analyse the incoming farmer/field message and return ONLY a JSON object (no markdown, no extra text) with exactly these keys:
{{
  "urgency": "HIGH" | "MEDIUM" | "LOW",
  "urgency_score": <integer 1-10>,
  "intent": "<concise intent label, e.g. Pest Report, Crop Disease, Irrigation Issue, Loan Query, Weather Damage, General Query>"
}}

Rules:
- HIGH (score 8-10): immediate crop loss risk, disease outbreak, flooding, chemical poisoning
- MEDIUM (score 4-7): moderate pest pressure, equipment breakdown, water scarcity
- LOW (score 1-3): general questions, status updates, documentation requests
"""),
    ("human", "Message: {message}"),
])

# ── 2. Named Entity Recognition ──────────────────────────────────────────────
NER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an agriculture NER engine.
Extract entities from the farmer message and return ONLY a JSON object (no markdown):
{{
  "farmer_id": "<farmer/account ID or null>",
  "crop_type": "<crop name or null>",
  "location": "<village/district/state or null>",
  "dates": ["<any dates or time references as strings>"],
  "issue_keywords": ["<key problem words>"]
}}
"""),
    ("human", "Message: {message}"),
])

# ── 3. Draft Response Generator ──────────────────────────────────────────────
DRAFT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful agriculture support officer writing an official response.
Given the farmer's message, urgency level, and intent, draft a professional, empathetic reply in 3-4 sentences.
- Acknowledge the issue clearly.
- Provide an immediate actionable step or reassurance.
- Mention escalation path for HIGH urgency.
- Close warmly.
Write ONLY the draft reply text, no labels or preamble.
"""),
    ("human", """Farmer Message: {message}
Urgency: {urgency}
Intent: {intent}
Sender: {sender_name}"""),
])

# ── 4. Summary ───────────────────────────────────────────────────────────────
SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Summarise the farmer's issue in one crisp sentence (max 20 words) for an internal dashboard."),
    ("human", "{message}"),
])


def _safe_json(text: str) -> dict:
    """Strip markdown fences and parse JSON safely."""
    text = re.sub(r"```(?:json)?", "", text).strip().strip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Attempt to extract first {...} block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {}


async def run_triage(message: str, sender_name: str, sender_email: str) -> dict:
    llm = get_llm()
    parser = StrOutputParser()

    # Run classification
    classify_chain = CLASSIFY_PROMPT | llm | parser
    classify_raw = await classify_chain.ainvoke({"message": message})
    classify_data = _safe_json(classify_raw)

    urgency = classify_data.get("urgency", "MEDIUM")
    urgency_score = int(classify_data.get("urgency_score", 5))
    intent = classify_data.get("intent", "General Query")

    # Run NER
    ner_chain = NER_PROMPT | llm | parser
    ner_raw = await ner_chain.ainvoke({"message": message})
    ner_data = _safe_json(ner_raw)

    entities = ExtractedEntities(
        farmer_id=ner_data.get("farmer_id"),
        crop_type=ner_data.get("crop_type"),
        location=ner_data.get("location"),
        dates=ner_data.get("dates", []),
        issue_keywords=ner_data.get("issue_keywords", []),
    )

    # Draft response
    draft_chain = DRAFT_PROMPT | llm | parser
    draft = await draft_chain.ainvoke({
        "message": message,
        "urgency": urgency,
        "intent": intent,
        "sender_name": sender_name,
    })

    # Summary
    summary_chain = SUMMARY_PROMPT | llm | parser
    summary = await summary_chain.ainvoke({"message": message})

    return {
        "urgency": urgency,
        "urgency_score": urgency_score,
        "intent": intent,
        "entities": entities,
        "draft_response": draft.strip(),
        "summary": summary.strip(),
    }
