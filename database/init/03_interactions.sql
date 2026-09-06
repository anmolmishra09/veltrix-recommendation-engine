CREATE TABLE interactions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    product_id BIGINT NOT NULL REFERENCES products(id),
    event_type VARCHAR(20) NOT NULL CHECK (event_type IN ('view', 'click', 'add_to_cart', 'purchase')),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    session_id VARCHAR(100)
);

-- Indexes for recommendation workloads
CREATE INDEX idx_interactions_user_id ON interactions(user_id);
CREATE INDEX idx_interactions_product_id ON interactions(product_id);
CREATE INDEX idx_interactions_timestamp ON interactions(timestamp);
-- Composite index for user-based timeline queries
CREATE INDEX idx_interactions_user_id_timestamp ON interactions(user_id, timestamp);