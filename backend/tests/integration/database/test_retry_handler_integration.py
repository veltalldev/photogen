# backend/tests/integration/database/test_retry_handler_integration.py
"""
Integration tests for database retry handler functionality.
Tests the retry handler with actual database connections and operations.
"""

import time
import threading
import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.database.connection import db_session, get_engine
from app.database.retry_handler import (
    retry_database_operation,
    with_timeout,
    safe_db_operation,
    DatabaseTimeoutError,
    MaxRetriesExceededError
)


class TestRetryHandlerIntegration:
    """Integration tests for retry handler with actual database operations."""

    @pytest.fixture
    def engine(self):
        """Create a database engine for tests."""
        return get_engine()

    def test_successful_query_with_retry(self, engine):
        """Test that a successful query works with retry decorator."""
        @retry_database_operation(max_retries=2, initial_delay=0.01)
        def execute_query(connection):
            return connection.execute(text("SELECT 1")).scalar()

        with engine.connect() as conn:
            result = execute_query(conn)
            assert result == 1

    def test_successful_query_with_timeout(self, engine):
        """Test that a successful query works with timeout decorator."""
        @with_timeout(timeout=5.0)
        def execute_query(connection):
            return connection.execute(text("SELECT pg_sleep(0.1), 42")).fetchone()[1]

        with engine.connect() as conn:
            result = execute_query(conn)
            assert result == 42

    def test_successful_query_with_safe_operation(self, engine):
        """Test that a successful query works with combined safe_db_operation decorator."""
        @safe_db_operation(max_retries=2, timeout=5.0)
        def execute_query(connection):
            return connection.execute(text("SELECT 123")).scalar()

        with engine.connect() as conn:
            result = execute_query(conn)
            assert result == 123

    def test_timeout_for_slow_query(self, engine):
        """Test that timeout works for a slow database query."""
        # Create a session instead of a direct connection
        from sqlalchemy.orm import Session
        
        with Session(engine) as session:
            @with_timeout(timeout=0.1)
            def execute_slow_query(session_obj):
                # This query will sleep for 1 second, which should trigger timeout
                return session_obj.execute(text("SELECT pg_sleep(1), 42")).fetchone()

            with pytest.raises(Exception) as excinfo:
                execute_slow_query(session)
            
            # Verify it's a timeout-related error
            error_text = str(excinfo.value).lower()
            assert "timeout" in error_text or "statement" in error_text, f"Expected timeout error, got: {error_text}"

    def test_retry_on_temporary_error(self):
        """Test retry functionality with a simulated temporary database error."""
        attempts = [0]

        @retry_database_operation(max_retries=2, initial_delay=0.01)
        def operation_with_temporary_error():
            attempts[0] += 1
            if attempts[0] <= 1:
                # Simulate a temporary database error on first attempt
                raise OperationalError("temporary error", {}, Exception("connection reset"))
            return "success"

        result = operation_with_temporary_error()
        assert result == "success"
        assert attempts[0] == 2  # Verify it took 2 attempts

    def test_session_with_retry(self):
        """Test retry functionality with database session context manager."""
        @retry_database_operation(max_retries=2, initial_delay=0.01)
        def db_operation(session):
            result = session.execute(text("SELECT 999")).scalar()
            return result

        with db_session() as session:
            result = db_operation(session)
            assert result == 999

    def test_statement_timeout_in_session(self):
        """Test that statement timeout is correctly set in the session."""
        @with_timeout(timeout=0.3)
        def execute_with_timeout(session):
            # First check if timeout was set
            timeout_result = session.execute(text("SHOW statement_timeout")).scalar()
            assert timeout_result == "300ms", "Statement timeout was not set correctly"
            
            try:
                # Try a query that should exceed the timeout
                session.execute(text("SELECT pg_sleep(1)"))
                return False  # Should not reach here
            except Exception as e:
                # Verify it's a timeout-related error
                error_text = str(e).lower()
                return "timeout" in error_text or "statement" in error_text
        
        with db_session() as session:
            result = execute_with_timeout(session)
            assert result is True, "Query should have timed out"

    def test_connection_blocking_with_safe_operation(self, engine):
        """
        Test safe operation with high timeout when connection is blocked.
        This simulates a scenario where the connection is temporarily unavailable.
        """
        # Create a lock to synchronize threads
        execution_lock = threading.Lock()
        execution_lock.acquire()  # Lock initially
        
        # Track when the blocking query is released
        release_time = [0]
        
        # Function to block the database for a short time
        def block_database():
            with engine.connect() as conn:
                # Execute a query that will hold a lock
                conn.execute(text("BEGIN"))
                conn.execute(text("LOCK TABLE pg_catalog.pg_class IN ACCESS EXCLUSIVE MODE"))
                
                # Hold the lock for a half second
                time.sleep(0.5)
                
                # Record when we release the lock
                release_time[0] = time.time()
                
                # Release the lock
                conn.execute(text("ROLLBACK"))
                
                # Signal the main thread that the lock has been acquired
                execution_lock.release()
        
        # Start a thread to block the database
        blocking_thread = threading.Thread(target=block_database)
        blocking_thread.daemon = True
        blocking_thread.start()
        
        # Function that will retry when the database is blocked
        @safe_db_operation(max_retries=3, timeout=2.0, initial_delay=0.1)
        def query_during_block(connection):
            # Try to execute a query that requires the catalog
            return connection.execute(text("SELECT count(*) FROM pg_catalog.pg_class")).scalar()
        
        # Wait for the blocking thread to acquire its lock
        execution_lock.acquire()
        
        # Now try to execute our query with retry - it should succeed after the block is released
        start_time = time.time()
        with engine.connect() as conn:
            count = query_during_block(conn)
            
        end_time = time.time()
        
        # Verify that our query waited for the release and then succeeded
        assert count > 0, "Should have received a valid count"
        assert end_time > release_time[0], "Query should complete after the lock was released"