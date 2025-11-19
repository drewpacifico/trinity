"""
Database Migration: Add User Registration Fields

This script adds the new fields to the users table:
- first_name
- last_name
- employee_id
- Makes password_hash NOT NULL
- Updates existing users with default values

Usage:
    python migrate_users_schema.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask
from models import db
from config import get_config
from sqlalchemy import text
import os


def migrate_users_table():
    """Add new fields to users table"""
    
    print("🔄 Starting user schema migration...\n")
    
    # Create Flask app
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    db.init_app(app)
    
    with app.app_context():
        # Check database type
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        is_sqlite = db_uri.startswith('sqlite')
        is_postgres = 'postgresql' in db_uri or 'postgres://' in db_uri
        
        print(f"📊 Database: {'SQLite' if is_sqlite else 'PostgreSQL'}")
        print(f"🔗 URI: {db_uri[:50]}...")
        print()
        
        try:
            # For SQLite, we need to handle schema changes carefully
            if is_sqlite:
                print("⚠️  SQLite detected - Will recreate table with new schema")
                print("    Existing user data will be preserved")
                print()
                
                # Check if new columns already exist
                result = db.session.execute(text("PRAGMA table_info(users)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'first_name' in columns:
                    print("✅ Migration already applied! New fields exist.")
                    return
                
                print("📝 Creating migration SQL...")
                
                # SQLite doesn't support ALTER TABLE easily, so we:
                # 1. Rename old table
                # 2. Create new table with updated schema
                # 3. Copy data
                # 4. Drop old table
                
                migration_sql = """
                -- Step 1: Rename existing table
                ALTER TABLE users RENAME TO users_old;
                
                -- Step 2: Create new table with updated schema
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    employee_id VARCHAR(50) NOT NULL UNIQUE,
                    email VARCHAR(255) UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    is_preview_mode BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                );
                
                -- Step 3: Copy existing data with default values
                INSERT INTO users (id, username, first_name, last_name, employee_id, email, password_hash, is_preview_mode, created_at, last_login)
                SELECT 
                    id,
                    username,
                    'User' as first_name,
                    COALESCE(username, 'Unknown') as last_name,
                    'EMP' || CAST(id AS TEXT) as employee_id,
                    email,
                    COALESCE(password_hash, 'legacy_user_no_password') as password_hash,
                    is_preview_mode,
                    created_at,
                    last_login
                FROM users_old;
                
                -- Step 4: Drop old table
                DROP TABLE users_old;
                """
                
                print("🚀 Executing migration...")
                for statement in migration_sql.split(';'):
                    if statement.strip():
                        db.session.execute(text(statement))
                
                db.session.commit()
                print("✅ SQLite migration complete!")
                
            elif is_postgres:
                print("🐘 PostgreSQL detected - Using ALTER TABLE")
                print()
                
                # Check if columns exist
                result = db.session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users'
                """))
                columns = [row[0] for row in result.fetchall()]
                
                if 'first_name' in columns:
                    print("✅ Migration already applied! New fields exist.")
                    return
                
                print("📝 Adding new columns...")
                
                # Add new columns (as nullable first)
                db.session.execute(text("ALTER TABLE users ADD COLUMN first_name VARCHAR(100)"))
                db.session.execute(text("ALTER TABLE users ADD COLUMN last_name VARCHAR(100)"))
                db.session.execute(text("ALTER TABLE users ADD COLUMN employee_id VARCHAR(50)"))
                
                print("📝 Setting default values for existing users...")
                
                # Update existing users with default values
                db.session.execute(text("""
                    UPDATE users 
                    SET first_name = 'User',
                        last_name = COALESCE(username, 'Unknown'),
                        employee_id = 'EMP' || CAST(id AS TEXT)
                    WHERE first_name IS NULL
                """))
                
                # Update password_hash for users without it
                db.session.execute(text("""
                    UPDATE users
                    SET password_hash = 'legacy_user_no_password'
                    WHERE password_hash IS NULL
                """))
                
                db.session.commit()
                
                print("📝 Making fields NOT NULL...")
                
                # Now make fields NOT NULL
                db.session.execute(text("ALTER TABLE users ALTER COLUMN first_name SET NOT NULL"))
                db.session.execute(text("ALTER TABLE users ALTER COLUMN last_name SET NOT NULL"))
                db.session.execute(text("ALTER TABLE users ALTER COLUMN employee_id SET NOT NULL"))
                db.session.execute(text("ALTER TABLE users ALTER COLUMN password_hash SET NOT NULL"))
                
                print("📝 Adding unique constraint to employee_id...")
                db.session.execute(text("ALTER TABLE users ADD CONSTRAINT users_employee_id_key UNIQUE (employee_id)"))
                
                db.session.commit()
                print("✅ PostgreSQL migration complete!")
            
            else:
                print("❌ Unknown database type")
                return
            
            # Verify migration
            print()
            print("🔍 Verifying migration...")
            result = db.session.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.fetchone()[0]
            print(f"✅ Found {user_count} users in migrated table")
            
            print()
            print("🎉 Migration completed successfully!")
            print()
            print("⚠️  IMPORTANT: Existing users have these default values:")
            print("   - first_name: 'User'")
            print("   - last_name: Their username")
            print("   - employee_id: 'EMP' + their user ID")
            print("   - password_hash: 'legacy_user_no_password' (cannot login)")
            print()
            print("📝 Next steps:")
            print("   1. Existing users should register again with the new form")
            print("   2. Or manually update their info in the database")
            print("   3. They will need to set a password to login")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    migrate_users_table()

