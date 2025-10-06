#!/usr/bin/env python3
"""
Database setup script for the DevOps Dashboard
Run this script to create the database and tables
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

load_dotenv()

def create_database():
    """Create the users database if it doesn't exist"""
    
    # Database connection parameters
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', 'password')
    database = os.getenv('DB_NAME', 'users')
    
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database='postgres'  # Connect to default postgres database first
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{database}'")
        exists = cursor.fetchone()
        
        if not exists:
            # Create database
            cursor.execute(f'CREATE DATABASE "{database}"')
            print(f"Database '{database}' created successfully!")
        else:
            print(f"Database '{database}' already exists.")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"Error creating database: {e}")
        return False

def create_tables():
    """Create the users table"""
    
    database_url = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/users')
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Create users table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            full_name VARCHAR(120) NOT NULL,
            role VARCHAR(50) NOT NULL DEFAULT 'user',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cursor.execute(create_table_sql)
        
        # Create updated_at trigger function
        trigger_function_sql = """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
        
        cursor.execute(trigger_function_sql)
        
        # Create trigger
        trigger_sql = """
        DROP TRIGGER IF EXISTS update_users_updated_at ON users;
        CREATE TRIGGER update_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """
        
        cursor.execute(trigger_sql)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Users table created successfully!")
        return True
        
    except psycopg2.Error as e:
        print(f"Error creating tables: {e}")
        return False

def insert_sample_data():
    """Insert sample data into the users table"""
    
    database_url = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/users')
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if users already exist
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Insert sample users
            sample_users = [
                ('admin', 'admin@example.com', 'Administrator', 'admin'),
                ('john_doe', 'john@example.com', 'John Doe', 'user'),
                ('jane_smith', 'jane@example.com', 'Jane Smith', 'moderator'),
                ('bob_wilson', 'bob@example.com', 'Bob Wilson', 'user'),
                ('alice_brown', 'alice@example.com', 'Alice Brown', 'user'),
            ]
            
            insert_sql = """
            INSERT INTO users (username, email, full_name, role)
            VALUES (%s, %s, %s, %s)
            """
            
            cursor.executemany(insert_sql, sample_users)
            conn.commit()
            
            print(f"Inserted {len(sample_users)} sample users!")
        else:
            print(f"Users table already has {count} users.")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"Error inserting sample data: {e}")
        return False

if __name__ == '__main__':
    print("Setting up database for DevOps Dashboard...")
    
    # Step 1: Create database
    if create_database():
        print("✓ Database created/exists")
    else:
        print("✗ Failed to create database")
        exit(1)
    
    # Step 2: Create tables
    if create_tables():
        print("✓ Tables created")
    else:
        print("✗ Failed to create tables")
        exit(1)
    
    # Step 3: Insert sample data
    if insert_sample_data():
        print("✓ Sample data inserted")
    else:
        print("✗ Failed to insert sample data")
        exit(1)
    
    print("\n🎉 Database setup completed successfully!")
    print("\nTo run the Flask application:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Update your .env file with correct database credentials")
    print("3. Run: python app.py")

