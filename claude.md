## Interactive Training Manual UX Plan (Flask Web App)

- **Core goals**: High retention, active recall, and practical readiness for new freight agents.
- **Guiding principles**: Chunked learning (chapters → modules), immediate practice (quizzes), spaced reinforcement, accessibility (TTS), and progress visibility.

### Website Structure (Flask)
- **Home/Dashboard**: Shows enrolled user, current chapter, progress bar, streaks, and resume button.
- **Chapters Index**: Lists all chapters from `project.md` (e.g., Chapter 1–9) with completion state.
- **Chapter Page**: Intro summary, estimated time, learning objectives, optional TTS playback, and module navigation.
- **Module View**: Content blocks with inline callouts, micro-quizzes, and quick “apply it” tasks.
- **Checkpoint Quiz**: 3–6 multiple-choice questions per chapter focusing on key takeaways.
- **Review Hub**: Missed questions, flashcards auto-generated from key points, and links back to modules.

### Engagement Features
- **Multiple-choice quizzes**: After each chapter, 3–6 questions focusing on core ideas and common confusions.
  - Immediate feedback, short rationale, link back to source section.
  - Require 80%+ to pass; failed items become flashcards.
- **TTS narration**: Optional chapter narration so users can listen while reviewing slides/notes.
  - Server-side generation and caching of audio per chapter.
  - Player with playback speed and chapter timestamps.
- **Micro-interactions**: Inline knowledge checks (1–2 questions) inside modules to maintain attention.
- **Progress mechanics**: Chapter completion badges, streaks, XP for quiz performance, and weekly goals.
- **Practical drills**: Scenario prompts (e.g., rate negotiation mini-sims) at the end of applicable modules.
- **Accessibility**: Keyboard-only navigation, captions for TTS, high-contrast mode, font scaling.

### Assessment & Feedback
- **Question design**: Focus on misconceptions; each distractor maps to a real-world mistake.
- **Rationale**: One-sentence explanation plus a "learn more" link to module anchor.
- **Mastery gating**: Passing score required to unlock the next chapter (configurable for admins).
- **Spaced review**: Daily 5–10 flashcards from previously missed questions and key definitions.

### Data & Persistence
- **User progress**: Track per user: chapters viewed, module time, quiz attempts, correct/incorrect by objective.
- **Question items**: Store question, choices, correct answer, rationale, tags (chapter/module/objective).
- **Analytics**: Drop-off points, hard questions, time-on-task, pass rates; export CSV for coaching.

### Authoring Workflow
- **Content source**: Parse `project.md` to auto-build chapters/modules and objectives.
- **Question bank**: YAML/JSON per chapter for MCQs; import tool with validation.
- **Preview mode**: Admin preview of chapter + quiz before publishing.

### Technical Plan (Flask)
- **Routes**:
  - `GET /` dashboard
  - `GET /chapters` list
  - `GET /chapters/<id>` details + TTS
  - `GET /modules/<id>` content + micro-quiz
  - `GET /chapters/<id>/quiz` start quiz
  - `POST /chapters/<id>/quiz/submit` evaluate
  - `GET /review` missed items/flashcards
  - `POST /tts/<chapter_id>` generate audio (admin) or on-demand cache
- **Templates**: Jinja2 with responsive layout, accessible components, and reusable quiz macro.
- **Storage**: SQLite to start; models for User, Chapter, Module, Question, Choice, Attempt, Flashcard.
- **TTS**: Pluggable provider (e.g., gTTS, Azure, Amazon Polly); cache audio files per chapter.

### Content Writing Guidelines

When creating or editing module content:
- **Keep it simple for new hires.** Avoid jargon like "vertical" when "market" or "industry" works. These are people new to freight brokerage.
- **Check the TOC first.** Before adding detailed content, check if the topic is covered in a later chapter. Reference forward ("You'll learn more about this in Chapter 4") rather than duplicating content.
- **No em dashes mid-sentence.** Avoid using em dashes (—) to divide information. Use periods for separate sentences or commas for lists. Hyphens in compound words (high-volume) and date ranges (September-November) are fine.
- **Add glossary links with images** for equipment terms when available. Include the image in the tooltip for visual learners.

### Content Organization Notes (from `project.md`)
- **Chapters identified**: 1) Welcome to Freight Brokerage 2) Understanding the Industry Landscape 3) The Role of a Freight Agent 4) Truck Types and Specifications 5) Load Types and Cargo Categories 6) Load Restrictions and Regulations 7) Building Your Customer Base 8) Sales Strategies for Freight Agents 9) Effective Follow-Up Systems.
- **Modules**: Use module subsections under each chapter (e.g., 1.1, 1.2, 1.3, 1.4 as seen in Chapter 1) as atomic learning units.
- **Learning objectives**: Extract 3–5 objectives per chapter; anchor quiz questions to objectives.
- **Question strategy**:
  - 1 question per objective (minimum); 3–6 total per chapter.
  - Each module gets 1 micro-check question; keep it single-select MCQ.
  - Include at least 1 scenario-based question per chapter to test applied knowledge.

### Next Steps
- Scaffold Flask app and models; wire up routes and templates.
- Build parser to ingest `project.md` headings into Chapter/Module tables.
- Create question YAML schema and a sample bank for Chapter 1.
- Integrate TTS for Chapter 1 narration with caching and transcript.
- Ship MVP: Chapters list, Chapter 1 page, quiz, and progress tracking.

---

## Current Implementation Status (Updated: Oct 3, 2025)

### ✅ Completed Features

**1. Cover Page**
- First page displays lines 1-27 from `project.md`
- Beautiful dark-themed design with full table of contents
- Shows all 9 chapters organized by parts (Foundations, Technical Knowledge, Business Development)
- Chapter 1 is clickable and navigates to Module 1.1
- Module listings displayed under Chapter 1 (Modules 1.1-1.6)
- Glossary link opens in new window

**2. Glossary System**
- Dedicated `/glossary` route with standalone HTML page (`templates/glossary.html`)
- 130+ terms parsed from project.md with structure: Module reference, Term name, Definition
- Real-time search functionality to filter terms
- Opens in new browser window from TOC
- No back button (user closes tab to return)

**3. Navigation & Page Structure**
- Page 0: Cover page
- Page 1: Table of Contents (old format, may be deprecated)
- Page 2: Module 1.1 (first module of Chapter 1)
- Pages 3-7: Modules 1.2-1.6
- Page 8: Chapter 1 Summary
- Page 9: Chapter 1 Action Items
- Arrow key navigation + clickable nav buttons
- Progress bar at top

**4. Content Formatting**
- Chapter titles converted from ALL CAPS to Title Case automatically
- Smart markdown preprocessing adds bold headers for section breaks
- HTML conversion with line break and list support
- Dark theme with gold/indigo/cyan accent colors

**5. Current Data Flow**
- `parse_project_outline()` - Extracts all 9 chapter titles + glossary flag
- `extract_chapter_content()` - Parses Chapter 1 into intro/modules/summary/action items
- `parse_glossary_terms()` - Structures 130+ glossary entries
- `build_pages()` - Assembles flat page array for navigation
- Only Chapter 1 is fully implemented; Chapters 2-9 are listed but not yet navigable

### 🔧 Technical Details

**Routes:**
- `GET /` - Redirects to page 0 (cover)
- `GET /page/<int:page_num>` - Main slideshow navigation
- `GET /glossary` - Standalone glossary page

**Templates:**
- `page.html` - Main slideshow template (handles cover, toc, intro, module, summary, action_items types)
- `glossary.html` - Standalone searchable glossary
- `base.html` - Legacy, not currently used
- `chapter.html` - Legacy, not currently used

**Key Functions:**
- `preprocess_content()` - Auto-detects headers in plain text and adds markdown formatting
- `convert_to_html()` - Converts markdown to HTML with nl2br and sane_lists extensions

### 📋 TODO / Not Yet Implemented

**From Original Plan:**
- [ ] Chapters 2-9 content extraction and navigation
- [ ] Multiple-choice quizzes after each chapter
- [ ] TTS narration with audio caching
- [ ] User authentication and progress tracking
- [ ] Flashcards for spaced repetition
- [ ] Mastery gating (passing scores to unlock chapters)
- [ ] Analytics and drop-off tracking
- [ ] Database (SQLite) for persistence
- [ ] Question bank YAML/JSON files

**Immediate Next Steps:**
- Expand `build_pages()` to include all 9 chapters (not just Chapter 1)
- Make Chapters 2-9 clickable with module navigation
- Consider removing redundant TOC page (Page 1) since cover serves same purpose
- Add quiz functionality for Chapter 1
- Implement user progress tracking