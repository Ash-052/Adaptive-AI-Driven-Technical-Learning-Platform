from fastapi import APIRouter
from app.api.routes import health, mastery, recommendation, submission, problems, tutor, user, auth, history

api_router = APIRouter()

# Include all module routers here
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(health.router, prefix="/system", tags=["System"])
api_router.include_router(mastery.router, prefix="/mastery", tags=["Mastery"])
api_router.include_router(recommendation.router, prefix="/recommendation", tags=["Recommendation"])
api_router.include_router(submission.router, prefix="", tags=["Submission"])
api_router.include_router(problems.router, prefix="/problem", tags=["Problems"])
api_router.include_router(tutor.router, prefix="/tutor", tags=["Tutor"])
api_router.include_router(user.router, prefix="/user", tags=["User"])
api_router.include_router(history.router, prefix="/history", tags=["History"])

