"""
Configuration settings for Trinity Training Guide

Supports both development (SQLite) and production (PostgreSQL) environments.
Configuration is selected based on FLASK_ENV environment variable.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent


class Config:
    """Base configuration shared across all environments"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'freight-training-secret-key-2025'
    
    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Disabled to avoid Windows console encoding issues
    
    # Session settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 7 * 24 * 60 * 60  # 7 days in seconds
    
    # Application settings
    PREVIEW_MODE_PASSWORD = os.environ.get('PREVIEW_MODE_PASSWORD') or 'preview123'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    
    # Pagination
    ITEMS_PER_PAGE = 20


class DevelopmentConfig(Config):
    """Development environment configuration"""
    
    DEBUG = True
    TESTING = False
    
    # SQLite database for development
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        f'sqlite:///{BASE_DIR / "training_guide.db"}'
    
    SQLALCHEMY_ECHO = False  # Disabled for Windows console compatibility
    
    # Development-specific settings
    EXPLAIN_TEMPLATE_LOADING = True


class TestingConfig(Config):
    """Testing environment configuration"""
    
    DEBUG = False
    TESTING = True
    
    # Use in-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Testing-specific settings
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing


class ProductionConfig(Config):
    """Production environment configuration"""
    
    DEBUG = False
    TESTING = False
    
    # PostgreSQL database for production
    # Try DATABASE_URI first (Digital Ocean standard), fall back to DATABASE_URL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or os.environ.get('DATABASE_URL')
    
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        # Fix for Heroku's postgres:// URL (should be postgresql://)
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    # Production security settings
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Production-specific settings
    PREFERRED_URL_SCHEME = 'https'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(env_name=None):
    """
    Get configuration object based on environment name.
    
    Args:
        env_name: Environment name ('development', 'testing', 'production')
                 If None, uses FLASK_ENV environment variable
    
    Returns:
        Configuration object
    """
    if env_name is None:
        env_name = os.environ.get('FLASK_ENV', 'development')
    
    return config.get(env_name, config['default'])

