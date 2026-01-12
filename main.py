from flask import Flask, render_template, redirect, url_for, request, session, jsonify
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

def parse_project_outline(markdown_text: str = None):
    """
    Get chapter list from database.
    markdown_text parameter kept for backward compatibility but not used.
    """
    chapters = []
    
    # Query chapters from database
    db_chapters = Chapter.query.order_by(Chapter.display_order).all()
    
    for ch in db_chapters:
        chapters.append({
            "id": ch.id,
            "title": ch.title
        })
    
    # Check if glossary exists
    has_glossary = GlossaryTerm.query.count() > 0
    if has_glossary:
        chapters.append({"id": "glossary", "title": "Glossary"})
    
    print(f"[parse_project_outline] Found {len(chapters)} chapters from database (including glossary: {has_glossary})")
    return chapters


def extract_chapter_content(markdown_text: str = None, chapter_id: int = 0):
    """
    Get chapter content from database.
    Parameters kept for backward compatibility but markdown_text is not used.
    """
    # Get chapter from database
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return {
            "chapter_id": chapter_id,
            "chapter_title": "",
            "intro": None,
            "modules": [],
            "summary": None,
            "action_items": None,
        }
    
    # Get chapter sections
    intro_section = ChapterSection.query.filter_by(
        chapter_id=chapter_id,
        section_type='intro'
    ).first()
    
    summary_section = ChapterSection.query.filter_by(
        chapter_id=chapter_id,
        section_type='summary'
    ).first()
    
    action_items_section = ChapterSection.query.filter_by(
        chapter_id=chapter_id,
        section_type='action_items'
    ).first()
    
    # Get modules
    db_modules = Module.query.filter_by(chapter_id=chapter_id).order_by(Module.display_order).all()
    
    modules = []
    for mod in db_modules:
        modules.append({
            "id": mod.id,
            "title": mod.title,
            "content": mod.content_markdown.splitlines() if mod.content_markdown else []
        })
    
    print(
        f"[extract_chapter_content] ch={chapter_id} modules={len(modules)} "
        f"summary={'yes' if summary_section else 'no'} action_items={'yes' if action_items_section else 'no'}"
    )
    
    return {
        "chapter_id": chapter_id,
        "chapter_title": chapter.title,
        "intro": intro_section.content_markdown if intro_section else None,
        "modules": modules,
        "summary": summary_section.content_markdown if summary_section else None,
        "action_items": action_items_section.content_markdown if action_items_section else None,
    }


def preprocess_content(text: str) -> str:
    """Add markdown formatting to plain text content by detecting patterns."""
    if not text:
        return ""
    
    lines = text.split('\n')
    processed = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            processed.append('')
            continue
        
        # Detect section headers - short lines (< 50 chars) followed by content
        # Common patterns: "Time Savings", "Risk Management", "Months 1-3: The Learning Phase"
        is_section_header = False
        if len(stripped) < 70 and i < len(lines) - 1:
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            # If this line is short and next line is substantial content (not another header)
            if next_line and len(next_line) > 50:
                # Check if it looks like a header (title case, ends with colon, or short phrase)
                if (stripped[0].isupper() and 
                    (stripped.endswith(':') or 
                     stripped.count(' ') <= 5 or
                     any(stripped.startswith(prefix) for prefix in ['Months ', 'Year ', 'Why ', 'What ', 'The ']))):
                    is_section_header = True
        
        if is_section_header:
            # Add blank line before header for spacing and make it bold
            if processed and processed[-1] != '':
                processed.append('')
            processed.append(f"**{stripped}**")
            processed.append('')
        else:
            processed.append(line)
    
    return '\n'.join(processed)


def process_callouts(text: str) -> str:
    """Convert callout syntax [TYPE] content to HTML with special styling."""
    if not text:
        return ""
    
    # Pattern: [TYPE] Content (on its own line or paragraph)
    callout_pattern = re.compile(r'\[([A-Z\s]+)\]\s*(.+?)(?=\n\n|\[(?:[A-Z\s]+)\]|$)', re.DOTALL)
    
    def replace_callout(match):
        callout_type = match.group(1).strip()
        content = match.group(2).strip()
        
        # Map types to styles and icons
        styles = {
            'PRO TIP': ('callout-tip', '💡'),
            'COMMON MISTAKE': ('callout-warning', '⚠️'),
            'REAL EXAMPLE': ('callout-example', '📊'),
            'KEY TAKEAWAY': ('callout-key', '🎯'),
            'IMPORTANT': ('callout-important', '⚡'),
            'NOTE': ('callout-note', '📝')
        }
        
        css_class, icon = styles.get(callout_type, ('callout-default', '📌'))
        
        return f'<div class="callout {css_class}"><div class="callout-title">{icon} <strong>{callout_type}</strong></div><div class="callout-content">{content}</div></div>\n\n'
    
    return callout_pattern.sub(replace_callout, text)


def convert_to_html(text: str) -> str:
    """Convert markdown text to HTML, preserving formatting."""
    if not text:
        return ""
    
    # Process callouts first (before markdown conversion)
    text_with_callouts = process_callouts(text)
    
    # Preprocess to add markdown formatting
    formatted_text = preprocess_content(text_with_callouts)
    
    # Convert markdown to HTML with extensions for better formatting
    md = markdown.Markdown(extensions=['nl2br', 'sane_lists'])
    return md.convert(formatted_text)


def estimate_visual_height(line: str, is_in_callout: bool = False, is_callout_start: bool = False) -> float:
    """
    Estimate the visual height cost of a line of text.
    Returns a "height score" where 1.0 = one line of regular text.
    
    Callouts are much taller due to borders, padding, and styling.
    """
    stripped = line.strip()
    
    # Empty lines
    if not stripped:
        return 0.5 if not is_in_callout else 0.3
    
    # Callout start line - includes title bar with icon + padding
    if is_callout_start:
        return 4.0  # Title + top padding + borders
    
    # Content inside callout - extra padding and line spacing
    if is_in_callout:
        char_count = len(stripped)
        # Callouts have padding and styled boxes, so they're taller
        lines_of_text = max(1, char_count / 50)  # ~50 chars per line in callouts
        return lines_of_text * 1.8  # 1.8x taller due to padding
    
    # Bold headers
    if stripped.startswith('**') and stripped.endswith('**'):
        return 2.5  # Headers are larger and have spacing
    
    # Regular text - estimate lines based on character count
    char_count = len(stripped)
    if char_count == 0:
        return 0.5
    
    # Assume ~60 chars per line for regular text
    lines_of_text = max(1, char_count / 60)
    return lines_of_text * 1.2  # Account for line height


def split_content_into_pages(content_text: str, max_height_score: float = 27.5) -> list:
    """
    Split long content into multiple pages based on estimated VISUAL HEIGHT.
    
    Instead of counting characters, we estimate how tall content will render:
    - Regular text: ~1.0-1.2 height units per line
    - Bold headers: ~2.5 height units (larger font + spacing)
    - Callout boxes: ~4.0 for title + 1.8x per line of content (padding + borders)
    
    Max height score of 28.0 = approximately viewport height without scrolling.
    Never splits callout blocks ([TYPE] content).
    """
    if not content_text:
        return [content_text]
    
    # Split by lines first
    lines = content_text.split('\n')
    pages = []
    current_page = []
    current_height = 0.0
    in_callout = False
    callout_lines = []
    callout_pattern = re.compile(r'^\[([A-Z\s]+)\]')
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Detect callout start
        is_callout_start = callout_pattern.match(stripped) is not None
        if is_callout_start:
            in_callout = True
            callout_lines = [line]
            continue  # Don't add yet, collect whole callout first
        
        # If in callout, collect lines
        if in_callout:
            callout_lines.append(line)
            # Detect callout end (empty line after content OR next line is not indented/content)
            is_last_line = (i == len(lines) - 1)
            if (stripped == '' and len(callout_lines) > 1) or is_last_line:
                # Callout is complete, calculate its total height
                callout_height = estimate_visual_height(callout_lines[0], False, True)  # Title
                for callout_line in callout_lines[1:]:
                    callout_height += estimate_visual_height(callout_line, True, False)
                
                # Be conservative - use 85% threshold for callouts to ensure they fit
                safety_threshold = max_height_score * 0.85
                
                # If adding callout would exceed safe limit, start new page
                if current_height + callout_height > safety_threshold and current_page:
                    pages.append('\n'.join(current_page))
                    current_page = callout_lines.copy()
                    current_height = callout_height
                else:
                    current_page.extend(callout_lines)
                    current_height += callout_height
                
                in_callout = False
                callout_lines = []
            continue
        
        # Regular line (not in callout)
        line_height = estimate_visual_height(line, False, False)
        
        # If adding this line would exceed limit, start new page
        if current_height + line_height > max_height_score and current_page:
            # If current line is a header, include it in next page
            if stripped.startswith('**'):
                pages.append('\n'.join(current_page))
                current_page = [line]
                current_height = line_height
            else:
                current_page.append(line)
                pages.append('\n'.join(current_page))
                current_page = []
                current_height = 0.0
        else:
            current_page.append(line)
            current_height += line_height
    
    # Add any remaining callout lines if still in callout (shouldn't happen but safety)
    if callout_lines:
        current_page.extend(callout_lines)
    
    # Add the last page
    if current_page:
        pages.append('\n'.join(current_page))
    
    return pages


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


def get_all_modules_completed(session_quiz_answers_or_user_id):
    """Check if all Chapter 1 modules are completed."""
    return get_chapter_completion_status(session_quiz_answers_or_user_id, 1)


def get_quiz_questions_for_module(module_id):
    """
    Get quiz questions for a module from database.
    Returns list of question dicts in the old format for compatibility.
    """
    quizzes = QuizQuestion.query.filter_by(module_id=module_id).order_by(QuizQuestion.display_order).all()
    
    questions = []
    for quiz in quizzes:
        # Get the quiz in the format expected by page rendering
        # Note: choices are in their original order (a, b, c, d) here
        # They'll be shuffled per user when displayed
        questions.append({
            "id": quiz.id,
            "question": quiz.question,
            "choices": [quiz.choice_a, quiz.choice_b, quiz.choice_c, quiz.choice_d],
            "correct_index": ['a', 'b', 'c', 'd'].index(quiz.correct_choice),
            "explanation": quiz.explanation
        })
    
    return questions


def build_pages(text: str = None):
    """
    Build a flat list of pages: Cover, TOC, then all chapters with modules, summaries, action items.
    Now queries from database instead of parsing markdown.
    
    Args:
        text: Optional markdown text (for backward compatibility, not used)
    """
    chapters = parse_project_outline(text)
    ch1 = extract_chapter_content(text, 1)
    ch2 = extract_chapter_content(text, 2)
    ch3 = extract_chapter_content(text, 3)
    ch4 = extract_chapter_content(text, 4)
    ch5 = extract_chapter_content(text, 5)
    ch6 = extract_chapter_content(text, 6)
    ch7 = extract_chapter_content(text, 7)
    ch8 = extract_chapter_content(text, 8)
    ch9 = extract_chapter_content(text, 9)
    
    pages = []
    module_page_map = {}  # Maps module_id -> page_num
    quiz_page_map = {}  # Maps quiz_id -> page_num
    summary_page_map = {}  # Maps chapter_id -> page_num for summary pages
    action_items_page_map = {}  # Maps chapter_id -> page_num for action_items pages
    
    # Page 0: Cover page (lines 1-27 of project.md)
    lines = text.splitlines() if text else []
    cover_content = "\n".join(lines[0:27]) if len(lines) >= 27 else ""
    pages.append({"type": "cover", "content": cover_content, "ch1_modules": ch1["modules"], "ch2_modules": ch2["modules"], "ch3_modules": ch3["modules"], "ch4_modules": ch4["modules"], "ch5_modules": ch5["modules"], "ch6_modules": ch6["modules"], "ch7_modules": ch7["modules"], "ch8_modules": ch8["modules"], "ch9_modules": ch9["modules"]})
    
    # Page 1: Table of Contents
    pages.append({"type": "toc", "chapters": chapters, "ch1_modules": ch1["modules"], "ch2_modules": ch2["modules"], "ch3_modules": ch3["modules"], "ch4_modules": ch4["modules"], "ch5_modules": ch5["modules"], "ch6_modules": ch6["modules"], "ch7_modules": ch7["modules"], "ch8_modules": ch8["modules"], "ch9_modules": ch9["modules"]})
    
    # Chapter 1 intro
    if ch1["intro"]:
        pages.append({
            "type": "intro",
            "chapter_id": 1,
            "chapter_title": ch1["chapter_title"],
            "content": ch1["intro"],
            "content_html": convert_to_html(ch1["intro"])
        })
    
    # Chapter 1 modules
    for mod in ch1["modules"]:
        module_page_map[mod["id"]] = len(pages)  # Record the first page number for this module
        content_text = "\n".join(mod["content"])
        
        # Split module content into multiple pages if needed
        content_pages = split_content_into_pages(content_text)
        
        for page_idx, page_content in enumerate(content_pages):
            pages.append({
                "type": "module",
                "chapter_id": 1,
                "chapter_title": ch1["chapter_title"],
                "module_id": mod["id"],
                "module_title": mod["title"],
                "content": page_content,
                "content_html": convert_to_html(page_content),
                "module_page_num": page_idx + 1,
                "module_total_pages": len(content_pages)
            })
        
        # Add quiz questions after the last page of each module (from database)
        quiz_questions = get_quiz_questions_for_module(mod["id"])
        
        if quiz_questions:
            for idx, quiz_question in enumerate(quiz_questions):
                quiz_page_map[quiz_question["id"]] = len(pages)  # Track quiz question page number
                pages.append({
                    "type": "quiz",
                    "chapter_id": 1,
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "quiz_question": quiz_question,
                    "question_number": idx + 1,
                    "total_questions": len(quiz_questions)
                })
    
    # Chapter 1 summary
    if ch1["summary"]:
        summary_page_map[1] = len(pages)
        pages.append({
            "type": "summary",
            "chapter_id": 1,
            "chapter_title": ch1["chapter_title"],
            "content": ch1["summary"],
            "content_html": convert_to_html(ch1["summary"])
        })
    
    # Chapter 1 action items
    if ch1["action_items"]:
        action_items_page_map[1] = len(pages)
        pages.append({
            "type": "action_items",
            "chapter_id": 1,
            "chapter_title": ch1["chapter_title"],
            "content": ch1["action_items"],
            "content_html": convert_to_html(ch1["action_items"])
        })
    
    # Chapter 2 intro
    if ch2["intro"]:
        pages.append({
            "type": "intro",
            "chapter_id": 2,
            "chapter_title": ch2["chapter_title"],
            "content": ch2["intro"],
            "content_html": convert_to_html(ch2["intro"])
        })
    
    # Chapter 2 modules
    for mod in ch2["modules"]:
        module_page_map[mod["id"]] = len(pages)  # Record the first page number for this module
        content_text = "\n".join(mod["content"])
        
        # Split module content into multiple pages if needed
        content_pages = split_content_into_pages(content_text)
        
        for page_idx, page_content in enumerate(content_pages):
            pages.append({
                "type": "module",
                "chapter_id": 2,
                "chapter_title": ch2["chapter_title"],
                "module_id": mod["id"],
                "module_title": mod["title"],
                "content": page_content,
                "content_html": convert_to_html(page_content),
                "module_page_num": page_idx + 1,
                "module_total_pages": len(content_pages)
            })
        
        # Add quiz questions after the last page of each module (from database)
        quiz_questions = get_quiz_questions_for_module(mod["id"])
        
        if quiz_questions:
            for idx, quiz_question in enumerate(quiz_questions):
                quiz_page_map[quiz_question["id"]] = len(pages)  # Track quiz question page number
                pages.append({
                    "type": "quiz",
                    "chapter_id": 2,
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "quiz_question": quiz_question,
                    "question_number": idx + 1,
                    "total_questions": len(quiz_questions)
                })
    
    # Chapter 2 summary
    if ch2["summary"]:
        summary_page_map[2] = len(pages)
        pages.append({
            "type": "summary",
            "chapter_id": 2,
            "chapter_title": ch2["chapter_title"],
            "content": ch2["summary"],
            "content_html": convert_to_html(ch2["summary"])
        })
    
    # Chapter 2 action items
    if ch2["action_items"]:
        action_items_page_map[2] = len(pages)
        pages.append({
            "type": "action_items",
            "chapter_id": 2,
            "chapter_title": ch2["chapter_title"],
            "content": ch2["action_items"],
            "content_html": convert_to_html(ch2["action_items"])
        })
    
    # Chapter 3 intro
    if ch3["intro"]:
        pages.append({
            "type": "intro",
            "chapter_id": 3,
            "chapter_title": ch3["chapter_title"],
            "content": ch3["intro"],
            "content_html": convert_to_html(ch3["intro"])
        })
    
    # Chapter 3 modules
    for mod in ch3["modules"]:
        module_page_map[mod["id"]] = len(pages)  # Record the first page number for this module
        content_text = "\n".join(mod["content"])
        
        # Split module content into multiple pages if needed
        content_pages = split_content_into_pages(content_text)
        
        for page_idx, page_content in enumerate(content_pages):
            pages.append({
                "type": "module",
                "chapter_id": 3,
                "chapter_title": ch3["chapter_title"],
                "module_id": mod["id"],
                "module_title": mod["title"],
                "content": page_content,
                "content_html": convert_to_html(page_content),
                "module_page_num": page_idx + 1,
                "module_total_pages": len(content_pages)
            })
        
        # Add quiz questions after the last page of each module (from database)
        quiz_questions = get_quiz_questions_for_module(mod["id"])
        
        if quiz_questions:
            for idx, quiz_question in enumerate(quiz_questions):
                quiz_page_map[quiz_question["id"]] = len(pages)  # Track quiz question page number
                pages.append({
                    "type": "quiz",
                    "chapter_id": 3,
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "quiz_question": quiz_question,
                    "question_number": idx + 1,
                    "total_questions": len(quiz_questions)
                })
    
    # Chapter 3 summary
    if ch3["summary"]:
        summary_page_map[3] = len(pages)
        pages.append({
            "type": "summary",
            "chapter_id": 3,
            "chapter_title": ch3["chapter_title"],
            "content": ch3["summary"],
            "content_html": convert_to_html(ch3["summary"])
        })
    
    # Chapter 3 action items
    if ch3["action_items"]:
        action_items_page_map[3] = len(pages)
        pages.append({
            "type": "action_items",
            "chapter_id": 3,
            "chapter_title": ch3["chapter_title"],
            "content": ch3["action_items"],
            "content_html": convert_to_html(ch3["action_items"])
        })
    
    # Chapter 4 intro
    if ch4["intro"]:
        pages.append({
            "type": "intro",
            "chapter_id": 4,
            "chapter_title": ch4["chapter_title"],
            "content": ch4["intro"],
            "content_html": convert_to_html(ch4["intro"])
        })
    
    # Chapter 4 modules
    for mod in ch4["modules"]:
        module_page_map[mod["id"]] = len(pages)  # Record the first page number for this module
        content_text = "\n".join(mod["content"])
        
        # Split module content into multiple pages if needed
        content_pages = split_content_into_pages(content_text)
        
        for page_idx, page_content in enumerate(content_pages):
            pages.append({
                "type": "module",
                "chapter_id": 4,
                "chapter_title": ch4["chapter_title"],
                "module_id": mod["id"],
                "module_title": mod["title"],
                "content": page_content,
                "content_html": convert_to_html(page_content),
                "module_page_num": page_idx + 1,
                "module_total_pages": len(content_pages)
            })
        
        # Add quiz questions after the last page of each module (from database)
        quiz_questions = get_quiz_questions_for_module(mod["id"])
        
        if quiz_questions:
            for idx, quiz_question in enumerate(quiz_questions):
                quiz_page_map[quiz_question["id"]] = len(pages)  # Track quiz question page number
                pages.append({
                    "type": "quiz",
                    "chapter_id": 4,
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "quiz_question": quiz_question,
                    "question_number": idx + 1,
                    "total_questions": len(quiz_questions)
                })
    
    # Chapter 4 summary
    if ch4["summary"]:
        summary_page_map[4] = len(pages)
        pages.append({
            "type": "summary",
            "chapter_id": 4,
            "chapter_title": ch4["chapter_title"],
            "content": ch4["summary"],
            "content_html": convert_to_html(ch4["summary"])
        })
    
    # Chapter 4 action items
    if ch4["action_items"]:
        action_items_page_map[4] = len(pages)
        pages.append({
            "type": "action_items",
            "chapter_id": 4,
            "chapter_title": ch4["chapter_title"],
            "content": ch4["action_items"],
            "content_html": convert_to_html(ch4["action_items"])
        })
    
    # ================================================================
    # CHAPTER 5
    # ================================================================
    
    # Chapter 5 intro
    if ch5["intro"]:
        pages.append({
            "type": "intro",
            "chapter_id": 5,
            "chapter_title": ch5["chapter_title"],
            "content": ch5["intro"],
            "content_html": convert_to_html(ch5["intro"])
        })
    
    # Chapter 5 modules
    for mod in ch5["modules"]:
        module_page_map[mod["id"]] = len(pages)
        content_text = "\n".join(mod["content"])
        content_pages = split_content_into_pages(content_text)
        
        for page_idx, page_content in enumerate(content_pages):
            pages.append({
                "type": "module",
                "chapter_id": 5,
                "chapter_title": ch5["chapter_title"],
                "module_id": mod["id"],
                "module_title": mod["title"],
                "content": page_content,
                "content_html": convert_to_html(page_content),
                "module_page_num": page_idx + 1,
                "module_total_pages": len(content_pages)
            })
        
        # Add quiz questions after the last page of each module (from database)
        quiz_questions = get_quiz_questions_for_module(mod["id"])
        
        if quiz_questions:
            for idx, quiz_question in enumerate(quiz_questions):
                quiz_page_map[quiz_question["id"]] = len(pages)
                pages.append({
                    "type": "quiz",
                    "chapter_id": 5,
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "quiz_question": quiz_question,
                    "question_number": idx + 1,
                    "total_questions": len(quiz_questions)
                })
    
    # Chapter 5 summary
    if ch5["summary"]:
        summary_page_map[5] = len(pages)
        pages.append({
            "type": "summary",
            "chapter_id": 5,
            "chapter_title": ch5["chapter_title"],
            "content": ch5["summary"],
            "content_html": convert_to_html(ch5["summary"])
        })
    
    # Chapter 5 action items
    if ch5["action_items"]:
        action_items_page_map[5] = len(pages)
        pages.append({
            "type": "action_items",
            "chapter_id": 5,
            "chapter_title": ch5["chapter_title"],
            "content": ch5["action_items"],
            "content_html": convert_to_html(ch5["action_items"])
        })
    
    # ================================================================
    # CHAPTER 6
    # ================================================================
    
    # Chapter 6 intro
    if ch6["intro"]:
        pages.append({
            "type": "intro",
            "chapter_id": 6,
            "chapter_title": ch6["chapter_title"],
            "content": ch6["intro"],
            "content_html": convert_to_html(ch6["intro"])
        })
    
    # Chapter 6 modules
    for mod in ch6["modules"]:
        module_page_map[mod["id"]] = len(pages)  # Record the first page number for this module
        content_text = "\n".join(mod["content"])
        
        # Split module content into multiple pages if needed
        content_pages = split_content_into_pages(content_text)
        
        for page_idx, page_content in enumerate(content_pages):
            pages.append({
                "type": "module",
                "chapter_id": 6,
                "chapter_title": ch6["chapter_title"],
                "module_id": mod["id"],
                "module_title": mod["title"],
                "content": page_content,
                "content_html": convert_to_html(page_content),
                "module_page_num": page_idx + 1,
                "module_total_pages": len(content_pages)
            })
        
        # Add quiz questions after the last page of each module (from database)
        quiz_questions = get_quiz_questions_for_module(mod["id"])
        
        if quiz_questions:
            for idx, quiz_question in enumerate(quiz_questions):
                quiz_page_map[quiz_question["id"]] = len(pages)  # Track quiz question page number
                pages.append({
                    "type": "quiz",
                    "chapter_id": 6,
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "quiz_question": quiz_question,
                    "question_number": idx + 1,
                    "total_questions": len(quiz_questions)
                })
    
    # Chapter 6 summary
    if ch6["summary"]:
        summary_page_map[6] = len(pages)
        pages.append({
            "type": "summary",
            "chapter_id": 6,
            "chapter_title": ch6["chapter_title"],
            "content": ch6["summary"],
            "content_html": convert_to_html(ch6["summary"])
        })
    
    # Chapter 6 action items
    if ch6["action_items"]:
        action_items_page_map[6] = len(pages)
        pages.append({
            "type": "action_items",
            "chapter_id": 6,
            "chapter_title": ch6["chapter_title"],
            "content": ch6["action_items"],
            "content_html": convert_to_html(ch6["action_items"])
        })
    
    # ================================================================
    # CHAPTER 7
    # ================================================================
    
    # Chapter 7 intro
    if ch7["intro"]:
        pages.append({
            "type": "intro",
            "chapter_id": 7,
            "chapter_title": ch7["chapter_title"],
            "content": ch7["intro"],
            "content_html": convert_to_html(ch7["intro"])
        })
    
    # Chapter 7 modules
    for mod in ch7["modules"]:
        module_page_map[mod["id"]] = len(pages)  # Record the first page number for this module
        content_text = "\n".join(mod["content"])
        
        # Split module content into multiple pages if needed
        content_pages = split_content_into_pages(content_text)
        
        for page_idx, page_content in enumerate(content_pages):
            pages.append({
                "type": "module",
                "chapter_id": 7,
                "chapter_title": ch7["chapter_title"],
                "module_id": mod["id"],
                "module_title": mod["title"],
                "content": page_content,
                "content_html": convert_to_html(page_content),
                "module_page_num": page_idx + 1,
                "module_total_pages": len(content_pages)
            })
        
        # Add quiz questions after the last page of each module (from database)
        quiz_questions = get_quiz_questions_for_module(mod["id"])
        
        if quiz_questions:
            for idx, quiz_question in enumerate(quiz_questions):
                quiz_page_map[quiz_question["id"]] = len(pages)  # Track quiz question page number
                pages.append({
                    "type": "quiz",
                    "chapter_id": 7,
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "quiz_question": quiz_question,
                    "question_number": idx + 1,
                    "total_questions": len(quiz_questions)
                })
    
    # Chapter 7 summary
    if ch7["summary"]:
        summary_page_map[7] = len(pages)
        pages.append({
            "type": "summary",
            "chapter_id": 7,
            "chapter_title": ch7["chapter_title"],
            "content": ch7["summary"],
            "content_html": convert_to_html(ch7["summary"])
        })
    
    # Chapter 7 action items
    if ch7["action_items"]:
        action_items_page_map[7] = len(pages)
        pages.append({
            "type": "action_items",
            "chapter_id": 7,
            "chapter_title": ch7["chapter_title"],
            "content": ch7["action_items"],
            "content_html": convert_to_html(ch7["action_items"])
        })
    
    # ================================================================
    # CHAPTER 8
    # ================================================================
    
    # Chapter 8 intro
    if ch8["intro"]:
        pages.append({
            "type": "intro",
            "chapter_id": 8,
            "chapter_title": ch8["chapter_title"],
            "content": ch8["intro"],
            "content_html": convert_to_html(ch8["intro"])
        })
    
    # Chapter 8 modules
    for mod in ch8["modules"]:
        module_page_map[mod["id"]] = len(pages)  # Record the first page number for this module
        content_text = "\n".join(mod["content"])
        
        # Split module content into multiple pages if needed
        content_pages = split_content_into_pages(content_text)
        
        for page_idx, page_content in enumerate(content_pages):
            pages.append({
                "type": "module",
                "chapter_id": 8,
                "chapter_title": ch8["chapter_title"],
                "module_id": mod["id"],
                "module_title": mod["title"],
                "content": page_content,
                "content_html": convert_to_html(page_content),
                "module_page_num": page_idx + 1,
                "module_total_pages": len(content_pages)
            })
        
        # Add quiz questions after the last page of each module (from database)
        quiz_questions = get_quiz_questions_for_module(mod["id"])
        
        if quiz_questions:
            for idx, quiz_question in enumerate(quiz_questions):
                quiz_page_map[quiz_question["id"]] = len(pages)  # Track quiz question page number
                pages.append({
                    "type": "quiz",
                    "chapter_id": 8,
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "quiz_question": quiz_question,
                    "question_number": idx + 1,
                    "total_questions": len(quiz_questions)
                })
    
    # Chapter 8 summary
    if ch8["summary"]:
        summary_page_map[8] = len(pages)
        pages.append({
            "type": "summary",
            "chapter_id": 8,
            "chapter_title": ch8["chapter_title"],
            "content": ch8["summary"],
            "content_html": convert_to_html(ch8["summary"])
        })
    
    # Chapter 8 action items
    if ch8["action_items"]:
        action_items_page_map[8] = len(pages)
        pages.append({
            "type": "action_items",
            "chapter_id": 8,
            "chapter_title": ch8["chapter_title"],
            "content": ch8["action_items"],
            "content_html": convert_to_html(ch8["action_items"])
        })
    
    # ================================================================
    # CHAPTER 9
    # ================================================================
    
    # Chapter 9 intro
    if ch9["intro"]:
        pages.append({
            "type": "intro",
            "chapter_id": 9,
            "chapter_title": ch9["chapter_title"],
            "content": ch9["intro"],
            "content_html": convert_to_html(ch9["intro"])
        })
    
    # Chapter 9 modules
    for mod in ch9["modules"]:
        module_page_map[mod["id"]] = len(pages)  # Record the first page number for this module
        content_text = "\n".join(mod["content"])
        
        # Split module content into multiple pages if needed
        content_pages = split_content_into_pages(content_text)
        
        for page_idx, page_content in enumerate(content_pages):
            pages.append({
                "type": "module",
                "chapter_id": 9,
                "chapter_title": ch9["chapter_title"],
                "module_id": mod["id"],
                "module_title": mod["title"],
                "content": page_content,
                "content_html": convert_to_html(page_content),
                "module_page_num": page_idx + 1,
                "module_total_pages": len(content_pages)
            })
        
        # Add quiz questions after the last page of each module (from database)
        quiz_questions = get_quiz_questions_for_module(mod["id"])
        
        if quiz_questions:
            for idx, quiz_question in enumerate(quiz_questions):
                quiz_page_map[quiz_question["id"]] = len(pages)  # Track quiz question page number
                pages.append({
                    "type": "quiz",
                    "chapter_id": 9,
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "quiz_question": quiz_question,
                    "question_number": idx + 1,
                    "total_questions": len(quiz_questions)
                })
    
    # Chapter 9 summary
    if ch9["summary"]:
        summary_page_map[9] = len(pages)
        pages.append({
            "type": "summary",
            "chapter_id": 9,
            "chapter_title": ch9["chapter_title"],
            "content": ch9["summary"],
            "content_html": convert_to_html(ch9["summary"])
        })
    
    # Chapter 9 action items
    if ch9["action_items"]:
        action_items_page_map[9] = len(pages)
        pages.append({
            "type": "action_items",
            "chapter_id": 9,
            "chapter_title": ch9["chapter_title"],
            "content": ch9["action_items"],
            "content_html": convert_to_html(ch9["action_items"])
        })
    
    # Add module_page_map, quiz_page_map, summary_page_map, and action_items_page_map to cover and TOC pages
    pages[0]["module_page_map"] = module_page_map
    pages[0]["quiz_page_map"] = quiz_page_map
    pages[0]["summary_page_map"] = summary_page_map
    pages[0]["action_items_page_map"] = action_items_page_map
    pages[1]["module_page_map"] = module_page_map
    pages[1]["quiz_page_map"] = quiz_page_map
    pages[1]["summary_page_map"] = summary_page_map
    pages[1]["action_items_page_map"] = action_items_page_map
    
    # Note: Glossary is now a separate page at /glossary, not part of page navigation
    
    print(f"[build_pages] Built {len(pages)} pages")
    return pages


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
    return render_template("pages/toc.html")


@app.route("/chapter/<int:chapter_num>/<page>")
def chapter(chapter_num, page):
    """
    Serve chapter pages (intro, summary, action_items)
    """
    if not session.get('logged_in') and not session.get('preview_mode'):
        return redirect(url_for("login"))

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


@app.route("/page/<int:page_num>", methods=["GET", "POST"])
def page(page_num: int):
    # Require login (unless accessing preview mode)
    if not session.get('logged_in') and not session.get('preview_mode'):
        return redirect(url_for("login"))
    
    try:
        text = PROJECT_MD_PATH.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        text = ""
    
    pages = build_pages(text) if text else []
    
    if page_num < 0 or page_num >= len(pages):
        page_num = 0
    
    current_page = pages[page_num] if pages else {"type": "error", "content": "No content found"}
    
    # Initialize session for quiz answers if not exists
    if 'quiz_answers' not in session:
        session['quiz_answers'] = {}
    
    # Check for preview mode query parameter
    if request.args.get('preview') == 'true':
        session['preview_mode'] = True
    elif 'preview' in request.args and request.args.get('preview') == 'false':
        session['preview_mode'] = False
    
    # Get current user for database operations
    user = get_current_user()
    
    # Shuffle quiz question choices BEFORE handling submission (so order is consistent)
    if current_page.get("type") == "quiz":
        quiz_id = current_page["quiz_question"]["id"]
        # Get the QuizQuestion object to use get_shuffled_for_user
        from models import QuizQuestion
        quiz_obj = QuizQuestion.query.get(quiz_id)
        
        if quiz_obj:
            # Get shuffled choices for this user (maintains consistent order per user)
            shuffled_data = quiz_obj.get_shuffled_for_user(user.id)
            
            # Replace quiz_question with shuffled version
            current_page["quiz_question"] = {
                "id": shuffled_data["id"],
                "question": shuffled_data["question"],
                "choices": shuffled_data["choices"],  # Already shuffled
                "correct_index": shuffled_data["correct_index"],  # Index in shuffled array
                "explanation": shuffled_data["explanation"],
                "answer_order": shuffled_data["answer_order"]  # Store order for answer submission
            }
            
            # Store answer_order in session for answer submission
            if 'quiz_answer_orders' not in session:
                session['quiz_answer_orders'] = {}
            session['quiz_answer_orders'][quiz_id] = shuffled_data["answer_order"]
            session.modified = True
    
    # Handle quiz answer submission (now uses database)
    quiz_feedback = None
    if request.method == "POST" and current_page.get("type") == "quiz":
        selected_answer = request.form.get("answer")
        if selected_answer is not None:
            selected_index = int(selected_answer)
            quiz_question = current_page["quiz_question"]

            # Get the stored answer_order from session (set when page was rendered above)
            # Fallback to answer_order from quiz_question dict if session doesn't have it
            answer_order = session.get('quiz_answer_orders', {}).get(
                quiz_question["id"],
                quiz_question.get("answer_order", ['a', 'b', 'c', 'd'])
            )

            # Submit answer to database
            result = update_user_quiz_answer(
                user.id,
                quiz_question["id"],
                selected_index,
                answer_order
            )

            if result['is_correct'] == True:
                # Correct answer - also update session for backward compatibility
                session['quiz_answers'][quiz_question["id"]] = True
                session.modified = True
                quiz_feedback = {
                    "correct": True,
                    "message": "Correct! " + result['explanation']
                }
            else:
                # Incorrect answer
                quiz_feedback = {
                    "correct": False,
                    "message": "That's not quite right. Please try again.",
                    "selected_index": selected_index
                }
    
    # Check if current quiz question has been answered correctly (from database)
    quiz_answered = False
    if current_page.get("type") == "quiz":
        quiz_id = current_page["quiz_question"]["id"]
        # Check database first
        quiz_answered = db_get_module_completion(user.id, current_page.get("module_id", ""))
        # Also check if this specific question was answered
        from models import UserQuizAnswer
        user_answer = UserQuizAnswer.query.filter_by(
            user_id=user.id,
            quiz_question_id=quiz_id
        ).first()
        if user_answer and user_answer.is_correct is not None:
            quiz_answered = bool(user_answer.is_correct)  # Explicit bool for template consistency
        # Update session for backward compatibility
        session['quiz_answers'][quiz_id] = quiz_answered
    
    prev_num = page_num - 1 if page_num > 0 else None
    
    # Check if in preview mode (bypasses all locks for content creators)
    # Check preview mode from session OR from user's database record
    preview_mode = session.get('preview_mode', False) or (user.is_preview_mode if user else False)
    
    # Only allow next if not a quiz OR quiz has been answered correctly (or in preview mode)
    next_allowed = True
    if current_page.get("type") == "quiz" and not quiz_answered and not preview_mode:
        next_allowed = False
    
    # MODULE ACCESS RESTRICTIONS DISABLED - All modules are now freely accessible
    # Uncomment the code below to re-enable sequential module locking
    
    # # Check if trying to access a locked page (module/summary/action_items)
    # if not preview_mode and current_page.get("type") == "module":
    #     # Check if previous modules are complete
    #     current_module_id = current_page.get("module_id")
    #     if current_module_id:
    #         # Define module sequences for each chapter
    #         chapter_1_modules = ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6"]
    #         chapter_2_modules = ["2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9"]
    #         chapter_3_modules = ["3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8", "3.9"]
    #         chapter_4_modules = ["4.1", "4.2", "4.3", "4.4", "4.5", "4.6", "4.7", "4.8", "4.9", "4.10", "4.11"]
    #         
    #         # Determine which chapter and check previous modules (using database)
    #         if current_module_id.startswith("1."):
    #             module_index = chapter_1_modules.index(current_module_id) if current_module_id in chapter_1_modules else 0
    #             if module_index > 0:
    #                 for i in range(module_index):
    #                     if not get_module_completion_status(user.id, chapter_1_modules[i]):
    #                         return redirect(url_for("page", page_num=1))
    #         elif current_module_id.startswith("2."):
    #             # For Chapter 2, first check if all Chapter 1 is complete
    #             if not get_chapter_completion_status(user.id, 1):
    #                 return redirect(url_for("page", page_num=1))
    #             # Then check previous Chapter 2 modules
    #             module_index = chapter_2_modules.index(current_module_id) if current_module_id in chapter_2_modules else 0
    #             if module_index > 0:
    #                 for i in range(module_index):
    #                     if not get_module_completion_status(user.id, chapter_2_modules[i]):
    #                         return redirect(url_for("page", page_num=1))
    #         elif current_module_id.startswith("3."):
    #             # For Chapter 3, first check if all Chapter 2 is complete
    #             if not get_chapter_completion_status(user.id, 2):
    #                 return redirect(url_for("page", page_num=1))
    #             # Then check previous Chapter 3 modules
    #             module_index = chapter_3_modules.index(current_module_id) if current_module_id in chapter_3_modules else 0
    #             if module_index > 0:
    #                 for i in range(module_index):
    #                     if not get_module_completion_status(user.id, chapter_3_modules[i]):
    #                         return redirect(url_for("page", page_num=1))
    #         elif current_module_id.startswith("4."):
    #             # For Chapter 4, first check if all Chapter 3 is complete
    #             if not get_chapter_completion_status(user.id, 3):
    #                 return redirect(url_for("page", page_num=1))
    #             # Then check previous Chapter 4 modules
    #             module_index = chapter_4_modules.index(current_module_id) if current_module_id in chapter_4_modules else 0
    #             if module_index > 0:
    #                 for i in range(module_index):
    #                     if not get_module_completion_status(user.id, chapter_4_modules[i]):
    #                         return redirect(url_for("page", page_num=1))
    #         elif current_module_id.startswith("5."):
    #             # For Chapter 5, first check if all Chapter 4 is complete
    #             if not get_chapter_completion_status(user.id, 4):
    #                 return redirect(url_for("page", page_num=1))
    #             # Then check previous Chapter 5 modules
    #             chapter_5_modules = ["5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "5.8", "5.9", "5.10"]
    #             module_index = chapter_5_modules.index(current_module_id) if current_module_id in chapter_5_modules else 0
    #             if module_index > 0:
    #                 for i in range(module_index):
    #                     if not get_module_completion_status(user.id, chapter_5_modules[i]):
    #                         return redirect(url_for("page", page_num=1))
    #         elif current_module_id.startswith("6."):
    #             # For Chapter 6, first check if all Chapter 5 is complete
    #             if not get_chapter_completion_status(user.id, 5):
    #                 return redirect(url_for("page", page_num=1))
    #             # Then check previous Chapter 6 modules
    #             chapter_6_modules = ["6.1", "6.2", "6.3", "6.4", "6.5", "6.6", "6.7", "6.8", "6.9", "6.10", "6.11"]
    #             module_index = chapter_6_modules.index(current_module_id) if current_module_id in chapter_6_modules else 0
    #             if module_index > 0:
    #                 for i in range(module_index):
    #                     if not get_module_completion_status(user.id, chapter_6_modules[i]):
    #                         return redirect(url_for("page", page_num=1))
    # 
    # # Lock summary and action items until all modules complete (unless in preview mode)
    # if not preview_mode and current_page.get("type") in ["summary", "action_items"]:
    #     chapter_id = current_page.get("chapter_id", 1)
    #     if not get_chapter_completion_status(user.id, chapter_id):
    #         # Redirect to TOC if trying to access locked summary/action items
    #         return redirect(url_for("page", page_num=1))
    
    next_num = page_num + 1 if page_num < len(pages) - 1 and next_allowed else None
    
    # Get module-specific page counter from page data (resets per module)
    module_page_num = None
    module_total_pages = None
    
    if current_page.get("type") == "module":
        # Multi-page module support
        module_page_num = current_page.get("module_page_num", 1)
        module_total_pages = current_page.get("module_total_pages", 1)
    elif current_page.get("type") in ["intro", "summary", "action_items"]:
        # Single-page sections
        module_page_num = 1
        module_total_pages = 1
    
    # Check module completion status
    module_completion = {}
    all_ch1_modules_complete = False
    all_ch2_modules_complete = False
    all_ch3_modules_complete = False
    all_ch4_modules_complete = False
    all_ch5_modules_complete = False
    all_ch6_modules_complete = False
    all_ch7_modules_complete = False
    all_ch8_modules_complete = False
    all_ch9_modules_complete = False
    if pages:
        # Get modules from all chapters' data stored in pages
        ch1_modules = pages[0].get("ch1_modules", [])
        ch2_modules = pages[0].get("ch2_modules", [])
        ch3_modules = pages[0].get("ch3_modules", [])
        ch4_modules = pages[0].get("ch4_modules", [])
        ch5_modules = pages[0].get("ch5_modules", [])
        ch6_modules = pages[0].get("ch6_modules", [])
        ch7_modules = pages[0].get("ch7_modules", [])
        ch8_modules = pages[0].get("ch8_modules", [])
        ch9_modules = pages[0].get("ch9_modules", [])
        
        # Get module completion from database
        for mod in ch1_modules:
            module_completion[mod["id"]] = get_module_completion_status(user.id, mod["id"])
        all_ch1_modules_complete = get_chapter_completion_status(user.id, 1)
        
        for mod in ch2_modules:
            module_completion[mod["id"]] = get_module_completion_status(user.id, mod["id"])
        all_ch2_modules_complete = get_chapter_completion_status(user.id, 2)
        
        for mod in ch3_modules:
            module_completion[mod["id"]] = get_module_completion_status(user.id, mod["id"])
        all_ch3_modules_complete = get_chapter_completion_status(user.id, 3)
        
        for mod in ch4_modules:
            module_completion[mod["id"]] = get_module_completion_status(user.id, mod["id"])
        all_ch4_modules_complete = get_chapter_completion_status(user.id, 4)
        
        for mod in ch5_modules:
            module_completion[mod["id"]] = get_module_completion_status(user.id, mod["id"])
        all_ch5_modules_complete = get_chapter_completion_status(user.id, 5)
        
        for mod in ch6_modules:
            module_completion[mod["id"]] = get_module_completion_status(user.id, mod["id"])
        all_ch6_modules_complete = get_chapter_completion_status(user.id, 6)
        
        for mod in ch7_modules:
            module_completion[mod["id"]] = get_module_completion_status(user.id, mod["id"])
        all_ch7_modules_complete = get_chapter_completion_status(user.id, 7)
        
        for mod in ch8_modules:
            module_completion[mod["id"]] = get_module_completion_status(user.id, mod["id"])
        all_ch8_modules_complete = get_chapter_completion_status(user.id, 8)
        
        for mod in ch9_modules:
            module_completion[mod["id"]] = get_module_completion_status(user.id, mod["id"])
        all_ch9_modules_complete = get_chapter_completion_status(user.id, 9)
    
    # Quiz map for TOC dropdown display (now from database)
    quiz_map = {}
    # Dynamically build quiz map from all modules
    all_modules = Module.query.all()
    for module in all_modules:
        quiz_map[module.id] = get_quiz_questions_for_module(module.id)
    
    return render_template(
        "page.html",
        page=current_page,
        page_num=page_num,
        total_pages=len(pages),
        prev_num=prev_num,
        next_num=next_num,
        quiz_feedback=quiz_feedback,
        quiz_answered=quiz_answered,
        module_page_num=module_page_num,
        module_total_pages=module_total_pages,
        module_completion=module_completion,
        all_ch1_modules_complete=all_ch1_modules_complete,
        all_ch2_modules_complete=all_ch2_modules_complete,
        all_ch3_modules_complete=all_ch3_modules_complete,
        all_ch4_modules_complete=all_ch4_modules_complete,
        all_ch5_modules_complete=all_ch5_modules_complete,
        all_ch6_modules_complete=all_ch6_modules_complete,
        all_ch7_modules_complete=all_ch7_modules_complete,
        all_ch8_modules_complete=all_ch8_modules_complete,
        all_ch9_modules_complete=all_ch9_modules_complete,
        preview_mode=preview_mode,
        quiz_map=quiz_map,
        quiz_answers=session.get('quiz_answers', {})
    )


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
            'image': '/static/images/step_deck_original.jpeg',
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
            # Successful login
            session['user_id'] = user.id
            session['username'] = user.username
            session['logged_in'] = True

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
            
            # Auto-login after registration
            session['user_id'] = new_user.id
            session['username'] = new_user.username
            session['logged_in'] = True
            
            return redirect(url_for("page", page_num=1))
            
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
    return redirect(url_for("page", page_num=0))


@app.route("/preview")
def preview():
    """Enable preview mode - unlocks all content for creators to review."""
    session['preview_mode'] = True
    session['logged_in'] = True
    session['username'] = 'preview_user'
    # Get or create preview user
    user = get_or_create_user('preview_user', is_preview=True)
    session['user_id'] = user.id
    return redirect(url_for("page", page_num=1))


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
        return redirect(url_for("page", page_num=1))
    
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
        return redirect(url_for("page", page_num=1))
    
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
        return redirect(url_for("page", page_num=1))
    
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
        return redirect(url_for("page", page_num=1))
    
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


if __name__ == "__main__":
    app.run(debug=True)
