"""
Unit tests for database connection module.
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import (
    get_database_url,
    create_connection_string,
    get_engine,
    check_connection,
    get_session_factory,
    DatabaseSession
)


class TestDatabaseConnection(unittest.TestCase):
    """Test cases for database connection module."""
    
    def test_get_database_url_from_env(self):
        """Test getting database URL from environment variable."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}):
            url = get_database_url()
            self.assertEqual(url, "postgresql://test:test@localhost/test")
    
    def test_get_database_url_default(self):
        """Test getting default database URL when not in environment."""
        with patch.dict(os.environ, clear=True):
            url = get_database_url()
            self.assertEqual(url, "postgresql://postgres:postgres@localhost/photo_gallery_dev")
    
    def test_create_connection_string(self):
        """Test creating connection string from components."""
        url = create_connection_string(
            host="testhost",
            port=5432,
            user="testuser",
            password="testpass",
            database="testdb"
        )
        self.assertEqual(url, "postgresql://testuser:testpass@testhost:5432/testdb")
    
    def test_create_connection_string_with_params(self):
        """Test creating connection string with additional parameters."""
        url = create_connection_string(
            host="testhost",
            port=5432,
            user="testuser",
            password="testpass",
            database="testdb",
            params={"connect_timeout": 10, "application_name": "test"}
        )
        # Check both parameters are in the URL (order may vary)
        self.assertIn("connect_timeout=10", url)
        self.assertIn("application_name=test", url)
    
    @patch("app.database.connection.create_engine")
    def test_get_engine(self, mock_create_engine):
        """Test creating SQLAlchemy engine."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        engine = get_engine("postgresql://test:test@localhost/test")
        
        mock_create_engine.assert_called_once()
        self.assertEqual(engine, mock_engine)
    
    @patch("app.database.connection.create_engine")
    def test_get_engine_error(self, mock_create_engine):
        """Test error handling when creating engine."""
        mock_create_engine.side_effect = SQLAlchemyError("Test error")
        
        with self.assertRaises(SQLAlchemyError):
            get_engine("postgresql://test:test@localhost/test")
    
    def test_test_connection_success(self):
        """Test successful connection test."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        result = check_connection(mock_engine)
        
        self.assertTrue(result)
        mock_engine.connect.assert_called_once()
        mock_conn.execute.assert_called_once()
    
    def test_test_connection_failure(self):
        """Test failed connection test."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = SQLAlchemyError("Test error")
        
        result = check_connection(mock_engine)
        
        self.assertFalse(result)
    
    def test_get_session_factory(self):
        """Test creating session factory."""
        mock_engine = MagicMock()
        
        factory = get_session_factory(mock_engine)
        
        self.assertIsNotNone(factory)
        self.assertTrue(callable(factory))
    
    def test_database_session_context_manager(self):
        """Test database session context manager."""
        mock_session = MagicMock()
        mock_factory = MagicMock(return_value=mock_session)
        
        with DatabaseSession(mock_factory) as session:
            self.assertEqual(session, mock_session)
        
        # Verify session was committed and closed
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
    
    def test_database_session_with_exception(self):
        """Test database session context manager with exception."""
        mock_session = MagicMock()
        mock_factory = MagicMock(return_value=mock_session)
        
        try:
            with DatabaseSession(mock_factory) as session:
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Verify session was rolled back and closed
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()