from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db.supabase import supabase
from app.services.code_execution_service import execute_user_code
from app.services.topic_mastery_service import update_mastery
from app.services.skill_service import update_global_skill
from datetime import datetime
import json

router = APIRouter()

class SubmissionRequest(BaseModel):
    user_id: str
    problem_id: str
    code: str

@router.post("/submit")
async def submit_code(request: SubmissionRequest):
    """
    Executes user code, calculates accuracy, and saves results to DB.
    """
    try:
        # 1. Fetch Problem
        prob_res = supabase.table('problems').select('*').eq('id', request.problem_id).single().execute()
        if not prob_res.data:
            raise HTTPException(status_code=404, detail="Problem not found")
        
        problem = prob_res.data
        test_cases_str = problem.get('test_cases', '[]')
        test_cases = json.loads(test_cases_str) if isinstance(test_cases_str, str) else test_cases_str
        
        # 2. Execute Code
        exec_res = execute_user_code(request.code, test_cases)
        accuracy = exec_res['passed'] / exec_res['total'] if exec_res['total'] > 0 else 0
        
        # 3. Save to user_attempts
        submission_data = {
            "user_id": request.user_id,
            "problem_id": request.problem_id,
            "topic": problem['topic'],
            "difficulty": problem['difficulty'],
            "accuracy": accuracy,
            "time_taken": 60, # Mocked or taken from front if available
            "attempts": 1,
            "created_at": datetime.now().isoformat()
        }
        supabase.table('user_attempts').insert(submission_data).execute()
        
        # 4. Update Models
        update_mastery(request.user_id, problem['topic'], accuracy, 60, 1)
        update_global_skill(request.user_id)
        
        return {
            "success": True,
            "passed": exec_res['passed'],
            "total": exec_res['total'],
            "accuracy": accuracy,
            "results": exec_res['results']
        }
    except Exception as e:
        print(f"SUBMISSION ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
