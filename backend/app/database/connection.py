"""
Database connection module for the Photo Gallery application.
Handles database connection setup, configuration, and management.
"""

import os
import logging
from typing import Dict, Any, Optional
from urllib.parse import quote_plus

from sqlalchemy import create_engine, Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session

# Configure logging
logger = logging.getLogger(__name__)

# Default connection parameters
DEFAULT_CONNECTION_PARAMS = {
    "connect_timeout": 10,
    "application_name": "photo_gallery",
    "client_encoding": "utf8"
}


def get_database_url() -> str:
    """
    Get the database URL from environment variables or use a default value.
    
    Returns:
        str: Database connection URL
    """
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        logger.warning("DATABASE_URL not set. Using default local development connection.")
        database_url = "postgresql://postgres:postgres@localhost/photo_gallery_dev"
    
    return database_url


def create_connection_string(
    host: str = "localhost",
    port: int = 5432,
    user: str = "postgres",
    password: str = "postgres",
    database: str = "photo_gallery_dev",
    params: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a PostgreSQL connection string from components.
    
    Args:
        host: Database host
        port: Database port
        user: Database user
        password: Database password
        database: Database name
        params: Additional connection parameters
    
    Returns:
        str: Formatted connection string
    """
    # Escape password for URL
    encoded_password = quote_plus(password)
    
    # Start with base connection string
    connection_string = f"postgresql://{user}:{encoded_password}@{host}:{port}/{database}"
    
    # Add any additional parameters
    if params:
        param_str = "&".join(f"{k}={v}" for k, v in params.items())
        connection_string = f"{connection_string}?{param_str}"
    
    return connection_string


def get_engine(database_url: Optional[str] = None, **kwargs) -> Engine:
    """
    Create a SQLAlchemy engine for database connections.
    
    Args:
        database_url: Database connection URL, defaults to environment variable
        **kwargs: Additional engine configuration parameters
    
    Returns:
        Engine: SQLAlchemy engine instance
    """
    if database_url is None:
        database_url = get_database_url()
    
    # Set default parameters if not provided
    engine_kwargs = {
        "pool_pre_ping": True,
        "echo": False
    }
    
    # Update with user-provided parameters
    engine_kwargs.update(kwargs)
    
    # Create and return engine
    try:
        engine = create_engine(database_url, **engine_kwargs)
        logger.info(f"Database engine created for {database_url.split('@')[-1]}")
        return engine
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database engine: {e}")
        raise
    
def get_engine(database_url: Optional[str] = None, **kwargs) -> Engine:
    """
    Create a SQLAlchemy engine for database connections with connection pooling.
    
    Args:
        database_url: Database connection URL, defaults to environment variable
        **kwargs: Additional engine configuration parameters
    
    Returns:
        Engine: SQLAlchemy engine instance with connection pooling
    """
    if database_url is None:
        database_url = get_database_url()
    
    # Set default parameters if not provided
    engine_kwargs = {
        "pool_pre_ping": True,  # Verify connections before use
        "pool_size": 5,         # Number of connections to keep open
        "max_overflow": 10,     # Max number of connections above pool_size
        "pool_timeout": 30,     # Seconds to wait for a connection
        "pool_recycle": 1800,   # Recycle connections after 30 minutes
        "echo": False           # Don't log all SQL
    }
    
    # Update with user-provided parameters
    engine_kwargs.update(kwargs)
    
    # Create and return engine
    try:
        engine = create_engine(database_url, **engine_kwargs)
        logger.info(f"Database engine created with connection pooling for {database_url.split('@')[-1]}")
        return engine
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database engine: {e}")
        raise
    
def test_connection(engine: Engine) -> bool:
    """
    Test the database connection.
    
    Args:
        engine: SQLAlchemy engine instance
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        # Execute a simple query to test connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection test successful")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection test failed: {e}")
        return False


def handle_connection_error(func):
    """
    Decorator to handle database connection errors.
    
    Args:
        func: Function to decorate
    
    Returns:
        Function: Decorated function with error handling
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            error_class = e.__class__.__name__
            logger.error(f"Database error ({error_class}): {str(e)}")
            
            # Specific error handling based on error type
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                logger.error("Database connection error: Check that the database is running and accessible")
            elif "authentication" in str(e).lower():
                logger.error("Database authentication error: Check username and password")
            elif "permission" in str(e).lower():
                logger.error("Database permission error: Check user permissions")
            
            # Re-raise the exception
            raise
    
    return wrapper