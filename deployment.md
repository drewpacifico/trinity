# Database Migration & Deployment Plan

## Executive Summary

**Current Architecture:**
- All quiz questions are hard-coded Python dictionaries in `main.py` (~1,300+ lines of quiz data)
- Training content is parsed from `project.md` at runtime (no persistence)
- User progress stored in Flask sessions (lost when cookies cleared)
- No multi-user support or persistent tracking

**Proposed Architecture:**
- SQLite database for development and testing
- PostgreSQL for production deployment
- Persistent user accounts with progress tracking
- Content managed through database (easier updates)
- Answer randomization per user (prevent memorization)

**Benefits:**
1. ✅ **Scalability** - Support multiple users with individual progress
2. ✅ **Data Persistence** - No lost progress from cleared sessions
3. ✅ **Content Management** - Update quizzes/content without code changes
4. ✅ **Analytics** - Track completion rates, common wrong answers, time spent
5. ✅ **Randomization** - Shuffle answer order per user/attempt
6. ✅ **Production Ready** - Easy PostgreSQL migration for server deployment

---

## Phase 1: Database Design

### Database Schema

#### Tables

**1. chapters**
```sql
CREATE TABLE chapters (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**2. modules**
```sql
CREATE TABLE modules (
    id VARCHAR(10) PRIMARY KEY,  -- e.g., "1.1", "2.3"
    chapter_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    content_markdown TEXT,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id)
);
```

**3. chapter_sections**
```sql
CREATE TABLE chapter_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id INTEGER NOT NULL,
    section_type VARCHAR(50) NOT NULL,  -- 'intro', 'summary', 'action_items'
    content_markdown TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id)
);
```

**4. quiz_questions**
```sql
CREATE TABLE quiz_questions (
    id VARCHAR(20) PRIMARY KEY,  -- e.g., "q1_1_1"
    module_id VARCHAR(10) NOT NULL,
    question TEXT NOT NULL,
    choice_a TEXT NOT NULL,
    choice_b TEXT NOT NULL,
    choice_c TEXT NOT NULL,
    choice_d TEXT NOT NULL,
    correct_choice CHAR(1) NOT NULL,  -- 'a', 'b', 'c', or 'd'
    explanation TEXT,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules(id)
);
```

**5. users**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),  -- For future auth
    is_preview_mode BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

**6. user_progress**
```sql
CREATE TABLE user_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    module_id VARCHAR(10) NOT NULL,
    completed BOOLEAN DEFAULT 0,
    completion_date TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (module_id) REFERENCES modules(id),
    UNIQUE(user_id, module_id)
);
```

**7. user_quiz_answers**
```sql
CREATE TABLE user_quiz_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    quiz_question_id VARCHAR(20) NOT NULL,
    selected_choice CHAR(1),  -- 'a', 'b', 'c', or 'd'
    is_correct BOOLEAN,
    answer_order TEXT,  -- JSON: ["b","d","a","c"] - shuffled order for this user
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (quiz_question_id) REFERENCES quiz_questions(id),
    UNIQUE(user_id, quiz_question_id)
);
```

**8. glossary_terms**
```sql
CREATE TABLE glossary_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term VARCHAR(255) NOT NULL,
    definition TEXT NOT NULL,
    category VARCHAR(100),
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Phase 2: Migration Script Development

### Step 2.1: Create Database Migration Tool

Create `db_migration.py`:

```python
import sqlite3
import json
from pathlib import Path
import re

class DatabaseMigrator:
    def __init__(self, db_path='training_guide.db'):
        self.db_path = db_path
        self.conn = None
        
    def initialize_database(self):
        """Create all tables with schema"""
        # Execute schema.sql
        pass
        
    def migrate_chapters(self, project_md_path):
        """Parse project.md and extract chapter info"""
        pass
        
    def migrate_modules(self, project_md_path):
        """Parse project.md and extract module content"""
        pass
        
    def migrate_quiz_questions(self, main_py_path):
        """Extract quiz questions from main.py"""
        pass
        
    def migrate_glossary(self, project_md_path):
        """Extract glossary terms from project.md"""
        pass
        
    def export_to_postgresql(self, pg_connection_string):
        """Export SQLite data to PostgreSQL"""
        pass
```

### Step 2.2: Extract Quiz Questions from main.py

The migration script needs to parse the existing quiz dictionaries:

```python
def migrate_quiz_questions_from_main_py(self):
    """
    Parse main.py to extract all quiz questions.
    Convert from:
        MODULE_1_1_QUIZ = [
            {
                "id": "q1_1_1",
                "question": "...",
                "choices": ["A", "B", "C", "D"],
                "correct_index": 1,
                "explanation": "..."
            }
        ]
    
    To database records with choices as separate columns.
    """
    # Use regex to find all MODULE_*_QUIZ arrays
    # Parse the dictionary structure
    # Insert into quiz_questions table
    pass
```

### Step 2.3: Extract Content from project.md

```python
def migrate_content_from_project_md(self):
    """
    Parse project.md using existing extract_chapter_content() logic.
    Store:
    - Chapter titles
    - Module content (keep markdown format)
    - Chapter intros, summaries, action items
    """
    # Reuse existing parse logic from main.py
    # Insert into modules and chapter_sections tables
    pass
```

---

## Phase 3: Application Refactoring

### Step 3.1: Create Database Models (SQLAlchemy)

Create `models.py`:

```python
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Chapter(db.Model):
    __tablename__ = 'chapters'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    display_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    modules = db.relationship('Module', back_populates='chapter', order_by='Module.display_order')
    sections = db.relationship('ChapterSection', back_populates='chapter')

class Module(db.Model):
    __tablename__ = 'modules'
    id = db.Column(db.String(10), primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content_markdown = db.Column(db.Text)
    display_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    chapter = db.relationship('Chapter', back_populates='modules')
    quiz_questions = db.relationship('QuizQuestion', back_populates='module', order_by='QuizQuestion.display_order')

class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'
    id = db.Column(db.String(20), primary_key=True)
    module_id = db.Column(db.String(10), db.ForeignKey('modules.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    choice_a = db.Column(db.Text, nullable=False)
    choice_b = db.Column(db.Text, nullable=False)
    choice_c = db.Column(db.Text, nullable=False)
    choice_d = db.Column(db.Text, nullable=False)
    correct_choice = db.Column(db.String(1), nullable=False)
    explanation = db.Column(db.Text)
    display_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    module = db.relationship('Module', back_populates='quiz_questions')
    
    def get_choices_shuffled(self, seed=None):
        """Return shuffled choices for this user/attempt"""
        # Implement shuffling logic with optional seed
        pass

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True)
    is_preview_mode = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    progress = db.relationship('UserProgress', back_populates='user')
    quiz_answers = db.relationship('UserQuizAnswer', back_populates='user')

class UserProgress(db.Model):
    __tablename__ = 'user_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    module_id = db.Column(db.String(10), db.ForeignKey('modules.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime)
    
    user = db.relationship('User', back_populates='progress')
    module = db.relationship('Module')

class UserQuizAnswer(db.Model):
    __tablename__ = 'user_quiz_answers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_question_id = db.Column(db.String(20), db.ForeignKey('quiz_questions.id'), nullable=False)
    selected_choice = db.Column(db.String(1))
    is_correct = db.Column(db.Boolean)
    answer_order = db.Column(db.Text)  # JSON string
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', back_populates='quiz_answers')
    quiz_question = db.relationship('QuizQuestion')
```

### Step 3.2: Refactor main.py to use Database

**Changes needed:**

1. **Remove hard-coded quiz arrays** (lines 11-1279)
   - Replace with database queries

2. **Replace `extract_chapter_content()`**
   ```python
   def get_chapter_content(chapter_id):
       """Fetch chapter content from database"""
       chapter = Chapter.query.get(chapter_id)
       modules = Module.query.filter_by(chapter_id=chapter_id).order_by(Module.display_order).all()
       # ... return structured data
   ```

3. **Replace `build_pages()` logic**
   - Query database instead of parsing markdown
   - Still build page list for navigation

4. **Update session management**
   - Replace session-based progress with User/UserProgress queries
   - Create default "anonymous" user for testing
   - Add user authentication later

5. **Update quiz answer checking**
   ```python
   def check_quiz_answer(user_id, quiz_id, selected_index):
       quiz = QuizQuestion.query.get(quiz_id)
       user_answer = UserQuizAnswer.query.filter_by(
           user_id=user_id,
           quiz_question_id=quiz_id
       ).first()
       
       # Get shuffled order for this user
       if user_answer and user_answer.answer_order:
           order = json.loads(user_answer.answer_order)
           selected_choice = order[selected_index]
       
       is_correct = (selected_choice == quiz.correct_choice)
       # Save answer to database
       # Update module completion status
   ```

---

## Phase 4: Answer Randomization Implementation

### Randomization Strategy

1. **First Quiz Attempt:**
   - Generate random order: `["b", "c", "a", "d"]`
   - Store in `user_quiz_answers.answer_order`
   - Display choices in shuffled order

2. **Subsequent Attempts:**
   - Use same order from `answer_order` field
   - Consistent experience for review

3. **Reset Option:**
   - Admin can reset user progress
   - Generates new random order

### Implementation Example

```python
import random
import json

def get_quiz_for_user(user_id, quiz_id):
    """Get quiz with shuffled answers for user"""
    quiz = QuizQuestion.query.get(quiz_id)
    user_answer = UserQuizAnswer.query.filter_by(
        user_id=user_id,
        quiz_question_id=quiz_id
    ).first()
    
    if user_answer and user_answer.answer_order:
        # Use existing order
        order = json.loads(user_answer.answer_order)
    else:
        # Generate new random order
        order = ['a', 'b', 'c', 'd']
        random.shuffle(order)
        
        # Save for consistency
        if not user_answer:
            user_answer = UserQuizAnswer(
                user_id=user_id,
                quiz_question_id=quiz_id,
                answer_order=json.dumps(order)
            )
            db.session.add(user_answer)
            db.session.commit()
    
    # Return shuffled choices
    choices_dict = {
        'a': quiz.choice_a,
        'b': quiz.choice_b,
        'c': quiz.choice_c,
        'd': quiz.choice_d
    }
    
    return {
        'id': quiz.id,
        'question': quiz.question,
        'choices': [choices_dict[letter] for letter in order],
        'correct_index': order.index(quiz.correct_choice),
        'explanation': quiz.explanation,
        'answer_order': order  # For answer submission
    }
```

---

## Phase 5: Testing & Validation

### Step 5.1: Data Integrity Verification

Create `verify_migration.py`:

```python
def verify_migration():
    """Verify all data migrated correctly"""
    
    # Count checks
    assert Chapter.query.count() == 6  # or 9, depending on content
    assert Module.query.count() == expected_count
    assert QuizQuestion.query.count() == total_quiz_count
    
    # Sample checks
    module_1_1 = Module.query.get("1.1")
    assert module_1_1.title == "Your Role as a Freight Agent"
    assert module_1_1.chapter_id == 1
    
    quiz_1_1_1 = QuizQuestion.query.get("q1_1_1")
    assert quiz_1_1_1.module_id == "1.1"
    assert quiz_1_1_1.correct_choice in ['a', 'b', 'c', 'd']
    
    # Check relationships
    chapter1 = Chapter.query.get(1)
    assert len(chapter1.modules) > 0
    
    print("✅ All data integrity checks passed")
```

### Step 5.2: Functional Testing

1. **Test navigation** - All pages load correctly
2. **Test quiz randomization** - Answers shuffle properly
3. **Test progress tracking** - Module completion persists
4. **Test preview mode** - Can access all content
5. **Test sequential unlocking** - Proper gating logic

---

## Phase 6: SQLite → PostgreSQL Migration

### Step 6.1: Export SQLite Data

Create `export_to_postgres.py`:

```python
import sqlite3
import psycopg2
import os

def migrate_sqlite_to_postgres(
    sqlite_path='training_guide.db',
    pg_host='localhost',
    pg_database='training_guide',
    pg_user='postgres',
    pg_password='password'
):
    """Migrate all data from SQLite to PostgreSQL"""
    
    # Connect to both databases
    sqlite_conn = sqlite3.connect(sqlite_path)
    pg_conn = psycopg2.connect(
        host=pg_host,
        database=pg_database,
        user=pg_user,
        password=pg_password
    )
    
    # Create PostgreSQL schema (same as SQLite)
    with open('schema_postgres.sql', 'r') as f:
        pg_conn.cursor().execute(f.read())
    
    # Migrate each table
    tables = [
        'chapters',
        'modules',
        'chapter_sections',
        'quiz_questions',
        'users',
        'user_progress',
        'user_quiz_answers',
        'glossary_terms'
    ]
    
    for table in tables:
        migrate_table(sqlite_conn, pg_conn, table)
    
    pg_conn.commit()
    print("✅ Migration to PostgreSQL complete")
```

### Step 6.2: PostgreSQL-Specific Schema Adjustments

Create `schema_postgres.sql`:

```sql
-- PostgreSQL uses SERIAL instead of AUTOINCREMENT
-- PostgreSQL has better JSONB support for answer_order

CREATE TABLE user_quiz_answers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    quiz_question_id VARCHAR(20) NOT NULL,
    selected_choice CHAR(1),
    is_correct BOOLEAN,
    answer_order JSONB,  -- PostgreSQL JSONB instead of TEXT
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (quiz_question_id) REFERENCES quiz_questions(id),
    UNIQUE(user_id, quiz_question_id)
);

-- Add indexes for performance
CREATE INDEX idx_user_progress_user_id ON user_progress(user_id);
CREATE INDEX idx_user_quiz_answers_user_id ON user_quiz_answers(user_id);
CREATE INDEX idx_modules_chapter_id ON modules(chapter_id);
CREATE INDEX idx_quiz_questions_module_id ON quiz_questions(module_id);
```

---

## Phase 7: Production Deployment

### Step 7.1: Environment Setup

**Development:**
- SQLite database file: `training_guide.db`
- Flask development server
- No authentication required

**Production:**
- PostgreSQL database (managed service recommended)
- Gunicorn/uWSGI web server
- Nginx reverse proxy
- SSL/TLS certificates
- User authentication enabled

### Step 7.2: Configuration Management

Create `config.py`:

```python
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///training_guide.db'
    
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # PostgreSQL: postgresql://user:pass@host:5432/dbname
```

### Step 7.3: Deployment Checklist

- [ ] Migrate all content to SQLite
- [ ] Test thoroughly in development
- [ ] Create PostgreSQL database on server
- [ ] Export SQLite → PostgreSQL
- [ ] Update Flask app configuration
- [ ] Set environment variables (DATABASE_URL, SECRET_KEY)
- [ ] Install requirements: `gunicorn`, `psycopg2`, `flask-sqlalchemy`
- [ ] Run database migrations: `flask db upgrade`
- [ ] Test on production server
- [ ] Set up SSL/TLS
- [ ] Configure backup strategy for PostgreSQL

---

## Phase 8: Content Management Interface (Future)

### Admin Dashboard (Optional)

Once database is set up, you can build an admin interface to:

1. **Add/Edit Quiz Questions** - No code changes needed
2. **Update Module Content** - Edit markdown directly in DB
3. **View User Progress** - Analytics dashboard
4. **Reset User Progress** - Admin tools
5. **Export Reports** - Completion rates, common mistakes

This would be a separate route like `/admin` with authentication.

---

## Implementation Timeline

### Week 1: Database Setup
- [ ] Design final schema
- [ ] Create `schema.sql` file
- [ ] Write `models.py` with SQLAlchemy classes
- [ ] Initialize SQLite database

### Week 2: Migration Scripts
- [ ] Write `db_migration.py`
- [ ] Extract quiz questions from `main.py`
- [ ] Extract content from `project.md`
- [ ] Run migration and verify data

### Week 3: Application Refactoring
- [ ] Update `main.py` to use database queries
- [ ] Implement user model and progress tracking
- [ ] Add answer randomization logic
- [ ] Test all features

### Week 4: Testing & Validation
- [ ] Comprehensive testing (all chapters, all quizzes)
- [ ] Fix bugs and edge cases
- [ ] Performance testing
- [ ] Document new architecture

### Week 5: PostgreSQL Migration
- [ ] Set up PostgreSQL database
- [ ] Write export script
- [ ] Test PostgreSQL version locally
- [ ] Prepare deployment configuration

### Week 6: Production Deployment
- [ ] Deploy to server
- [ ] Configure web server (Nginx/Gunicorn)
- [ ] Set up SSL
- [ ] Final testing
- [ ] Go live!

---

## File Structure After Migration

```
Trinity-Training-Guide/
├── main.py                    # Refactored to use database
├── models.py                  # NEW: SQLAlchemy models
├── config.py                  # NEW: Configuration management
├── db_migration.py           # NEW: Migration script
├── verify_migration.py       # NEW: Validation script
├── export_to_postgres.py     # NEW: PostgreSQL export
├── schema.sql                # NEW: SQLite schema
├── schema_postgres.sql       # NEW: PostgreSQL schema
├── training_guide.db         # NEW: SQLite database
├── requirements.txt          # UPDATE: Add new dependencies
├── project.md                # KEEP: Original content (reference)
├── templates/
│   ├── base.html
│   ├── chapter.html
│   ├── glossary.html
│   ├── index.html
│   └── page.html
└── static/                    # CSS, JS if needed
```

---

## Dependencies to Add

Update `requirements.txt`:

```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
markdown==3.5.1
psycopg2-binary==2.9.9      # For PostgreSQL
gunicorn==21.2.0            # For production
python-dotenv==1.0.0        # For environment variables
```

---

## Rollback Plan

If migration fails or issues arise:

1. **Keep original `main.py`** - Rename to `main_original.py`
2. **Keep `project.md`** - Original content preserved
3. **Git branch strategy** - Create `database-migration` branch
4. **Can revert to file-based version** if needed

The beauty of this approach is that no data is lost - everything comes from existing files, so you can always go back.

---

## Key Decisions to Make

Before starting migration:

1. **User Authentication:**
   - Start with anonymous users?
   - Add username/password login?
   - Use email verification?

2. **Progress Tracking:**
   - Should users be able to reset their progress?
   - Should admins see aggregate statistics?

3. **Content Updates:**
   - Keep `project.md` as source of truth?
   - Or move content management to database completely?

4. **Hosting:**
   - Which server/platform? (AWS, DigitalOcean, Heroku, etc.)
   - Self-managed or managed database service?

---

## Recommendation: Best Approach

**My recommendation is YES, migrate to a database:**

1. **Start with SQLite** - Easy development, no server needed
2. **Build migration script** - Preserve all existing data
3. **Refactor incrementally** - One feature at a time
4. **Test thoroughly** - Verify all functionality works
5. **Deploy with PostgreSQL** - Production-ready and scalable

This gives you the best of both worlds:
- Easy local development with SQLite
- Production-ready with PostgreSQL
- No data loss (everything comes from existing files)
- Can add features like user accounts, analytics, etc.
- Proper answer randomization per user

The migration will take some work upfront, but you'll have a much more maintainable and scalable application for deployment.

---

## Next Steps

1. **Review this plan** - Decide if this approach makes sense
2. **Confirm database schema** - Any additional fields needed?
3. **Choose user model** - Anonymous vs authenticated users
4. **Start with migration script** - Extract data from current files
5. **Test locally with SQLite** - Verify everything works
6. **Plan production deployment** - Server, database, domain

Would you like me to start implementing any part of this plan? I can begin with:
- Creating the database schema files
- Writing the migration script
- Refactoring the models.py file
- Or any other component you'd like to tackle first

