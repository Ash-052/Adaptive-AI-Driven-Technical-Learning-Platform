from fastapi import APIRouter, HTTPException
from app.services.topic_mastery_service import get_user_progress
from app.services.user_service import get_user_stats, get_submission_history

router = APIRouter()

@router.get("/{user_id}/progress")
async def get_combined_progress(user_id: str):
    try:
        return get_user_progress(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/profile")
async def user_profile(user_id: str):
    return get_user_stats(user_id)

@router.get("/{user_id}/history")
async def user_history(user_id: str):
    return {"history": get_submission_history(user_id)}

@router.get("/{user_id}/analytics")
async def user_analytics(user_id: str):
    return {
        "progress": get_user_progress(user_id),
        "stats": get_user_stats(user_id)
    }
