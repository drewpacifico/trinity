"""
Database initialization script for Trinity Training Guide

This script creates the database tables and optionally loads initial data.
Run this before starting the migration process.

Usage:
    python init_db.py              # Create tables only
    python init_db.py --drop       # Drop existing tables and recreate
    python init_db.py --test       # Create test user
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask
from models import db, User, Chapter, Module, ChapterSection, QuizQuestion, GlossaryTerm
from config import DevelopmentConfig


def create_app():
    """Create Flask application with database configuration"""
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)
    
    # Initialize database
    db.init_app(app)
    
    return app


def init_database(drop_existing=False):
    """
    Initialize database tables.
    
    Args:
        drop_existing: If True, drops all existing tables first
    """
    app = create_app()
    
    with app.app_context():
        if drop_existing:
            print("⚠️  Dropping all existing tables...")
            db.drop_all()
            print("✅ Tables dropped")
        
        print("📦 Creating database tables...")
        db.create_all()
        print("✅ Database tables created successfully")
        
        # Verify tables were created
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\n📋 Created tables ({len(tables)}):")
        for table in sorted(tables):
            print(f"   • {table}")


def create_test_user():
    """Create a test user for development"""
    app = create_app()
    
    with app.app_context():
        # Check if test user already exists
        existing_user = User.query.filter_by(username='test_user').first()
        if existing_user:
            print("ℹ️  Test user 'test_user' already exists")
            return
        
        # Create test user
        test_user = User(
            username='test_user',
            email='test@example.com',
            is_preview_mode=False
        )
        db.session.add(test_user)
        
        # Create preview user
        preview_user = User(
            username='preview',
            email='preview@example.com',
            is_preview_mode=True
        )
        db.session.add(preview_user)
        
        db.session.commit()
        
        print("✅ Test users created:")
        print("   • username: test_user (regular user)")
        print("   • username: preview (preview mode enabled)")


def verify_database():
    """Verify database structure and show statistics"""
    app = create_app()
    
    with app.app_context():
        print("\n📊 Database Statistics:")
        print(f"   • Chapters: {Chapter.query.count()}")
        print(f"   • Modules: {Module.query.count()}")
        print(f"   • Chapter Sections: {ChapterSection.query.count()}")
        print(f"   • Quiz Questions: {QuizQuestion.query.count()}")
        print(f"   • Glossary Terms: {GlossaryTerm.query.count()}")
        print(f"   • Users: {User.query.count()}")
        
        if Chapter.query.count() == 0:
            print("\n⚠️  Database is empty. Run migration script to load data.")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Initialize Trinity Training Guide database'
    )
    parser.add_argument(
        '--drop',
        action='store_true',
        help='Drop existing tables before creating new ones'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Create test users for development'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify database and show statistics'
    )
    
    args = parser.parse_args()
    
    print("🚀 Trinity Training Guide - Database Initialization\n")
    
    try:
        # Initialize database
        init_database(drop_existing=args.drop)
        
        # Create test users if requested
        if args.test:
            print("\n👤 Creating test users...")
            create_test_user()
        
        # Verify database
        if args.verify or args.test:
            verify_database()
        
        print("\n✅ Database initialization complete!")
        print("\n📝 Next steps:")
        print("   1. Run: python db_migration.py")
        print("   2. Start app: python main.py")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

