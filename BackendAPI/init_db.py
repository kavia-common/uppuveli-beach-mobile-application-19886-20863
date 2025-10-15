"""Database initialization script.

This script creates all database tables based on the SQLAlchemy ORM models.

Usage:
    python init_db.py

Environment Variables Required:
    DATABASE_URL - PostgreSQL connection string (e.g., postgresql://user:pass@host:port/dbname)
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    from src.api.config import get_settings
    from src.api.db import Base, _create_engine_from_url
    
    settings = get_settings()
    
    if not settings.database_url:
        logger.error("DATABASE_URL is not set. Please configure it in .env file.")
        sys.exit(1)
    
    logger.info("Connecting to database...")
    
    try:
        engine = _create_engine_from_url(settings.database_url)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("✓ Database connection successful")
        
        # Create all tables
        logger.info("Creating tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ All tables created successfully")
        
        # List created tables
        logger.info("\nCreated tables:")
        for table_name in sorted(Base.metadata.tables.keys()):
            logger.info(f"  - {table_name}")
        
        engine.dispose()
        logger.info("\n✓ Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
