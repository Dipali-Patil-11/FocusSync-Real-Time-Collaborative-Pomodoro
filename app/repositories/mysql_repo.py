"""
MySQLRepository backwards compatibility alias to PostgresRepository.
Production uses Supabase PostgreSQL via PostgresRepository.
"""
from app.repositories.postgres_repo import PostgresRepository

class MySQLRepository(PostgresRepository):
    pass
