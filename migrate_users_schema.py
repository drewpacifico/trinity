"""
Migration Script: Make User Fields Nullable in Production Database

This script modifies the users table in PostgreSQL to allow NULL values
for optional fields: first_name, last_name, employee_id, email, password_hash, last_login

Usage:
    python migrate_users_schema.py                    # Preview changes (dry-run)
    python migrate_users_schema.py --apply           # Apply changes
"""

import os
import sys
import argparse
from pathlib import Path

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError

# Get database URI from environment
database_uri = os.environ.get('DATABASE_URI') or os.environ.get('DATABASE_URL')

if not database_uri:
    print("[ERROR] DATABASE_URI or DATABASE_URL not set!")
    print("\nSet it with:")
    print("  PowerShell: $env:DATABASE_URI = 'postgresql://...'")
    print("  Or create a .env file with DATABASE_URI=...")
    sys.exit(1)

# Fix postgres:// to postgresql:// if needed
if database_uri.startswith('postgres://'):
    database_uri = database_uri.replace('postgres://', 'postgresql://', 1)


def check_current_schema(engine):
    """Check current schema of users table"""
    with engine.connect() as conn:
        # Get column information
        result = conn.execute(text("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """))
        
        columns = {}
        for row in result.fetchall():
            columns[row[0]] = {
                'data_type': row[1],
                'is_nullable': row[2] == 'YES',
                'default': row[3]
            }
        
        return columns


def migrate_schema(engine, apply=False):
    """Migrate users table schema to allow NULL values"""
    
    print("="*60)
    print("USER TABLE SCHEMA MIGRATION")
    print("="*60)
    
    # Hide password in output
    safe_uri = database_uri.split('@')[1] if '@' in database_uri else database_uri
    print(f"\nDatabase: ...@{safe_uri}")
    
    if not apply:
        print("\n[DRY RUN MODE] - No changes will be made")
    else:
        print("\n[APPLY MODE] - Changes will be applied!")
    
    print()
    
    try:
        # Check current schema
        print("[*] Checking current schema...")
        current_schema = check_current_schema(engine)
        
        print("\nCurrent schema:")
        fields_to_migrate = ['first_name', 'last_name', 'employee_id', 'email', 'password_hash', 'last_login']
        
        changes_needed = []
        for field in fields_to_migrate:
            if field in current_schema:
                nullable = current_schema[field]['is_nullable']
                print(f"   {field:20} - NULL allowed: {nullable}")
                if not nullable:
                    changes_needed.append(field)
            else:
                print(f"   {field:20} - NOT FOUND")
        
        if not changes_needed:
            print("\n[SUCCESS] All fields already allow NULL values!")
            print("   No migration needed.")
            return
        
        print(f"\n[*] Found {len(changes_needed)} fields that need to be modified:")
        for field in changes_needed:
            print(f"   • {field}")
        
        if not apply:
            print("\n[DRY RUN] Would execute the following SQL:")
            print()
            for field in changes_needed:
                sql = f"ALTER TABLE users ALTER COLUMN {field} DROP NOT NULL;"
                print(f"   {sql}")
            print("\nRun with --apply to execute these changes.")
            return
        
        # Apply changes
        print("\n[*] Applying schema changes...")
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                for field in changes_needed:
                    sql = f"ALTER TABLE users ALTER COLUMN {field} DROP NOT NULL;"
                    print(f"   Executing: {sql}")
                    conn.execute(text(sql))
                
                # Commit transaction
                trans.commit()
                print("\n[SUCCESS] Schema migration completed!")
                
                # Verify changes
                print("\n[*] Verifying changes...")
                new_schema = check_current_schema(engine)
                all_nullable = True
                for field in changes_needed:
                    if field in new_schema:
                        nullable = new_schema[field]['is_nullable']
                        if not nullable:
                            all_nullable = False
                            print(f"   [WARNING] {field} still not nullable!")
                        else:
                            print(f"   [OK] {field} is now nullable")
                
                if all_nullable:
                    print("\n[SUCCESS] All fields are now nullable!")
                    print("   You can now run: python sync_to_production.py")
                
            except Exception as e:
                trans.rollback()
                print(f"\n[ERROR] Migration failed: {e}")
                print("   Changes have been rolled back.")
                raise
        
    except OperationalError as e:
        print(f"\n[ERROR] Database connection failed: {e}")
        print("\nTroubleshooting:")
        print("   1. Verify your IP address is whitelisted in DigitalOcean")
        print("   2. Check your connection string is correct")
        print("   3. Verify database is running")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Migrate users table schema to allow NULL values'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Apply changes (default is dry-run)'
    )
    
    args = parser.parse_args()
    
    try:
        engine = create_engine(database_uri)
        migrate_schema(engine, apply=args.apply)
    
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
