from typing import Optional, Dict, Any
from supabase import create_client, Client
from core.config import settings
from core.logger import logger


class SupabaseManager:
    """Manages Supabase database operations"""
    
    def __init__(self):
        try:
            self.client: Client = create_client(
                settings.supabase.url,
                settings.supabase.service_role_key
            )
            logger.info("Successfully connected to Supabase")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {str(e)}")
            raise