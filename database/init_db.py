import os
import pymysql
from app.config import Config
from app.utilities.logger import logger

def initialize_database():
    try:
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            autocommit=True
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}")
            cursor.execute(f"USE {Config.MYSQL_DB}")
            
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            if os.path.exists(schema_path):
                with open(schema_path, 'r', encoding='utf-8') as f:
                    statements = f.read().split(';')
                    for stmt in statements:
                        stmt = stmt.strip()
                        if stmt:
                            cursor.execute(stmt)
            logger.info(f"Database {Config.MYSQL_DB} initialized successfully.")
        conn.close()
        return True
    except Exception as e:
        logger.warning(f"Could not initialize MySQL database: {e}")
        return False

if __name__ == '__main__':
    initialize_database()
