import time
from fastapi import APIRouter, HTTPException
from backend.models import TriageRequest, TriageResponse
from backend.agent import run_triage

router = APIRouter()


@router.post("/triage", response_model=TriageResponse)
async def triage_message(request: TriageRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    start = time.monotonic()
    try:
        result = await run_triage(
            message=request.message,
            sender_name=request.sender_name or "Unknown",
            sender_email=request.sender_email or "",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    elapsed_ms = int((time.monotonic() - start) * 1000)

    return TriageResponse(
        urgency=result["urgency"],
        urgency_score=result["urgency_score"],
        intent=result["intent"],
        entities=result["entities"],
        draft_response=result["draft_response"],
        summary=result["summary"],
        processing_time_ms=elapsed_ms,
    )


@router.get("/health")
async def health():
    return {"status": "ok"}
