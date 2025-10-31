import json
import os
from typing import Optional
from pydantic import BaseModel, Field, validator


class SupabaseConfig(BaseModel):
    url: str
    service_role_key: str


class LoggingConfig(BaseModel):
    level: str = "INFO"
    retention_days: int = Field(default=30, ge=1, le=365)
    log_directory: str = "logs"


class APIConfig(BaseModel):
    title: str = "Eagle Chat Server"
    description: str = "Multi-tenant chatbot backend for WordPress"
    version: str = "1.0.0"
    development_mode: bool = Field(default=False, description="Enable development mode for testing")


class CallbackConfig(BaseModel):
    retry_attempts: int = Field(default=3, ge=1, le=10)
    retry_delay_seconds: int = Field(default=3, ge=1, le=30)


class Settings(BaseModel):
    supabase: SupabaseConfig
    logging: LoggingConfig
    api: APIConfig
    callback: CallbackConfig = CallbackConfig()

    @classmethod
    def load_from_file(cls, config_path: str = "config.json") -> "Settings":
        """Load configuration from JSON file"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Configuration file '{config_path}' not found. "
                "Please create it based on config.example.json"
            )
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        return cls(**config_data)


# Load settings
try:
    settings = Settings.load_from_file()
except FileNotFoundError:
    # For development, create a minimal config if the file doesn't exist
    print("Warning: config.json not found. Using example configuration.")
    settings = Settings(
        supabase=SupabaseConfig(
            url="<supabase_project_url>",
            service_role_key="<supabase_service_role_key>"
        ),
        logging=LoggingConfig(),
        api=APIConfig(),
        callback=CallbackConfig()
    )