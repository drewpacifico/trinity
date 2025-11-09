"""
Check what's actually in the production database from the app's perspective.
"""

import os
os.environ['FLASK_ENV'] = 'production'

from main import app, db
from models import Chapter, Module, QuizQuestion, User

print("=" * 60)
print("DATABASE CHECK - What the app sees")
print("=" * 60)

with app.app_context():
    # Show database URI (hide password)
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if db_uri:
        safe_uri = db_uri.split('@')[1] if '@' in db_uri else db_uri
        print(f"Database: ...@{safe_uri}")
    else:
        print("ERROR: No database URI!")
    print()
    
    # Count records
    try:
        chapter_count = Chapter.query.count()
        module_count = Module.query.count()
        quiz_count = QuizQuestion.query.count()
        user_count = User.query.count()
        
        print(f"📊 Record Counts:")
        print(f"   • Chapters: {chapter_count}")
        print(f"   • Modules: {module_count}")
        print(f"   • Quiz Questions: {quiz_count}")
        print(f"   • Users: {user_count}")
        print()
        
        if chapter_count == 0:
            print("❌ No chapters found!")
            print()
            print("Let's check the tables...")
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Available tables: {tables}")
        else:
            print("✅ Data exists in database!")
            print()
            print("Sample chapters:")
            for ch in Chapter.query.limit(3).all():
                print(f"   • Chapter {ch.chapter_number}: {ch.title}")
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        import traceback
        traceback.print_exc()

print()
print("=" * 60)

