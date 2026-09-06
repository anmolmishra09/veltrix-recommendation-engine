-- Insert 10 users with deterministic IDs
INSERT INTO users (id, created_at, country, age_group) VALUES
(1, '2026-01-01 00:00:00+00', 'USA', '25-34'),
(2, '2026-01-02 00:00:00+00', 'Canada', '35-44'),
(3, '2026-01-03 00:00:00+00', 'UK', '18-24'),
(4, '2026-01-04 00:00:00+00', 'Germany', '45-54'),
(5, '2026-01-05 00:00:00+00', 'France', '25-34'),
(6, '2026-01-06 00:00:00+00', 'Japan', '35-44'),
(7, '2026-01-07 00:00:00+00', 'Australia', '18-24'),
(8, '2026-01-08 00:00:00+00', 'Brazil', '45-54'),
(9, '2026-01-09 00:00:00+00', 'India', '25-34'),
(10, '2026-01-10 00:00:00+00', 'Mexico', '35-44')
ON CONFLICT (id) DO NOTHING;

-- Reset the sequence to avoid conflicts on future inserts
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));