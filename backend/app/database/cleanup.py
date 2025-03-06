"""
app/database/cleanup.py - Implements database cleanup functionality for tests

This module should be placed in the app/database/ directory and provides functions
to reset the database to a clean state between tests.

It implements ENV-DB-2.4.2 (Database reset function) and works with the 
table dependency map from ENV-DB-2.4.3.1.
"""
import logging
from typing import List, Optional, Set, Dict, Callable
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.utils.table_dependency import TableDependencyMap, get_dependency_map

logger = logging.getLogger(__name__)

def truncate_tables(engine: Engine, table_names: Optional[List[str]] = None) -> None:
    """
    Truncate specified tables or all tables if none specified.
    Tables are truncated in the correct order based on foreign key constraints.
    
    Args:
        engine: SQLAlchemy engine to use for database operations
        table_names: List of table names to truncate, or None for all tables
    """
    # Get dependency map to determine truncation order
    dependency_map = get_dependency_map(engine)
    
    # If no specific tables are provided, truncate all tables
    if table_names is None:
        table_names = dependency_map.tables
    
    # Determine truncation order for specified tables
    # If only a subset of tables is specified, we need to find dependencies
    if len(table_names) < len(dependency_map.tables):
        # Get all tables that need to be truncated, including dependencies
        tables_to_truncate = set(table_names)
        
        # Ensure the truncation set includes dependent tables
        # Otherwise, foreign key constraints might be violated
        for table in table_names:
            dependent_tables = dependency_map.get_dependent_tables(table)
            tables_to_truncate.update(dependent_tables)
        
        # Get ordered list of all tables
        all_tables_order = dependency_map.get_truncation_order()
        
        # Filter to the tables we need to truncate
        truncation_order = [t for t in all_tables_order if t in tables_to_truncate]
    else:
        # If truncating all tables, use the complete truncation order
        truncation_order = dependency_map.get_truncation_order()
    
    logger.debug(f"Truncating tables in order: {truncation_order}")
    
    with engine.begin() as conn:
        # Temporarily disable foreign key constraints to allow truncation
        conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        
        # Truncate each table in the determined order
        for table in truncation_order:
            if table in table_names:
                conn.execute(text(f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE'))
                logger.debug(f"Truncated table: {table}")
        
        # Re-enable foreign key constraints
        conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    
    logger.info(f"Truncated {len(truncation_order)} tables")

def reset_sequences(engine: Engine, sequences: Optional[List[str]] = None) -> None:
    """
    Reset specified sequences or all sequences if none specified.
    
    Args:
        engine: SQLAlchemy engine to use for database operations
        sequences: List of sequence names to reset, or None for all sequences
    """
    with engine.begin() as conn:
        # If no specific sequences provided, get all sequences from the database
        if sequences is None:
            result = conn.execute(text(
                "SELECT sequencename FROM pg_sequences "
                "WHERE schemaname = 'public'"
            ))
            sequences = [row[0] for row in result]
        
        # Reset each sequence to 1
        for sequence in sequences:
            conn.execute(text(f'ALTER SEQUENCE "{sequence}" RESTART WITH 1'))
            logger.debug(f"Reset sequence: {sequence}")
    
    logger.info(f"Reset {len(sequences)} sequences")

def verify_clean_state(engine: Engine) -> Dict[str, bool]:
    """
    Verify that the database is in a clean state as defined by the 
    Photo Gallery Database Initial State Specification.
    
    Args:
        engine: SQLAlchemy engine to use for database operations
        
    Returns:
        Dictionary with verification results for each check
    """
    results = {
        "tables_exist": True,
        "tables_empty": True,
        "sequences_reset": True,
        "settings_correct": True
    }
    
    with engine.begin() as conn:
        # 1. Check that all tables exist
        dependency_map = get_dependency_map(engine)
        expected_tables = set(dependency_map.tables)
        
        # 2. Check that all tables are empty
        for table in expected_tables:
            result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
            count = result.scalar()
            if count > 0:
                logger.warning(f"Table {table} is not empty: {count} rows")
                results["tables_empty"] = False
        
        # 3. Check that sequences are reset to the appropriate values
        result = conn.execute(text(
            "SELECT sequencename, last_value FROM pg_sequences "
            "WHERE schemaname = 'public'"
        ))
        
        for row in result:
            sequence_name, last_value = row
            # Most sequences should be at 1 in a clean state
            if last_value != 1:
                logger.warning(f"Sequence {sequence_name} is not reset: {last_value}")
                results["sequences_reset"] = False
        
        # 4. Check database settings
        # This could be extended to check specific settings from the configuration
        # For now, just check a few critical settings
        result = conn.execute(text("SHOW search_path"))
        search_path = result.scalar()
        if "public" not in search_path:
            logger.warning(f"Unexpected search_path: {search_path}")
            results["settings_correct"] = False
    
    return results

def clean_database(engine: Engine) -> Dict[str, bool]:
    """
    Reset the database to a clean state by truncating all tables and
    resetting all sequences.
    
    Args:
        engine: SQLAlchemy engine to use for database operations
        
    Returns:
        Dictionary with verification results after cleaning
    """
    # Truncate all tables in the correct order
    truncate_tables(engine)
    
    # Reset all sequences
    reset_sequences(engine)
    
    # Verify clean state
    return verify_clean_state(engine)

def create_cleanup_fixture(engine_fixture: Callable) -> Callable:
    """
    Factory function to create a pytest fixture for database cleanup.
    
    Args:
        engine_fixture: Fixture function that provides the database engine
        
    Returns:
        Fixture function for database cleanup
    """
    def _cleanup_fixture(request):
        """
        Fixture to clean the database before and/or after tests.
        
        The cleanup strategy can be configured through markers:
        - @pytest.mark.clean_before: Clean before the test
        - @pytest.mark.clean_after: Clean after the test
        - @pytest.mark.truncate_tables: Specify tables to truncate
        
        Examples:
            @pytest.mark.clean_before
            def test_something(cleanup_db):
                # Database is clean at the start of the test
                ...
                
            @pytest.mark.clean_after
            def test_something(cleanup_db):
                # Database will be cleaned after the test
                ...
                
            @pytest.mark.truncate_tables(['users', 'posts'])
            def test_something(cleanup_db):
                # Only users and posts tables are truncated
                ...
        """
        engine = engine_fixture(request)
        
        # Check markers for cleanup configuration
        clean_before = request.node.get_closest_marker("clean_before") is not None
        clean_after = request.node.get_closest_marker("clean_after") is not None
        truncate_marker = request.node.get_closest_marker("truncate_tables")
        
        tables_to_truncate = None
        if truncate_marker is not None:
            tables_to_truncate = truncate_marker.args[0] if truncate_marker.args else None
        
        # Clean database before test if requested
        if clean_before:
            logger.info("Cleaning database before test")
            if tables_to_truncate:
                truncate_tables(engine, tables_to_truncate)
            else:
                clean_database(engine)
        
        # Yield control to the test
        yield
        
        # Clean database after test if requested
        if clean_after:
            logger.info("Cleaning database after test")
            if tables_to_truncate:
                truncate_tables(engine, tables_to_truncate)
            else:
                clean_database(engine)
    
    return _cleanup_fixture

# Pre-configured fixtures for common cleanup patterns

def create_function_scoped_cleanup_fixture(engine_fixture: Callable) -> Callable:
    """
    Create a function-scoped fixture that cleans the database before each test.
    
    Args:
        engine_fixture: Fixture function that provides the database engine
        
    Returns:
        Function-scoped fixture that cleans the database before each test
    """
    def _fixture(request):
        """Clean the database before each test function."""
        engine = engine_fixture(request)
        
        # Clean database before test
        logger.info("Cleaning database before test function")
        clean_database(engine)
        
        # Yield control to the test
        yield
    
    return _fixture

def create_class_scoped_cleanup_fixture(engine_fixture: Callable) -> Callable:
    """
    Create a class-scoped fixture that cleans the database before each test class.
    
    Args:
        engine_fixture: Fixture function that provides the database engine
        
    Returns:
        Class-scoped fixture that cleans the database before each test class
    """
    def _fixture(request):
        """Clean the database before each test class."""
        engine = engine_fixture(request)
        
        # Clean database before test class
        logger.info("Cleaning database before test class")
        clean_database(engine)
        
        # Yield control to the test class
        yield
    
    return _fixture

def create_module_scoped_cleanup_fixture(engine_fixture: Callable) -> Callable:
    """
    Create a module-scoped fixture that cleans the database before each test module.
    
    Args:
        engine_fixture: Fixture function that provides the database engine
        
    Returns:
        Module-scoped fixture that cleans the database before each test module
    """
    def _fixture(request):
        """Clean the database before each test module."""
        engine = engine_fixture(request)
        
        # Clean database before test module
        logger.info("Cleaning database before test module")
        clean_database(engine)
        
        # Yield control to the test module
        yield
    
    return _fixture