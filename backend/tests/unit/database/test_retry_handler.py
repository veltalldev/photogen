# backend/tests/unit/database/test_retry_handler.py
"""
Unit tests for database retry handler functionality.
"""

import time
import unittest
from unittest.mock import MagicMock, patch

import pytest
import sqlalchemy.exc
from sqlalchemy.orm import Session

from app.database.retry_handler import (
    DatabaseTimeoutError,
    MaxRetriesExceededError,
    retry_database_operation,
    with_timeout,
    safe_db_operation,
    RETRIABLE_EXCEPTIONS,
    NON_RETRIABLE_EXCEPTIONS
)


class TestRetryDatabaseOperation:
    """Test cases for retry_database_operation decorator."""

    def test_successful_operation(self):
        """Test that a successful operation completes normally."""
        mock_func = MagicMock(return_value="success")
        decorated_func = retry_database_operation()(mock_func)
        
        result = decorated_func()
        
        assert result == "success"
        mock_func.assert_called_once()
    
    def test_retry_on_retriable_exception(self):
        """Test that the function retries on retriable exceptions."""
        mock_func = MagicMock(
            side_effect=[
                sqlalchemy.exc.OperationalError("statement", {}, Exception("connection error")),
                "success"
            ]
        )
        decorated_func = retry_database_operation(initial_delay=0.01)(mock_func)
        
        result = decorated_func()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_max_retries_exceeded(self):
        """Test that MaxRetriesExceededError is raised after max retries."""
        error = sqlalchemy.exc.OperationalError("statement", {}, Exception("connection error"))
        mock_func = MagicMock(side_effect=[error, error, error])
        decorated_func = retry_database_operation(max_retries=2, initial_delay=0.01)(mock_func)
        
        with pytest.raises(MaxRetriesExceededError):
            decorated_func()
        
        assert mock_func.call_count == 3  # Initial + 2 retries
    
    def test_non_retriable_exceptions(self):
        """Test that non-retriable exceptions are not retried."""
        # Test with an exception that's explicitly in NON_RETRIABLE_EXCEPTIONS
        data_error = sqlalchemy.exc.DataError("Invalid data format", None, None)
        mock_func = MagicMock(side_effect=data_error)
        
        decorated_func = retry_database_operation(
            initial_delay=0.01  # Small delay for faster tests
        )(mock_func)
        
        with pytest.raises(sqlalchemy.exc.DataError):
            decorated_func()
        
        # Verify it was only called once (no retries)
        mock_func.assert_called_once()
        
        # Reset the mock
        mock_func.reset_mock()
        
        # Now test with a custom exception that's not in either list
        class CustomException(Exception):
            pass
        
        custom_error = CustomException("Custom exception")
        mock_func = MagicMock(side_effect=custom_error)
        
        decorated_func = retry_database_operation(
            initial_delay=0.01
        )(mock_func)
        
        with pytest.raises(CustomException):
            decorated_func()
        
        # Verify it was only called once (no retries)
        mock_func.assert_called_once()
    
    def test_retry_with_custom_exceptions(self):
        """Test retry with custom retriable exceptions."""
        custom_exception = ValueError("Custom error")
        mock_func = MagicMock(side_effect=[custom_exception, "success"])
        decorated_func = retry_database_operation(
            initial_delay=0.01,
            retriable_exceptions=(ValueError,)
        )(mock_func)
        
        result = decorated_func()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_backoff_delay_increases(self):
        """Test that backoff delay increases with retries."""
        with patch('time.sleep') as mock_sleep:
            error = sqlalchemy.exc.OperationalError("statement", {}, Exception("connection error"))
            mock_func = MagicMock(side_effect=[error, error, error, "success"])
            
            decorated_func = retry_database_operation(
                max_retries=3,
                initial_delay=0.1,
                backoff_factor=2
            )(mock_func)
            
            result = decorated_func()
            
            assert result == "success"
            assert mock_func.call_count == 4
            
            # Check sleep durations follow backoff pattern
            assert mock_sleep.call_count == 3
            assert mock_sleep.call_args_list[0][0][0] == 0.1
            assert mock_sleep.call_args_list[1][0][0] == 0.2
            assert mock_sleep.call_args_list[2][0][0] == 0.4


class TestWithTimeout:
    """Test cases for with_timeout decorator."""
    
    def test_operation_within_timeout(self):
        """Test that an operation within the timeout completes normally."""
        mock_func = MagicMock(return_value="success")
        decorated_func = with_timeout(timeout=1.0)(mock_func)
        
        result = decorated_func()
        
        assert result == "success"
        mock_func.assert_called_once()
    
    @patch('time.time')
    def test_operation_timeout(self, mock_time):
        """Test that DatabaseTimeoutError is raised when the operation times out."""
        # Mock time.time to return sequence of values indicating timeout
        mock_time.side_effect = [0, 2.0]  # Start time, check time (exceeds timeout)
        
        mock_func = MagicMock(side_effect=Exception("Operation failed"))
        decorated_func = with_timeout(timeout=1.0)(mock_func)
        
        with pytest.raises(DatabaseTimeoutError):
            decorated_func()
    
    def test_statement_timeout_for_session(self):
        """Test that statement_timeout is set for PostgreSQL sessions."""
        mock_session = MagicMock(spec=Session)
        mock_execute = MagicMock()
        mock_session.execute = mock_execute
        
        def func_with_session(session):
            return "success"
        
        decorated_func = with_timeout(timeout=2.0)(func_with_session)
        result = decorated_func(mock_session)
        
        assert result == "success"
        mock_execute.assert_called_once_with("SET statement_timeout = 2000")


class TestSafeDatabaseOperation:
    """Test cases for the combined safe_db_operation decorator."""
    
    def test_successful_operation(self):
        """Test that a successful operation completes normally with safe_db_operation."""
        mock_func = MagicMock(return_value="success")
        decorated_func = safe_db_operation()(mock_func)
        
        result = decorated_func()
        
        assert result == "success"
        mock_func.assert_called_once()
    
    def test_retry_and_timeout(self):
        """Test that safe_db_operation provides both retry and timeout functionality."""
        # Create a function that fails once then succeeds but takes time
        calls = [0]
        
        def test_function():
            calls[0] += 1
            if calls[0] == 1:
                # First call fails with a retriable error
                raise sqlalchemy.exc.OperationalError("statement", {}, Exception("connection error"))
            # Second call succeeds
            return "success"
        
        # Use patch to avoid actual time delays
        with patch('time.sleep'):
            decorated_func = safe_db_operation(max_retries=2, timeout=1.0)(test_function)
            result = decorated_func()
            
            assert result == "success"
            assert calls[0] == 2  # Function should be called twice
    
    @patch('time.time')
    def test_timeout_takes_precedence(self, mock_time):
        """Test that timeout takes precedence over retries."""
        # Mock time.time() to simulate timeout
        mock_time.side_effect = [0, 2, 2]  # Start time, check time (exceeds timeout)
        
        # Create a function that always fails with a retriable error
        mock_func = MagicMock(
            side_effect=sqlalchemy.exc.OperationalError("statement", {}, Exception("connection error"))
        )
        
        decorated_func = safe_db_operation(max_retries=3, timeout=1.0)(mock_func)
        
        with pytest.raises(DatabaseTimeoutError):
            decorated_func()
        
        assert mock_func.call_count == 1  # Function should be called only once before timeout