"""
Import JSON data into MySQL production database

This script imports data from JSON files (exported from SQLite) into
the MySQL production database on Hostinger VPS.

Usage:
    python import_data.py                    # Import from 'exports' directory
    python import_data.py --input exports    # Import from custom directory
    python import_data.py --tables chapters,modules  # Import specific tables only
    python import_data.py --clear            # Clear tables before importing
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask
from models import (
    db, Chapter, Module, ChapterSection, QuizQuestion,
    GlossaryTerm, User, UserProgress, UserQuizAnswer
)
from config import get_config
import os


def create_app():
    """Create Flask app with production config"""
    app = Flask(__name__)
    env = os.environ.get('FLASK_ENV', 'production')
    config = get_config(env)
    app.config.from_object(config)
    db.init_app(app)
    return app


def parse_datetime(dt_string):
    """Parse ISO format datetime string"""
    if dt_string is None:
        return None
    try:
        return datetime.fromisoformat(dt_string)
    except ValueError:
        return None


def import_chapters(data, clear=False):
    """Import chapters"""
    if clear:
        Chapter.query.delete()
        db.session.commit()
        print("    [*] Cleared existing chapters")

    imported = 0
    skipped = 0

    for item in data:
        existing = Chapter.query.get(item['id'])
        if existing:
            skipped += 1
            continue

        chapter = Chapter(
            id=item['id'],
            title=item['title'],
            display_order=item['display_order'],
            created_at=parse_datetime(item.get('created_at'))
        )
        db.session.add(chapter)
        imported += 1

    db.session.commit()
    return imported, skipped


def import_modules(data, clear=False):
    """Import modules"""
    if clear:
        Module.query.delete()
        db.session.commit()
        print("    [*] Cleared existing modules")

    imported = 0
    skipped = 0

    for item in data:
        existing = Module.query.get(item['id'])
        if existing:
            skipped += 1
            continue

        module = Module(
            id=item['id'],
            chapter_id=item['chapter_id'],
            title=item['title'],
            content_markdown=item.get('content_markdown'),
            display_order=item['display_order'],
            created_at=parse_datetime(item.get('created_at'))
        )
        db.session.add(module)
        imported += 1

    db.session.commit()
    return imported, skipped


def import_chapter_sections(data, clear=False):
    """Import chapter sections"""
    if clear:
        ChapterSection.query.delete()
        db.session.commit()
        print("    [*] Cleared existing chapter sections")

    imported = 0
    skipped = 0

    for item in data:
        existing = ChapterSection.query.get(item['id'])
        if existing:
            skipped += 1
            continue

        section = ChapterSection(
            id=item['id'],
            chapter_id=item['chapter_id'],
            section_type=item['section_type'],
            content_markdown=item.get('content_markdown'),
            created_at=parse_datetime(item.get('created_at'))
        )
        db.session.add(section)
        imported += 1

    db.session.commit()
    return imported, skipped


def import_quiz_questions(data, clear=False):
    """Import quiz questions"""
    if clear:
        QuizQuestion.query.delete()
        db.session.commit()
        print("    [*] Cleared existing quiz questions")

    imported = 0
    skipped = 0

    for item in data:
        existing = QuizQuestion.query.get(item['id'])
        if existing:
            skipped += 1
            continue

        quiz = QuizQuestion(
            id=item['id'],
            module_id=item['module_id'],
            question=item['question'],
            choice_a=item['choice_a'],
            choice_b=item['choice_b'],
            choice_c=item['choice_c'],
            choice_d=item['choice_d'],
            correct_choice=item['correct_choice'],
            explanation=item.get('explanation'),
            display_order=item['display_order'],
            created_at=parse_datetime(item.get('created_at'))
        )
        db.session.add(quiz)
        imported += 1

    db.session.commit()
    return imported, skipped


def import_glossary_terms(data, clear=False):
    """Import glossary terms"""
    if clear:
        GlossaryTerm.query.delete()
        db.session.commit()
        print("    [*] Cleared existing glossary terms")

    imported = 0
    skipped = 0

    for item in data:
        existing = GlossaryTerm.query.get(item['id'])
        if existing:
            skipped += 1
            continue

        term = GlossaryTerm(
            id=item['id'],
            term=item['term'],
            definition=item['definition'],
            category=item.get('category'),
            display_order=item.get('display_order'),
            created_at=parse_datetime(item.get('created_at'))
        )
        db.session.add(term)
        imported += 1

    db.session.commit()
    return imported, skipped


def import_users(data, clear=False):
    """Import users"""
    if clear:
        User.query.delete()
        db.session.commit()
        print("    [*] Cleared existing users")

    imported = 0
    skipped = 0

    for item in data:
        existing = User.query.get(item['id'])
        if existing:
            skipped += 1
            continue

        user = User(
            id=item['id'],
            username=item['username'],
            first_name=item.get('first_name'),
            last_name=item.get('last_name'),
            employee_id=item.get('employee_id'),
            email=item.get('email'),
            is_preview_mode=item.get('is_preview_mode', False),
            created_at=parse_datetime(item.get('created_at')),
            last_login=parse_datetime(item.get('last_login'))
        )
        db.session.add(user)
        imported += 1

    db.session.commit()
    return imported, skipped


def import_user_progress(data, clear=False):
    """Import user progress"""
    if clear:
        UserProgress.query.delete()
        db.session.commit()
        print("    [*] Cleared existing user progress")

    imported = 0
    skipped = 0

    for item in data:
        existing = UserProgress.query.get(item['id'])
        if existing:
            skipped += 1
            continue

        progress = UserProgress(
            id=item['id'],
            user_id=item['user_id'],
            module_id=item['module_id'],
            completed=item.get('completed', False),
            completion_date=parse_datetime(item.get('completion_date'))
        )
        db.session.add(progress)
        imported += 1

    db.session.commit()
    return imported, skipped


def import_user_quiz_answers(data, clear=False):
    """Import user quiz answers"""
    if clear:
        UserQuizAnswer.query.delete()
        db.session.commit()
        print("    [*] Cleared existing user quiz answers")

    imported = 0
    skipped = 0

    for item in data:
        existing = UserQuizAnswer.query.get(item['id'])
        if existing:
            skipped += 1
            continue

        answer = UserQuizAnswer(
            id=item['id'],
            user_id=item['user_id'],
            quiz_question_id=item['quiz_question_id'],
            selected_choice=item.get('selected_choice'),
            is_correct=item.get('is_correct'),
            answer_order=item.get('answer_order'),
            answered_at=parse_datetime(item.get('answered_at'))
        )
        db.session.add(answer)
        imported += 1

    db.session.commit()
    return imported, skipped


def main():
    parser = argparse.ArgumentParser(description='Import JSON data into MySQL')
    parser.add_argument(
        '--input', '-i',
        default='exports',
        help='Input directory with JSON files (default: exports)'
    )
    parser.add_argument(
        '--tables', '-t',
        help='Comma-separated list of tables to import (default: all)'
    )
    parser.add_argument(
        '--clear', '-c',
        action='store_true',
        help='Clear existing data before importing'
    )
    parser.add_argument(
        '--create-tables',
        action='store_true',
        help='Create database tables before importing'
    )
    args = parser.parse_args()

    input_dir = Path(args.input)
    if not input_dir.exists():
        print(f"[!] Error: Input directory '{input_dir}' not found")
        sys.exit(1)

    print("=" * 60)
    print("TRINITY TRAINING GUIDE - DATA IMPORT")
    print("=" * 60)
    print(f"\n[*] Input directory: {input_dir.absolute()}")

    app = create_app()

    # Show database connection info (masked)
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_uri:
        # Mask password in connection string
        if '@' in db_uri:
            parts = db_uri.split('@')
            masked = parts[0].rsplit(':', 1)[0] + ':****@' + parts[1]
        else:
            masked = db_uri
        print(f"[*] Database: {masked}")

    with app.app_context():
        # Create tables if requested
        if args.create_tables:
            print("\n[*] Creating database tables...")
            db.create_all()
            print("    [+] Tables created")

        # Define import order (respects foreign key dependencies)
        import_order = [
            ('chapters', import_chapters),
            ('modules', import_modules),
            ('chapter_sections', import_chapter_sections),
            ('quiz_questions', import_quiz_questions),
            ('glossary_terms', import_glossary_terms),
            ('users', import_users),
            ('user_progress', import_user_progress),
            ('user_quiz_answers', import_user_quiz_answers)
        ]

        # Filter tables if specified
        if args.tables:
            requested = [t.strip() for t in args.tables.split(',')]
            import_order = [(name, func) for name, func in import_order if name in requested]

        results = {}

        for table_name, import_func in import_order:
            json_file = input_dir / f"{table_name}.json"

            if not json_file.exists():
                print(f"\n[!] {table_name}.json not found, skipping")
                continue

            print(f"\n[*] Importing {table_name}...")

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                imported, skipped = import_func(data, clear=args.clear)
                results[table_name] = {'imported': imported, 'skipped': skipped}
                print(f"    [+] Imported: {imported}, Skipped: {skipped}")

            except Exception as e:
                print(f"    [!] Error: {e}")
                results[table_name] = {'error': str(e)}

        # Summary
        print("\n" + "=" * 60)
        print("IMPORT SUMMARY")
        print("=" * 60)
        for table_name, result in results.items():
            if 'error' in result:
                print(f"   {table_name}: ERROR - {result['error']}")
            else:
                print(f"   {table_name}: {result['imported']} imported, {result['skipped']} skipped")

        print("\n[+] Import completed!")


if __name__ == '__main__':
    main()
