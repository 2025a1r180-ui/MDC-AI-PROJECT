-- Echo Journal Production PostgreSQL Schema
-- Migration target for Milestone 6: Production Hardening
-- Enforces strict constraints, foreign key cascades, and optimal indexes

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(32) DEFAULT 'user' NOT NULL,
    opt_in_external_ai BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS entries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    mood VARCHAR(64),
    tags TEXT,
    word_count INTEGER DEFAULT 0 NOT NULL,
    reading_time_minutes INTEGER DEFAULT 1 NOT NULL,
    analysis_status VARCHAR(64) DEFAULT 'pending',
    primary_emotion VARCHAR(64),
    emotion_scores JSONB,
    sentiment_label VARCHAR(64),
    sentiment_score REAL,
    model_name VARCHAR(128),
    model_version VARCHAR(64),
    analyzed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indices for performance and account isolation enforcement
CREATE INDEX IF NOT EXISTS idx_entries_user_id ON entries(user_id);
CREATE INDEX IF NOT EXISTS idx_entries_created_at ON entries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_entries_user_date ON entries(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_entries_primary_emotion ON entries(primary_emotion);
