from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.db.supabase import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health", summary="Check system health")
async def health_check(db: Client = Depends(get_db)):
    """
    Health check endpoint that verifies connectivity to Supabase.
    """
    try:
        # A simple query to check connectivity (e.g., fetching a single row from a known table)
        # Since tables might not exist yet, we can check if the client itself is instantiated properly.
        # But for robust DB connectivity check, we try to call a basic method, like auth.get_session() or checking a generic table.
        # Here we just try to fetch 1 row from a non-existent/existent table to see if the network call succeeds.
        response = db.table("user_attempts").select("id").limit(1).execute()
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database connectivity failed: {str(e)}")
        # We don't fail the health check if the table doesn't exist (e.g. code 42P01), 
        # but if the connection is down entirely, it will throw a different error.
        db_status = f"error: {str(e)}"
        raise HTTPException(status_code=503, detail="Service Unavailable: Database connection failed.")

    return {
        "status": "ok",
        "database": db_status
    }
