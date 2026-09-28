from fastapi import APIRouter, HTTPException
from app.db.supabase import supabase

router = APIRouter()

@router.get("/{user_id}")
async def get_user_history(user_id: str):
    """
    Returns full submission history for a specific user.
    """
    try:
        # Join with problems to get the title
        res = supabase.table('user_attempts').select('*, problems(title)') \
            .eq('user_id', user_id).order('created_at', desc=True).execute()
        
        # Handle tuple response if necessary
        if isinstance(res, tuple):
            data = res[0][1] if len(res[0]) > 1 else []
        else:
            data = res.data
            
        return data
    except Exception as e:
        print(f"History Fetch Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
