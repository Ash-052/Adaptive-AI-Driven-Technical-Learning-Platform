import random
import json
from app.db.supabase import supabase
from app.services.recommendation_service import get_next_problem

async def get_problem_for_user(user_id: str):
    """
    Selects the best problem for the user based on ML recommendations and history.
    """
    # 1. Get recommendation (topic, difficulty)
    recommendation = await get_next_problem(user_id)
    topic = recommendation["topic"]
    difficulty = recommendation["difficulty"]
    
    # 2. Get user's solved problem IDs
    try:
        history_res = supabase.table('user_attempts') \
            .select('problem_id') \
            .eq('user_id', user_id) \
            .eq('accuracy', 1.0) \
            .execute()
        solved_ids = [item['problem_id'] for item in history_res.data] if history_res.data else []
    except Exception as e:
        print(f"Error fetching solved history: {e}")
        solved_ids = []

    # 3. Query problems for the recommended topic and difficulty
    try:
        # Fetch up to 10 candidates to choose from
        query = supabase.table('problems') \
            .select('*') \
            .eq('topic', topic) \
            .eq('difficulty', difficulty)
            
        if solved_ids:
            # Postgrest syntax for NOT IN (neq.all or filtered after fetch)
            # Since solved_ids can be large, we'll fetch and filter locally or use .not_.in_
            query = query.not_.in_('id', solved_ids)
            
        response = query.limit(10).execute()
        candidates = response.data if response.data else []
        
        # 4. Fallback Logic
        if not candidates:
            print(f"No problems found for {topic} D{difficulty}. Trying different difficulty...")
            # Try same topic, any difficulty
            fallback_res = supabase.table('problems') \
                .select('*') \
                .eq('topic', topic) \
                .not_.in_('id', solved_ids) \
                .limit(10).execute()
            candidates = fallback_res.data if fallback_res.data else []
            
        if not candidates:
            print("Still no problems. Returning any unsolved problem...")
            # Any unsolved problem
            any_res = supabase.table('problems') \
                .select('*') \
                .not_.in_('id', solved_ids) \
                .limit(5).execute()
            candidates = any_res.data if any_res.data else []

        if not candidates:
            # Final Fallback: Generate using GPT
            from app.services.problem_generator import generator
            print(f"No DB problems found. Generating new problem for {topic} D{difficulty} using GPT...")
            generated_problem = generator.generate_problem(topic, difficulty)
            
            if generated_problem:
                # Store in DB for future use
                try:
                    # Prepare for DB (serialize JSON fields)
                    db_entry = generated_problem.copy()
                    db_entry["test_cases"] = json.dumps(db_entry["test_cases"])
                    db_entry["hints"] = json.dumps(db_entry["hints"])
                    
                    db_res = supabase.table('problems').insert(db_entry).execute()
                    if db_res.data:
                        return db_res.data[0], recommendation
                except Exception as e:
                    print(f"Error saving GPT problem to DB: {e}")
                    return generated_problem, recommendation
            
            return None, recommendation

        # 5. Pick Randomly from candidates
        selected_problem = random.choice(candidates)
        return selected_problem, recommendation

    except Exception as e:
        print(f"Error in problem selection: {e}")
        return None, recommendation

async def get_problem_by_id(problem_id: str):
    try:
        response = supabase.table('problems').select('*').eq('id', problem_id).single().execute()
        return response.data
    except Exception as e:
        print(f"Error fetching problem {problem_id}: {e}")
        return None
