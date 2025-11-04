-- PostgreSQL Schema for Trinity Training Guide
-- This schema is used for production deployment

-- Chapters table
CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Modules table
CREATE TABLE IF NOT EXISTS modules (
    id VARCHAR(10) PRIMARY KEY,
    chapter_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    content_markdown TEXT,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
);

-- Chapter sections (intro, summary, action_items)
CREATE TABLE IF NOT EXISTS chapter_sections (
    id SERIAL PRIMARY KEY,
    chapter_id INTEGER NOT NULL,
    section_type VARCHAR(50) NOT NULL,
    content_markdown TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
);

-- Quiz questions
CREATE TABLE IF NOT EXISTS quiz_questions (
    id VARCHAR(20) PRIMARY KEY,
    module_id VARCHAR(10) NOT NULL,
    question TEXT NOT NULL,
    choice_a TEXT NOT NULL,
    choice_b TEXT NOT NULL,
    choice_c TEXT NOT NULL,
    choice_d TEXT NOT NULL,
    correct_choice CHAR(1) NOT NULL CHECK(correct_choice IN ('a', 'b', 'c', 'd')),
    explanation TEXT,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    is_preview_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- User progress tracking
CREATE TABLE IF NOT EXISTS user_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    module_id VARCHAR(10) NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    completion_date TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE,
    UNIQUE(user_id, module_id)
);

-- User quiz answers (with JSONB support for better performance)
CREATE TABLE IF NOT EXISTS user_quiz_answers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    quiz_question_id VARCHAR(20) NOT NULL,
    selected_choice CHAR(1),
    is_correct BOOLEAN,
    answer_order JSONB,  -- PostgreSQL JSONB for better querying
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (quiz_question_id) REFERENCES quiz_questions(id) ON DELETE CASCADE,
    UNIQUE(user_id, quiz_question_id)
);

-- Glossary terms
CREATE TABLE IF NOT EXISTS glossary_terms (
    id SERIAL PRIMARY KEY,
    term VARCHAR(255) NOT NULL,
    definition TEXT NOT NULL,
    category VARCHAR(100),
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_modules_chapter_id ON modules(chapter_id);
CREATE INDEX IF NOT EXISTS idx_quiz_questions_module_id ON quiz_questions(module_id);
CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON user_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_progress_module_id ON user_progress(module_id);
CREATE INDEX IF NOT EXISTS idx_user_quiz_answers_user_id ON user_quiz_answers(user_id);
CREATE INDEX IF NOT EXISTS idx_user_quiz_answers_quiz_id ON user_quiz_answers(quiz_question_id);
CREATE INDEX IF NOT EXISTS idx_glossary_terms_term ON glossary_terms(term);

-- PostgreSQL-specific: Create GIN index for JSONB answer_order
CREATE INDEX IF NOT EXISTS idx_user_quiz_answers_order_gin ON user_quiz_answers USING GIN (answer_order);

