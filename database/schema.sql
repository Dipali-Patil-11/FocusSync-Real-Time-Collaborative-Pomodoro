-- FocusSync PostgreSQL / Supabase Schema

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    session_code VARCHAR(10) PRIMARY KEY,
    creator_token VARCHAR(64) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Participants table (Max 2 per session)
CREATE TABLE IF NOT EXISTS participants (
    participant_token VARCHAR(64) PRIMARY KEY,
    session_code VARCHAR(10) NOT NULL REFERENCES sessions(session_code) ON DELETE CASCADE,
    username VARCHAR(50) NOT NULL,
    slot INT NOT NULL,
    is_online BOOLEAN DEFAULT TRUE,
    sid VARCHAR(64) NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_participants_session_code ON participants(session_code);
CREATE INDEX IF NOT EXISTS idx_participants_sid ON participants(sid);

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
