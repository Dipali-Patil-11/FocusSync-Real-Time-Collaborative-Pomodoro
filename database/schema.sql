CREATE DATABASE IF NOT EXISTS focussync_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE focussync_db;

-- Rooms table
CREATE TABLE IF NOT EXISTS rooms (
    room_code VARCHAR(10) PRIMARY KEY,
    creator_token VARCHAR(64) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Participants table (Max 2 per room)
CREATE TABLE IF NOT EXISTS participants (
    participant_token VARCHAR(64) PRIMARY KEY,
    room_code VARCHAR(10) NOT NULL,
    username VARCHAR(50) NOT NULL,
    slot INT NOT NULL,
    is_online TINYINT(1) DEFAULT 1,
    sid VARCHAR(64) NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (room_code) REFERENCES rooms(room_code) ON DELETE CASCADE,
    INDEX idx_room_code (room_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Timers table
CREATE TABLE IF NOT EXISTS timers (
    room_code VARCHAR(10) PRIMARY KEY,
    mode VARCHAR(20) NOT NULL DEFAULT 'FOCUS',
    status VARCHAR(20) NOT NULL DEFAULT 'IDLE',
    duration INT NOT NULL DEFAULT 1500,
    remaining_seconds INT NOT NULL DEFAULT 1500,
    started_at DOUBLE NULL,
    target_end_time DOUBLE NULL,
    completed_sessions INT NOT NULL DEFAULT 0,
    updated_at DOUBLE NOT NULL,
    FOREIGN KEY (room_code) REFERENCES rooms(room_code) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Settings table
CREATE TABLE IF NOT EXISTS settings (
    room_code VARCHAR(10) PRIMARY KEY,
    focus_duration INT NOT NULL DEFAULT 25,
    short_break_duration INT NOT NULL DEFAULT 5,
    long_break_duration INT NOT NULL DEFAULT 15,
    auto_start TINYINT(1) DEFAULT 0,
    sound_enabled TINYINT(1) DEFAULT 1,
    FOREIGN KEY (room_code) REFERENCES rooms(room_code) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
