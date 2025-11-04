"""
Simple Quiz Import Script

This script allows you to easily add new quiz questions to the database.
Perfect for AI-generated content - just paste the questions in the format below and run!

Usage:
    python import_quizzes.py

The script will prompt you to paste quiz data in JSON format, then import it directly.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask
from models import db, QuizQuestion
from config import DevelopmentConfig, ProductionConfig
import os


def create_app():
    """Create Flask application with database configuration"""
    app = Flask(__name__)
    
    # Use production config if DATABASE_URL is set, otherwise development
    if os.environ.get('DATABASE_URL'):
        app.config.from_object(ProductionConfig)
        print("🗄️  Using PRODUCTION database (PostgreSQL)")
    else:
        app.config.from_object(DevelopmentConfig)
        print("🗄️  Using DEVELOPMENT database (SQLite)")
    
    db.init_app(app)
    return app


def import_from_json(quiz_data):
    """
    Import quiz questions from JSON data.
    
    Expected format:
    {
        "module_id": "7.1",
        "questions": [
            {
                "id": "q7_1_1",
                "question": "Your question here?",
                "choices": {
                    "a": "First choice",
                    "b": "Second choice",
                    "c": "Third choice",
                    "d": "Fourth choice"
                },
                "correct_choice": "b",
                "explanation": "Explanation of the correct answer..."
            }
        ]
    }
    """
    module_id = quiz_data.get('module_id')
    questions = quiz_data.get('questions', [])
    
    if not module_id:
        print("❌ Error: 'module_id' is required")
        return False
    
    if not questions:
        print("❌ Error: No questions found")
        return False
    
    imported_count = 0
    updated_count = 0
    
    for idx, q_data in enumerate(questions, 1):
        # Validate required fields
        required = ['id', 'question', 'choices', 'correct_choice', 'explanation']
        missing = [field for field in required if field not in q_data]
        if missing:
            print(f"⚠️  Skipping question {idx}: Missing fields {missing}")
            continue
        
        # Check if question already exists
        existing = QuizQuestion.query.get(q_data['id'])
        
        if existing:
            # Update existing question
            existing.module_id = module_id
            existing.question = q_data['question']
            existing.choice_a = q_data['choices']['a']
            existing.choice_b = q_data['choices']['b']
            existing.choice_c = q_data['choices']['c']
            existing.choice_d = q_data['choices']['d']
            existing.correct_choice = q_data['correct_choice']
            existing.explanation = q_data['explanation']
            existing.display_order = idx
            updated_count += 1
            print(f"✏️  Updated: {q_data['id']}")
        else:
            # Create new question
            new_question = QuizQuestion(
                id=q_data['id'],
                module_id=module_id,
                question=q_data['question'],
                choice_a=q_data['choices']['a'],
                choice_b=q_data['choices']['b'],
                choice_c=q_data['choices']['c'],
                choice_d=q_data['choices']['d'],
                correct_choice=q_data['correct_choice'],
                explanation=q_data['explanation'],
                display_order=idx
            )
            db.session.add(new_question)
            imported_count += 1
            print(f"✅ Added: {q_data['id']}")
    
    try:
        db.session.commit()
        print(f"\n🎉 Success! Imported {imported_count} new questions, updated {updated_count} existing questions")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error saving to database: {e}")
        return False


def import_from_simple_format(text_data):
    """
    Import from a simpler text format that's easy for AI to generate.
    
    Format:
    MODULE: 7.1
    
    Q: q7_1_1
    Question: Your question text here?
    A: First choice
    B: Second choice
    C: Third choice
    D: Fourth choice
    CORRECT: B
    EXPLANATION: Why B is correct...
    
    Q: q7_1_2
    Question: Another question?
    ...
    """
    lines = text_data.strip().split('\n')
    
    module_id = None
    questions = []
    current_q = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith('MODULE:'):
            module_id = line.replace('MODULE:', '').strip()
        
        elif line.startswith('Q:'):
            # Save previous question if exists
            if current_q and current_q.get('id'):
                questions.append(current_q)
            # Start new question
            current_q = {
                'id': line.replace('Q:', '').strip(),
                'choices': {}
            }
        
        elif line.startswith('Question:') and current_q:
            current_q['question'] = line.replace('Question:', '').strip()
        
        elif line.startswith('A:') and current_q:
            current_q['choices']['a'] = line.replace('A:', '').strip()
        
        elif line.startswith('B:') and current_q:
            current_q['choices']['b'] = line.replace('B:', '').strip()
        
        elif line.startswith('C:') and current_q:
            current_q['choices']['c'] = line.replace('C:', '').strip()
        
        elif line.startswith('D:') and current_q:
            current_q['choices']['d'] = line.replace('D:', '').strip()
        
        elif line.startswith('CORRECT:') and current_q:
            correct = line.replace('CORRECT:', '').strip().lower()
            current_q['correct_choice'] = correct
        
        elif line.startswith('EXPLANATION:') and current_q:
            current_q['explanation'] = line.replace('EXPLANATION:', '').strip()
    
    # Add last question
    if current_q and current_q.get('id'):
        questions.append(current_q)
    
    if not module_id:
        print("❌ Error: MODULE not specified")
        return False
    
    # Convert to JSON format and import
    return import_from_json({
        'module_id': module_id,
        'questions': questions
    })


def interactive_mode():
    """Interactive mode - prompts user for input"""
    print("=" * 70)
    print("📝 QUIZ QUESTION IMPORTER")
    print("=" * 70)
    print("\nChoose input format:")
    print("1) JSON format (structured)")
    print("2) Simple text format (easier for AI)")
    print("3) Load from file")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == '1':
        print("\nPaste your JSON data (Ctrl+Z then Enter on Windows, Ctrl+D on Mac/Linux when done):")
        print("-" * 70)
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        
        json_text = '\n'.join(lines)
        try:
            quiz_data = json.loads(json_text)
            return import_from_json(quiz_data)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            return False
    
    elif choice == '2':
        print("\nPaste your quiz data in simple format (Ctrl+Z then Enter on Windows, Ctrl+D on Mac/Linux when done):")
        print("Example format:")
        print("  MODULE: 7.1")
        print("  Q: q7_1_1")
        print("  Question: Your question?")
        print("  A: Choice A")
        print("  B: Choice B")
        print("  C: Choice C")
        print("  D: Choice D")
        print("  CORRECT: B")
        print("  EXPLANATION: Because...")
        print("-" * 70)
        
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        
        text_data = '\n'.join(lines)
        return import_from_simple_format(text_data)
    
    elif choice == '3':
        filepath = input("\nEnter file path: ").strip()
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try JSON first
            try:
                quiz_data = json.loads(content)
                return import_from_json(quiz_data)
            except json.JSONDecodeError:
                # Try simple format
                return import_from_simple_format(content)
        except FileNotFoundError:
            print(f"❌ File not found: {filepath}")
            return False
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return False
    
    else:
        print("❌ Invalid choice")
        return False


def main():
    """Main entry point"""
    app = create_app()
    
    with app.app_context():
        # Check if database is accessible
        try:
            db.session.execute('SELECT 1')
        except Exception as e:
            print(f"❌ Cannot connect to database: {e}")
            print("\nMake sure:")
            print("- Database is initialized (run: python init_db.py)")
            print("- Database connection settings are correct in config.py")
            return
        
        # Run interactive import
        success = interactive_mode()
        
        if success:
            print("\n✨ Import complete!")
        else:
            print("\n❌ Import failed")


if __name__ == "__main__":
    main()

