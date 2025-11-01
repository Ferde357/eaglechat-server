import json
import os
from typing import Optional
from pydantic import BaseModel, Field, validator

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If dotenv not available, manually load .env file
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value


class SupabaseConfig(BaseModel):
    url: str = Field(default_factory=lambda: os.getenv('SUPABASE_URL', ''))
    service_role_key: str = Field(default_factory=lambda: os.getenv('SUPABASE_SERVICE_ROLE_KEY', ''))
    
    @validator('url')
    def validate_url(cls, v):
        if not v:
            raise ValueError("SUPABASE_URL environment variable is required")
        return v
    
    @validator('service_role_key')
    def validate_service_role_key(cls, v):
        if not v:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is required")
        return v


class LoggingConfig(BaseModel):
    level: str = "INFO"
    retention_days: int = Field(default=30, ge=1, le=365)
    log_directory: str = "logs"


class APIConfig(BaseModel):
    title: str = "Eagle Chat Server"
    description: str = "Multi-tenant chatbot backend for WordPress"
    version: str = "1.0.0"
    development_mode: bool = Field(default=False, description="Enable development mode for testing")
    secret_key: str = Field(default_factory=lambda: os.getenv('API_SECRET_KEY', 'default-secret-key-change-in-production'))


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
        """Load configuration from JSON file (secrets come from environment variables)"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Configuration file '{config_path}' not found. "
                "Please create it with non-sensitive settings"
            )
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Supabase config comes from environment variables now
        config_data['supabase'] = {}
        
        return cls(**config_data)


# Load settings
try:
    settings = Settings.load_from_file()
except FileNotFoundError:
    # For development, create a minimal config if the file doesn't exist
    print("Warning: config.json not found. Using example configuration.")
    settings = Settings(
        supabase=SupabaseConfig(),  # Will use environment variables
        logging=LoggingConfig(),
        api=APIConfig(),
        callback=CallbackConfig()
    )