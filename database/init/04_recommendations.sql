CREATE TABLE recommendations (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    product_id BIGINT NOT NULL REFERENCES products(id),
    score DOUBLE PRECISION NOT NULL CHECK (score >= 0),
    position INTEGER NOT NULL CHECK (position >= 1),
    model_version VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fetching recommendations by user ordered by position
CREATE INDEX idx_recommendations_user_id_position ON recommendations(user_id, position);