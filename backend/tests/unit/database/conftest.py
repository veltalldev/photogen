# backend/tests/unit/database/conftest.py
"""
Pytest fixtures for database unit tests.
"""

import pytest
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.connection import get_engine, get_session_factory


@pytest.fixture
def mock_engine():
    """
    Fixture for a mock SQLAlchemy engine.
    
    Returns:
        MagicMock: A mock engine object
    """
    engine = MagicMock()
    
    # Mock the connect method and connection context
    mock_connection = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 1
    mock_connection.execute.return_value = mock_result
    
    # Make engine's connect method return a connection context
    engine.connect.return_value.__enter__.return_value = mock_connection
    
    return engine


@pytest.fixture
def mock_session():
    """
    Fixture for a mock SQLAlchemy session.
    
    Returns:
        MagicMock: A mock session object
    """
    session = MagicMock(spec=Session)
    
    # Mock session methods
    mock_result = MagicMock()
    mock_result.scalar.return_value = 1
    session.execute.return_value = mock_result
    
    return session


@pytest.fixture
def patched_engine():
    """
    Fixture that patches the get_engine function to return a mock engine.
    
    Yields:
        MagicMock: The mock engine being used
    """
    engine = MagicMock()
    
    # Configure mock engine behavior
    mock_connection = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 1
    mock_connection.execute.return_value = mock_result
    
    engine.connect.return_value.__enter__.return_value = mock_connection
    
    with patch('app.database.connection.get_engine', return_value=engine):
        yield engine