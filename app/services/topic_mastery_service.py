from app.db.supabase import supabase
from datetime import datetime

TOPICS = [
    "basics", "arrays", "strings", "recursion", "sorting",
    "searching", "dynamic_programming", "graphs", "trees"
]

def initialize_user_mastery(user_id: str):
    """Create zero-valued mastery records for topics that have no record yet."""
    try:
        existing = supabase.table('user_topic_mastery').select('topic').eq('user_id', user_id).execute()
        existing_topics = {
            row['topic'] for row in _extract_rows(existing)
            if isinstance(row, dict) and 'topic' in row
        }
        records = [
            {
                "user_id": user_id,
                "topic": topic,
                "skill": 0.0,
                "attempt_count": 0,
            }
            for topic in TOPICS if topic not in existing_topics
        ]
        if not records:
            return []
        res = supabase.table('user_topic_mastery').upsert(records, on_conflict='user_id, topic').execute()
        return res.data if hasattr(res, 'data') else res
    except Exception as e:
        print(f"Error initializing mastery for user {user_id}: {e}")
        return None

def _extract_rows(res):
    if res is None:
        return []
    if hasattr(res, 'data'):
        return res.data if isinstance(res.data, list) else ([res.data] if res.data else [])
    if isinstance(res, (list, tuple)):
        if len(res) > 0 and isinstance(res[0], dict):
            return res
        if len(res) > 0 and isinstance(res[0], list):
            return res[0]
    return []

def get_user_mastery(user_id: str):
    """Retrieves a user's full topic mastery profile."""
    try:
        res = supabase.table('user_topic_mastery').select('topic, skill').eq('user_id', user_id).execute()
        rows = _extract_rows(res)
        if rows:
            stored_mastery = {
                item['topic']: item.get('skill', 0.0)
                for item in rows if isinstance(item, dict) and 'topic' in item
            }
            return {topic: stored_mastery.get(topic, 0.0) for topic in TOPICS}
        initialize_user_mastery(user_id)
        return {topic: 0.0 for topic in TOPICS}
    except Exception as e:
        print(f"Error getting mastery for user {user_id}: {e}")
        return {topic: 0.0 for topic in TOPICS}

def update_mastery(user_id: str, topic: str, success: float, time_taken: float, attempts: int):
    """Updates a user's mastery for a specific topic after a problem submission."""
    try:
        # 1. Fetch current mastery
        res = supabase.table('user_topic_mastery').select('skill, attempt_count').eq('user_id', user_id).eq('topic', topic).execute()
        rows = _extract_rows(res)
        
        if not rows:
            initialize_user_mastery(user_id)
            current_mastery = 0.0
            total_attempts = 0
        else:
            current_mastery = rows[0].get('skill', 0.0)
            total_attempts = rows[0].get('attempt_count', 0)

        accuracy = max(0.0, min(1.0, float(success)))
        new_mastery = current_mastery + (1.0 - current_mastery) * 0.2 * accuracy

        # 5. Update database
        updated_record = {
            "skill": new_mastery,
            "attempt_count": total_attempts + 1,
            "last_updated": datetime.now().isoformat()
        }
        res_up = supabase.table('user_topic_mastery').update(updated_record).eq('user_id', user_id).eq('topic', topic).execute()
        up_rows = _extract_rows(res_up)
        return up_rows[0] if up_rows else None

    except Exception as e:
        print(f"Error updating mastery for user {user_id}, topic {topic}: {e}")
        return None

def get_weak_topics(user_id: str):
    """Returns topics where user mastery is below 0.4."""
    try:
        res = supabase.table('user_topic_mastery').select('topic').eq('user_id', user_id).lt('skill', 0.4).execute()
        rows = _extract_rows(res)
        return [item['topic'] for item in rows if isinstance(item, dict) and 'topic' in item]
    except Exception as e:
        print(f"Error getting weak topics for user {user_id}: {e}")
        return []

def get_strong_topics(user_id: str):
    """Returns topics where user mastery is above 0.75."""
    try:
        res = supabase.table('user_topic_mastery').select('topic').eq('user_id', user_id).gt('skill', 0.75).execute()
        rows = _extract_rows(res)
        return [item['topic'] for item in rows if isinstance(item, dict) and 'topic' in item]
    except Exception as e:
        print(f"Error getting strong topics for user {user_id}: {e}")
        return []

def get_user_progress(user_id: str):
    """Combined view of global skill score and topic mastery."""
    try:
        # 1. Get Skill Score from users table
        user_res = supabase.table('users').select('skill_score').eq('id', user_id).single().execute()
        skill_score = user_res.data.get('skill_score', 0.3) if user_res.data else 0.3
        
        # 2. Get Topic Mastery
        mastery = get_user_mastery(user_id)
        
        # 3. Check if new user (no attempts)
        attempts_res = supabase.table('user_attempts').select('id', count='exact').eq('user_id', user_id).execute()
        has_attempts = False
        if isinstance(attempts_res, tuple):
             has_attempts = attempts_res[1] > 0
        else:
             has_attempts = (attempts_res.count or 0) > 0
        
        return {
            "user_id": user_id,
            "skill_score": skill_score,
            "topic_mastery": mastery,
            "is_new_user": not has_attempts
        }
    except Exception as e:
        print(f"Error getting progress for user {user_id}: {e}")
        return {"user_id": user_id, "skill_score": 0.3, "topic_mastery": {}, "is_new_user": True}
