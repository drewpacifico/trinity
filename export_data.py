"""
Export SQLite data to JSON for MySQL migration

This script exports all data from the local SQLite database to JSON files
that can be imported into the MySQL production database on Hostinger.

Usage:
    python export_data.py                    # Export all tables
    python export_data.py --output exports   # Export to custom directory
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
from config import DevelopmentConfig


def create_app():
    """Create Flask app with development (SQLite) config"""
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)
    db.init_app(app)
    return app


def serialize_datetime(obj):
    """JSON serializer for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def export_chapters():
    """Export all chapters"""
    chapters = Chapter.query.order_by(Chapter.display_order).all()
    return [
        {
            'id': c.id,
            'title': c.title,
            'display_order': c.display_order,
            'created_at': c.created_at.isoformat() if c.created_at else None
        }
        for c in chapters
    ]


def export_modules():
    """Export all modules"""
    modules = Module.query.order_by(Module.chapter_id, Module.display_order).all()
    return [
        {
            'id': m.id,
            'chapter_id': m.chapter_id,
            'title': m.title,
            'content_markdown': m.content_markdown,
            'display_order': m.display_order,
            'created_at': m.created_at.isoformat() if m.created_at else None
        }
        for m in modules
    ]


def export_chapter_sections():
    """Export all chapter sections"""
    sections = ChapterSection.query.order_by(ChapterSection.chapter_id).all()
    return [
        {
            'id': s.id,
            'chapter_id': s.chapter_id,
            'section_type': s.section_type,
            'content_markdown': s.content_markdown,
            'created_at': s.created_at.isoformat() if s.created_at else None
        }
        for s in sections
    ]


def export_quiz_questions():
    """Export all quiz questions"""
    quizzes = QuizQuestion.query.order_by(QuizQuestion.module_id, QuizQuestion.display_order).all()
    return [
        {
            'id': q.id,
            'module_id': q.module_id,
            'question': q.question,
            'choice_a': q.choice_a,
            'choice_b': q.choice_b,
            'choice_c': q.choice_c,
            'choice_d': q.choice_d,
            'correct_choice': q.correct_choice,
            'explanation': q.explanation,
            'display_order': q.display_order,
            'created_at': q.created_at.isoformat() if q.created_at else None
        }
        for q in quizzes
    ]


def export_glossary_terms():
    """Export all glossary terms"""
    terms = GlossaryTerm.query.order_by(GlossaryTerm.display_order).all()
    return [
        {
            'id': t.id,
            'term': t.term,
            'definition': t.definition,
            'category': t.category,
            'display_order': t.display_order,
            'created_at': t.created_at.isoformat() if t.created_at else None
        }
        for t in terms
    ]


def export_users():
    """Export all users (excluding password hashes for security)"""
    users = User.query.all()
    return [
        {
            'id': u.id,
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'employee_id': u.employee_id,
            'email': u.email,
            'is_preview_mode': u.is_preview_mode,
            'created_at': u.created_at.isoformat() if u.created_at else None,
            'last_login': u.last_login.isoformat() if u.last_login else None
        }
        for u in users
    ]


def export_user_progress():
    """Export all user progress records"""
    progress = UserProgress.query.all()
    return [
        {
            'id': p.id,
            'user_id': p.user_id,
            'module_id': p.module_id,
            'completed': p.completed,
            'completion_date': p.completion_date.isoformat() if p.completion_date else None
        }
        for p in progress
    ]


def export_user_quiz_answers():
    """Export all user quiz answers"""
    answers = UserQuizAnswer.query.all()
    return [
        {
            'id': a.id,
            'user_id': a.user_id,
            'quiz_question_id': a.quiz_question_id,
            'selected_choice': a.selected_choice,
            'is_correct': a.is_correct,
            'answer_order': a.answer_order,
            'answered_at': a.answered_at.isoformat() if a.answered_at else None
        }
        for a in answers
    ]


def main():
    parser = argparse.ArgumentParser(description='Export SQLite data to JSON')
    parser.add_argument(
        '--output', '-o',
        default='exports',
        help='Output directory for JSON files (default: exports)'
    )
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("TRINITY TRAINING GUIDE - DATA EXPORT")
    print("=" * 60)

    app = create_app()

    with app.app_context():
        # Export all tables
        exports = {
            'chapters': export_chapters,
            'modules': export_modules,
            'chapter_sections': export_chapter_sections,
            'quiz_questions': export_quiz_questions,
            'glossary_terms': export_glossary_terms,
            'users': export_users,
            'user_progress': export_user_progress,
            'user_quiz_answers': export_user_quiz_answers
        }

        all_data = {}

        for table_name, export_func in exports.items():
            print(f"\n[*] Exporting {table_name}...")
            data = export_func()
            all_data[table_name] = data

            # Write individual file
            file_path = output_dir / f"{table_name}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"    [+] {len(data)} records -> {file_path}")

        # Write combined file
        combined_path = output_dir / "all_data.json"
        with open(combined_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False, default=serialize_datetime)

        print(f"\n[+] Combined export -> {combined_path}")

        # Summary
        print("\n" + "=" * 60)
        print("EXPORT SUMMARY")
        print("=" * 60)
        for table_name, data in all_data.items():
            print(f"   {table_name}: {len(data)} records")

        print(f"\n[+] Export completed! Files saved to: {output_dir.absolute()}")
        print("\n[*] Next steps:")
        print("   1. Copy the 'exports' folder to your Hostinger VPS")
        print("   2. Run: python import_data.py --input exports")


if __name__ == '__main__':
    main()
