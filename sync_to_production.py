"""
Database Sync Script - Sync Local SQLite to Production PostgreSQL

This script transfers data from the local SQLite database to the production
PostgreSQL database on the server. It handles all models and maintains
referential integrity.

Usage:
    python sync_to_production.py                    # Full sync
    python sync_to_production.py --dry-run          # Preview changes without applying
    python sync_to_production.py --tables chapters modules  # Sync specific tables only
    python sync_to_production.py --skip-users       # Skip user data
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask
from models import (
    db, Chapter, Module, ChapterSection, QuizQuestion,
    User, UserProgress, UserQuizAnswer, GlossaryTerm
)
from config import get_config, DevelopmentConfig, ProductionConfig


class DatabaseSyncer:
    """Syncs data from local SQLite to production PostgreSQL"""
    
    def __init__(self, dry_run=False, skip_users=False, tables=None):
        self.dry_run = dry_run
        self.skip_users = skip_users
        self.tables = tables or []
        
        # Create Flask apps for both environments
        self.local_app = Flask(__name__)
        self.local_app.config.from_object(DevelopmentConfig)
        db.init_app(self.local_app)
        
        self.prod_app = Flask(__name__)
        prod_config = ProductionConfig()
        if not prod_config.SQLALCHEMY_DATABASE_URI:
            raise ValueError(
                "Production database URI not configured!\n"
                "Please set DATABASE_URI or DATABASE_URL environment variable."
            )
        self.prod_app.config.from_object(prod_config)
        db.init_app(self.prod_app)
        
        # Create separate database sessions
        self.local_engine = create_engine(self.local_app.config['SQLALCHEMY_DATABASE_URI'])
        self.prod_engine = create_engine(self.prod_app.config['SQLALCHEMY_DATABASE_URI'])
        
        self.LocalSession = sessionmaker(bind=self.local_engine)
        self.ProdSession = sessionmaker(bind=self.prod_engine)
        
        self.stats = {
            'created': {},
            'updated': {},
            'skipped': {},
            'errors': {}
        }
        # User ID mapping: local_id -> prod_id
        self.user_id_map = {}
    
    def should_sync_table(self, table_name):
        """Check if a table should be synced based on filters"""
        if self.skip_users and table_name in ['users', 'user_progress', 'user_quiz_answers']:
            return False
        if self.tables and table_name not in self.tables:
            return False
        return True
    
    def sync_chapters(self):
        """Sync chapters (no dependencies)"""
        if not self.should_sync_table('chapters'):
            return
        
        print("\n[*] Syncing Chapters...")
        local_session = self.LocalSession()
        prod_session = self.ProdSession()
        
        try:
            local_chapters = local_session.query(Chapter).all()
            print(f"   Found {len(local_chapters)} chapters in local database")
            
            for local_chapter in local_chapters:
                # Check if exists in production
                prod_chapter = prod_session.query(Chapter).get(local_chapter.id)
                
                if prod_chapter:
                    # Update existing
                    prod_chapter.title = local_chapter.title
                    prod_chapter.display_order = local_chapter.display_order
                    prod_chapter.created_at = local_chapter.created_at
                    if not self.dry_run:
                        prod_session.commit()
                    self.stats['updated']['chapters'] = self.stats['updated'].get('chapters', 0) + 1
                    print(f"   [OK] Updated Chapter {local_chapter.id}: {local_chapter.title}")
                else:
                    # Create new
                    new_chapter = Chapter(
                        id=local_chapter.id,
                        title=local_chapter.title,
                        display_order=local_chapter.display_order,
                        created_at=local_chapter.created_at
                    )
                    prod_session.add(new_chapter)
                    if not self.dry_run:
                        prod_session.commit()
                    self.stats['created']['chapters'] = self.stats['created'].get('chapters', 0) + 1
                    print(f"   + Created Chapter {local_chapter.id}: {local_chapter.title}")
        
        except Exception as e:
            print(f"   [!] Error syncing chapters: {e}")
            self.stats['errors']['chapters'] = str(e)
            prod_session.rollback()
        finally:
            local_session.close()
            prod_session.close()
    
    def sync_modules(self):
        """Sync modules (depends on chapters)"""
        if not self.should_sync_table('modules'):
            return
        
        print("\n[*] Syncing Modules...")
        local_session = self.LocalSession()
        prod_session = self.ProdSession()
        
        try:
            local_modules = local_session.query(Module).all()
            print(f"   Found {len(local_modules)} modules in local database")
            
            for local_module in local_modules:
                # Verify chapter exists in production
                prod_chapter = prod_session.query(Chapter).get(local_module.chapter_id)
                if not prod_chapter:
                    print(f"   [!] Skipping Module {local_module.id}: Chapter {local_module.chapter_id} not found in production")
                    self.stats['skipped']['modules'] = self.stats['skipped'].get('modules', 0) + 1
                    continue
                
                prod_module = prod_session.query(Module).get(local_module.id)
                
                if prod_module:
                    # Update existing
                    prod_module.chapter_id = local_module.chapter_id
                    prod_module.title = local_module.title
                    prod_module.content_markdown = local_module.content_markdown
                    prod_module.display_order = local_module.display_order
                    prod_module.created_at = local_module.created_at
                    if not self.dry_run:
                        prod_session.commit()
                    self.stats['updated']['modules'] = self.stats['updated'].get('modules', 0) + 1
                    print(f"   [OK] Updated Module {local_module.id}: {local_module.title}")
                else:
                    # Create new
                    new_module = Module(
                        id=local_module.id,
                        chapter_id=local_module.chapter_id,
                        title=local_module.title,
                        content_markdown=local_module.content_markdown,
                        display_order=local_module.display_order,
                        created_at=local_module.created_at
                    )
                    prod_session.add(new_module)
                    if not self.dry_run:
                        prod_session.commit()
                    self.stats['created']['modules'] = self.stats['created'].get('modules', 0) + 1
                    print(f"   + Created Module {local_module.id}: {local_module.title}")
        
        except Exception as e:
            print(f"   [!] Error syncing modules: {e}")
            self.stats['errors']['modules'] = str(e)
            prod_session.rollback()
        finally:
            local_session.close()
            prod_session.close()
    
    def sync_chapter_sections(self):
        """Sync chapter sections (depends on chapters)"""
        if not self.should_sync_table('chapter_sections'):
            return
        
        print("\n[*] Syncing Chapter Sections...")
        local_session = self.LocalSession()
        prod_session = self.ProdSession()
        
        try:
            local_sections = local_session.query(ChapterSection).all()
            print(f"   Found {len(local_sections)} chapter sections in local database")
            
            for local_section in local_sections:
                # Verify chapter exists
                prod_chapter = prod_session.query(Chapter).get(local_section.chapter_id)
                if not prod_chapter:
                    print(f"   [!] Skipping Section {local_section.id}: Chapter {local_section.chapter_id} not found")
                    self.stats['skipped']['chapter_sections'] = self.stats['skipped'].get('chapter_sections', 0) + 1
                    continue
                
                # Check if exists (by chapter_id and section_type)
                prod_section = prod_session.query(ChapterSection).filter_by(
                    chapter_id=local_section.chapter_id,
                    section_type=local_section.section_type
                ).first()
                
                if prod_section:
                    # Update existing
                    prod_section.content_markdown = local_section.content_markdown
                    prod_section.created_at = local_section.created_at
                    if not self.dry_run:
                        prod_session.commit()
                    self.stats['updated']['chapter_sections'] = self.stats['updated'].get('chapter_sections', 0) + 1
                    print(f"   [OK] Updated Section {local_section.chapter_id}.{local_section.section_type}")
                else:
                    # Create new
                    new_section = ChapterSection(
                        chapter_id=local_section.chapter_id,
                        section_type=local_section.section_type,
                        content_markdown=local_section.content_markdown,
                        created_at=local_section.created_at
                    )
                    prod_session.add(new_section)
                    if not self.dry_run:
                        prod_session.commit()
                    self.stats['created']['chapter_sections'] = self.stats['created'].get('chapter_sections', 0) + 1
                    print(f"   + Created Section {local_section.chapter_id}.{local_section.section_type}")
        
        except Exception as e:
            print(f"   [!] Error syncing chapter sections: {e}")
            self.stats['errors']['chapter_sections'] = str(e)
            prod_session.rollback()
        finally:
            local_session.close()
            prod_session.close()
    
    def sync_quiz_questions(self):
        """Sync quiz questions (depends on modules)"""
        if not self.should_sync_table('quiz_questions'):
            return
        
        print("\n[*] Syncing Quiz Questions...")
        local_session = self.LocalSession()
        prod_session = self.ProdSession()
        
        try:
            local_quizzes = local_session.query(QuizQuestion).all()
            print(f"   Found {len(local_quizzes)} quiz questions in local database")
            
            for local_quiz in local_quizzes:
                # Verify module exists
                prod_module = prod_session.query(Module).get(local_quiz.module_id)
                if not prod_module:
                    print(f"   [!] Skipping Quiz {local_quiz.id}: Module {local_quiz.module_id} not found")
                    self.stats['skipped']['quiz_questions'] = self.stats['skipped'].get('quiz_questions', 0) + 1
                    continue
                
                prod_quiz = prod_session.query(QuizQuestion).get(local_quiz.id)
                
                if prod_quiz:
                    # Update existing
                    prod_quiz.module_id = local_quiz.module_id
                    prod_quiz.question = local_quiz.question
                    prod_quiz.choice_a = local_quiz.choice_a
                    prod_quiz.choice_b = local_quiz.choice_b
                    prod_quiz.choice_c = local_quiz.choice_c
                    prod_quiz.choice_d = local_quiz.choice_d
                    prod_quiz.correct_choice = local_quiz.correct_choice
                    prod_quiz.explanation = local_quiz.explanation
                    prod_quiz.display_order = local_quiz.display_order
                    prod_quiz.created_at = local_quiz.created_at
                    if not self.dry_run:
                        prod_session.commit()
                    self.stats['updated']['quiz_questions'] = self.stats['updated'].get('quiz_questions', 0) + 1
                else:
                    # Create new
                    new_quiz = QuizQuestion(
                        id=local_quiz.id,
                        module_id=local_quiz.module_id,
                        question=local_quiz.question,
                        choice_a=local_quiz.choice_a,
                        choice_b=local_quiz.choice_b,
                        choice_c=local_quiz.choice_c,
                        choice_d=local_quiz.choice_d,
                        correct_choice=local_quiz.correct_choice,
                        explanation=local_quiz.explanation,
                        display_order=local_quiz.display_order,
                        created_at=local_quiz.created_at
                    )
                    prod_session.add(new_quiz)
                    if not self.dry_run:
                        prod_session.commit()
                    self.stats['created']['quiz_questions'] = self.stats['created'].get('quiz_questions', 0) + 1
            
            print(f"   Processed {len(local_quizzes)} quiz questions")
        
        except Exception as e:
            print(f"   [!] Error syncing quiz questions: {e}")
            self.stats['errors']['quiz_questions'] = str(e)
            prod_session.rollback()
        finally:
            local_session.close()
            prod_session.close()
    
    def sync_glossary_terms(self):
        """Sync glossary terms (no dependencies)"""
        if not self.should_sync_table('glossary_terms'):
            return
        
        print("\n[*] Syncing Glossary Terms...")
        local_session = self.LocalSession()
        prod_session = self.ProdSession()
        
        try:
            local_terms = local_session.query(GlossaryTerm).all()
            print(f"   Found {len(local_terms)} glossary terms in local database")
            
            for local_term in local_terms:
                # Check if exists (by term name)
                prod_term = prod_session.query(GlossaryTerm).filter_by(term=local_term.term).first()
                
                if prod_term:
                    # Update existing
                    prod_term.definition = local_term.definition
                    prod_term.category = local_term.category
                    prod_term.display_order = local_term.display_order
                    prod_term.created_at = local_term.created_at
                    if not self.dry_run:
                        prod_session.commit()
                    self.stats['updated']['glossary_terms'] = self.stats['updated'].get('glossary_terms', 0) + 1
                else:
                    # Create new
                    new_term = GlossaryTerm(
                        term=local_term.term,
                        definition=local_term.definition,
                        category=local_term.category,
                        display_order=local_term.display_order,
                        created_at=local_term.created_at
                    )
                    prod_session.add(new_term)
                    if not self.dry_run:
                        prod_session.commit()
                    self.stats['created']['glossary_terms'] = self.stats['created'].get('glossary_terms', 0) + 1
            
            print(f"   Processed {len(local_terms)} glossary terms")
        
        except Exception as e:
            print(f"   [!] Error syncing glossary terms: {e}")
            self.stats['errors']['glossary_terms'] = str(e)
            prod_session.rollback()
        finally:
            local_session.close()
            prod_session.close()
    
    def sync_users(self):
        """Sync users (no dependencies) and build ID mapping"""
        if not self.should_sync_table('users'):
            return
        
        print("\n[*] Syncing Users...")
        local_session = self.LocalSession()
        prod_session = self.ProdSession()
        
        try:
            local_users = local_session.query(User).all()
            print(f"   Found {len(local_users)} users in local database")
            
            for local_user in local_users:
                # Check if exists (by username)
                prod_user = prod_session.query(User).filter_by(username=local_user.username).first()
                
                if prod_user:
                    # Update existing (but preserve password hash if user already has one)
                    if not prod_user.password_hash and local_user.password_hash:
                        prod_user.password_hash = local_user.password_hash
                    prod_user.first_name = local_user.first_name
                    prod_user.last_name = local_user.last_name
                    prod_user.employee_id = local_user.employee_id
                    prod_user.email = local_user.email
                    prod_user.is_preview_mode = local_user.is_preview_mode
                    prod_user.created_at = local_user.created_at
                    prod_user.last_login = local_user.last_login
                    if not self.dry_run:
                        prod_session.commit()
                    # Map local ID to production ID
                    self.user_id_map[local_user.id] = prod_user.id
                    self.stats['updated']['users'] = self.stats['updated'].get('users', 0) + 1
                    print(f"   [OK] Updated User: {local_user.username} (ID: {local_user.id} -> {prod_user.id})")
                else:
                    # Create new
                    new_user = User(
                        username=local_user.username,
                        first_name=local_user.first_name,
                        last_name=local_user.last_name,
                        employee_id=local_user.employee_id,
                        email=local_user.email,
                        password_hash=local_user.password_hash,
                        is_preview_mode=local_user.is_preview_mode,
                        created_at=local_user.created_at,
                        last_login=local_user.last_login
                    )
                    prod_session.add(new_user)
                    if not self.dry_run:
                        prod_session.flush()  # Flush to get the ID assigned
                        # Map local ID to production ID
                        self.user_id_map[local_user.id] = new_user.id
                        prod_session.commit()
                        print(f"   [+] Created User: {local_user.username} (ID: {local_user.id} -> {new_user.id})")
                    else:
                        # In dry-run, we can't get the actual ID, so skip mapping
                        print(f"   [+] Would create User: {local_user.username} (ID: {local_user.id} -> ?)")
                    self.stats['created']['users'] = self.stats['created'].get('users', 0) + 1
        
        except Exception as e:
            print(f"   [!] Error syncing users: {e}")
            self.stats['errors']['users'] = str(e)
            prod_session.rollback()
        finally:
            local_session.close()
            prod_session.close()
    
    def sync_user_progress(self):
        """Sync user progress (depends on users and modules)"""
        if not self.should_sync_table('user_progress'):
            return
        
        print("\n[*] Syncing User Progress...")
        local_session = self.LocalSession()
        prod_session = self.ProdSession()
        
        try:
            local_progress = local_session.query(UserProgress).all()
            print(f"   Found {len(local_progress)} progress records in local database")
            
            # Pre-fetch all modules to avoid repeated queries
            all_modules = {m.id for m in prod_session.query(Module.id).all()}
            
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            # Process in batches for better performance
            batch_size = 50
            for i, local_p in enumerate(local_progress, 1):
                # Show progress every 50 records
                if i % batch_size == 0:
                    print(f"   Processing... {i}/{len(local_progress)} ({created_count} created, {updated_count} updated, {skipped_count} skipped)")
                
                # Map local user_id to production user_id
                prod_user_id = self.user_id_map.get(local_p.user_id)
                if not prod_user_id:
                    skipped_count += 1
                    continue
                
                # Verify module exists
                if local_p.module_id not in all_modules:
                    skipped_count += 1
                    continue
                
                # Check if exists (by user_id and module_id)
                prod_p = prod_session.query(UserProgress).filter_by(
                    user_id=prod_user_id,
                    module_id=local_p.module_id
                ).first()
                
                if prod_p:
                    # Update existing
                    prod_p.completed = local_p.completed
                    prod_p.completion_date = local_p.completion_date
                    updated_count += 1
                else:
                    # Create new
                    new_p = UserProgress(
                        user_id=prod_user_id,
                        module_id=local_p.module_id,
                        completed=local_p.completed,
                        completion_date=local_p.completion_date
                    )
                    prod_session.add(new_p)
                    created_count += 1
                
                # Commit in batches (every 50 records) instead of one-by-one
                if not self.dry_run and i % batch_size == 0:
                    prod_session.commit()
            
            # Commit remaining records
            if not self.dry_run:
                prod_session.commit()
            
            self.stats['created']['user_progress'] = created_count
            self.stats['updated']['user_progress'] = updated_count
            self.stats['skipped']['user_progress'] = skipped_count
            
            print(f"   Completed: {created_count} created, {updated_count} updated, {skipped_count} skipped")
        
        except Exception as e:
            print(f"   [!] Error syncing user progress: {e}")
            self.stats['errors']['user_progress'] = str(e)
            prod_session.rollback()
        finally:
            local_session.close()
            prod_session.close()
    
    def sync_user_quiz_answers(self):
        """Sync user quiz answers (depends on users and quiz questions)"""
        if not self.should_sync_table('user_quiz_answers'):
            return
        
        print("\n[*] Syncing User Quiz Answers...")
        local_session = self.LocalSession()
        prod_session = self.ProdSession()
        
        try:
            local_answers = local_session.query(UserQuizAnswer).all()
            print(f"   Found {len(local_answers)} quiz answers in local database")
            
            # Pre-fetch all quiz IDs to avoid repeated queries
            all_quizzes = {q.id for q in prod_session.query(QuizQuestion.id).all()}
            
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            # Process in batches for better performance
            batch_size = 50
            for i, local_answer in enumerate(local_answers, 1):
                # Show progress every 50 records
                if i % batch_size == 0:
                    print(f"   Processing... {i}/{len(local_answers)} ({created_count} created, {updated_count} updated, {skipped_count} skipped)")
                
                # Map local user_id to production user_id
                prod_user_id = self.user_id_map.get(local_answer.user_id)
                if not prod_user_id:
                    skipped_count += 1
                    continue
                
                # Verify quiz exists
                if local_answer.quiz_question_id not in all_quizzes:
                    skipped_count += 1
                    continue
                
                # Check if exists (by user_id and quiz_question_id)
                prod_answer = prod_session.query(UserQuizAnswer).filter_by(
                    user_id=prod_user_id,
                    quiz_question_id=local_answer.quiz_question_id
                ).first()
                
                if prod_answer:
                    # Update existing
                    prod_answer.selected_choice = local_answer.selected_choice
                    prod_answer.is_correct = local_answer.is_correct
                    prod_answer.answer_order = local_answer.answer_order
                    prod_answer.answered_at = local_answer.answered_at
                    updated_count += 1
                else:
                    # Create new
                    new_answer = UserQuizAnswer(
                        user_id=prod_user_id,
                        quiz_question_id=local_answer.quiz_question_id,
                        selected_choice=local_answer.selected_choice,
                        is_correct=local_answer.is_correct,
                        answer_order=local_answer.answer_order,
                        answered_at=local_answer.answered_at
                    )
                    prod_session.add(new_answer)
                    created_count += 1
                
                # Commit in batches (every 50 records) instead of one-by-one
                if not self.dry_run and i % batch_size == 0:
                    prod_session.commit()
            
            # Commit remaining records
            if not self.dry_run:
                prod_session.commit()
            
            self.stats['created']['user_quiz_answers'] = created_count
            self.stats['updated']['user_quiz_answers'] = updated_count
            self.stats['skipped']['user_quiz_answers'] = skipped_count
            
            print(f"   Completed: {created_count} created, {updated_count} updated, {skipped_count} skipped")
        
        except Exception as e:
            print(f"   [!] Error syncing user quiz answers: {e}")
            self.stats['errors']['user_quiz_answers'] = str(e)
            prod_session.rollback()
        finally:
            local_session.close()
            prod_session.close()
    
    def sync_all(self):
        """Sync all tables in the correct order"""
        print("="*60)
        print("DATABASE SYNC: Local SQLite -> Production PostgreSQL")
        print("="*60)
        
        if self.dry_run:
            print("\n[DRY RUN MODE] - No changes will be made\n")
        
        # Sync in dependency order
        self.sync_chapters()
        self.sync_modules()
        self.sync_chapter_sections()
        self.sync_quiz_questions()
        self.sync_glossary_terms()
        
        if not self.skip_users:
            self.sync_users()
            self.sync_user_progress()
            self.sync_user_quiz_answers()
        
        self.print_summary()
    
    def print_summary(self):
        """Print sync summary statistics"""
        print("\n" + "="*60)
        print("SYNC SUMMARY")
        print("="*60)
        
        total_created = sum(self.stats['created'].values())
        total_updated = sum(self.stats['updated'].values())
        total_skipped = sum(self.stats['skipped'].values())
        
        print(f"\nCreated: {total_created}")
        for table, count in self.stats['created'].items():
            if count > 0:
                print(f"   • {table}: {count}")
        
        print(f"\nUpdated: {total_updated}")
        for table, count in self.stats['updated'].items():
            if count > 0:
                print(f"   • {table}: {count}")
        
        if total_skipped > 0:
            print(f"\nSkipped: {total_skipped}")
            for table, count in self.stats['skipped'].items():
                if count > 0:
                    print(f"   • {table}: {count}")
        
        if self.stats['errors']:
            print(f"\n[WARNING] Errors:")
            for table, error in self.stats['errors'].items():
                print(f"   • {table}: {error}")
        
        if self.dry_run:
            print("\n[WARNING] This was a dry run. No changes were made.")
            print("   Run without --dry-run to apply changes.")
        else:
            print("\n[SUCCESS] Sync completed!")
        
        print("="*60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Sync local SQLite database to production PostgreSQL'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying them'
    )
    parser.add_argument(
        '--skip-users',
        action='store_true',
        help='Skip syncing user data (users, progress, answers)'
    )
    parser.add_argument(
        '--tables',
        nargs='+',
        help='Only sync specific tables (e.g., --tables chapters modules)',
        choices=['chapters', 'modules', 'chapter_sections', 'quiz_questions',
                 'glossary_terms', 'users', 'user_progress', 'user_quiz_answers']
    )
    
    args = parser.parse_args()
    
    try:
        syncer = DatabaseSyncer(
            dry_run=args.dry_run,
            skip_users=args.skip_users,
            tables=args.tables
        )
        syncer.sync_all()
    
    except ValueError as e:
        print(f"\n[ERROR] Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Sync failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

