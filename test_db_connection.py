#!/usr/bin/env python3
"""
Simple database connection test script
"""
import os
import sys
import logging
import psycopg2
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection using psycopg2 directly"""
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    logger.info(f"Testing database connection to: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")
    
    try:
        # Parse the database URL
        conn = psycopg2.connect(database_url)
        logger.info("Database connection successful!")
        
        # Test a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        logger.info(f"Query test successful: {result}")
        
        # Test if users table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            );
        """)
        table_exists = cursor.fetchone()[0]
        logger.info(f"Users table exists: {table_exists}")
        
        cursor.close()
        conn.close()
        logger.info("Database connection test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        logger.exception("Full error details:")
        return False

if __name__ == '__main__':
    logger.info("Starting database connection test...")
    success = test_database_connection()
    if success:
        logger.info("Database connection test PASSED")
        sys.exit(0)
    else:
        logger.error("Database connection test FAILED")
        sys.exit(1)
