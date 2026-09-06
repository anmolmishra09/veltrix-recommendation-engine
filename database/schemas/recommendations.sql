-- Recommendations table to track served recommendations
CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    context JSONB,
    model_version VARCHAR(100),
    experiment_id VARCHAR(100),
    num_candidates INTEGER,
    num_returned INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for recommendations
CREATE INDEX IF NOT EXISTS idx_recommendations_user_id ON recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_created_at ON recommendations(created_at);
CREATE INDEX IF NOT EXISTS idx_recommendations_model_version ON recommendations(model_version);
CREATE INDEX IF NOT EXISTS idx_recommendations_experiment_id ON recommendations(experiment_id);