import os
import sys
import psycopg

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import Config
from app.repositories.postgres_repo import PostgresRepository
from app.models.room import Room, generate_room_code
from app.models.participant import Participant
from app.models.timer import TimerState
from app.models.settings import RoomSettings

def verify_postgres_configuration():
    print("==================================================")
    print("CHECKING POSTGRESQL / SUPABASE CONFIGURATION")
    print("==================================================")

    if not Config.DB_HOST:
        print("DATABASE MODE: IN-MEMORY FALLBACK (No DB Host configured in environment)")
        return False

    db_config = {
        'host': Config.DB_HOST,
        'port': Config.DB_PORT,
        'user': Config.DB_USER,
        'password': Config.DB_PASSWORD,
        'database': Config.DB_NAME,
        'sslmode': Config.DB_SSLMODE
    }

    print(f"Configured Database Target: {db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['database']} (sslmode={db_config['sslmode']})")

    try:
        # Test connection
        conn = psycopg.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            dbname=db_config['database'],
            sslmode=db_config['sslmode'],
            connect_timeout=5
        )
        print("[OK] PostgreSQL / Supabase Connection Successful!")

        with conn.cursor() as cursor:
            # Execute schema.sql
            schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
            if os.path.exists(schema_path):
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                    cursor.execute(schema_sql)
                print("[OK] Database Schema Initialized Successfully!")

        conn.close()

        # Test PostgreSQL Repository CRUD & Persistence
        repo = PostgresRepository(db_config)
        code = "PGTEST"

        # 1. Room Persistence
        room = Room(room_code=code, creator_token="token-pg-1")
        repo.create_room(room)
        fetched_room = repo.get_room(code)
        assert fetched_room is not None
        assert fetched_room.room_code == code
        print("[OK] PostgreSQL Room Persistence Verified")

        # 2. Participant Persistence
        p = Participant(participant_token="token-pg-1", room_code=code, username="PGUser", slot=1)
        repo.add_participant(p)
        fetched_p = repo.get_participant("token-pg-1")
        assert fetched_p is not None
        assert fetched_p.username == "PGUser"
        print("[OK] PostgreSQL Participant Persistence Verified")

        # 3. Timer Persistence
        t = TimerState(room_code=code, mode="FOCUS", duration=1500, remaining_seconds=1500)
        repo.save_timer(t)
        fetched_t = repo.get_timer(code)
        assert fetched_t is not None
        assert fetched_t.duration == 1500
        print("[OK] PostgreSQL Timer Persistence Verified")

        # 4. Settings Persistence
        s = RoomSettings(room_code=code, focus_duration=30)
        repo.save_settings(s)
        fetched_s = repo.get_settings(code)
        assert fetched_s is not None
        assert fetched_s.focus_duration == 30
        print("[OK] PostgreSQL Settings Persistence Verified")

        # Clean up test room
        repo.delete_room(code)
        print("==================================================")
        print("DATABASE MODE: SUPABASE POSTGRESQL — ALL PERSISTENCE TESTS PASSED!")
        print("==================================================")
        return True

    except Exception as e:
        print("==================================================")
        print(f"DATABASE MODE: IN-MEMORY FALLBACK (PostgreSQL Connection Failed: {e})")
        print("==================================================")
        return False

def test_postgres_persistence():
    # Execute verification function
    result = verify_postgres_configuration()
    # If no DB host is configured in the local test environment, verify that fallback handling operates cleanly
    if not Config.DB_HOST:
        print("[INFO] No DATABASE_HOST present in local test environment. Fallback mode verified.")
        assert result is False
    else:
        assert result is True

if __name__ == '__main__':
    verify_postgres_configuration()

