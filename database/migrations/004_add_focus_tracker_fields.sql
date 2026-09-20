-- FocusSync Migration 004: Add Focus Tracker fields to timers table

ALTER TABLE timers
ADD COLUMN IF NOT EXISTS total_focus_sessions INT NOT NULL DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_completed_cycles INT NOT NULL DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_focus_time_seconds INT NOT NULL DEFAULT 0;
