"""
Database connection module for Supabase.

Provides Supabase client for data operations.
Tables are created manually via Supabase dashboard.
"""

from supabase import create_client, Client
from typing import Optional
from ..config import Config


class DatabaseConnection:
    """Manages Supabase client connection."""
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        Initialize Supabase client.
        
        Args:
            url: Optional Supabase URL. If not provided, uses Config.
            key: Optional service role key. If not provided, uses Config.
        """
        Config.validate()
        self.url = url or Config.SUPABASE_URL
        self.key = key or Config.SUPABASE_KEY
        self._client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """Get or create Supabase client."""
        if self._client is None:
            self._client = create_client(self.url, self.key)
        return self._client


# Global instance
db = DatabaseConnection()

