import json
import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.db.supabase import supabase
from app.services.ai_tutor_service import tutor_service

logger = logging.getLogger(__name__)
router = APIRouter()

class TutorRequest(BaseModel):
    problem_id: Optional[str] = None
    user_code: Optional[str] = ""
    topic: Optional[str] = ""
    difficulty: Optional[int] = 1
    skill_level: Optional[float] = 0.5
    solution_code: Optional[str] = ""

def _get_problem_dict(request: TutorRequest) -> dict:
    if request.problem_id:
        try:
            res = supabase.table('problems').select('*').eq('id', request.problem_id).single().execute()
            data = res.data if hasattr(res, 'data') else res
            if data and isinstance(data, dict):
                prob = dict(data)
                for field in ['hints', 'test_cases']:
                    if isinstance(prob.get(field), str):
                        try:
                            prob[field] = json.loads(prob[field])
                        except Exception:
                            pass
                return prob
        except Exception as e:
            logger.warning(f"Failed to fetch problem {request.problem_id}: {e}")

    topic = request.topic or "basics"
    diff = request.difficulty or 1
    return {
        "title": f"{topic.capitalize()} Challenge Level {diff}",
        "description": f"Solve this {topic} problem (Difficulty Level {diff}). Implement solution() function.",
        "topic": topic,
        "difficulty": diff,
        "constraints": "O(n) time complexity",
        "hints": []
    }

@router.post("/hint")
async def get_hint(request: TutorRequest):
    problem = _get_problem_dict(request)
    return tutor_service.generate_hint(
        problem, 
        request.user_code or "", 
        request.topic or problem.get("topic", "basics"), 
        request.difficulty or problem.get("difficulty", 1)
    )

@router.post("/explain")
async def get_explanation(request: TutorRequest):
    problem = _get_problem_dict(request)
    solution_to_explain = request.solution_code or problem.get("solution") or request.user_code or ""
    return tutor_service.explain_solution(problem, solution_to_explain, request.skill_level or 0.5)

@router.post("/analyze")
async def get_analysis(request: TutorRequest):
    problem = _get_problem_dict(request)
    return tutor_service.analyze_code(problem, request.user_code or "")

