"""
Integration tests for database connection module.
"""

import os
import pytest
from sqlalchemy import text

from app.database.connection import (
    get_engine,
    check_connection,
    db_session,
    DatabaseSession,
    get_session_factory
)


@pytest.fixture
def test_db_url():
    """Get test database URL from environment or use default."""
    return os.environ.get("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost/photo_gallery_test")


@pytest.fixture
def engine(test_db_url):
    """Create database engine for testing."""
    return get_engine(test_db_url)


def test_connection_to_database(engine):
    """Test connection to actual database."""
    assert check_connection(engine)


def test_execute_query(engine):
    """Test executing a simple query."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_session_context_manager(engine):
    """Test session context manager with actual database."""
    # Create a temporary table for testing
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, value TEXT)"))
        conn.commit()
    
    try:
        # Create a session factory using the test engine
        session_factory = get_session_factory(engine)
        
        # Use DatabaseSession with the test-specific session factory
        with DatabaseSession(session_factory) as session:
            session.execute(text("INSERT INTO test_table (value) VALUES ('test_value')"))
        
        # Verify data was committed
        with engine.connect() as conn:
            result = conn.execute(text("SELECT value FROM test_table WHERE value = 'test_value'"))
            assert result.scalar() == 'test_value'
    finally:
        # Clean up - drop the test table
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS test_table"))
            conn.commit()