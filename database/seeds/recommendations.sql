-- Seed data for recommendations
INSERT INTO recommendations (user_id, context, model_version, experiment_id, num_candidates, num_returned, created_at) VALUES
(1, '{"source": "homepage", "device": "mobile"}', 'v1.0.0', 'exp_001', 100, 10, '2026-09-01 10:04:00'),
(2, '{"source": "email_promotion", "campaign": "summer_sale"}', 'v1.0.0', 'exp_001', 100, 10, '2026-09-01 11:04:00'),
(3, '{"source": "search", "query": "yoga accessories"}', 'v1.0.0', NULL, 100, 10, '2026-09-01 12:01:00');