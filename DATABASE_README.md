# Database Setup Guide

This guide explains how to use the new database models for Trinity Training Guide.

## Files Created

### Core Files
- **`models.py`** - SQLAlchemy models (8 tables + helper functions)
- **`config.py`** - Configuration for dev/test/production environments
- **`init_db.py`** - Database initialization script
- **`requirements.txt`** - Python dependencies

### Schema Files
- **`schema.sql`** - SQLite schema (for development)
- **`schema_postgres.sql`** - PostgreSQL schema (for production)

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
# Create tables
python init_db.py

# Create tables + test users
python init_db.py --test

# Drop existing tables and recreate
python init_db.py --drop --test

# Verify database structure
python init_db.py --verify
```

### 3. Test the Models

```python
from flask import Flask
from models import db, User, Chapter, Module
from config import DevelopmentConfig

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
db.init_app(app)

with app.app_context():
    # Get test user
    user = User.query.filter_by(username='test_user').first()
    print(f"User: {user}")
    
    # Query chapters
    chapters = Chapter.query.order_by(Chapter.display_order).all()
    print(f"Chapters: {len(chapters)}")
```

---

## Database Models

### 1. Chapter
Represents a training chapter (e.g., "Understanding Your Role")

**Key Fields:**
- `id` - Chapter number (1-6+)
- `title` - Chapter title
- `display_order` - Sort order

**Relationships:**
- `modules` - All modules in this chapter
- `sections` - Intro, summary, action_items

**Methods:**
- `to_dict()` - Convert to JSON-serializable dict

### 2. Module
Represents a training module (e.g., "1.1: Your Role as a Freight Agent")

**Key Fields:**
- `id` - Module ID like "1.1", "2.3"
- `chapter_id` - Parent chapter
- `title` - Module title
- `content_markdown` - Full module content

**Relationships:**
- `chapter` - Parent chapter
- `quiz_questions` - All quizzes for this module
- `user_progress` - Completion tracking

### 3. ChapterSection
Chapter intro, summary, or action items

**Key Fields:**
- `chapter_id` - Parent chapter
- `section_type` - 'intro', 'summary', 'action_items'
- `content_markdown` - Section content

### 4. QuizQuestion
Quiz questions with multiple choice answers

**Key Fields:**
- `id` - Question ID like "q1_1_1"
- `module_id` - Parent module
- `question` - Question text
- `choice_a`, `choice_b`, `choice_c`, `choice_d` - Answer choices
- `correct_choice` - Correct answer ('a', 'b', 'c', or 'd')
- `explanation` - Why answer is correct

**Methods:**
- `get_shuffled_for_user(user_id)` - Returns shuffled quiz with consistent order per user
- `get_choices_dict()` - Returns choices as {'a': 'text', 'b': 'text', ...}

### 5. User
User/trainee account

**Key Fields:**
- `id` - User ID
- `username` - Unique username
- `email` - Optional email
- `is_preview_mode` - True for preview access

**Methods:**
- `get_completed_modules()` - Returns list of completed module IDs
- `get_module_completion_status(module_id)` - Check if module complete
- `get_chapter_completion_status(chapter_id)` - Check if chapter complete

### 6. UserProgress
Tracks module completion

**Key Fields:**
- `user_id` - User ID
- `module_id` - Module ID
- `completed` - True when all quizzes answered correctly
- `completion_date` - When completed

**Methods:**
- `mark_complete()` - Mark as completed
- `mark_incomplete()` - Reset progress

### 7. UserQuizAnswer
Tracks user answers to quiz questions

**Key Fields:**
- `user_id` - User ID
- `quiz_question_id` - Question ID
- `selected_choice` - Letter chosen ('a', 'b', 'c', or 'd')
- `is_correct` - True if correct
- `answer_order` - JSON array showing shuffle order for this user

### 8. GlossaryTerm
Glossary definitions

**Key Fields:**
- `term` - Term name
- `definition` - Definition text
- `category` - Optional category

---

## Helper Functions

### `get_or_create_user(username, is_preview=False)`
Get existing user or create new one

```python
from models import get_or_create_user

user = get_or_create_user('student1')
```

### `get_module_completion_status(user_id, module_id)`
Check if user completed a module (all quizzes correct)

```python
from models import get_module_completion_status

is_complete = get_module_completion_status(1, '1.1')
```

### `get_chapter_completion_status(user_id, chapter_id)`
Check if user completed all modules in a chapter

```python
from models import get_chapter_completion_status

chapter_done = get_chapter_completion_status(1, 1)
```

### `update_user_quiz_answer(user_id, quiz_id, selected_index, answer_order)`
Record user's answer to a quiz question

```python
from models import update_user_quiz_answer

result = update_user_quiz_answer(
    user_id=1,
    quiz_id='q1_1_1',
    selected_index=1,  # User clicked second choice
    answer_order=['b', 'a', 'd', 'c']  # Shuffled order
)
print(result['is_correct'])
print(result['explanation'])
```

---

## Answer Randomization

The system shuffles quiz choices per user but maintains consistency:

### How It Works

1. **First Attempt:**
   - User sees quiz question
   - System generates random order: `['c', 'a', 'd', 'b']`
   - Saves order to `user_quiz_answers.answer_order`
   - Shows choices in shuffled order

2. **Subsequent Views:**
   - User revisits same question
   - System loads saved order from database
   - Shows same shuffle order (consistent experience)

3. **Answer Checking:**
   - User clicks choice at index 2 (zero-based)
   - System looks up: `answer_order[2]` = `'d'`
   - Compares to `quiz_question.correct_choice`
   - Records result

### Example Usage

```python
from models import QuizQuestion

# Get shuffled quiz for user
quiz = QuizQuestion.query.get('q1_1_1')
shuffled = quiz.get_shuffled_for_user(user_id=1)

# Display to user
print(shuffled['question'])
for i, choice in enumerate(shuffled['choices']):
    print(f"{i}. {choice}")

# User selects index 2
selected_index = 2

# Submit answer
from models import update_user_quiz_answer
result = update_user_quiz_answer(
    user_id=1,
    quiz_id='q1_1_1',
    selected_index=selected_index,
    answer_order=shuffled['answer_order']
)

if result['is_correct']:
    print("✅ Correct!")
else:
    print("❌ Try again")
print(result['explanation'])
```

---

## Configuration Environments

### Development (default)
- Uses SQLite: `training_guide.db`
- Debug mode enabled
- SQL queries printed to console

```bash
export FLASK_ENV=development
python main.py
```

### Testing
- Uses in-memory SQLite
- For unit tests

```bash
export FLASK_ENV=testing
pytest
```

### Production
- Uses PostgreSQL from `DATABASE_URL` env var
- HTTPS required for cookies
- Debug disabled

```bash
export FLASK_ENV=production
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
gunicorn main:app
```

---

## Database Schema Visualization

```
chapters (1-6+)
  ├─ modules (1.1, 1.2, ..., 2.1, 2.2, ...)
  │   └─ quiz_questions (q1_1_1, q1_1_2, ...)
  │       └─ user_quiz_answers (tracks answers & shuffle order)
  └─ chapter_sections (intro, summary, action_items)

users (student accounts)
  ├─ user_progress (module completion)
  └─ user_quiz_answers (quiz responses)

glossary_terms (independent)
```

---

## Common Queries

### Get all chapters with modules
```python
chapters = Chapter.query.order_by(Chapter.display_order).all()
for chapter in chapters:
    print(f"Chapter {chapter.id}: {chapter.title}")
    for module in chapter.modules:
        print(f"  - {module.id}: {module.title}")
```

### Get user progress
```python
user = User.query.get(1)
completed = user.get_completed_modules()
print(f"Completed modules: {completed}")
```

### Get chapter intro/summary
```python
intro = ChapterSection.query.filter_by(
    chapter_id=1,
    section_type='intro'
).first()
print(intro.content_markdown)
```

### Get all quiz questions for a module
```python
module = Module.query.get('1.1')
for quiz in module.quiz_questions:
    print(f"{quiz.id}: {quiz.question}")
```

### Check if user can access next module
```python
def can_access_module(user_id, module_id):
    """Check if user has completed prerequisites"""
    module = Module.query.get(module_id)
    chapter = module.chapter
    
    # First module in chapter - check previous chapter
    if module.display_order == 1:
        if chapter.id == 1:
            return True  # First module overall
        prev_chapter_complete = get_chapter_completion_status(
            user_id, chapter.id - 1
        )
        return prev_chapter_complete
    
    # Check previous module in same chapter
    prev_modules = Module.query.filter_by(
        chapter_id=chapter.id
    ).filter(
        Module.display_order < module.display_order
    ).order_by(Module.display_order.desc()).first()
    
    if prev_modules:
        return get_module_completion_status(user_id, prev_modules.id)
    
    return True
```

---

## Next Steps

1. ✅ Database models created
2. ⏭️ Create migration script (`db_migration.py`) to extract data from `main.py` and `project.md`
3. ⏭️ Run migration to populate database
4. ⏭️ Refactor `main.py` to use database instead of hard-coded data
5. ⏭️ Test all functionality
6. ⏭️ Deploy with PostgreSQL

---

## Troubleshooting

### Database locked error
SQLite doesn't handle concurrent writes well. For production, use PostgreSQL.

### Foreign key constraint failed
Ensure parent records exist before creating children:
1. Create Chapter before Modules
2. Create Module before QuizQuestions
3. Create User before UserProgress

### Migration fails
```bash
# Reset database and try again
python init_db.py --drop
python db_migration.py
```

### Check database file
```bash
# View SQLite database
sqlite3 training_guide.db
.tables
.schema chapters
SELECT * FROM chapters;
```

---

## Production Deployment Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Set `SECRET_KEY` to random secure value
- [ ] Set `DATABASE_URL` to PostgreSQL connection string
- [ ] Run `python init_db.py` on production database
- [ ] Run migration script to populate data
- [ ] Test all functionality
- [ ] Set up database backups
- [ ] Configure SSL/TLS for HTTPS
- [ ] Use Gunicorn or uWSGI (not Flask dev server)

---

For questions or issues, refer to `deployment.md` for the full migration plan.

