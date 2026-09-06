-- Seed data for experiments
INSERT INTO experiments (experiment_id, name, description, start_timestamp, end_timestamp, status, config, metadata) VALUES
('exp_001', 'Recommendation Model A/B Test', 'Testing new ranking model vs baseline', '2026-09-01 00:00:00', '2026-09-30 23:59:59', 'active', '{"traffic_allocation": {"control": 0.5, "treatment": 0.5}, "metrics": ["ctr", "conversion_rate"]}', '{"owner": "ml-team", "priority": "high"}'),
('exp_002', 'Homepage Layout Test', 'Testing new homepage layout for engagement', '2026-09-05 00:00:00', '2026-09-15 23:59:59', 'active', '{"traffic_allocation": {"control": 0.5, "treatment": 0.5}, "metrics": ["bounce_rate", "session_duration"]}', '{"owner": "ux-team", "priority": "medium"}');

-- Seed data for experiment assignments
INSERT INTO experiment_assignments (experiment_id, user_id, variant, model_version, assigned_at, metadata) VALUES
(1, 1, 'control', 'v1.0.0', '2026-09-01 10:00:00', '{}'),
(1, 2, 'treatment', 'v1.2.0', '2026-09-01 11:00:00', '{}'),
(1, 3, 'control', 'v1.0.0', '2026-09-01 12:00:00', '{}'),
(1, 4, 'treatment', 'v1.2.0', '2026-09-01 13:00:00', '{}'),
(1, 5, 'control', 'v1.0.0', '2026-09-01 14:00:00', '{}'),
(1, 6, 'treatment', 'v1.2.0', '2026-09-01 15:00:00', '{}'),
(1, 7, 'control', 'v1.0.0', '2026-09-01 16:00:00', '{}'),
(1, 8, 'treatment', 'v1.2.0', '2026-09-01 17:00:00', '{}'),
(1, 9, 'control', 'v1.0.0', '2026-09-01 18:00:00', '{}'),
(1, 10, 'treatment', 'v1.2.0', '2026-09-01 19:00:00', '{}');