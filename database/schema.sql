-- FocusSync PostgreSQL / Supabase Schema

-- Users table
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

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    session_code VARCHAR(10) PRIMARY KEY,
    session_id VARCHAR(36) UNIQUE NOT NULL,
    creator_token VARCHAR(64) NOT NULL,
    creator_user_id VARCHAR(64) NULL REFERENCES users(user_id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Participants table (Max 5 per session)
CREATE TABLE IF NOT EXISTS participants (
    participant_token VARCHAR(64) PRIMARY KEY,
    session_code VARCHAR(10) NOT NULL REFERENCES sessions(session_code) ON DELETE CASCADE,
    user_id VARCHAR(64) NULL REFERENCES users(user_id) ON DELETE SET NULL,
    username VARCHAR(50) NOT NULL,
    slot INT NOT NULL,
    is_online BOOLEAN DEFAULT TRUE,
    sid VARCHAR(64) NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_participants_session_code ON participants(session_code);
CREATE INDEX IF NOT EXISTS idx_participants_sid ON participants(sid);
CREATE INDEX IF NOT EXISTS idx_participants_user_id ON participants(user_id);

-- Timers table
CREATE TABLE IF NOT EXISTS timers (
    session_code VARCHAR(10) PRIMARY KEY REFERENCES sessions(session_code) ON DELETE CASCADE,
    mode VARCHAR(20) NOT NULL DEFAULT 'FOCUS',
    status VARCHAR(20) NOT NULL DEFAULT 'IDLE',
    duration INT NOT NULL DEFAULT 1500,
    remaining_seconds INT NOT NULL DEFAULT 1500,
    started_at DOUBLE PRECISION NULL,
    target_end_time DOUBLE PRECISION NULL,
    completed_sessions INT NOT NULL DEFAULT 0,
    total_focus_sessions INT NOT NULL DEFAULT 0,
    total_completed_cycles INT NOT NULL DEFAULT 0,
    total_focus_time_seconds INT NOT NULL DEFAULT 0,
    updated_at DOUBLE PRECISION NOT NULL
);

-- Settings table
CREATE TABLE IF NOT EXISTS settings (
    session_code VARCHAR(10) PRIMARY KEY REFERENCES sessions(session_code) ON DELETE CASCADE,
    focus_duration INT NOT NULL DEFAULT 25,
    short_break_duration INT NOT NULL DEFAULT 5,
    long_break_duration INT NOT NULL DEFAULT 15,
    long_break_interval INT NOT NULL DEFAULT 4,
    auto_start BOOLEAN DEFAULT FALSE,
    sound_enabled BOOLEAN DEFAULT TRUE
);

-- User Session History table
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
    CONSTRAINT uk_user_session UNIQUE (user_id, session_id)
);

CREATE INDEX IF NOT EXISTS idx_history_user_id ON user_session_history(user_id);
CREATE INDEX IF NOT EXISTS idx_history_session_code ON user_session_history(session_code);
CREATE INDEX IF NOT EXISTS idx_history_session_id ON user_session_history(session_id);
