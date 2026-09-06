-- Interactions table
CREATE TABLE IF NOT EXISTS interactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('view', 'click', 'search', 'add_to_cart', 'purchase', 'like', 'wishlist', 'impression')),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(255),
    context JSONB,
    metadata JSONB,
    -- For recommendation tracking
    recommendation_id INTEGER, -- Reference to recommendations table if this interaction came from a recommendation
    ranking_position INTEGER,  -- Position in the recommendation list
    recommendation_score DECIMAL(5, 4) -- Score assigned by the ranking model
);

-- Indexes for interactions
CREATE INDEX IF NOT EXISTS idx_interactions_user_id ON interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_interactions_product_id ON interactions(product_id);
CREATE INDEX IF NOT EXISTS idx_interactions_event_type ON interactions(event_type);
CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON interactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_interactions_session_id ON interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_interactions_user_product ON interactions(user_id, product_id);
CREATE INDEX IF NOT EXISTS idx_interactions_user_event ON interactions(user_id, event_type);
CREATE INDEX IF NOT EXISTS idx_interactions_product_event ON interactions(product_id, event_type);