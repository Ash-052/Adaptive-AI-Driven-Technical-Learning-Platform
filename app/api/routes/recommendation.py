from fastapi import APIRouter, HTTPException
from app.services.recommendation_service import get_next_problem

router = APIRouter()

@router.get("/{user_id}")
async def get_user_recommendation(user_id: str):
    """
    Returns the recommended next topic and difficulty for a specific user.
    """
    try:
        recommendation = await get_next_problem(user_id)
        if not recommendation:
            raise HTTPException(status_code=404, detail="Could not generate recommendation")
        return recommendation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
