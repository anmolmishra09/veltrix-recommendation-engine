"""
Realistic demo data generator for the recommendation platform.
Generates sample datasets for users, products, interactions, and transactions
with enough data to demonstrate multiple users, categories, repeated interactions,
purchases, cold-start cases, and different popularity distributions.
"""
import os
import json
import random
import numpy as np
from datetime import datetime, timedelta
import csv

# Set random seeds for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

def generate_users(num_users=1000):
    """Generate realistic user data."""
    print(f"Generating {num_users} users...")

    users = []
    locations = [
        "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX",
        "Phoenix, AZ", "Philadelphia, PA", "San Antonio, TX", "San Diego, CA",
        "Dallas, TX", "San Jose, CA", "Austin, TX", "Jacksonville, FL",
        "Fort Worth, TX", "Columbus, OH", "Charlotte, NC", "San Francisco, CA",
        "Indianapolis, IN", "Seattle, WA", "Denver, CO", "Washington, DC"
    ]

    age_groups = [
        (18, 24, 0.15),   # 15% aged 18-24
        (25, 34, 0.25),   # 25% aged 25-34
        (35, 44, 0.20),   # 20% aged 35-44
        (45, 54, 0.15),   # 15% aged 45-54
        (55, 64, 0.10),   # 10% aged 55-64
        (65, 80, 0.15)    # 15% aged 65+
    ]

    for i in range(1, num_users + 1):
        # Select age group based on distribution
        age_group = random.choices(age_groups, weights=[w for _, _, w in age_groups])[0]
        age_min, age_max, _ = age_group
        age = random.randint(age_min, age_max)

        # Registration date (last 2 years)
        days_ago = random.randint(1, 730)
        registration_date = datetime.now() - timedelta(days=days_ago)

        user = {
            "id": i,
            "external_id": f"user_{i:06d}",
            "age": age,
            "gender": random.choice(["Male", "Female", "Non-binary", "Prefer not to say"]),
            "location": random.choice(locations),
            "registration_timestamp": registration_date.isoformat(),
            "metadata": {
                "signup_source": random.choice(["web", "mobile_app", "social_media", "email_campaign", "referral"]),
                "newsletter_subscription": random.choice([True, False]),
                "loyalty_tier": random.choice(["none", "bronze", "silver", "gold", "platinum"])
            }
        }
        users.append(user)

    return users

def generate_products(num_products=500):
    """Generate realistic product data."""
    print(f"Generating {num_products} products...")

    products = []
    categories = [
        {"name": "Electronics", "subcategories": ["Smartphones", "Laptops", "Tablets", "Headphones", "Cameras", "Gaming"]},
        {"name": "Clothing", "subcategories": ["Men's Clothing", "Women's Clothing", "Kids' Clothing", "Shoes", "Accessories"]},
        {"name": "Home & Garden", "subcategories": ["Furniture", "Home Decor", "Kitchenware", "Gardening", "Bedding"]},
        {"name": "Sports & Outdoors", "subcategories": ["Fitness Equipment", "Outdoor Gear", "Sports Apparel", "Cycling"]},
        {"name": "Beauty & Personal Care", "subcategories": ["Skincare", "Makeup", "Haircare", "Fragrances", "Personal Care"]},
        {"name": "Books & Media", "subcategories": ["Books", "Movies", "Music", "Games", "Magazines"]},
        {"name": "Toys & Games", "subcategories": ["Action Figures", "Board Games", "Educational Toys", "Video Games", "Puzzles"]},
        {"name": "Automotive", "subcategories": ["Parts & Accessories", "Tools", "Car Care", "Tires"]}
    ]

    brands = {
        "Electronics": ["Apple", "Samsung", "Sony", "LG", "Dell", "HP", "Lenovo", "Asus", "Microsoft", "Bose"],
        "Clothing": ["Nike", "Adidas", "H&M", "Zara", "Uniqlo", "Levi's", "Gap", "Under Armour", "Puma", "Lululemon"],
        "Home & Garden": ["IKEA", "Ashley Furniture", "Wayfair", "Bed Bath & Beyond", "Crate & Barrel", "Williams Sonoma"],
        "Sports & Outdoors": ["Patagonia", "The North Face", "Columbia", "REI Co-op", "Under Armour", "Nike", "Adidas"],
        "Beauty & Personal Care": ["L'Oreal", "Estée Lauder", "Procter & Gamble", "Unilever", "Shiseido", "Johnson & Johnson"],
        "Books & Media": ["Penguin Random House", "HarperCollins", "Simon & Schuster", "Hachette", "Macmillan"],
        "Toys & Games": ["Hasbro", "Mattel", "LEGO", "Nintendo", "PlayStation", "Xbox"],
        "Automotive": ["Michelin", "Goodyear", "Bosch", "Pennzoil", "3M", "Shell"]
    }

    for i in range(1, num_products + 1):
        # Select category and subcategory
        category_data = random.choice(categories)
        category = category_data["name"]
        subcategory = random.choice(category_data["subcategories"])

        # Select brand based on category
        brand = random.choice(brands.get(category, ["Generic Brand"]))

        # Generate price based on category
        price_ranges = {
            "Electronics": (50, 2000),
            "Clothing": (10, 500),
            "Home & Garden": (20, 1500),
            "Sports & Outdoors": (15, 800),
            "Beauty & Personal Care": (5, 200),
            "Books & Media": (5, 100),
            "Toys & Games": (5, 200),
            "Automotive": (10, 500)
        }

        min_price, max_price = price_ranges.get(category, (10, 100))
        price = round(random.uniform(min_price, max_price), 2)

        # Inventory (some products may be out of stock)
        inventory_weights = [0.7, 0.2, 0.1]  # 70% in stock, 20% low stock, 10% out of stock
        inventory_choice = random.choices([1, 2, 3], weights=inventory_weights)[0]
        if inventory_choice == 1:
            inventory = random.randint(10, 100)
        elif inventory_choice == 2:
            inventory = random.randint(1, 9)
        else:
            inventory = 0

        # Creation date (last year)
        days_ago = random.randint(1, 365)
        creation_date = datetime.now() - timedelta(days=days_ago)

        product = {
            "id": i,
            "name": f"{brand} {fake_product_name(category, subcategory)} {i}",
            "category": category,
            "subcategory": subcategory,
            "price": price,
            "description": fake_product_description(category, subcategory, brand),
            "brand": brand,
            "inventory": inventory,
            "metadata": {
                "weight_kg": round(random.uniform(0.1, 20.0), 2),
                "dimensions": f"{random.randint(5, 50)}x{random.randint(5, 50)}x{random.randint(5, 50)} cm",
                "warranty_months": random.choice([0, 6, 12, 24, 36]) if category in ["Electronics", "Home & Garden", "Sports & Outdoors"] else 0,
                "energy_rating": random.choice(["A+++", "A++", "A+", "A", "B", "C", "D", "E"]) if category in ["Electronics", "Home & Garden"] else None
            }
        }
        products.append(product)

    return products

def fake_product_name(category, subcategory):
    """Generate a realistic product name based on category."""
    names = {
        "Electronics": ["Smart", "Pro", "Max", "Plus", "Ultra", "Lite", "Mini", "Air", "Pod", "Watch"],
        "Clothing": ["Classic", "Premium", "Essentials", "Performance", "Flex", "Sport", "Graphic", "Basic"],
        "Home & Garden": ["Deluxe", "Comfort", "Premium", "Basic", "Essential", "Elite", "Professional", "Studio"],
        "Sports & Outdoors": ["Pro", "Elite", "Performance", "Trail", "Peak", "Summit", "Apex", "Vortex"],
        "Beauty & Personal Care": ["Essential", "Intensive", "Repair", "Glow", "Pure", "Natural", "Organic", "Luxe"],
        "Books & Media": ["Edition", "Volume", "Part", "Collection", "Series", "Anthology", "Guide", "Handbook"],
        "Toys & Games": ["Adventure", "Educational", "Creative", "Fun", "Super", "Mega", "Ultra", "Max"],
        "Automotive": ["Performance", "Racing", "Touring", "All-Season", "Winter", "Eco", "Premium", "Pro"]
    }

    return random.choice(names.get(category, ["Product"]))

def fake_product_description(category, subcategory, brand):
    """Generate a realistic product description."""
    templates = {
        "Electronics": f"The {brand} {fake_product_name(category, subcategory)} delivers cutting-edge performance with advanced features designed for modern users. Experience seamless connectivity, stunning display quality, and reliable battery life.",
        "Clothing": f"Crafted from premium materials, this {brand} {fake_product_name(category, subcategory)} offers comfort, style, and durability. Perfect for everyday wear or special occasions.",
        "Home & Garden": f"Enhance your living space with this {brand} {fake_product_name(category, subcategory)}. Designed for both functionality and aesthetics, it's the perfect addition to any home.",
        "Sports & Outdoors": f"Whether you're hitting the trails or the gym, this {brand} {fake_product_name(category, subcategory)} provides the performance and durability you need to push your limits.",
        "Beauty & Personal Care": f"Indulge in luxury with this {brand} {fake_product_name(category, subcategory)}. Formulated with high-quality ingredients to nourish, protect, and enhance your natural beauty.",
        "Books & Media": f"Discover a captivating story or expand your knowledge with this {brand} {fake_product_name(category, subcategory)}. Perfect for entertainment, education, or inspiration.",
        "Toys & Games": f"Spark imagination and creativity with this {brand} {fake_product_name(category, subcategory)}. Hours of fun await as children explore, learn, and grow through play.",
        "Automotive": f"Keep your vehicle running smoothly with this {brand} {fake_product_name(category, subcategory)}. Engineered for reliability and performance to ensure safety on the road."
    }

    return templates.get(category, f"This {brand} {fake_product_name(category, subcategory)} offers quality and value for your needs.")

def generate_interactions(users, products, num_interactions=10000):
    """Generate realistic interaction data."""
    print(f"Generating {num_interactions} interactions...")

    interactions = []
    event_types = [
        ("view", 0.40),      # 40% views
        ("click", 0.25),     # 25% clicks
        ("purchase", 0.08),  # 8% purchases
        ("add_to_cart", 0.12), # 12% add to cart
        ("like", 0.06),      # 6% likes
        ("wishlist", 0.04),  # 4% wishlist
        ("search", 0.03),    # 3% searches
        ("impression", 0.02) # 2% impressions
    ]

    # Create lookup dictionaries for faster access
    user_dict = {u["id"]: u for u in users}
    product_dict = {p["id"]: p for p in products}

    # Generate interactions over the last 6 months
    start_date = datetime.now() - timedelta(days=180)

    for i in range(1, num_interactions + 1):
        # Select random user and product
        user = random.choice(users)
        product = random.choice(products)

        # Select event type based on distribution
        event_type = random.choices([et for et, _ in event_types], weights=[w for _, w in event_types])[0]

        # Generate timestamp within last 6 months
        days_ago = random.randint(0, 180)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        seconds_ago = random.randint(0, 59)

        timestamp = start_date + timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago, seconds=seconds_ago)

        # Session ID (users have multiple sessions)
        session_id = f"session_{user['id']}_{random.randint(1, 10):02d}"

        # Context based on event type
        context = {}
        if event_type in ["view", "click"]:
            context["source"] = random.choice(["homepage", "category_page", "search_results", "recommendations", "email", "social_media"])
        elif event_type == "search":
            context["query"] = fake_search_query(product["category"])
            context["results_count"] = random.randint(0, 100)
        elif event_type in ["purchase", "add_to_cart"]:
            context["quantity"] = random.randint(1, 5)
            context["payment_method"] = random.choice(["credit_card", "paypal", "bank_transfer", "gift_card"])

        interaction = {
            "id": i,
            "user_id": user["id"],
            "product_id": product["id"],
            "event_type": event_type,
            "timestamp": timestamp.isoformat(),
            "session_id": session_id,
            "context": context,
            "metadata": {
                "device": random.choice(["mobile", "desktop", "tablet"]),
                "browser": random.choice(["Chrome", "Firefox", "Safari", "Edge"]),
                "referrer": random.choice(["direct", "google", "facebook", "instagram", "email", "other"])
            }
        }

        # For recommendation tracking (some interactions come from recommendations)
        if random.random() < 0.3:  # 30% of interactions are from recommendations
            interaction["recommendation_id"] = random.randint(1, 1000) if i > 100 else None
            interaction["ranking_position"] = random.randint(1, 10) if interaction["recommendation_id"] else None
            interaction["recommendation_score"] = round(random.uniform(0.1, 0.99), 4) if interaction["recommendation_id"] else None

        interactions.append(interaction)

    return interactions

def fake_search_query(category):
    """Generate a realistic search query based on category."""
    queries = {
        "Electronics": ["wireless headphones", "laptop stand", "phone case", "bluetooth speaker", "smart watch", "tablet", "gaming mouse", "usb cable"],
        "Clothing": ["summer dress", "running shoes", "winter coat", "jeans", "t-shirt", "sneakers", "jacket", "activewear"],
        "Home & Garden": ["throw pillows", "bed sheets", "kitchen organizer", "desk lamp", "indoor plant", "storage bins", "picture frame", "candle set"],
        "Sports & Outdoors": ["yoga mat", "dumbbells", "running shoes", "backpack", "water bottle", "tent", "sleeping bag", "bike lock"],
        "Beauty & Personal Care": ["moisturizer", "shampoo", "face wash", "lipstick", "mascara", "cleanser", "serum", "deodorant"],
        "Books & Media": ["bestseller novel", "cookbook", "self help", "history book", "biography", "fantasy", "mystery", "sci-fi"],
        "Toys & Games": ["building blocks", "puzzle set", "action figure", "board game", "doll", "rc car", "educational toy", "video game"],
        "Automotive": ["car wax", "tire pressure gauge", "jumper cables", "phone mount", "seat cover", "steering wheel cover", "floor mats", "air freshener"]
    }

    return random.choice(queries.get(category, ["product"]))

def generate_transactions(users, products, interactions):
    """Generate transaction data from purchase interactions."""
    print("Generating transaction data from purchases...")

    transactions = []
    transaction_id = 1

    # Filter purchase interactions
    purchase_interactions = [i for i in interactions if i["event_type"] == "purchase"]

    for interaction in purchase_interactions:
        user = next(u for u in users if u["id"] == interaction["user_id"])
        product = next(p for p in products if p["id"] == interaction["product_id"])

        # Get quantity from context
        quantity = interaction["context"].get("quantity", 1)

        # Calculate total amount
        unit_price = product["price"]
        total_amount = unit_price * quantity

        # Apply random discount (10% of purchases have discount)
        discount_amount = 0
        if random.random() < 0.1:
            discount_percent = random.choice([5, 10, 15, 20, 25])
            discount_amount = round(total_amount * (discount_percent / 100), 2)

        final_amount = round(total_amount - discount_amount, 2)

        transaction = {
            "id": transaction_id,
            "user_id": user["id"],
            "product_id": product["id"],
            "interaction_id": interaction["id"],
            "quantity": quantity,
            "unit_price": unit_price,
            "total_amount": total_amount,
            "discount_amount": discount_amount,
            "final_amount": final_amount,
            "timestamp": interaction["timestamp"],
            "payment_method": interaction["context"].get("payment_method", "credit_card"),
            "status": "completed",
            "metadata": {
                "shipping_address": f"{random.randint(100, 999)} {fake_street_name()}, {fake_city()}, {fake_state()} {fake_zip()}",
                "billing_address_same": random.choice([True, False]),
                "order_source": interaction["context"].get("source", "website"),
                "currency": "USD"
            }
        }

        transactions.append(transaction)
        transaction_id += 1

    return transactions

def fake_street_name():
    """Generate a realistic street name."""
    prefixes = ["Oak", "Maple", "Pine", "Elm", "Cedar", "Walnut", "Cherry", "Birch"]
    suffixes = ["Street", "Avenue", "Boulevard", "Drive", "Lane", "Road", "Court", "Place"]
    return f"{random.choice(prefixes)} {random.choice(suffixes)}"

def fake_city():
    """Generate a realistic city name."""
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]
    return random.choice(cities)

def fake_state():
    """Generate a realistic state abbreviation."""
    states = ["NY", "CA", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]
    return random.choice(states)

def fake_zip():
    """Generate a realistic ZIP code."""
    return f"{random.randint(10000, 99999):05d}"

def save_to_csv(data, filename, fieldnames=None):
    """Save data to CSV file."""
    os.makedirs("./data", exist_ok=True)
    filepath = os.path.join("./data", filename)

    if not data:
        print(f"No data to save for {filename}")
        return

    if fieldnames is None:
        # Flatten nested structures for CSV
        flattened_data = []
        all_keys = set()
        for item in data:
            flat_item = {}
            for key, value in item.items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        flat_item[f"{key}_{subkey}"] = subvalue
                elif isinstance(value, list):
                    flat_item[key] = json.dumps(value)
                else:
                    flat_item[key] = value
            flattened_data.append(flat_item)
            all_keys.update(flat_item.keys())
        # Ensure all items have all keys, fill missing with None
        if flattened_data:
            fieldnames = sorted(list(all_keys))
            data_to_write = []
            for flat_item in flattened_data:
                # Fill missing keys
                complete_item = {k: flat_item.get(k, None) for k in fieldnames}
                data_to_write.append(complete_item)
        else:
            fieldnames = []
            data_to_write = []
    else:
        data_to_write = data

    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        if data_to_write and fieldnames:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data_to_write)

    print(f"Saved {len(data)} records to {filepath}")

def save_to_json(data, filename):
    """Save data to JSON file."""
    os.makedirs("./data", exist_ok=True)
    filepath = os.path.join("./data", filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

    print(f"Saved {len(data)} records to {filepath}")

def main():
    """Main function to generate all demo data."""
    print("Starting demo data generation...")
    print("=" * 50)

    # Generate data
    users = generate_users(1000)
    products = generate_products(500)
    interactions = generate_interactions(users, products, 10000)
    transactions = generate_transactions(users, products, interactions)

    # Save data
    print("\nSaving data...")
    save_to_json(users, "users.json")
    save_to_json(products, "products.json")
    save_to_json(interactions, "interactions.json")
    save_to_json(transactions, "transactions.json")

    # Also save as CSV for easy import
    save_to_csv(users, "users.csv")
    save_to_csv(products, "products.csv")
    save_to_csv(interactions, "interactions.csv")
    save_to_csv(transactions, "transactions.csv")

    print("\n" + "=" * 50)
    print("Demo data generation completed!")
    print(f"Generated:")
    print(f"  - {len(users)} users")
    print(f"  - {len(products)} products")
    print(f"  - {len(interactions)} interactions")
    print(f"  - {len(transactions)} transactions")
    print("\nData saved to ./data/ directory")

if __name__ == "__main__":
    main()