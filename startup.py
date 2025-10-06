#!/usr/bin/env python3
"""
Startup script with enhanced debugging for container initialization
"""
import os
import sys
import logging
from dotenv import load_dotenv

def setup_logging():
    """Configure logging for container startup"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def log_environment():
    """Log environment variables and system information"""
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("CONTAINER STARTUP DEBUG INFORMATION")
    logger.info("=" * 60)
    
    # System information
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Process ID: {os.getpid()}")
    
    # Environment file loading
    env_file = '.env'
    if os.path.exists(env_file):
        logger.info(f"Environment file '{env_file}' found")
        load_dotenv()
        logger.info("Environment variables loaded from .env file")
    else:
        logger.warning(f"Environment file '{env_file}' not found")
    
    # Key environment variables
    key_vars = [
        'DATABASE_URL',
        'SECRET_KEY',
        'FLASK_ENV',
        'FLASK_DEBUG',
        'PYTHONUNBUFFERED',
        'LOG_LEVEL',
        'USERS_PER_PAGE'
    ]
    
    logger.info("Environment variables:")
    for var in key_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive information
            if 'DATABASE_URL' in var:
                # Show only the host part of the database URL
                if '@' in value:
                    masked_value = value.split('@')[1] if '@' in value else value
                    logger.info(f"  {var}: ***@{masked_value}")
                else:
                    logger.info(f"  {var}: {value}")
            elif 'SECRET' in var.upper():
                logger.info(f"  {var}: ***masked***")
            else:
                logger.info(f"  {var}: {value}")
        else:
            logger.warning(f"  {var}: NOT SET")
    
    # File system check
    logger.info("File system check:")
    important_files = ['app.py', 'config.py', 'requirements.txt', '.env']
    for file in important_files:
        if os.path.exists(file):
            logger.info(f"  {file}: EXISTS")
        else:
            logger.warning(f"  {file}: MISSING")
    
    logger.info("=" * 60)

def main():
    """Main startup function"""
    logger = setup_logging()
    
    try:
        log_environment()
        
        logger.info("Starting Flask application...")
        
        # Test database connection first
        logger.info("Testing database connectivity...")
        try:
            import test_db_connection
            if not test_db_connection.test_database_connection():
                logger.error("Database connection test failed, aborting startup")
                sys.exit(1)
            logger.info("Database connection test passed")
        except Exception as e:
            logger.error(f"Database connection test error: {str(e)}")
            logger.exception("Database test error details:")
            sys.exit(1)
        
        # Import and run the Flask app
        from app import app, create_tables
        
        # Create application context and initialize database
        with app.app_context():
            logger.info("Creating application context")
            try:
                logger.info("Starting database initialization...")
                create_tables()
                logger.info("Database initialization completed successfully")
            except Exception as e:
                logger.error(f"Database initialization failed: {str(e)}")
                logger.exception("Full traceback:")
                raise
        
        # Start the Flask server
        logger.info("Starting Flask development server on 0.0.0.0:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        logger.exception("Full traceback:")
        sys.exit(1)

if __name__ == '__main__':
    main()
