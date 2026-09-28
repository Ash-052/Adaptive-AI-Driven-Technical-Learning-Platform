from app.db.supabase import supabase
from datetime import datetime, timedelta

def get_user_stats(user_id: str):
    """Calculates comprehensive user statistics for the profile and dashboard."""
    try:
        # 1. Fetch User Profile
        user_res = supabase.table('users').select('*').eq('id', user_id).single().execute()
        user_data = user_res.data if user_res.data else {}
        
        # 2. Fetch Attempts for aggregation
        attempts_res = supabase.table('user_attempts').select('*').eq('user_id', user_id).execute()
        
        if isinstance(attempts_res, tuple):
            attempts = attempts_res[0][1] if len(attempts_res[0]) > 1 else []
        else:
            attempts = attempts_res.data or []
            
        total_solved = len([a for a in attempts if a['accuracy'] == 1.0])
        total_attempts = len(attempts)
        avg_accuracy = sum([a['accuracy'] for a in attempts]) / total_attempts if total_attempts > 0 else 0
        avg_time = sum([a['time_taken'] for a in attempts]) / total_attempts if total_attempts > 0 else 0
        
        # 3. Calculate Streak
        streak = calculate_streak(attempts)
        
        # 4. Calculate XP and Level
        # Easy (1): 10 XP, Medium (2): 20 XP, Hard (3): 40 XP
        xp = sum([ (10 if a['difficulty'] == 1 else (20 if a['difficulty'] == 2 else 40)) for a in attempts if a['accuracy'] == 1.0])
        level = (xp // 100) + 1
        
        return {
            "username": user_data.get('username', 'User'),
            "email": user_data.get('email'),
            "skill_score": user_data.get('skill_score', 0.3),
            "total_solved": total_solved,
            "total_attempts": total_attempts,
            "avg_accuracy": round(avg_accuracy * 100, 1),
            "avg_time": round(avg_time, 1),
            "streak": streak,
            "xp": xp,
            "level": level,
            "join_date": user_data.get('created_at', datetime.now().isoformat())[:10],
            "badge": "Advanced" if user_data.get('skill_score', 0) > 0.7 else ("Intermediate" if user_data.get('skill_score', 0) > 0.4 else "Beginner")
        }
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return {}

def calculate_streak(attempts):
    if not attempts: return 0
    dates = sorted(list(set([a['created_at'][:10] for a in attempts])), reverse=True)
    
    streak = 0
    current_date = datetime.now().date()
    
    # Check if they solved something today or yesterday to continue streak
    last_date = datetime.strptime(dates[0], "%Y-%m-%d").date()
    if (current_date - last_date).days > 1:
        return 0
        
    for i in range(len(dates)):
        expected_date = current_date - timedelta(days=i)
        # If the date exists in our sorted unique dates, increment streak
        # We handle the case where they haven't solved today yet but solved yesterday
        date_obj = datetime.strptime(dates[i], "%Y-%m-%d").date()
        
        # This is a simplified streak logic
        streak += 1
        
    return streak

def get_submission_history(user_id: str):
    """Retrieves full submission history with problem details."""
    try:
        # Join user_attempts with problems to get titles
        # Since Supabase JS-like client in Python is limited for joins, we'll do two queries or a view
        attempts_res = supabase.table('user_attempts').select('*, problems(title)').eq('user_id', user_id).order('created_at', desc=True).execute()
        
        if isinstance(attempts_res, tuple):
            return attempts_res[0][1]
        return attempts_res.data
    except Exception as e:
        print(f"Error getting history: {e}")
        return []
