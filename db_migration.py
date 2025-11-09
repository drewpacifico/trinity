"""
Database Migration Script for Trinity Training Guide

This script extracts data from existing files and populates the database:
- Chapters, modules, and content from project.md
- Quiz questions from main.py
- Glossary terms from project.md

Usage:
    python db_migration.py                    # Full migration
    python db_migration.py --chapters-only    # Only migrate chapters/modules
    python db_migration.py --quizzes-only     # Only migrate quiz questions
    python db_migration.py --glossary-only    # Only migrate glossary
    python db_migration.py --verify           # Verify migration results
"""

import sys
import re
import ast
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask
from models import (
    db, Chapter, Module, ChapterSection, QuizQuestion, 
    GlossaryTerm, User, get_or_create_user
)
from config import get_config
import os


def create_app():
    """Create Flask application with database configuration"""
    app = Flask(__name__)
    # Use production config if FLASK_ENV=production, otherwise development
    env = os.environ.get('FLASK_ENV', 'development')
    config = get_config(env)
    app.config.from_object(config)
    db.init_app(app)
    return app


class ContentMigrator:
    """Migrates chapter content from project.md"""
    
    def __init__(self, project_md_path='project.md'):
        self.project_md_path = Path(project_md_path)
        if not self.project_md_path.exists():
            raise FileNotFoundError(f"Could not find {project_md_path}")
        
        self.content = self.project_md_path.read_text(encoding='utf-8')
    
    def extract_chapters(self):
        """
        Extract chapter information from project.md
        Returns list of dicts: [{'id': 1, 'title': '...', 'order': 1}, ...]
        """
        chapters = {}
        
        # Look for both "Chapter X:" and "CHAPTER X:" patterns
        patterns = [
            re.compile(r"^Chapter\s+(\d+):\s*(.+)$", re.IGNORECASE | re.MULTILINE),
            re.compile(r"^CHAPTER\s+(\d+):\s*(.+)$", re.IGNORECASE | re.MULTILINE)
        ]
        
        for pattern in patterns:
            for match in pattern.finditer(self.content):
                chapter_id = int(match.group(1))
                title = match.group(2).strip()
                
                # Convert all-caps to title case
                if title.isupper():
                    title = title.title()
                
                if chapter_id not in chapters:
                    chapters[chapter_id] = {
                        'id': chapter_id,
                        'title': title,
                        'order': chapter_id
                    }
        
        return sorted(chapters.values(), key=lambda x: x['order'])
    
    def extract_chapter_content(self, chapter_id):
        """
        Extract all content for a specific chapter.
        Returns dict with: intro, modules, summary, action_items
        """
        chapter_pattern = re.compile(rf"^CHAPTER\s+{chapter_id}:\s*(.+)$", re.MULTILINE)
        next_chapter_pattern = re.compile(r"^CHAPTER\s+\d+:\s*", re.MULTILINE)
        module_pattern = re.compile(r"^Module\s+(\d+\.\d+):\s*(.+)$", re.MULTILINE)
        summary_pattern = re.compile(rf"^CHAPTER\s+{chapter_id}\s+SUMMARY", re.IGNORECASE | re.MULTILINE)
        action_items_pattern = re.compile(rf"^ACTION\s+ITEMS\s+FOR\s+CHAPTER\s+{chapter_id}", re.IGNORECASE | re.MULTILINE)
        
        lines = self.content.splitlines()
        in_chapter = False
        chapter_title = None
        intro_lines = []
        modules = []
        current_module = None
        summary_lines = []
        action_items_lines = []
        in_summary = False
        in_action_items = False
        
        for raw_line in lines:
            stripped = raw_line.strip()
            
            # Check if entering this chapter
            chapter_match = chapter_pattern.match(stripped)
            if not in_chapter and chapter_match:
                in_chapter = True
                chapter_title = chapter_match.group(1).strip()
                if chapter_title.isupper():
                    chapter_title = chapter_title.title()
                continue
            
            if not in_chapter:
                continue
            
            # Check if entering next chapter (exit)
            if next_chapter_pattern.match(stripped):
                break
            
            # Check for summary section
            if summary_pattern.match(stripped):
                in_summary = True
                in_action_items = False
                if current_module:
                    modules.append(current_module)
                    current_module = None
                continue
            
            # Check for action items section
            if action_items_pattern.match(stripped):
                in_action_items = True
                in_summary = False
                if current_module:
                    modules.append(current_module)
                    current_module = None
                continue
            
            # Check for module header
            module_match = module_pattern.match(stripped)
            if module_match and not in_summary and not in_action_items:
                if current_module:
                    modules.append(current_module)
                current_module = {
                    'id': module_match.group(1),
                    'title': module_match.group(2).strip(),
                    'content': []
                }
                continue
            
            # Collect content
            if in_summary:
                summary_lines.append(raw_line)
            elif in_action_items:
                action_items_lines.append(raw_line)
            elif current_module is not None:
                current_module['content'].append(raw_line)
            else:
                if stripped:  # Only add non-empty lines to intro
                    intro_lines.append(raw_line)
        
        # Add last module if exists
        if current_module:
            modules.append(current_module)
        
        return {
            'chapter_id': chapter_id,
            'chapter_title': chapter_title,
            'intro': '\n'.join(intro_lines).strip() if intro_lines else None,
            'modules': modules,
            'summary': '\n'.join(summary_lines).strip() if summary_lines else None,
            'action_items': '\n'.join(action_items_lines).strip() if action_items_lines else None
        }
    
    def migrate_chapters(self):
        """Migrate all chapters to database"""
        chapters_data = self.extract_chapters()
        
        print(f"\n[*] Migrating {len(chapters_data)} chapters...")
        
        for chapter_data in chapters_data:
            # Check if chapter already exists
            existing = Chapter.query.get(chapter_data['id'])
            if existing:
                print(f"   • Chapter {chapter_data['id']} already exists, skipping")
                continue
            
            chapter = Chapter(
                id=chapter_data['id'],
                title=chapter_data['title'],
                display_order=chapter_data['order']
            )
            db.session.add(chapter)
            print(f"   [+] Chapter {chapter_data['id']}: {chapter_data['title']}")
        
        db.session.commit()
        print(f"[+] Chapters migrated successfully\n")
    
    def migrate_modules(self):
        """Migrate all modules and chapter sections"""
        chapters = Chapter.query.order_by(Chapter.display_order).all()
        
        total_modules = 0
        total_sections = 0
        
        for chapter in chapters:
            print(f"\n[*] Migrating Chapter {chapter.id}: {chapter.title}")
            
            # Extract chapter content
            content = self.extract_chapter_content(chapter.id)
            
            if not content['chapter_title']:
                print(f"   ⚠️  No content found for Chapter {chapter.id}")
                continue
            
            # Migrate chapter sections (intro, summary, action_items)
            if content['intro']:
                existing = ChapterSection.query.filter_by(
                    chapter_id=chapter.id,
                    section_type='intro'
                ).first()
                
                if not existing:
                    intro = ChapterSection(
                        chapter_id=chapter.id,
                        section_type='intro',
                        content_markdown=content['intro']
                    )
                    db.session.add(intro)
                    print(f"   [+] Intro section")
                    total_sections += 1
            
            if content['summary']:
                existing = ChapterSection.query.filter_by(
                    chapter_id=chapter.id,
                    section_type='summary'
                ).first()
                
                if not existing:
                    summary = ChapterSection(
                        chapter_id=chapter.id,
                        section_type='summary',
                        content_markdown=content['summary']
                    )
                    db.session.add(summary)
                    print(f"   [+] Summary section")
                    total_sections += 1
            
            if content['action_items']:
                existing = ChapterSection.query.filter_by(
                    chapter_id=chapter.id,
                    section_type='action_items'
                ).first()
                
                if not existing:
                    action_items = ChapterSection(
                        chapter_id=chapter.id,
                        section_type='action_items',
                        content_markdown=content['action_items']
                    )
                    db.session.add(action_items)
                    print(f"   [+] Action Items section")
                    total_sections += 1
            
            # Migrate modules
            for idx, mod_data in enumerate(content['modules']):
                existing = Module.query.get(mod_data['id'])
                if existing:
                    print(f"   • Module {mod_data['id']} already exists, skipping")
                    continue
                
                module = Module(
                    id=mod_data['id'],
                    chapter_id=chapter.id,
                    title=mod_data['title'],
                    content_markdown='\n'.join(mod_data['content']),
                    display_order=idx + 1
                )
                db.session.add(module)
                print(f"   [+] Module {mod_data['id']}: {mod_data['title']}")
                total_modules += 1
            
            db.session.commit()
        
        print(f"\n[+] Migrated {total_modules} modules and {total_sections} chapter sections\n")


class QuizMigrator:
    """Migrates quiz questions from main.py"""
    
    def __init__(self, main_py_path='main.py'):
        self.main_py_path = Path(main_py_path)
        if not self.main_py_path.exists():
            raise FileNotFoundError(f"Could not find {main_py_path}")
        
        self.content = self.main_py_path.read_text(encoding='utf-8')
    
    def extract_quiz_arrays(self):
        """
        Extract all MODULE_X_Y_QUIZ arrays from main.py
        Returns dict: {'MODULE_1_1_QUIZ': [...], 'MODULE_1_2_QUIZ': [...]}
        """
        quiz_arrays = {}
        
        lines = self.content.splitlines()
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for MODULE_X_Y_QUIZ = [
            match = re.match(r'^(MODULE_\d+_\d+_QUIZ)\s*=\s*\[', line)
            if match:
                var_name = match.group(1)
                
                # Collect lines until we find the closing bracket
                array_lines = [lines[i]]
                bracket_count = lines[i].count('[') - lines[i].count(']')
                i += 1
                
                while i < len(lines) and bracket_count > 0:
                    array_lines.append(lines[i])
                    bracket_count += lines[i].count('[') - lines[i].count(']')
                    i += 1
                
                # Parse the complete array
                try:
                    array_str = '\n'.join(array_lines)
                    # Extract just the assignment value (after the =)
                    array_str = array_str.split('=', 1)[1].strip()
                    quiz_data = ast.literal_eval(array_str)
                    quiz_arrays[var_name] = quiz_data
                    print(f"   [+] Found {var_name}: {len(quiz_data)} questions")
                except Exception as e:
                    print(f"   [!] Error parsing {var_name}: {e}")
            else:
                i += 1
        
        return quiz_arrays
    
    def parse_module_id_from_var_name(self, var_name):
        """
        Convert MODULE_1_2_QUIZ to module_id '1.2'
        """
        match = re.match(r'MODULE_(\d+)_(\d+)_QUIZ', var_name)
        if match:
            return f"{match.group(1)}.{match.group(2)}"
        return None
    
    def migrate_quizzes(self):
        """Migrate all quiz questions to database"""
        print("\n[*] Extracting quiz questions from main.py...")
        quiz_arrays = self.extract_quiz_arrays()
        
        total_questions = 0
        
        for var_name, questions in quiz_arrays.items():
            module_id = self.parse_module_id_from_var_name(var_name)
            if not module_id:
                print(f"   ⚠️  Could not parse module ID from {var_name}")
                continue
            
            # Verify module exists
            module = Module.query.get(module_id)
            if not module:
                print(f"   ⚠️  Module {module_id} not found in database, skipping {var_name}")
                continue
            
            print(f"\n   [*] Migrating {var_name} -> Module {module_id}")
            
            for idx, q in enumerate(questions):
                try:
                    # Check if question already exists
                    existing = QuizQuestion.query.get(q['id'])
                    if existing:
                        print(f"      • {q['id']} already exists, skipping")
                        continue
                    
                    # Verify question structure
                    if 'choices' not in q:
                        print(f"      [!] {q.get('id', 'unknown')}: missing 'choices' field - skipping")
                        continue
                    if 'correct_index' not in q:
                        print(f"      [!] {q.get('id', 'unknown')}: missing 'correct_index' field - skipping")
                        continue
                    
                    # Convert correct_index to letter
                    choices = q['choices']
                    correct_index = q['correct_index']
                    correct_letter = ['a', 'b', 'c', 'd'][correct_index]
                except Exception as e:
                    print(f"      [!] Error with question: {e}")
                    print(f"          Question data: {q}")
                    continue
                
                # Create quiz question
                quiz = QuizQuestion(
                    id=q['id'],
                    module_id=module_id,
                    question=q['question'],
                    choice_a=choices[0],
                    choice_b=choices[1],
                    choice_c=choices[2],
                    choice_d=choices[3],
                    correct_choice=correct_letter,
                    explanation=q.get('explanation', ''),
                    display_order=idx + 1
                )
                db.session.add(quiz)
                print(f"      [+] {q['id']}")
                total_questions += 1
            
            db.session.commit()
        
        print(f"\n[+] Migrated {total_questions} quiz questions\n")


class GlossaryMigrator:
    """Migrates glossary terms from project.md"""
    
    def __init__(self, project_md_path='project.md'):
        self.project_md_path = Path(project_md_path)
        if not self.project_md_path.exists():
            raise FileNotFoundError(f"Could not find {project_md_path}")
        
        self.content = self.project_md_path.read_text(encoding='utf-8')
    
    def extract_glossary_terms(self):
        """
        Extract glossary terms from project.md
        Returns list of dicts: [{'term': '...', 'definition': '...'}, ...]
        """
        terms = []
        
        # Find glossary section
        glossary_pattern = re.compile(r'^GLOSSARY OF FREIGHT AGENT TERMS', re.IGNORECASE | re.MULTILINE)
        match = glossary_pattern.search(self.content)
        
        if not match:
            print("   ⚠️  Glossary section not found")
            return terms
        
        # Get content after glossary header
        glossary_start = match.end()
        glossary_content = self.content[glossary_start:]
        
        # Pattern for term definitions (bold term followed by definition)
        # Looks for: **Term**: Definition or **Term** - Definition
        term_pattern = re.compile(
            r'\*\*([^*]+)\*\*[:\-]\s*(.+?)(?=\n\*\*|\n\n|\Z)',
            re.DOTALL
        )
        
        for match in term_pattern.finditer(glossary_content):
            term = match.group(1).strip()
            definition = match.group(2).strip()
            
            # Clean up definition (remove extra whitespace)
            definition = ' '.join(definition.split())
            
            if term and definition:
                terms.append({
                    'term': term,
                    'definition': definition
                })
        
        return terms
    
    def migrate_glossary(self):
        """Migrate glossary terms to database"""
        print("\n[*] Migrating glossary terms...")
        
        terms = self.extract_glossary_terms()
        
        if not terms:
            print("   [!] No glossary terms found")
            return
        
        migrated = 0
        for idx, term_data in enumerate(terms):
            # Check if term already exists
            existing = GlossaryTerm.query.filter_by(
                term=term_data['term']
            ).first()
            
            if existing:
                continue
            
            term = GlossaryTerm(
                term=term_data['term'],
                definition=term_data['definition'],
                display_order=idx + 1
            )
            db.session.add(term)
            migrated += 1
        
        db.session.commit()
        print(f"[+] Migrated {migrated} glossary terms\n")


def verify_migration():
    """Verify that migration completed successfully"""
    print("\n" + "="*60)
    print("MIGRATION VERIFICATION")
    print("="*60)
    
    # Count records
    chapter_count = Chapter.query.count()
    module_count = Module.query.count()
    section_count = ChapterSection.query.count()
    quiz_count = QuizQuestion.query.count()
    glossary_count = GlossaryTerm.query.count()
    
    print(f"\n[*] Database Statistics:")
    print(f"   • Chapters: {chapter_count}")
    print(f"   • Modules: {module_count}")
    print(f"   • Chapter Sections: {section_count}")
    print(f"   • Quiz Questions: {quiz_count}")
    print(f"   • Glossary Terms: {glossary_count}")
    
    # Verify data integrity
    print(f"\n[*] Data Integrity Checks:")
    
    # Check each chapter has modules
    issues = []
    for chapter in Chapter.query.all():
        if len(chapter.modules) == 0:
            issues.append(f"Chapter {chapter.id} has no modules")
    
    # Check each module has quizzes
    modules_without_quizzes = []
    for module in Module.query.all():
        if len(module.quiz_questions) == 0:
            modules_without_quizzes.append(module.id)
    
    if modules_without_quizzes:
        issues.append(f"{len(modules_without_quizzes)} modules without quizzes: {', '.join(modules_without_quizzes[:5])}...")
    
    # Check quiz question IDs match module IDs
    quiz_mismatch = []
    for quiz in QuizQuestion.query.all():
        # Quiz ID format: qX_Y_Z, Module ID format: X.Y
        quiz_parts = quiz.id.split('_')
        if len(quiz_parts) >= 3:
            expected_module = f"{quiz_parts[0][1:]}.{quiz_parts[1]}"
            if quiz.module_id != expected_module:
                quiz_mismatch.append(f"{quiz.id} → {quiz.module_id} (expected {expected_module})")
    
    if quiz_mismatch:
        issues.append(f"{len(quiz_mismatch)} quiz questions with mismatched module IDs")
    
    if issues:
        print("   [!] Issues found:")
        for issue in issues:
            print(f"      - {issue}")
    else:
        print("   [+] All integrity checks passed!")
    
    # Sample data
    print(f"\n[*] Sample Data:")
    
    # Show first chapter with modules
    first_chapter = Chapter.query.order_by(Chapter.display_order).first()
    if first_chapter:
        print(f"\n   Chapter {first_chapter.id}: {first_chapter.title}")
        for module in first_chapter.modules[:3]:
            print(f"      • {module.id}: {module.title} ({len(module.quiz_questions)} quizzes)")
    
    # Show sample quiz
    sample_quiz = QuizQuestion.query.first()
    if sample_quiz:
        print(f"\n   Sample Quiz: {sample_quiz.id}")
        print(f"      Question: {sample_quiz.question[:80]}...")
        print(f"      Correct: {sample_quiz.correct_choice.upper()}")
    
    print("\n" + "="*60)


def main():
    """Main migration entry point"""
    parser = argparse.ArgumentParser(
        description='Migrate Trinity Training Guide data to database'
    )
    parser.add_argument(
        '--chapters-only',
        action='store_true',
        help='Only migrate chapters and modules'
    )
    parser.add_argument(
        '--quizzes-only',
        action='store_true',
        help='Only migrate quiz questions'
    )
    parser.add_argument(
        '--glossary-only',
        action='store_true',
        help='Only migrate glossary terms'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify migration results'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("TRINITY TRAINING GUIDE - DATABASE MIGRATION")
    print("="*60)
    
    app = create_app()
    
    try:
        with app.app_context():
            # Determine what to migrate
            migrate_all = not (args.chapters_only or args.quizzes_only or args.glossary_only or args.verify)
            
            if args.verify:
                verify_migration()
                return
            
            # Migrate chapters and modules
            if migrate_all or args.chapters_only:
                content_migrator = ContentMigrator()
                content_migrator.migrate_chapters()
                content_migrator.migrate_modules()
            
            # Migrate quiz questions
            if migrate_all or args.quizzes_only:
                quiz_migrator = QuizMigrator()
                quiz_migrator.migrate_quizzes()
            
            # Migrate glossary
            if migrate_all or args.glossary_only:
                glossary_migrator = GlossaryMigrator()
                glossary_migrator.migrate_glossary()
            
            # Always verify at the end of a full migration
            if migrate_all:
                verify_migration()
            
            print("\n[+] Migration completed successfully!")
            print("\n[*] Next steps:")
            print("   1. Verify data: python db_migration.py --verify")
            print("   2. Test queries: python -i -c 'from models import *'")
            print("   3. Refactor main.py to use database")
            
    except Exception as e:
        print(f"\n[!] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

