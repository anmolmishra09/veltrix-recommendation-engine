#!/usr/bin/env python3
"""
Database initialization script.
Creates tables and loads seed data.
"""
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    """Create the recommendation database if it doesn't exist."""
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'postgres')
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'recommendation_db'")
        exists = cursor.fetchone()

        if not exists:
            cursor.execute('CREATE DATABASE recommendation_db')
            print("Database 'recommendation_db' created successfully")
        else:
            print("Database 'recommendation_db' already exists")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error creating database: {e}")
        sys.exit(1)

def load_schema():
    """Load the database schema from SQL files."""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
            database='recommendation_db'
        )
        cursor = conn.cursor()

        # Load schema files
        schema_files = [
            'database/schemas/users.sql',
            'database/schemas/products.sql',
            'database/schemas/interactions.sql',
            'database/schemas/recommendations.sql',
            'database/schemas/experiments.sql'
        ]

        for schema_file in schema_files:
            if os.path.exists(schema_file):
                with open(schema_file, 'r') as f:
                    sql = f.read()
                    cursor.execute(sql)
                print(f"Loaded schema from {schema_file}")
            else:
                print(f"Warning: Schema file {schema_file} not found")

        conn.commit()
        cursor.close()
        conn.close()
        print("Schema loaded successfully")

    except Exception as e:
        print(f"Error loading schema: {e}")
        sys.exit(1)

def load_seed_data():
    """Load seed data from SQL files."""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
            database='recommendation_db'
        )
        cursor = conn.cursor()

        # Load seed data files
        seed_files = [
            'database/seeds/users.sql',
            'database/seeds/products.sql',
            'database/seeds/interactions.sql',
            'database/seeds/recommendations.sql',
            'database/seeds/experiments.sql'
        ]

        for seed_file in seed_files:
            if os.path.exists(seed_file):
                with open(seed_file, 'r') as f:
                    sql = f.read()
                    cursor.execute(sql)
                print(f"Loaded seed data from {seed_file}")
            else:
                print(f"Warning: Seed file {seed_file} not found")

        conn.commit()
        cursor.close()
        conn.close()
        print("Seed data loaded successfully")

    except Exception as e:
        print(f"Error loading seed data: {e}")
        sys.exit(1)

def main():
    """Main function to initialize the database."""
    print("Initializing database...")

    create_database()
    load_schema()
    load_seed_data()

    print("Database initialization completed successfully!")

if __name__ == '__main__':
    main()