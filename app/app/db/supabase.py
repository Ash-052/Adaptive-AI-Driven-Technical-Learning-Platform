from supabase import create_client, Client
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    _instance: Client = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            logger.info("Initializing Supabase client singleton...")
            settings = get_settings()
            try:
                cls._instance = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                logger.info("Supabase client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                raise e
        return cls._instance

def get_db() -> Client:
    return SupabaseClient.get_client()

supabase: Client = get_db()
