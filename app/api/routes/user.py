from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field
from app.core.security import ALGORITHM, SECRET_KEY
from app.db.supabase import supabase
from app.services.topic_mastery_service import get_user_progress
from app.services.user_service import get_user_stats, get_submission_history

router = APIRouter()
bearer_scheme = HTTPBearer()


class ProfileUpdateRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr


def get_authenticated_user_id(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token")


@router.put("/profile")
async def update_profile(request: ProfileUpdateRequest, user_id: str = Depends(get_authenticated_user_id)):
    try:
        user_res = supabase.table('users').select('id').eq('id', user_id).execute()
        user_rows = user_res.data if hasattr(user_res, 'data') else []
        if not user_rows:
            raise HTTPException(status_code=404, detail="User not found")

        email_res = supabase.table('users').select('id').eq('email', request.email).neq('id', user_id).execute()
        email_rows = email_res.data if hasattr(email_res, 'data') else []
        if email_rows:
            raise HTTPException(status_code=409, detail="Email already in use")

        supabase.table('users').update({
            "username": request.username.strip(),
            "email": request.email,
        }).eq('id', user_id).execute()
        return {"status": "success", "profile": get_user_stats(user_id)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile update failed: {str(e)}")


@router.get("/{user_id}/progress")
async def get_combined_progress(user_id: str):
    try:
        return get_user_progress(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/profile")
async def user_profile(user_id: str):
    return get_user_stats(user_id)


@router.get("/{user_id}/history")
async def user_history(user_id: str):
    return {"history": get_submission_history(user_id)}


@router.get("/{user_id}/analytics")
async def user_analytics(user_id: str):
    return {
        "progress": get_user_progress(user_id),
        "stats": get_user_stats(user_id)
    }
