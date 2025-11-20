"""
Quick script to test PostgreSQL database connection.
Run this to verify your IP address is whitelisted and connection works.
"""

import os
import sys
from pathlib import Path

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Get database URI from environment
database_uri = os.environ.get('DATABASE_URI') or os.environ.get('DATABASE_URL')

if not database_uri:
    print("[ERROR] DATABASE_URI or DATABASE_URL not set!")
    print("\nSet it with:")
    print("  PowerShell: $env:DATABASE_URI = 'postgresql://...'")
    print("  Or create a .env file with DATABASE_URI=...")
    sys.exit(1)

# Hide password in output
safe_uri = database_uri.split('@')[1] if '@' in database_uri else database_uri
print(f"Testing connection to: ...@{safe_uri}")
print()

try:
    from sqlalchemy import create_engine, text
    
    print("Connecting to database...")
    engine = create_engine(database_uri)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"[SUCCESS] Connection successful!")
        print(f"\nPostgreSQL Version: {version}")
        
        # Test if we can query tables
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result.fetchall()]
        
        if tables:
            print(f"\nFound {len(tables)} tables:")
            for table in tables[:10]:  # Show first 10
                print(f"   • {table}")
            if len(tables) > 10:
                print(f"   ... and {len(tables) - 10} more")
        else:
            print("\n[WARNING] No tables found. Database might be empty.")
            print("   Run: python init_db.py (with FLASK_ENV=production)")
    
    print("\n[SUCCESS] All tests passed! Your IP is whitelisted and connection works.")
    print("   You can now run: python sync_to_production.py --dry-run")

except Exception as e:
    print(f"\n[ERROR] Connection failed!")
    print(f"\nError: {e}")
    print("\nTroubleshooting:")
    print("   1. Verify your IP address is added to Network Access in DigitalOcean")
    print("   2. Check your connection string is correct")
    print("   3. Verify database is running (check DigitalOcean dashboard)")
    print("   4. Check firewall/antivirus isn't blocking port 25060")
    sys.exit(1)

