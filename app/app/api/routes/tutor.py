from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.ai_tutor_service import tutor_service

router = APIRouter()

class TutorRequest(BaseModel):
    problem_id: str
    user_code: Optional[str] = ""
    topic: Optional[str] = ""
    difficulty: Optional[int] = 1
    skill_level: Optional[float] = 0.5
    solution_code: Optional[str] = ""

@router.post("/hint")
async def get_hint(request: TutorRequest):
    # In a real app, you'd fetch the problem from DB here using problem_id
    # For now, we'll assume a placeholder problem object
    problem = {"title": "Active Problem", "description": "Analyzing your current code..."}
    return tutor_service.generate_hint(problem, request.user_code, request.topic, request.difficulty)

@router.post("/explain")
async def get_explanation(request: TutorRequest):
    problem = {"title": "Active Problem"}
    return tutor_service.explain_solution(problem, request.solution_code, request.skill_level)

@router.post("/analyze")
async def get_analysis(request: TutorRequest):
    problem = {"title": "Active Problem"}
    return tutor_service.analyze_code(problem, request.user_code)
