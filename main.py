from flask import Flask, render_template, redirect, url_for, request, session, jsonify, flash
import re
import json
from pathlib import Path
import markdown
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()


# Database imports
from models import (
    db, Chapter, Module, ChapterSection, QuizQuestion, 
    GlossaryTerm, User, get_or_create_user,
    get_module_completion_status as db_get_module_completion,
    get_chapter_completion_status as db_get_chapter_completion,
    update_user_quiz_answer
)
from config import get_config

app = Flask(__name__)

# Load configuration
config = get_config()
app.config.from_object(config)

# Initialize database
db.init_app(app)

PROJECT_MD_PATH = Path(__file__).parent / "project.md"

# ============================================================================
# USER SESSION MANAGEMENT
# ============================================================================

def get_current_user():
    """
    Get or create the current user from session.
    For now, uses anonymous users. Can be extended for authentication later.
    """
    # Check if user ID is in session
    user_id = session.get('user_id')
    
    if user_id:
        user = User.query.get(user_id)
        if user:
            # Sync preview_mode from database to session
            # Database is the source of truth - always sync from database
            if user.is_preview_mode:
                session['preview_mode'] = True
            else:
                # Clear session preview_mode if database says user shouldn't have it
                session['preview_mode'] = False
            session.modified = True
            return user
    
    # Check for preview mode
    is_preview = session.get('preview_mode', False)
    
    # Create or get anonymous user
    if is_preview:
        username = 'preview_user'
    else:
        username = session.get('username', 'anonymous_user')
    
    user = get_or_create_user(username, is_preview=is_preview)
    session['user_id'] = user.id
    session['username'] = user.username
    
    # Sync preview_mode from database to session (database is source of truth)
    if user.is_preview_mode:
        session['preview_mode'] = True
    else:
        session['preview_mode'] = False
    session.modified = True
    
    return user


# ============================================================================
# DATABASE QUERY FUNCTIONS
# ============================================================================


def extract_glossary(markdown_text: str):
    """Extract glossary terms from the markdown."""
    lines = markdown_text.splitlines()
    in_glossary = False
    glossary_lines = []
    
    for raw_line in lines:
        stripped = raw_line.strip()
        if re.match(r"^GLOSSARY OF FREIGHT AGENT TERMS$", stripped, flags=re.IGNORECASE):
            in_glossary = True
            continue
        if in_glossary and stripped:
            glossary_lines.append(raw_line)
    
    print(f"[extract_glossary] Found {len(glossary_lines)} glossary terms")
    return "\n".join(glossary_lines).strip()


def parse_glossary_terms(markdown_text: str):
    """Parse glossary into structured term objects."""
    glossary_text = extract_glossary(markdown_text)
    terms = []
    
    # Pattern: "Mod X.X - Term Name - Definition"
    # Use " - " (space-hyphen-space) as delimiter to support hyphenated terms like "Less-Than-Truckload"
    pattern = re.compile(r'^(Mod\s+[\d.]+)\s+-\s+(.+?)\s+-\s+(.+)$')
    
    for line in glossary_text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = pattern.match(line)
        if match:
            terms.append({
                'module': match.group(1).strip(),
                'name': match.group(2).strip(),
                'definition': match.group(3).strip()
            })
    
    print(f"[parse_glossary_terms] Parsed {len(terms)} structured terms")
    return terms


def get_module_completion_status(session_quiz_answers_or_user_id, module_id):
    """
    Check if all quizzes for a module are completed.
    Now uses database instead of session storage.
    
    Args:
        session_quiz_answers_or_user_id: Can be user_id (int) or legacy session dict
        module_id: Module ID like "1.1", "2.3", etc.
    """
    # Handle both old (session dict) and new (user_id) calling conventions
    if isinstance(session_quiz_answers_or_user_id, int):
        user_id = session_quiz_answers_or_user_id
        # Use database function
        return db_get_module_completion(user_id, module_id)
    else:
        # Legacy session-based: Get current user and use database
        user = get_current_user()
        return db_get_module_completion(user.id, module_id)


def get_chapter_completion_status(session_quiz_answers_or_user_id, chapter_num):
    """
    Check if all modules in a chapter are completed.
    Now uses database instead of session storage.
    
    Args:
        session_quiz_answers_or_user_id: Can be user_id (int) or legacy session dict
        chapter_num: Chapter number (1, 2, 3, etc.)
    """
    # Handle both old (session dict) and new (user_id) calling conventions
    if isinstance(session_quiz_answers_or_user_id, int):
        user_id = session_quiz_answers_or_user_id
        # Use database function
        return db_get_chapter_completion(user_id, chapter_num)
    else:
        # Legacy session-based: Get current user and use database
        user = get_current_user()
        return db_get_chapter_completion(user.id, chapter_num)




@app.route("/")
def index():
    # Check if user is logged in
    if not session.get('logged_in'):
        return redirect(url_for("home"))
    return redirect(url_for("cover"))


@app.route("/home")
def home():
    """Home page with login/register options"""
    # If already logged in, redirect to training
    if session.get('logged_in'):
        return redirect(url_for("cover"))
    return render_template("home.html")


# ============================================================================
# NEW TEMPLATE-BASED ROUTES (Professional Refactor)
# ============================================================================

@app.route("/cover")
def cover():
    """Professional cover page"""
    if not session.get('logged_in') and not session.get('preview_mode'):
        return redirect(url_for("login"))
    return render_template("pages/cover.html")


@app.route("/toc")
def toc():
    """Table of contents page"""
    if not session.get('logged_in') and not session.get('preview_mode'):
        return redirect(url_for("login"))

    user = get_current_user()
    preview_mode = session.get('preview_mode', False) or (user.is_preview_mode if user else False)

    # Build module completion status
    module_completion = {}
    all_modules = Module.query.order_by(Module.id).all()
    for mod in all_modules:
        module_completion[mod.id] = get_module_completion_status(user.id, mod.id) if user else False

    # Get chapter completion status
    chapter_complete = {}
    for ch_num in range(1, 10):
        chapter_complete[ch_num] = get_chapter_completion_status(user.id, ch_num) if user else False

    # Build module_locked dictionary
    module_locked = {}
    if not preview_mode:
        # Build chapter_modules dynamically from database (future-proof for new sub-modules)
        chapter_modules = {}
        for mod in all_modules:
            ch_id = mod.chapter_id
            if ch_id not in chapter_modules:
                chapter_modules[ch_id] = []
            chapter_modules[ch_id].append(mod.id)

        # Sort each chapter's modules correctly (e.g., 2.2 before 2.2.1 before 2.3)
        for ch_id in chapter_modules:
            chapter_modules[ch_id].sort(key=lambda x: [int(p) for p in x.split('.')])

        for ch_num, modules in chapter_modules.items():
            prev_chapter_complete = chapter_complete.get(ch_num - 1, True) if ch_num > 1 else True
            for i, mod_id in enumerate(modules):
                if i == 0:
                    # First module of chapter - locked if previous chapter not complete
                    module_locked[mod_id] = not prev_chapter_complete
                else:
                    # Check if this is a sub-module (e.g., 2.2.1)
                    is_sub_module = len(mod_id.split('.')) == 3

                    if is_sub_module:
                        # For sub-modules, check if the module BEFORE the parent is complete
                        # e.g., for 2.2.1, check if 2.1 is complete (not 2.2)
                        # Sub-modules are content within the parent module - quiz comes AFTER sub-modules
                        parent_id = '.'.join(mod_id.split('.')[:2])  # "2.2.1" -> "2.2"
                        parent_idx = modules.index(parent_id) if parent_id in modules else 0
                        if parent_idx == 0:
                            # Parent is first module of chapter
                            module_locked[mod_id] = not prev_chapter_complete
                        else:
                            # Check module before the parent
                            prev_mod_id = modules[parent_idx - 1]
                            # Skip any sub-modules when looking for the previous main module
                            while len(prev_mod_id.split('.')) == 3 and parent_idx > 1:
                                parent_idx -= 1
                                prev_mod_id = modules[parent_idx - 1]
                            module_locked[mod_id] = not module_completion.get(prev_mod_id, True)
                    else:
                        # Other modules - locked if previous module not complete
                        prev_mod_id = modules[i - 1]
                        # Default to True (complete) if not in dict - allows progression for modules without quizzes
                        module_locked[mod_id] = not module_completion.get(prev_mod_id, True)

    # Build chapter_locked dictionary
    chapter_locked = {}
    if not preview_mode:
        for ch_num in range(1, 10):
            if ch_num == 1:
                chapter_locked[ch_num] = False
            else:
                chapter_locked[ch_num] = not chapter_complete.get(ch_num - 1, False)

    return render_template(
        "pages/toc.html",
        preview_mode=preview_mode,
        module_completion=module_completion,
        module_locked=module_locked,
        chapter_locked=chapter_locked,
        chapter_complete=chapter_complete
    )


@app.route("/chapter/<int:chapter_num>/<page>")
def chapter(chapter_num, page):
    """
    Serve chapter pages (intro, summary, action_items)
    """
    if not session.get('logged_in') and not session.get('preview_mode'):
        return redirect(url_for("login"))

    # Mark chapter intro as seen when user views it
    if page == 'intro':
        seen_intros = session.get('seen_intros', [])
        if chapter_num not in seen_intros:
            seen_intros.append(chapter_num)
            session['seen_intros'] = seen_intros
            session.modified = True

    # Check if chapter is locked for non-preview users
    user = get_current_user()
    preview_mode = session.get('preview_mode', False) or (user.is_preview_mode if user else False)

    if not preview_mode and user and chapter_num > 1:
        # Check if previous chapter is complete
        prev_chapter_complete = get_chapter_completion_status(user.id, chapter_num - 1)
        if not prev_chapter_complete:
            flash("This chapter is locked. Please complete the previous chapter first.", "warning")
            return redirect(url_for("toc"))

    # Chapter titles for progress bar
    chapter_titles = {
        1: "Welcome to Freight Brokerage",
        2: "Understanding the Industry Landscape",
        3: "The Role of a Freight Agent",
        4: "Truck Types and Specifications",
        5: "Load Types and Cargo Categories",
        6: "Load Restrictions and Regulations",
        7: "Building Your Customer Base",
        8: "Sales Strategies for Freight Agents",
        9: "Effective Follow-Up Systems"
    }

    # Module counts per chapter
    module_counts = {1: 6, 2: 9, 3: 9, 4: 11, 5: 10, 6: 11, 7: 5, 8: 9, 9: 9}

    # Valid page types
    valid_pages = ['intro', 'summary', 'action_items']
    if page not in valid_pages:
        return redirect(url_for("toc"))

    # Calculate progress (placeholder - can be enhanced with user progress tracking)
    progress_percent = 0

    # Navigation URLs
    if page == 'intro':
        prev_url = url_for('toc') if chapter_num == 1 else url_for('chapter', chapter_num=chapter_num-1, page='action_items')
        next_url = url_for('module', module_id=f'{chapter_num}.1')
    elif page == 'summary':
        prev_url = url_for('module', module_id=f'{chapter_num}.{module_counts.get(chapter_num, 6)}')
        next_url = url_for('chapter', chapter_num=chapter_num, page='action_items')
    elif page == 'action_items':
        prev_url = url_for('chapter', chapter_num=chapter_num, page='summary')
        next_url = url_for('chapter', chapter_num=chapter_num+1, page='intro') if chapter_num < 9 else url_for('toc')

    template_path = f"chapters/chapter{chapter_num}/{page}.html"

    return render_template(
        template_path,
        chapter_num=chapter_num,
        chapter_title=chapter_titles.get(chapter_num, ""),
        progress_percent=progress_percent,
        prev_url=prev_url,
        next_url=next_url
    )


@app.route("/module/<module_id>")
def module(module_id):
    """
    Serve individual module pages
    Supports both 2-part IDs (e.g., "2.2") and 3-part IDs (e.g., "2.2.1") for sub-modules
    """
    if not session.get('logged_in') and not session.get('preview_mode'):
        return redirect(url_for("login"))

    # Parse module ID (e.g., "1.1" -> chapter 1, module 1, or "2.2.1" -> chapter 2, module 2, sub-module 1)
    try:
        parts = module_id.split('.')
        chapter_num = int(parts[0])
        module_num = int(parts[1])
        sub_module_num = int(parts[2]) if len(parts) > 2 else None
    except (ValueError, IndexError):
        return redirect(url_for("toc"))

    # If this is the first module (X.1) and user hasn't seen the chapter intro, redirect to intro
    if module_num == 1 and sub_module_num is None:
        seen_intros = session.get('seen_intros', [])
        if chapter_num not in seen_intros:
            return redirect(url_for('chapter', chapter_num=chapter_num, page='intro'))

    # Check if module is locked for non-preview users
    user = get_current_user()
    preview_mode = session.get('preview_mode', False) or (user.is_preview_mode if user else False)

    if not preview_mode and user:
        # Get chapter completion status
        chapter_complete = {}
        for ch_num in range(1, 10):
            chapter_complete[ch_num] = get_chapter_completion_status(user.id, ch_num)

        # Get module completion status and build chapter_modules dynamically from DB
        module_completion = {}
        chapter_modules = {}
        all_modules = Module.query.order_by(Module.id).all()
        for mod in all_modules:
            module_completion[mod.id] = get_module_completion_status(user.id, mod.id)
            ch_id = mod.chapter_id
            if ch_id not in chapter_modules:
                chapter_modules[ch_id] = []
            chapter_modules[ch_id].append(mod.id)

        # Sort each chapter's modules correctly (e.g., 2.2 before 2.2.1 before 2.3)
        for ch_id in chapter_modules:
            chapter_modules[ch_id].sort(key=lambda x: [int(p) for p in x.split('.')])

        # Check if current module is locked
        is_locked = False
        modules_in_chapter = chapter_modules.get(chapter_num, [])

        if module_id in modules_in_chapter:
            idx = modules_in_chapter.index(module_id)
            if idx == 0:
                # First module of chapter - locked if previous chapter not complete
                prev_chapter_complete = chapter_complete.get(chapter_num - 1, True) if chapter_num > 1 else True
                is_locked = not prev_chapter_complete
            else:
                # Check if this is a sub-module (e.g., 2.2.1)
                is_sub_module = len(module_id.split('.')) == 3

                if is_sub_module:
                    # For sub-modules, check if the module BEFORE the parent is complete
                    # e.g., for 2.2.1, check if 2.1 is complete (not 2.2)
                    # Sub-modules are content within the parent module - quiz comes AFTER sub-modules
                    parent_id = '.'.join(module_id.split('.')[:2])  # "2.2.1" -> "2.2"
                    parent_idx = modules_in_chapter.index(parent_id) if parent_id in modules_in_chapter else 0
                    if parent_idx == 0:
                        # Parent is first module of chapter
                        prev_chapter_complete = chapter_complete.get(chapter_num - 1, True) if chapter_num > 1 else True
                        is_locked = not prev_chapter_complete
                    else:
                        # Check module before the parent
                        prev_mod_id = modules_in_chapter[parent_idx - 1]
                        # Skip any sub-modules when looking for the previous main module
                        while len(prev_mod_id.split('.')) == 3 and parent_idx > 1:
                            parent_idx -= 1
                            prev_mod_id = modules_in_chapter[parent_idx - 1]
                        is_locked = not module_completion.get(prev_mod_id, True)
                else:
                    # Not first module - locked if previous module not complete
                    prev_mod_id = modules_in_chapter[idx - 1]
                    # Default to True (unlocked) if module not in dict - allows progression for modules without quizzes
                    is_locked = not module_completion.get(prev_mod_id, True)

        if is_locked:
            flash("This module is locked. Please complete the previous modules first.", "warning")
            return redirect(url_for("toc"))

    # Chapter titles for progress bar
    chapter_titles = {
        1: "Welcome to Freight Brokerage",
        2: "Understanding the Industry Landscape",
        3: "The Role of a Freight Agent",
        4: "Truck Types and Specifications",
        5: "Load Types and Cargo Categories",
        6: "Load Restrictions and Regulations",
        7: "Building Your Customer Base",
        8: "Sales Strategies for Freight Agents",
        9: "Effective Follow-Up Systems"
    }

    # Module counts per chapter
    module_counts = {1: 6, 2: 9, 3: 9, 4: 11, 5: 10, 6: 11, 7: 5, 8: 9, 9: 9}
    max_module = module_counts.get(chapter_num, 6)

    # Sub-module configuration: maps parent module to number of sub-modules
    sub_module_counts = {
        "2.2": 6,  # Module 2.2 has sub-modules 2.2.1 through 2.2.6
    }

    parent_module_id = f"{chapter_num}.{module_num}"
    max_sub_module = sub_module_counts.get(parent_module_id, 0)

    # Calculate progress
    if sub_module_num:
        # For sub-modules, calculate progress within the parent module range
        base_progress = int(((module_num - 1) / max_module) * 100)
        sub_progress = int((sub_module_num / max_sub_module) * (100 / max_module))
        progress_percent = base_progress + sub_progress
    else:
        progress_percent = int((module_num / max_module) * 100)

    # Navigation URLs
    if sub_module_num:
        # Sub-module navigation
        if sub_module_num == 1:
            # First sub-module - previous goes to parent module
            prev_url = url_for('module', module_id=parent_module_id)
        else:
            # Previous sub-module
            prev_url = url_for('module', module_id=f'{parent_module_id}.{sub_module_num - 1}')

        if sub_module_num >= max_sub_module:
            # Last sub-module - check if parent module has quiz
            quiz_count = QuizQuestion.query.filter_by(module_id=parent_module_id).count()
            if quiz_count > 0:
                next_url = url_for('quiz', module_id=parent_module_id, question_num=1)
            elif module_num >= max_module:
                next_url = url_for('chapter', chapter_num=chapter_num, page='summary')
            else:
                next_url = url_for('module', module_id=f'{chapter_num}.{module_num + 1}')
        else:
            # Next sub-module
            next_url = url_for('module', module_id=f'{parent_module_id}.{sub_module_num + 1}')
    else:
        # Regular module navigation
        if module_num == 1:
            prev_url = url_for('chapter', chapter_num=chapter_num, page='intro')
        else:
            # Check if previous module has sub-modules
            prev_module_id = f'{chapter_num}.{module_num-1}'
            prev_max_sub = sub_module_counts.get(prev_module_id, 0)
            if prev_max_sub > 0:
                # Previous module has sub-modules - check if last sub-module has quiz
                prev_quiz_count = QuizQuestion.query.filter_by(module_id=prev_module_id).count()
                if prev_quiz_count > 0:
                    prev_url = url_for('quiz', module_id=prev_module_id, question_num=prev_quiz_count)
                else:
                    prev_url = url_for('module', module_id=f'{prev_module_id}.{prev_max_sub}')
            else:
                # Check if previous module has quiz
                prev_quiz_count = QuizQuestion.query.filter_by(module_id=prev_module_id).count()
                if prev_quiz_count > 0:
                    prev_url = url_for('quiz', module_id=prev_module_id, question_num=prev_quiz_count)
                else:
                    prev_url = url_for('module', module_id=prev_module_id)

        # Check if this module has sub-modules
        if max_sub_module > 0:
            # Has sub-modules - next goes to first sub-module
            next_url = url_for('module', module_id=f'{parent_module_id}.1')
        else:
            # Check if this module has quiz questions
            quiz_count = QuizQuestion.query.filter_by(module_id=module_id).count()

            if quiz_count > 0:
                # Has quiz - next goes to quiz
                next_url = url_for('quiz', module_id=module_id, question_num=1)
            elif module_num >= max_module:
                # No quiz, last module - go to summary
                next_url = url_for('chapter', chapter_num=chapter_num, page='summary')
            else:
                # No quiz - go to next module
                next_url = url_for('module', module_id=f'{chapter_num}.{module_num+1}')

    template_path = f"chapters/chapter{chapter_num}/module_{module_id.replace('.', '_')}.html"

    return render_template(
        template_path,
        module_id=module_id,
        chapter_num=chapter_num,
        chapter_title=chapter_titles.get(chapter_num, ""),
        progress_percent=progress_percent,
        prev_url=prev_url,
        next_url=next_url,
        has_quiz=QuizQuestion.query.filter_by(module_id=parent_module_id if sub_module_num else module_id).count() > 0
    )


@app.route("/quiz/<module_id>", defaults={'question_num': 1})
@app.route("/quiz/<module_id>/<int:question_num>")
def quiz(module_id, question_num):
    """
    Serve individual quiz questions, one per page
    """
    if not session.get('logged_in') and not session.get('preview_mode'):
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    # Parse module ID
    try:
        parts = module_id.split('.')
        chapter_num = int(parts[0])
        module_num = int(parts[1])
    except (ValueError, IndexError):
        return redirect(url_for("toc"))

    # Chapter titles
    chapter_titles = {
        1: "Welcome to Freight Brokerage",
        2: "Understanding the Industry Landscape",
        3: "The Role of a Freight Agent",
        4: "Truck Types and Specifications",
        5: "Load Types and Cargo Categories",
        6: "Load Restrictions and Regulations",
        7: "Building Your Customer Base",
        8: "Sales Strategies for Freight Agents",
        9: "Effective Follow-Up Systems"
    }

    # Module counts per chapter
    module_counts = {1: 6, 2: 9, 3: 9, 4: 11, 5: 10, 6: 11, 7: 5, 8: 9, 9: 9}
    max_module = module_counts.get(chapter_num, 6)

    # Get quiz questions for this module
    db_questions = QuizQuestion.query.filter_by(module_id=module_id).order_by(QuizQuestion.display_order).all()

    if not db_questions:
        # No quiz questions - go to next module or summary
        if module_num >= max_module:
            return redirect(url_for('chapter', chapter_num=chapter_num, page='summary'))
        else:
            return redirect(url_for('module', module_id=f'{chapter_num}.{module_num+1}'))

    # Validate question number
    if question_num < 1 or question_num > len(db_questions):
        return redirect(url_for('quiz', module_id=module_id, question_num=1))

    # Get the current question
    current_question = db_questions[question_num - 1]
    question_data = current_question.get_shuffled_for_user(user.id)
    total_questions = len(db_questions)

    # Navigation
    prev_url = url_for('quiz', module_id=module_id, question_num=question_num-1) if question_num > 1 else url_for('module', module_id=module_id)

    if question_num >= total_questions:
        # Last question - next goes to next module or summary
        if module_num >= max_module:
            next_url = url_for('chapter', chapter_num=chapter_num, page='summary')
        else:
            next_url = url_for('module', module_id=f'{chapter_num}.{module_num+1}')
    else:
        next_url = url_for('quiz', module_id=module_id, question_num=question_num+1)

    # Check if user already answered this question
    from models import UserQuizAnswer
    existing_answer = UserQuizAnswer.query.filter_by(
        user_id=user.id,
        quiz_question_id=current_question.id
    ).first()

    already_answered = existing_answer and existing_answer.selected_choice is not None
    was_correct = bool(existing_answer.is_correct) if already_answered else None

    # Add selected_choice to question_data so template can highlight wrong answer
    if already_answered and existing_answer.selected_choice:
        question_data['selected_choice'] = existing_answer.selected_choice

    return render_template(
        "pages/quiz.html",
        module_id=module_id,
        chapter_num=chapter_num,
        chapter_title=chapter_titles.get(chapter_num, ""),
        question=question_data,
        question_num=question_num,
        total_questions=total_questions,
        prev_url=prev_url,
        next_url=next_url,
        already_answered=already_answered,
        was_correct=was_correct,
        progress_percent=int((module_num / max_module) * 100)
    )


@app.route("/submit-quiz/<module_id>/<int:question_num>", methods=["POST"])
def submit_quiz(module_id, question_num=1):
    """Handle quiz answer submission"""
    if not session.get('logged_in') and not session.get('preview_mode'):
        return jsonify({'error': 'Not logged in'}), 401

    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 401

    data = request.get_json() if request.is_json else request.form

    question_id = data.get('question_id')
    selected_index = int(data.get('selected_index', data.get('answer', 0)))
    answer_order = data.get('answer_order', ['a', 'b', 'c', 'd'])

    if isinstance(answer_order, str):
        if answer_order.strip():
            try:
                answer_order = json.loads(answer_order)
            except json.JSONDecodeError:
                answer_order = ['a', 'b', 'c', 'd']
        else:
            answer_order = ['a', 'b', 'c', 'd']

    result = update_user_quiz_answer(user.id, question_id, selected_index, answer_order)

    if request.is_json:
        return jsonify(result)
    else:
        # For form submission, redirect to next question or next module
        return redirect(url_for('quiz', module_id=module_id, question_num=question_num))


# ============================================================================
# END NEW TEMPLATE-BASED ROUTES
# ============================================================================



@app.route("/debug_locks")
def debug_locks():
    """Debug endpoint to see locking state - REMOVE IN PRODUCTION"""
    from models import User

    user_id = session.get('user_id')
    username = session.get('username', 'not set')
    logged_in = session.get('logged_in', False)
    session_preview = session.get('preview_mode', 'not set')

    user = User.query.get(user_id) if user_id else None
    db_preview = user.is_preview_mode if user else 'no user'

    # Calculate preview_mode the same way the page route does
    preview_mode = session.get('preview_mode', False) or (user.is_preview_mode if user else False)

    # Get module completion for chapter 1
    ch1_completion = {}
    ch1_modules = ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6"]
    for mod_id in ch1_modules:
        ch1_completion[mod_id] = get_module_completion_status(user.id, mod_id) if user else False

    # Build module_locked the same way
    module_locked = {}
    if not preview_mode:
        for i, mod_id in enumerate(ch1_modules):
            if i == 0:
                module_locked[mod_id] = False
            else:
                prev_mod_id = ch1_modules[i-1]
                module_locked[mod_id] = not ch1_completion.get(prev_mod_id, True)

    debug_info = f"""
    <h1>Lock Debug Info</h1>
    <h2>Session State</h2>
    <ul>
        <li><b>user_id:</b> {user_id}</li>
        <li><b>username:</b> {username}</li>
        <li><b>logged_in:</b> {logged_in}</li>
        <li><b>session preview_mode:</b> {session_preview}</li>
    </ul>

    <h2>Database State</h2>
    <ul>
        <li><b>User found:</b> {user is not None}</li>
        <li><b>DB is_preview_mode:</b> {db_preview}</li>
    </ul>

    <h2>Calculated Values</h2>
    <ul>
        <li><b>Final preview_mode:</b> {preview_mode}</li>
    </ul>

    <h2>Chapter 1 Module Completion</h2>
    <ul>
    """
    for mod_id, complete in ch1_completion.items():
        debug_info += f"<li><b>{mod_id}:</b> {complete}</li>"

    debug_info += """
    </ul>

    <h2>Chapter 1 Module Locked State</h2>
    <ul>
    """
    for mod_id, locked in module_locked.items():
        debug_info += f"<li><b>{mod_id}:</b> {'🔒 LOCKED' if locked else '🔓 UNLOCKED'}</li>"

    debug_info += """
    </ul>

    <p><a href="/page/1">Go to TOC</a></p>
    """

    return debug_info


@app.route("/glossary")
def glossary():
    # Require login
    if not session.get('logged_in') and not session.get('preview_mode'):
        return redirect(url_for("login"))

    try:
        text = PROJECT_MD_PATH.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        text = ""

    glossary_terms = parse_glossary_terms(text) if text else []

    # Filter out truck types (they're now on the /trucks page)
    truck_term_names = {
        'Dry Van Trailer',
        'Refrigerated Trailer (Reefer)',
        'Flatbed Trailer',
        'Step Deck (Drop Deck) Trailer',
        'Tanker Trailer',
        'Box Truck'
    }
    glossary_terms = [term for term in glossary_terms if term['name'] not in truck_term_names]

    return render_template(
        "glossary.html",
        glossary_terms=glossary_terms
    )


@app.route("/trucks")
def trucks():
    """Truck types reference page with images"""
    # Require login
    if not session.get('logged_in') and not session.get('preview_mode'):
        return redirect(url_for("login"))

    # Define truck types with their images and definitions
    truck_data = [
        {
            'id': 'dry-van-trailer',
            'name': 'Dry Van Trailer',
            'module': 'Mod 4.2',
            'image': '/static/images/dry_van.jpeg',
            'definition': "The most common trailer in trucking: an enclosed rectangular box (53'×8.5'×9' interior) with 43,000-45,000 lb capacity. Used for palletized goods, boxed retail products, and any general freight not requiring temperature control. Benefits include weather protection, cargo security, and versatility across industries."
        },
        {
            'id': 'refrigerated-trailer-reefer',
            'name': 'Refrigerated Trailer (Reefer)',
            'module': 'Mod 4.2',
            'image': '/static/images/reefer.jpeg',
            'definition': "Insulated trailers with self-powered refrigeration units maintaining temperatures from -20°F (frozen) to +70°F (climate-controlled). Capacity 40,000-42,000 lbs. Essential for frozen foods, fresh produce, dairy, meat, pharmaceuticals, and anything temperature-sensitive."
        },
        {
            'id': 'flatbed-trailer',
            'name': 'Flatbed Trailer',
            'module': 'Mod 4.3',
            'image': '/static/images/flatbed.jpeg',
            'definition': "An open platform trailer (48' or 53' long × 8.5' wide × 5' deck height) without sides or roof. Used for lumber, steel, pipe, machinery, construction materials, and anything requiring top or side loading. Freight is secured with chains, straps, and blocking/bracing."
        },
        {
            'id': 'step-deck-drop-deck-trailer',
            'name': 'Step Deck (Drop Deck) Trailer',
            'module': 'Mod 4.4',
            'image': '/static/images/step_deck.jpeg',
            'definition': "A flatbed with two deck levels: the front section sits at standard 5' height for about 10 feet, then 'steps down' to approximately 3.5' off ground for the remaining 43 feet. This design allows freight 10-11 feet tall to stay under the 13.5-14' highway height limit."
        },
        {
            'id': 'tanker-trailer',
            'name': 'Tanker Trailer',
            'module': 'Mod 4.6',
            'image': '/static/images/tanker.jpeg',
            'definition': "Cylindrical trailers designed for liquid cargo, with capacities ranging from 5,000-9,000 gallons depending on product density and weight limits. Used for fuel, chemicals, milk, food-grade liquids, and industrial fluids. Tankers are specialized: a fuel tanker can't haul milk."
        },
        {
            'id': 'box-truck',
            'name': 'Box Truck',
            'module': 'Mod 4.2',
            'image': '/static/images/box_truck.jpeg',
            'definition': "A medium-duty truck with an integrated cargo box (typically 12-26 feet long), also called a straight truck or cube van. The cab and cargo area are one unit. Used for local deliveries, LTL consolidation, last-mile delivery, and moving services. Highly maneuverable for urban and residential access."
        },
        {
            'id': 'sprinter-van',
            'name': 'Sprinter Van',
            'module': 'Mod 5.8',
            'image': '/static/images/sprinter_van.jpeg',
            'definition': "A cargo van (typically 12-15 feet long with 3,000-5,000 lb capacity) used for expedited hot shot deliveries, small urgent shipments, and last-mile service. Drivers don't need a CDL since these are Class 2-3 vehicles under 10,000 lbs GVWR. Faster and more economical than full trucks for small time-critical freight."
        },
        {
            'id': 'conestoga-trailer',
            'name': 'Conestoga Trailer',
            'module': 'Mod 4.5',
            'image': '/static/images/conestoga1.jpg',
            'image2': '/static/images/conestoga2.jpg',
            'definition': "A flatbed trailer with a retractable rolling tarp system that slides open for side loading, then closes for weather protection. Combines flatbed accessibility with enclosed trailer protection. Ideal for freight needing forklift side-loading but also requiring protection from weather. Premium of $100-300 over standard flatbed."
        }
    ]

    return render_template(
        "trucks.html",
        trucks=truck_data
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login with username and password."""
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        if not username:
            return render_template("login.html", error="Please enter your username")

        if not password:
            return render_template("login.html", error="Please enter your password")

        # Find user by username (case-insensitive)
        from models import User
        user = User.query.filter_by(username=username).first()

        if user and user.password_hash and user.check_password(password):
            # Successful login - clear any stale session data first
            session.clear()

            session['user_id'] = user.id
            session['username'] = user.username
            session['logged_in'] = True
            session['preview_mode'] = user.is_preview_mode  # Explicitly sync from database
            session['quiz_answers'] = {}

            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()

            return redirect(url_for("cover"))
        else:
            # Invalid credentials
            return render_template("login.html", error="Invalid username or password")

    # GET request - show login page
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Simple registration - just enter your name to start."""
    if request.method == "POST":
        # Get username (name) from form and convert to lowercase
        username = request.form.get("username", "").strip().lower()
        
        # Validation
        if not username or len(username) < 2:
            return render_template("register.html", error="Please enter your name (at least 2 characters)")
        
        # Check for duplicate username (case-insensitive)
        from models import User
        if User.query.filter_by(username=username).first():
            return render_template("register.html", error="This name is already registered. Please login instead.")
        
        # Create new user (simple - just username)
        try:
            new_user = User(
                username=username,
                is_preview_mode=False
            )
            
            db.session.add(new_user)
            db.session.commit()

            # Auto-login after registration - clear any stale session first
            session.clear()
            session['user_id'] = new_user.id
            session['username'] = new_user.username
            session['logged_in'] = True
            session['preview_mode'] = False  # New users never have preview mode
            session['quiz_answers'] = {}

            return redirect(url_for("toc"))
            
        except Exception as e:
            db.session.rollback()
            return render_template("register.html", error=f"Registration failed: {str(e)}")
    
    # GET request - show registration page
    return render_template("register.html")


@app.route("/logout")
def logout():
    """Logout and clear session."""
    session.clear()
    return redirect(url_for("home"))


@app.route("/reset")
def reset():
    """Reset all quiz progress and redirect to home."""
    session.clear()
    return redirect(url_for("home"))


@app.route("/preview")
def preview():
    """Enable preview mode - unlocks all content for creators to review."""
    session['preview_mode'] = True
    session['logged_in'] = True
    session['username'] = 'preview_user'
    # Get or create preview user
    user = get_or_create_user('preview_user', is_preview=True)
    session['user_id'] = user.id
    return redirect(url_for("toc"))


# ============================================================================
# QUIZ QUESTION MANAGEMENT ROUTES
# ============================================================================

@app.route("/quiz_questions")
def quiz_questions():
    """Display quiz question management interface"""
    # Require preview mode
    user = get_current_user()
    preview_mode = session.get('preview_mode', False) or (user.is_preview_mode if user else False)
    if not preview_mode:
        return redirect(url_for("toc"))
    
    # Get all quiz questions
    questions = QuizQuestion.query.order_by(QuizQuestion.module_id, QuizQuestion.display_order).all()
    
    # Get all modules for dropdown
    modules = Module.query.order_by(Module.chapter_id, Module.display_order).all()
    
    # Get all chapters for filtering
    chapters = Chapter.query.order_by(Chapter.display_order).all()
    
    return render_template('quiz_questions.html', 
                         questions=questions, 
                         modules=modules, 
                         chapters=chapters,
                         preview_mode=preview_mode)


@app.route("/add_quiz_question", methods=['POST'])
def add_quiz_question():
    """Add a new quiz question"""
    # Require preview mode
    user = get_current_user()
    preview_mode = session.get('preview_mode', False) or (user.is_preview_mode if user else False)
    if not preview_mode:
        return redirect(url_for("toc"))
    
    try:
        # Get form data
        question_id = request.form.get('question_id')
        module_id = request.form.get('module_id')
        question = request.form.get('question')
        choice_a = request.form.get('choice_a')
        choice_b = request.form.get('choice_b')
        choice_c = request.form.get('choice_c')
        choice_d = request.form.get('choice_d')
        correct_choice = request.form.get('correct_choice')
        explanation = request.form.get('explanation')
        display_order = request.form.get('display_order', 1)
        
        # Validate required fields
        if not all([question_id, module_id, question, choice_a, choice_b, choice_c, choice_d, correct_choice, explanation]):
            return redirect(url_for('quiz_questions', error='All fields are required'))
        
        # Check if question ID already exists
        existing = QuizQuestion.query.get(question_id)
        if existing:
            return redirect(url_for('quiz_questions', error=f'Question ID {question_id} already exists'))
        
        # Create new question
        new_question = QuizQuestion(
            id=question_id,
            module_id=module_id,
            question=question,
            choice_a=choice_a,
            choice_b=choice_b,
            choice_c=choice_c,
            choice_d=choice_d,
            correct_choice=correct_choice,
            explanation=explanation,
            display_order=int(display_order)
        )
        
        db.session.add(new_question)
        db.session.commit()
        
        return redirect(url_for('quiz_questions', success='Question added successfully!'))
    
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('quiz_questions', error=f'Error adding question: {str(e)}'))


@app.route("/update_quiz_question/<question_id>", methods=['POST'])
def update_quiz_question(question_id):
    """Update an existing quiz question"""
    # Require preview mode
    user = get_current_user()
    preview_mode = session.get('preview_mode', False) or (user.is_preview_mode if user else False)
    if not preview_mode:
        return redirect(url_for("toc"))
    
    try:
        # Get the question
        question = QuizQuestion.query.get_or_404(question_id)
        
        # Update fields
        question.module_id = request.form.get('module_id')
        question.question = request.form.get('question')
        question.choice_a = request.form.get('choice_a')
        question.choice_b = request.form.get('choice_b')
        question.choice_c = request.form.get('choice_c')
        question.choice_d = request.form.get('choice_d')
        question.correct_choice = request.form.get('correct_choice')
        question.explanation = request.form.get('explanation')
        question.display_order = int(request.form.get('display_order', 1))
        
        db.session.commit()
        
        return redirect(url_for('quiz_questions', success='Question updated successfully!'))
    
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('quiz_questions', error=f'Error updating question: {str(e)}'))


@app.route("/delete_quiz_question/<question_id>", methods=['POST'])
def delete_quiz_question(question_id):
    """Delete a quiz question"""
    # Require preview mode
    user = get_current_user()
    preview_mode = session.get('preview_mode', False) or (user.is_preview_mode if user else False)
    if not preview_mode:
        return redirect(url_for("toc"))
    
    try:
        question = QuizQuestion.query.get_or_404(question_id)
        db.session.delete(question)
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


# ============================================================================
# CLI Commands for User Management
# ============================================================================
# Usage:
#   flask user-add <username> <password>     - Add a new user
#   flask user-password <username> <password> - Change user's password
#   flask user-list                          - List all users
#   flask user-delete <username>             - Delete a user
# ============================================================================

import click

@app.cli.command("user-add")
@click.argument("username")
@click.argument("password")
def cli_user_add(username, password):
    """Add a new user with a password."""
    from models import User
    username = username.strip().lower()

    # Check if user already exists
    existing = User.query.filter_by(username=username).first()
    if existing:
        click.echo(f"Error: User '{username}' already exists.")
        return

    # Create user
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f"User '{username}' created successfully.")


@app.cli.command("user-password")
@click.argument("username")
@click.argument("password")
def cli_user_password(username, password):
    """Change a user's password."""
    from models import User
    username = username.strip().lower()

    user = User.query.filter_by(username=username).first()
    if not user:
        click.echo(f"Error: User '{username}' not found.")
        return

    user.set_password(password)
    db.session.commit()
    click.echo(f"Password updated for user '{username}'.")


@app.cli.command("user-list")
def cli_user_list():
    """List all users."""
    from models import User
    users = User.query.all()

    if not users:
        click.echo("No users found.")
        return

    click.echo(f"{'Username':<20} {'Has Password':<15} {'Preview Mode':<15} {'Last Login'}")
    click.echo("-" * 70)
    for user in users:
        has_pw = "Yes" if user.password_hash else "No"
        preview = "Yes" if user.is_preview_mode else "No"
        last_login = user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "Never"
        click.echo(f"{user.username:<20} {has_pw:<15} {preview:<15} {last_login}")


@app.cli.command("user-delete")
@click.argument("username")
def cli_user_delete(username):
    """Delete a user."""
    from models import User
    username = username.strip().lower()

    user = User.query.filter_by(username=username).first()
    if not user:
        click.echo(f"Error: User '{username}' not found.")
        return

    db.session.delete(user)
    db.session.commit()
    click.echo(f"User '{username}' deleted.")


@app.cli.command("user-preview")
@click.argument("username")
@click.option("--on", "enable", flag_value=True, help="Enable preview mode (full access)")
@click.option("--off", "enable", flag_value=False, help="Disable preview mode (locked progression)")
def cli_user_preview(username, enable):
    """Enable or disable preview mode for a user (full access to all content)."""
    from models import User
    username = username.strip().lower()

    user = User.query.filter_by(username=username).first()
    if not user:
        click.echo(f"Error: User '{username}' not found.")
        return

    if enable is None:
        # No flag provided, show current status
        status = "enabled" if user.is_preview_mode else "disabled"
        click.echo(f"User '{username}' preview mode is currently {status}.")
        click.echo("Use --on or --off to change.")
        return

    user.is_preview_mode = enable
    db.session.commit()

    status = "enabled" if enable else "disabled"
    click.echo(f"Preview mode {status} for user '{username}'.")
    if enable:
        click.echo("User now has full access to all chapters and modules.")
    else:
        click.echo("User must complete quizzes to unlock chapters.")


@app.cli.command("user-reset")
@click.argument("username")
@click.option("--confirm", is_flag=True, help="Confirm the reset without prompting")
def cli_user_reset(username, confirm):
    """Reset all progress for a user (quiz answers and module completion)."""
    from models import User, UserProgress, UserQuizAnswer
    username = username.strip().lower()

    user = User.query.filter_by(username=username).first()
    if not user:
        click.echo(f"Error: User '{username}' not found.")
        return

    # Count existing progress
    quiz_count = UserQuizAnswer.query.filter_by(user_id=user.id).count()
    progress_count = UserProgress.query.filter_by(user_id=user.id).count()

    if quiz_count == 0 and progress_count == 0:
        click.echo(f"User '{username}' has no progress to reset.")
        return

    click.echo(f"User '{username}' has:")
    click.echo(f"  - {quiz_count} quiz answers")
    click.echo(f"  - {progress_count} module progress records")

    if not confirm:
        if not click.confirm("Are you sure you want to delete all progress?"):
            click.echo("Cancelled.")
            return

    # Delete all progress
    UserQuizAnswer.query.filter_by(user_id=user.id).delete()
    UserProgress.query.filter_by(user_id=user.id).delete()
    db.session.commit()

    click.echo(f"All progress reset for user '{username}'.")
    click.echo("User will need to log out and back in for changes to take effect.")


if __name__ == "__main__":
    app.run(debug=True)
