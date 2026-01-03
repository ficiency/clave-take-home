"""
Test Supabase connection.

Verifies that environment variables are loaded correctly
and that the Supabase client can be initialized.
"""

import sys
from etl.db.connection import db
from etl.config import Config

# Configure UTF-8 encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


def main():
    print("Testing Supabase connection...")
    print("-" * 50)
    
    # Test configuration
    try:
        Config.validate()
        print("[OK] Configuration validated")
        print(f"  URL: {Config.SUPABASE_URL[:30]}..." if Config.SUPABASE_URL else "  URL: Not set")
        print(f"  Key: {'*' * 20}...{Config.SUPABASE_KEY[-10:]}" if Config.SUPABASE_KEY else "  Key: Not set")
    except ValueError as e:
        print(f"[ERROR] Configuration error: {e}")
        return
    
    # Test client initialization
    try:
        client = db.client
        print("[OK] Supabase client initialized successfully")
        print("[OK] Connection ready to use")
        print("\nYou can now use 'db.client' to interact with Supabase")
        
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        print("\nMake sure:")
        print("  1. SUPABASE_URL is correct in .env")
        print("  2. SUPABASE_KEY is correct in .env")
        print("  3. You have internet connection")
        return
    
    print("-" * 50)
    print("Connection test completed successfully! [OK]")


if __name__ == "__main__":
    main()

