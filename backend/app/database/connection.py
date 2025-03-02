"""
Database connection module for the Photo Gallery application.
Handles database connection setup, configuration, and management.
"""

import os
import logging
from typing import Dict, Any, Optional
from urllib.parse import quote_plus

from sqlalchemy import create_engine, Engine, text
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
    
def check_connection(engine: Engine) -> bool:
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
            conn.execute(text("SELECT 1"))
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

def get_session_factory(engine: Optional[Engine] = None) -> sessionmaker:
    """
    Create a session factory for database sessions.
    
    Args:
        engine: SQLAlchemy engine instance, created if not provided
    
    Returns:
        sessionmaker: SQLAlchemy session factory
    """
    if engine is None:
        engine = get_engine()
    
    # Create session factory
    session_factory = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False
    )
    
    logger.debug("Session factory created")
    return session_factory


# Create default engine and session factory
default_engine = get_engine()
SessionFactory = get_session_factory(default_engine)


def get_db_session() -> Session:
    """
    Get a new database session.
    
    Returns:
        Session: SQLAlchemy database session
    """
    return SessionFactory()

class DatabaseSession:
    """
    Context manager for database sessions.
    
    Ensures that sessions are properly closed and that transactions
    are committed or rolled back as appropriate.
    """
    
    def __init__(self, session_factory=None):
        """
        Initialize the context manager.
        
        Args:
            session_factory: Session factory to use, defaults to global SessionFactory
        """
        if session_factory is None:
            session_factory = SessionFactory
        self.session_factory = session_factory
        self.session = None
    
    def __enter__(self) -> Session:
        """
        Enter the context, creating a new session.
        
        Returns:
            Session: Active database session
        """
        self.session = self.session_factory()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context, closing the session.
        
        Args:
            exc_type: Exception type, if an exception occurred
            exc_val: Exception value, if an exception occurred
            exc_tb: Exception traceback, if an exception occurred
        """
        if exc_type is not None:
            # An exception occurred, roll back transaction
            logger.debug(f"Rolling back transaction due to {exc_type.__name__}: {exc_val}")
            self.session.rollback()
        else:
            # No exception, commit transaction
            try:
                self.session.commit()
            except SQLAlchemyError as e:
                logger.error(f"Failed to commit transaction: {e}")
                self.session.rollback()
                raise
        
        # Always close session
        self.session.close()


# Convenience function for using the context manager
def db_session():
    """
    Get a database session context manager.
    
    Usage:
        with db_session() as session:
            # Use session here
    
    Returns:
        DatabaseSession: Database session context manager
    """
    return DatabaseSession()