from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import topic_mastery_service

router = APIRouter()

class MasteryUpdateRequest(BaseModel):
    user_id: str
    topic: str
    success: float
    time: float
    attempts: int

@router.get("/{user_id}", tags=["Mastery"])
def get_mastery_profile(user_id: str):
    mastery = topic_mastery_service.get_user_mastery(user_id)
    if not mastery:
        raise HTTPException(status_code=404, detail="User not found or has no mastery data.")
    return mastery

@router.post("/update", tags=["Mastery"])
def update_user_mastery(request: MasteryUpdateRequest):
    updated = topic_mastery_service.update_mastery(
        user_id=request.user_id,
        topic=request.topic,
        success=request.success,
        time_taken=request.time,
        attempts=request.attempts
    )
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update mastery.")
    return {"status": "success", "updated_mastery": updated}

@router.get("/weak/{user_id}", tags=["Mastery"])
def get_user_weak_topics(user_id: str):
    topics = topic_mastery_service.get_weak_topics(user_id)
    return {"user_id": user_id, "weak_topics": topics}

@router.get("/strong/{user_id}", tags=["Mastery"])
def get_user_strong_topics(user_id: str):
    topics = topic_mastery_service.get_strong_topics(user_id)
    return {"user_id": user_id, "strong_topics": topics}

@router.post("/initialize/{user_id}", tags=["Mastery"])
def initialize_mastery(user_id: str):
    """Endpoint to explicitly initialize a user's mastery topics."""
    result = topic_mastery_service.initialize_user_mastery(user_id)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to initialize mastery.")
    return {"status": "success", "message": f"Mastery for user {user_id} initialized."}
