"""
Database models for Trinity Training Guide

This module defines all SQLAlchemy models for the training application.
Supports both SQLite (development) and PostgreSQL (production).
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json
import random

db = SQLAlchemy()


class Chapter(db.Model):
    """Represents a training chapter (e.g., Chapter 1: Understanding Your Role)"""
    __tablename__ = 'chapters'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    display_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    modules = db.relationship('Module', back_populates='chapter', 
                            order_by='Module.display_order',
                            cascade='all, delete-orphan')
    sections = db.relationship('ChapterSection', back_populates='chapter',
                              cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Chapter {self.id}: {self.title}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'display_order': self.display_order,
            'module_count': len(self.modules)
        }


class Module(db.Model):
    """Represents a training module (e.g., Module 1.1: Your Role as a Freight Agent)"""
    __tablename__ = 'modules'
    
    id = db.Column(db.String(10), primary_key=True)  # e.g., "1.1", "2.3"
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content_markdown = db.Column(db.Text)
    display_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    chapter = db.relationship('Chapter', back_populates='modules')
    quiz_questions = db.relationship('QuizQuestion', back_populates='module',
                                    order_by='QuizQuestion.display_order',
                                    cascade='all, delete-orphan')
    user_progress = db.relationship('UserProgress', back_populates='module',
                                   cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Module {self.id}: {self.title}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'chapter_id': self.chapter_id,
            'title': self.title,
            'display_order': self.display_order,
            'quiz_count': len(self.quiz_questions)
        }


class ChapterSection(db.Model):
    """Represents chapter intro, summary, or action items"""
    __tablename__ = 'chapter_sections'
    
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    section_type = db.Column(db.String(50), nullable=False)  # 'intro', 'summary', 'action_items'
    content_markdown = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    chapter = db.relationship('Chapter', back_populates='sections')
    
    def __repr__(self):
        return f'<ChapterSection {self.chapter_id}.{self.section_type}>'


class QuizQuestion(db.Model):
    """Represents a quiz question with multiple choice answers"""
    __tablename__ = 'quiz_questions'
    
    id = db.Column(db.String(20), primary_key=True)  # e.g., "q1_1_1"
    module_id = db.Column(db.String(10), db.ForeignKey('modules.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    choice_a = db.Column(db.Text, nullable=False)
    choice_b = db.Column(db.Text, nullable=False)
    choice_c = db.Column(db.Text, nullable=False)
    choice_d = db.Column(db.Text, nullable=False)
    correct_choice = db.Column(db.String(1), nullable=False)  # 'a', 'b', 'c', or 'd'
    explanation = db.Column(db.Text)
    display_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    module = db.relationship('Module', back_populates='quiz_questions')
    user_answers = db.relationship('UserQuizAnswer', back_populates='quiz_question',
                                  cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<QuizQuestion {self.id}>'
    
    def to_dict(self):
        """Convert to dictionary (without answer key)"""
        return {
            'id': self.id,
            'module_id': self.module_id,
            'question': self.question,
            'choices': [self.choice_a, self.choice_b, self.choice_c, self.choice_d],
            'explanation': self.explanation
        }
    
    def get_choices_dict(self):
        """Get choices as a dictionary keyed by letter"""
        return {
            'a': self.choice_a,
            'b': self.choice_b,
            'c': self.choice_c,
            'd': self.choice_d
        }
    
    def get_shuffled_for_user(self, user_id):
        """
        Get quiz question with shuffled answers for a specific user.
        If user has already seen this question, returns the same shuffle order.
        Otherwise, generates and saves a new random order.
        
        Returns:
            dict with keys: id, question, choices (list), correct_index, 
                          explanation, answer_order (for submission)
        """
        # Check if user has an existing answer record with shuffle order
        user_answer = UserQuizAnswer.query.filter_by(
            user_id=user_id,
            quiz_question_id=self.id
        ).first()
        
        if user_answer and user_answer.answer_order:
            # Use existing shuffle order
            order = json.loads(user_answer.answer_order)
        else:
            # Generate new random order
            order = ['a', 'b', 'c', 'd']
            random.shuffle(order)
            
            # Save order for this user (create record if doesn't exist)
            if not user_answer:
                user_answer = UserQuizAnswer(
                    user_id=user_id,
                    quiz_question_id=self.id,
                    answer_order=json.dumps(order)
                )
                db.session.add(user_answer)
                db.session.commit()
            else:
                user_answer.answer_order = json.dumps(order)
                db.session.commit()
        
        # Build shuffled choices
        choices_dict = self.get_choices_dict()
        shuffled_choices = [choices_dict[letter] for letter in order]
        correct_index = order.index(self.correct_choice)
        
        return {
            'id': self.id,
            'question': self.question,
            'choices': shuffled_choices,
            'correct_index': correct_index,
            'explanation': self.explanation,
            'answer_order': order  # Include for answer validation
        }


class User(db.Model):
    """Represents a user/trainee"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    first_name = db.Column(db.String(100))  # Optional for simple login
    last_name = db.Column(db.String(100))   # Optional for simple login
    employee_id = db.Column(db.String(50), unique=True)  # Optional for simple login
    email = db.Column(db.String(255), unique=True)
    password_hash = db.Column(db.String(255))  # Optional - no password needed for simple login
    is_preview_mode = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    progress = db.relationship('UserProgress', back_populates='user',
                              cascade='all, delete-orphan')
    quiz_answers = db.relationship('UserQuizAnswer', back_populates='user',
                                  cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'employee_id': self.employee_id,
            'email': self.email,
            'is_preview_mode': self.is_preview_mode,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def get_completed_modules(self):
        """Get list of completed module IDs"""
        return [p.module_id for p in self.progress if p.completed]
    
    def get_module_completion_status(self, module_id):
        """Check if a specific module is completed"""
        progress = UserProgress.query.filter_by(
            user_id=self.id,
            module_id=module_id
        ).first()
        return progress.completed if progress else False
    
    def get_chapter_completion_status(self, chapter_id):
        """Check if all modules in a chapter are completed"""
        chapter = Chapter.query.get(chapter_id)
        if not chapter:
            return False
        
        for module in chapter.modules:
            if not self.get_module_completion_status(module.id):
                return False
        
        return True


class UserProgress(db.Model):
    """Tracks which modules a user has completed"""
    __tablename__ = 'user_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    module_id = db.Column(db.String(10), db.ForeignKey('modules.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', back_populates='progress')
    module = db.relationship('Module', back_populates='user_progress')
    
    # Unique constraint: one progress record per user per module
    __table_args__ = (
        db.UniqueConstraint('user_id', 'module_id', name='unique_user_module'),
    )
    
    def __repr__(self):
        return f'<UserProgress user={self.user_id} module={self.module_id} completed={self.completed}>'
    
    def mark_complete(self):
        """Mark this module as completed"""
        self.completed = True
        self.completion_date = datetime.utcnow()
        db.session.commit()
    
    def mark_incomplete(self):
        """Mark this module as incomplete (for resets)"""
        self.completed = False
        self.completion_date = None
        db.session.commit()


class UserQuizAnswer(db.Model):
    """Tracks user answers to quiz questions"""
    __tablename__ = 'user_quiz_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_question_id = db.Column(db.String(20), db.ForeignKey('quiz_questions.id'), nullable=False)
    selected_choice = db.Column(db.String(1))  # 'a', 'b', 'c', or 'd' (actual choice, not shuffled index)
    is_correct = db.Column(db.Boolean)
    answer_order = db.Column(db.Text)  # JSON: ["b","d","a","c"] - shuffled order for this user
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='quiz_answers')
    quiz_question = db.relationship('QuizQuestion', back_populates='user_answers')
    
    # Unique constraint: one answer record per user per question
    __table_args__ = (
        db.UniqueConstraint('user_id', 'quiz_question_id', name='unique_user_quiz'),
    )
    
    def __repr__(self):
        return f'<UserQuizAnswer user={self.user_id} quiz={self.quiz_question_id} correct={self.is_correct}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'quiz_question_id': self.quiz_question_id,
            'selected_choice': self.selected_choice,
            'is_correct': self.is_correct,
            'answered_at': self.answered_at.isoformat() if self.answered_at else None
        }


class GlossaryTerm(db.Model):
    """Represents a term in the freight agent glossary"""
    __tablename__ = 'glossary_terms'
    
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(255), nullable=False)
    definition = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))  # e.g., "Transportation Modes", "Documentation"
    display_order = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<GlossaryTerm {self.term}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'term': self.term,
            'definition': self.definition,
            'category': self.category
        }


# Helper functions for common queries

def get_or_create_user(username, is_preview=False):
    """Get existing user or create new one"""
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username, is_preview_mode=is_preview)
        db.session.add(user)
        db.session.commit()
    return user


def get_module_completion_status(user_id, module_id):
    """Check if a user has completed a module (all quizzes correct)"""
    module = Module.query.get(module_id)
    if not module or not module.quiz_questions:
        return False
    
    for quiz in module.quiz_questions:
        answer = UserQuizAnswer.query.filter_by(
            user_id=user_id,
            quiz_question_id=quiz.id
        ).first()
        
        if not answer or not answer.is_correct:
            return False
    
    # All quizzes answered correctly - ensure progress record exists
    progress = UserProgress.query.filter_by(
        user_id=user_id,
        module_id=module_id
    ).first()
    
    if not progress:
        progress = UserProgress(
            user_id=user_id,
            module_id=module_id,
            completed=True,
            completion_date=datetime.utcnow()
        )
        db.session.add(progress)
        db.session.commit()
    elif not progress.completed:
        progress.mark_complete()
    
    return True


def get_chapter_completion_status(user_id, chapter_id):
    """Check if all modules in a chapter are completed"""
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return False
    
    for module in chapter.modules:
        if not get_module_completion_status(user_id, module.id):
            return False
    
    return True


def update_user_quiz_answer(user_id, quiz_id, selected_index, answer_order):
    """
    Update user's answer to a quiz question.

    Args:
        user_id: User ID
        quiz_id: Quiz question ID
        selected_index: Index (0-3) selected by user in shuffled choices
        answer_order: List like ['b', 'a', 'd', 'c'] representing shuffle order

    Returns:
        dict with keys: is_correct, explanation
    """
    quiz = QuizQuestion.query.get(quiz_id)
    if not quiz:
        return {'is_correct': False, 'explanation': 'Quiz question not found'}

    # Convert selected index to actual choice letter
    selected_choice = answer_order[selected_index]
    is_correct = bool(selected_choice == quiz.correct_choice)
    
    # Update or create answer record
    answer = UserQuizAnswer.query.filter_by(
        user_id=user_id,
        quiz_question_id=quiz_id
    ).first()
    
    if answer:
        answer.selected_choice = selected_choice
        answer.is_correct = is_correct
        answer.answered_at = datetime.utcnow()
    else:
        answer = UserQuizAnswer(
            user_id=user_id,
            quiz_question_id=quiz_id,
            selected_choice=selected_choice,
            is_correct=is_correct,
            answer_order=json.dumps(answer_order)
        )
        db.session.add(answer)
    
    db.session.commit()

    # Check if module is now complete
    if is_correct:
        get_module_completion_status(user_id, quiz.module_id)

    return {
        'is_correct': is_correct,
        'explanation': quiz.explanation
    }

