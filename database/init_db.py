import os
import psycopg
from app.config import Config
from app.utilities.logger import logger

def initialize_database():
    if not Config.DB_HOST:
        logger.info("No database host configured. Skipping database initialization.")
        return False

    try:
        conn = psycopg.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            dbname=Config.DB_NAME,
            sslmode=Config.DB_SSLMODE,
            autocommit=True,
            connect_timeout=10
        )
        with conn.cursor() as cursor:
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            if os.path.exists(schema_path):
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                    cursor.execute(schema_sql)
            logger.info(f"Supabase PostgreSQL database {Config.DB_NAME} initialized successfully.")
        conn.close()
        return True
    except Exception as e:
        logger.warning(f"Could not initialize PostgreSQL database: {e}")
        return False

if __name__ == '__main__':
    initialize_database()
