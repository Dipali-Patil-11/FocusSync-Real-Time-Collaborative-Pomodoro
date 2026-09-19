import psycopg
from app.config import Config
from app.repositories.memory_repo import MemoryRepository
from app.repositories.postgres_repo import PostgresRepository
from database.init_db import initialize_database
from app.utilities.logger import logger

_repository_instance = None
_db_mode = "Unknown"

def init_db(app_config: Config):
    global _repository_instance, _db_mode

    db_config = {
        'host': app_config.DB_HOST,
        'port': app_config.DB_PORT,
        'user': app_config.DB_USER,
        'password': app_config.DB_PASSWORD,
        'database': app_config.DB_NAME,
        'sslmode': app_config.DB_SSLMODE
    }

    if not app_config.DB_HOST:
        _repository_instance = MemoryRepository()
        _db_mode = "In-Memory Fallback"
        logger.info("========================================")
        logger.info("Database Mode: In-Memory Fallback (Thread-Safe Local Dev)")
        logger.info("========================================")
        return _repository_instance

    try:
        # Test PostgreSQL / Supabase connection
        conn = psycopg.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            dbname=db_config['database'],
            sslmode=db_config['sslmode'],
            connect_timeout=5
        )
        conn.close()

        # Initialize schema tables safely
        initialize_database()

        _repository_instance = PostgresRepository(db_config)
        _db_mode = "Supabase PostgreSQL"
        logger.info("========================================")
        logger.info("Database Mode: Supabase PostgreSQL (Connected)")
        logger.info("========================================")
    except Exception as e:
        if not app_config.DEBUG:
            logger.critical("========================================")
            logger.critical(f"FATAL: Production database connection to PostgreSQL failed: {e}")
            logger.critical("========================================")
            raise RuntimeError(f"Database connection failure in production: {e}")
        else:
            _repository_instance = MemoryRepository()
            _db_mode = "In-Memory Fallback"
            logger.warning("========================================")
            logger.warning(f"PostgreSQL connection failed ({e}). Falling back to In-Memory Storage.")
            logger.warning("Database Mode: In-Memory Fallback (Thread-Safe)")
            logger.warning("========================================")

    return _repository_instance

def get_repository():
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = MemoryRepository()
        _db_mode = "In-Memory Fallback"
    return _repository_instance

def get_db_mode():
    global _db_mode
    return _db_mode
