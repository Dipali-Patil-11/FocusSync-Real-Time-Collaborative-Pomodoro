import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'focussync-secret-key-super-secure-2026')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    
    # Database configuration (support both DATABASE_* and MYSQL_* variable names)
    MYSQL_HOST = os.environ.get('DATABASE_HOST') or os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('DATABASE_PORT') or os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('DATABASE_USER') or os.environ.get('MYSQL_USER', 'focussync_user')
    MYSQL_PASSWORD = os.environ.get('DATABASE_PASSWORD') or os.environ.get('MYSQL_PASSWORD', 'focussync_password')
    MYSQL_DB = os.environ.get('DATABASE_NAME') or os.environ.get('MYSQL_DB', 'focussync_db')
    
    # SocketIO CORS configuration
    SOCKETIO_CORS_ORIGINS = os.environ.get('SOCKETIO_CORS_ORIGINS', '*')
    
    # Defaults
    DEFAULT_FOCUS_MINUTES = 25
    DEFAULT_SHORT_BREAK_MINUTES = 5
    DEFAULT_LONG_BREAK_MINUTES = 15
    MAX_PARTICIPANTS = 2
