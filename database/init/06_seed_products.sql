-- Insert 20 products with deterministic IDs
INSERT INTO products (id, title, category, brand, price, description, created_at) VALUES
(1, 'Wireless Headphones', 'Electronics', 'Sony', 129.99, 'Noise-cancelling wireless headphones', '2026-01-01 00:00:00+00'),
(2, 'Running Shoes', 'Sports', 'Nike', 89.99, 'Lightweight running shoes for marathon training', '2026-01-02 00:00:00+00'),
(3, 'Laptop', 'Electronics', 'Dell', 999.99, '15-inch laptop with Intel i7 processor', '2026-01-03 00:00:00+00'),
(4, 'Smartphone', 'Electronics', 'Apple', 1099.99, 'Latest generation smartphone', '2026-01-04 00:00:00+00'),
(5, 'Coffee Maker', 'Home Appliances', 'Keurig', 79.99, 'Single-serve coffee maker', '2026-01-05 00:00:00+00'),
(6, 'Backpack', 'Accessories', 'North Face', 59.99, 'Water-resistant hiking backpack', '2026-01-06 00:00:00+00'),
(7, 'Mechanical Keyboard', 'Electronics', 'Logitech', 149.99, 'RGB mechanical gaming keyboard', '2026-01-07 00:00:00+00'),
(8, 'Monitor', 'Electronics', 'LG', 299.99, '27-inch 4K Ultra HD monitor', '2026-01-08 00:00:00+00'),
(9, 'T-Shirt', 'Clothing', 'Nike', 19.99, 'Cotton crew-neck t-shirt', '2026-01-09 00:00:00+00'),
(10, 'Gaming Mouse', 'Electronics', 'Razer', 69.99, 'High-precision gaming mouse', '2026-01-10 00:00:00+00'),
(11, 'Bluetooth Speaker', 'Electronics', 'JBL', 49.99, 'Portable waterproof Bluetooth speaker', '2026-01-11 00:00:00+00'),
(12, 'Digital Camera', 'Electronics', 'Canon', 499.99, 'Mirrorless digital camera with 24MP sensor', '2026-01-12 00:00:00+00'),
(13, 'Running Shorts', 'Sports', 'Adidas', 34.99, 'Moisture-wicking running shorts', '2026-01-13 00:00:00+00'),
(14, 'Yoga Mat', 'Sports', 'Manduka', 24.99, 'Extra-thick yoga mat for joint protection', '2026-01-14 00:00:00+00'),
(15, 'Desk Lamp', 'Home Appliances', 'Philips', 29.99, 'Adjustable LED desk lamp', '2026-01-15 00:00:00+00'),
(16, 'Water Bottle', 'Accessories', 'Hydro Flask', 39.99, 'Insulated stainless steel water bottle', '2026-01-16 00:00:00+00'),
(17, 'Hoodie', 'Clothing', 'Champion', 49.99, 'Pullover hoodie with fleece lining', '2026-01-17 00:00:00+00'),
(18, 'Wireless Charger', 'Electronics', 'Anker', 29.99, '10W fast wireless charging pad', '2026-01-18 00:00:00+00'),
(19, 'Projector', 'Electronics', 'Epson', 599.99, '1080p home theater projector', '2026-01-19 00:00:00+00'),
(20, 'Electric Toothbrush', 'Health', 'Oral-B', 89.99, 'Rechargeable electric toothbrush with pressure sensor', '2026-01-20 00:00:00+00')
ON CONFLICT (id) DO NOTHING;

-- Reset the sequence to avoid conflicts on future inserts
SELECT setval('products_id_seq', (SELECT MAX(id) FROM products));