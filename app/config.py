import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'focussync-secret-key-super-secure-2026')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    
    # PostgreSQL / Supabase Database configuration
    DB_HOST = os.environ.get('DATABASE_HOST') or os.environ.get('POSTGRES_HOST') or os.environ.get('MYSQL_HOST', '')
    DB_PORT = int(os.environ.get('DATABASE_PORT') or os.environ.get('POSTGRES_PORT') or os.environ.get('MYSQL_PORT', 5432))
    DB_USER = os.environ.get('DATABASE_USER') or os.environ.get('POSTGRES_USER') or os.environ.get('MYSQL_USER', '')
    DB_PASSWORD = os.environ.get('DATABASE_PASSWORD') or os.environ.get('POSTGRES_PASSWORD') or os.environ.get('MYSQL_PASSWORD', '')
    DB_NAME = os.environ.get('DATABASE_NAME') or os.environ.get('POSTGRES_DB') or os.environ.get('MYSQL_DB', 'postgres')
    DB_SSLMODE = os.environ.get('DATABASE_SSLMODE', 'require')

    # Backward compatibility aliases
    MYSQL_HOST = DB_HOST
    MYSQL_PORT = DB_PORT
    MYSQL_USER = DB_USER
    MYSQL_PASSWORD = DB_PASSWORD
    MYSQL_DB = DB_NAME
    
    # SocketIO CORS configuration
    SOCKETIO_CORS_ORIGINS = os.environ.get('SOCKETIO_CORS_ORIGINS', '*')
    
    # Defaults
    DEFAULT_FOCUS_MINUTES = 25
    DEFAULT_SHORT_BREAK_MINUTES = 5
    DEFAULT_LONG_BREAK_MINUTES = 15
    MAX_PARTICIPANTS = 2
