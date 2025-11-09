"""
Initialize database tables for production deployment.

This script creates all database tables and runs initial migrations.
Run this once after deploying to a new database.

Usage:
    python init_db.py
"""

import os
import sys

# Ensure we're using production config
os.environ['FLASK_ENV'] = 'production'

print("🔄 Initializing database...")
print(f"FLASK_ENV: {os.environ.get('FLASK_ENV')}")
print(f"DATABASE_URI set: {'Yes' if os.environ.get('DATABASE_URI') else 'No'}")
print(f"DATABASE_URL set: {'Yes' if os.environ.get('DATABASE_URL') else 'No'}")
print()

try:
    # Import app and database
    from main import app, db
    from config import get_config
    
    config = get_config('production')
    db_uri = config.SQLALCHEMY_DATABASE_URI
    
    if not db_uri:
        print("❌ Error: No database URI configured!")
        print("Please set DATABASE_URI or DATABASE_URL environment variable.")
        sys.exit(1)
    
    # Hide password in output
    safe_uri = db_uri.split('@')[1] if '@' in db_uri else db_uri
    print(f"📊 Database: ...@{safe_uri}")
    print()
    
    with app.app_context():
        print("Creating all tables...")
        db.create_all()
        print("✅ Tables created successfully!")
        print()
        
        # Check what tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"📋 Created {len(tables)} tables:")
        for table in sorted(tables):
            print(f"   • {table}")
        print()
        
        print("✅ Database initialization complete!")
        print()
        print("Next steps:")
        print("1. Run: python db_migration.py")
        print("2. This will populate the database with training content")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
