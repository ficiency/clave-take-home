"""
Configuration module for ETL pipeline.

Reads environment variables from .env file for Supabase connection.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Configuration class for Supabase connection."""
    
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present."""
        if not cls.SUPABASE_URL:
            raise ValueError("SUPABASE_URL is required")
        if not cls.SUPABASE_KEY:
            raise ValueError("SUPABASE_KEY is required")
        return True

