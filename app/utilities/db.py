import pymysql
from app.config import Config
from app.repositories.memory_repo import MemoryRepository
from app.repositories.mysql_repo import MySQLRepository
from app.utilities.logger import logger

_repository_instance = None
_db_mode = "Unknown"

def init_db(app_config: Config):
    global _repository_instance, _db_mode

    db_config = {
        'host': app_config.MYSQL_HOST,
        'port': app_config.MYSQL_PORT,
        'user': app_config.MYSQL_USER,
        'password': app_config.MYSQL_PASSWORD,
        'database': app_config.MYSQL_DB
    }

    try:
        # Test connection
        conn = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            connect_timeout=2
        )
        conn.close()
        _repository_instance = MySQLRepository(db_config)
        _db_mode = "MySQL 8"
        logger.info("========================================")
        logger.info("Database Mode: MySQL 8 (Connected)")
        logger.info("========================================")
    except Exception as e:
        _repository_instance = MemoryRepository()
        _db_mode = "In-Memory Fallback"
        logger.warning("========================================")
        logger.warning(f"MySQL unavailable ({e}). Falling back to In-Memory Storage.")
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
