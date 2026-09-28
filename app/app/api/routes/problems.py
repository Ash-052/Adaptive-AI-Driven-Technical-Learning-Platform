from fastapi import APIRouter, HTTPException
from app.services.problem_service import get_problem_for_user, get_problem_by_id

router = APIRouter()

@router.get("/next/{user_id}")
async def get_next_problem_for_user(user_id: str):
    """
    Returns the next recommended problem for the user.
    """
    try:
        problem, recommendation = await get_problem_for_user(user_id)
        if not problem:
            raise HTTPException(status_code=404, detail="No available problems found for the user.")
        
        return {
            "problem": problem,
            "recommendation": {
                "topic": recommendation["topic"],
                "difficulty": recommendation["difficulty"],
                "confidence": recommendation["confidence"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{problem_id}")
async def get_problem_details(problem_id: str):
    """
    Returns the details of a specific problem.
    """
    try:
        problem = await get_problem_by_id(problem_id)
        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found.")
        return problem
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
