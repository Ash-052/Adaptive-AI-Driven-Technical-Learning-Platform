from app.db.supabase import supabase
from app.services.topic_mastery_service import update_mastery
from datetime import datetime
import json
from app.services.executor_service import run_code
from app.services.skill_service import update_global_skill

async def process_submission(user_id: str, problem_id: str, code: str, topic: str, difficulty: int, time_taken: float, attempts: int):
    """
    Processes a new submission: Executes code, saves to DB, and updates mastery.
    """
    try:
        # 1. Fetch Problem Test Cases
        print(f"FETCHING PROBLEM: {problem_id}")
        prob_res = supabase.table('problems').select('test_cases').eq('id', problem_id).single().execute()
        
        # Handle the tuple pattern if necessary
        if isinstance(prob_res, tuple):
             prob_data = prob_res[0][1] if len(prob_res[0]) > 1 else None
        else:
             prob_data = prob_res.data
             
        if not prob_data:
            return {"status": "error", "message": "Problem not found in database"}
        
        test_cases_str = prob_data.get('test_cases', '[]')
        print(f"TEST CASES TYPE: {type(test_cases_str)}")
        
        # Parse JSON if stored as string
        if isinstance(test_cases_str, str):
            try:
                test_cases = json.loads(test_cases_str)
            except:
                # If it fails, maybe it's already a list representation?
                test_cases = eval(test_cases_str) if test_cases_str.startswith('[') else []
        else:
            test_cases = test_cases_str

        # 2. Execute Code
        print("STARTING EXECUTION...")
        execution_result = run_code(code, test_cases)
        accuracy = execution_result['passed'] / execution_result['total'] if execution_result['total'] > 0 else 0

        # 3. Save Attempt to DB
        submission_data = {
            "user_id": user_id,
            "problem_id": problem_id,
            "topic": topic,
            "accuracy": accuracy,
            "time_taken": time_taken,
            "attempts": attempts,
            "difficulty": difficulty,
            "created_at": datetime.now().isoformat()
        }
        supabase.table('user_attempts').insert(submission_data).execute()
        
        # 4. Update Topic Mastery
        updated_mastery = update_mastery(
            user_id=user_id,
            topic=topic,
            success=accuracy,
            time_taken=time_taken,
            attempts=attempts
        )
        
        # 5. Update Global Skill (LSTM Inference)
        new_global_skill = update_global_skill(user_id)
        
        return {
            "status": "success",
            "execution": execution_result,
            "new_mastery": updated_mastery,
            "new_skill": new_global_skill,
            "feedback": "Perfect! All tests passed." if accuracy == 1.0 else f"Passed {execution_result['passed']}/{execution_result['total']} test cases."
        }
    except Exception as e:
        import traceback
        print(f"SUBMISSION ERROR: {str(e)}")
        traceback.print_exc()
        return {"status": "error", "message": f"Execution failed: {str(e)}"}
        
    except Exception as e:
        print(f"Error processing submission for user {user_id}: {e}")
        return {"status": "error", "message": str(e)}
