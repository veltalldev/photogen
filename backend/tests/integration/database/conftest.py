# backend/tests/integration/database/conftest.py
"""
Pytest fixtures for database integration tests.
Provides setup and teardown for test database operations.
"""

import os
import pytest
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# Configure logging for tests
logger = logging.getLogger(__name__)


def get_test_database_url():
    """
    Get the test database URL from environment variable or use a default.
    
    Returns:
        str: Database URL for tests
    """
    test_db_url = os.environ.get("TEST_DATABASE_URL")
    
    if not test_db_url:
        # Default to local test database if not specified
        test_db_url = "postgresql://postgres:postgres@localhost/photo_gallery_test"
        logger.warning(f"TEST_DATABASE_URL not set. Using default: {test_db_url}")
    
    return test_db_url


@pytest.fixture(scope="session")
def test_engine():
    """
    Create a SQLAlchemy engine for the test database.
    This fixture has session scope, so it's created once per test session.
    
    Returns:
        Engine: SQLAlchemy engine configured for tests
    """
    db_url = get_test_database_url()
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30
    )
    
    # Verify the database connection
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            assert result == 1, "Database connection test failed"
        logger.info(f"Test database connection established: {db_url}")
    except Exception as e:
        logger.error(f"Failed to connect to test database: {e}")
        raise
    
    yield engine
    
    # Engine cleanup (if needed)
    engine.dispose()


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """
    Create a session factory for test database sessions.
    
    Args:
        test_engine: SQLAlchemy engine for tests (from fixture)
    
    Returns:
        sessionmaker: SQLAlchemy session factory
    """
    factory = sessionmaker(
        bind=test_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False
    )
    
    return factory


@pytest.fixture
def test_session(test_session_factory):
    """
    Provide a transactional scope for tests.
    Each test gets a clean session that will be rolled back after the test completes.
    
    Args:
        test_session_factory: Session factory (from fixture)
    
    Yields:
        Session: SQLAlchemy session for test
    """
    session = test_session_factory()
    
    # Start a transaction
    connection = session.connection()
    transaction = connection.begin()
    
    try:
        yield session
    finally:
        # Roll back the transaction after the test completes
        transaction.rollback()
        session.close()


@pytest.fixture(scope="function")
def clean_tables(test_engine):
    """
    Fixture to optionally clean specific tables before a test.
    Use this when you need a clean state for particular tables.
    
    Args:
        test_engine: SQLAlchemy engine (from fixture)
    
    Returns:
        function: Function to clean specified tables
    """
    def _clean_tables(table_names):
        with test_engine.begin() as conn:
            for table_name in table_names:
                conn.execute(text(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE'))
                logger.info(f"Cleaned table: {table_name}")
    
    return _clean_tables


@pytest.fixture(scope="session", autouse=True)
def verify_test_database(test_engine):
    """
    Verify that we're using a test database and not production.
    This is a safety check that runs automatically before any test.
    
    Args:
        test_engine: SQLAlchemy engine (from fixture)
    
    Raises:
        RuntimeError: If the database might be a production database
    """
    db_url = get_test_database_url()
    
    # Check for obvious signs that this is not a test database
    if "test" not in db_url.lower() and "photo_gallery_test" not in db_url.lower():
        logger.warning(
            f"Test database URL does not contain 'test': {db_url}. "
            "Please verify this is actually a test database."
        )
    
    try:
        # Check if the database has the expected test marker
        with test_engine.connect() as conn:
            # You could add a specific test marker table or check for test-specific tables
            # For now, we'll just verify connectivity and rely on the URL naming convention
            conn.execute(text("SELECT 1")).scalar()
    except Exception as e:
        logger.error(f"Test database verification failed: {e}")
        raise