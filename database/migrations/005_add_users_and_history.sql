-- FocusSync Migration 005: Add Users and User Session History tables
-- Non-destructive migration

CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(64) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE NULL
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

ALTER TABLE sessions ADD COLUMN IF NOT EXISTS session_id VARCHAR(36);
-- Backfill session_id for any existing sessions if present
UPDATE sessions SET session_id = md5(random()::text || clock_timestamp()::text) WHERE session_id IS NULL;
ALTER TABLE sessions ALTER COLUMN session_id SET NOT NULL;
ALTER TABLE sessions ADD CONSTRAINT uk_sessions_session_id UNIQUE (session_id);

ALTER TABLE sessions ADD COLUMN IF NOT EXISTS creator_user_id VARCHAR(64) NULL REFERENCES users(user_id) ON DELETE SET NULL;
ALTER TABLE participants ADD COLUMN IF NOT EXISTS user_id VARCHAR(64) NULL REFERENCES users(user_id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS user_session_history (
    history_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_code VARCHAR(10) NOT NULL,
    session_id VARCHAR(36) NOT NULL,
    role VARCHAR(20) DEFAULT 'PARTICIPANT',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP WITH TIME ZONE NULL,
    focus_sessions_completed INT DEFAULT 0,
    focus_time_seconds INT DEFAULT 0,
    current_cycle_focus_sessions INT DEFAULT 0,
    cycles_completed INT DEFAULT 0,
    CONSTRAINT uk_user_session_id UNIQUE (user_id, session_id)
);

CREATE INDEX IF NOT EXISTS idx_history_user_id ON user_session_history(user_id);
CREATE INDEX IF NOT EXISTS idx_history_session_code ON user_session_history(session_code);
CREATE INDEX IF NOT EXISTS idx_history_session_id ON user_session_history(session_id);
