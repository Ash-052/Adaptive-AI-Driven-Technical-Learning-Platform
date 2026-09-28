from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.db.supabase import supabase
from app.core.security import get_password_hash, verify_password, create_access_token
from app.services.topic_mastery_service import initialize_user_mastery
import uuid

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
async def register(request: RegisterRequest):
    try:
        # 1. Check if user exists
        res = supabase.table('users').select('id').eq('email', request.email).execute()
        # Handle the specific tuple format (data, count) where data[1] is the list
        if isinstance(res, tuple):
            data, count = res
            existing_users = data[1] if len(data) > 1 else []
        else:
            existing_users = res.data
            
        if existing_users:
            raise HTTPException(status_code=400, detail="Email already registered")

        # 2. Hash password and insert
        user_id = str(uuid.uuid4())
        hashed_pwd = get_password_hash(request.password)
        
        user_data = {
            "id": user_id,
            "email": request.email,
            "username": request.username,
            "password": hashed_pwd,
            "skill_score": 0.3
        }
        
        supabase.table('users').insert(user_data).execute()
        # 3. Initialize mastery for new user
        initialize_user_mastery(user_id)
        return {"status": "success", "message": "User registered successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"REGISTRATION ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login")
async def login(request: LoginRequest):
    try:
        # 1. Fetch user
        res = supabase.table('users').select('*').eq('email', request.email).execute()
        
        if isinstance(res, tuple):
            data, count = res
            users = data[1] if len(data) > 1 else []
        else:
            users = res.data
            
        if not users:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user = users[0]
        
        # 2. Verify password
        if not verify_password(request.password, user['password']):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # 3. Create token
        token = create_access_token(user['id'])
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user['id'],
            "username": user['username']
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"LOGIN ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
