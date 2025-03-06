"""
tests/unit/database/test_cleanup.py - Tests for the database cleanup functionality

This test file should be placed in the tests/unit/database/ directory and verifies
the functionality of the database cleanup module.

Part of the implementation for ENV-DB-2.4.2 (Database reset function) and ENV-DB-2.4.4 (Sequence reset function)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.database.cleanup import (
    truncate_tables, 
    reset_sequences, 
    verify_clean_state, 
    clean_database,
    create_cleanup_fixture,
    create_function_scoped_cleanup_fixture,
    create_class_scoped_cleanup_fixture,
    create_module_scoped_cleanup_fixture
)


class TestDatabaseCleanup:
    """Tests for database cleanup functionality"""
    
    def setup_mock_engine(self):
        """Set up a mock SQLAlchemy engine with connection and execution context"""
        # Create mock engine
        mock_engine = Mock(spec=Engine)
        
        # Create mock connection and result
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.scalar.return_value = 0
        mock_conn.execute.return_value = mock_result
        
        # Set up begin context
        mock_engine.begin.return_value.__enter__.return_value = mock_conn
        
        return mock_engine, mock_conn, mock_result
    
    @patch('app.database.cleanup.get_dependency_map')
    def test_truncate_tables_all(self, mock_get_dependency_map):
        """Test truncating all tables"""
        # Set up mock dependency map
        mock_dependency_map = Mock()
        mock_dependency_map.tables = ["table1", "table2", "table3"]
        mock_dependency_map.get_truncation_order.return_value = ["table3", "table2", "table1"]
        mock_get_dependency_map.return_value = mock_dependency_map
        
        # Set up mock engine
        mock_engine, mock_conn, _ = self.setup_mock_engine()
        
        # Call truncate_tables with no specific tables (all tables)
        truncate_tables(mock_engine)
        
        # Verify dependency map was queried
        mock_get_dependency_map.assert_called_once_with(mock_engine)
        mock_dependency_map.get_truncation_order.assert_called_once()
        
        # Verify SET CONSTRAINTS commands were executed
        mock_conn.execute.assert_any_call(text("SET CONSTRAINTS ALL DEFERRED"))
        mock_conn.execute.assert_any_call(text("SET CONSTRAINTS ALL IMMEDIATE"))
        
        # Verify each table was truncated in the correct order
        truncate_calls = [
            call(text('TRUNCATE TABLE "table3" RESTART IDENTITY CASCADE')),
            call(text('TRUNCATE TABLE "table2" RESTART IDENTITY CASCADE')),
            call(text('TRUNCATE TABLE "table1" RESTART IDENTITY CASCADE'))
        ]
        for truncate_call in truncate_calls:
            assert truncate_call in mock_conn.execute.call_args_list
    
    @patch('app.database.cleanup.get_dependency_map')
    def test_truncate_tables_specific(self, mock_get_dependency_map):
        """Test truncating specific tables"""
        # Set up mock dependency map
        mock_dependency_map = Mock()
        mock_dependency_map.tables = ["table1", "table2", "table3", "table4"]
        mock_dependency_map.get_truncation_order.return_value = ["table3", "table2", "table4", "table1"]
        mock_dependency_map.get_dependent_tables.return_value = set()
        mock_get_dependency_map.return_value = mock_dependency_map
        
        # Set up mock engine
        mock_engine, mock_conn, _ = self.setup_mock_engine()
        
        # Call truncate_tables with specific tables
        truncate_tables(mock_engine, ["table1", "table3"])
        
        # Verify dependency map was queried
        mock_get_dependency_map.assert_called_once_with(mock_engine)
        mock_dependency_map.get_truncation_order.assert_called_once()
        
        # Verify SET CONSTRAINTS commands were executed
        mock_conn.execute.assert_any_call(text("SET CONSTRAINTS ALL DEFERRED"))
        mock_conn.execute.assert_any_call(text("SET CONSTRAINTS ALL IMMEDIATE"))
        
        # Verify only the specified tables were truncated in the correct order
        truncate_calls = [
            call(text('TRUNCATE TABLE "table3" RESTART IDENTITY CASCADE')),
            call(text('TRUNCATE TABLE "table1" RESTART IDENTITY CASCADE'))
        ]
        for truncate_call in truncate_calls:
            assert truncate_call in mock_conn.execute.call_args_list
        
        # Verify table2 and table4 were not truncated
        assert call(text('TRUNCATE TABLE "table2" RESTART IDENTITY CASCADE')) not in mock_conn.execute.call_args_list
        assert call(text('TRUNCATE TABLE "table4" RESTART IDENTITY CASCADE')) not in mock_conn.execute.call_args_list
    
    @patch('app.database.cleanup.get_dependency_map')
    def test_truncate_tables_with_dependencies(self, mock_get_dependency_map):
        """Test truncating tables with their dependencies"""
        # Set up mock dependency map
        mock_dependency_map = Mock()
        mock_dependency_map.tables = ["table1", "table2", "table3", "table4"]
        mock_dependency_map.get_truncation_order.return_value = ["table3", "table2", "table4", "table1"]
        
        # Set up dependencies: table2 depends on table1
        def get_dependent_tables(table):
            if table == "table1":
                return {"table2"}
            return set()
        
        mock_dependency_map.get_dependent_tables.side_effect = get_dependent_tables
        mock_get_dependency_map.return_value = mock_dependency_map
        
        # Set up mock engine
        mock_engine, mock_conn, _ = self.setup_mock_engine()
        
        # Call truncate_tables with table1 (should also truncate table2)
        truncate_tables(mock_engine, ["table1"])
        
        # Verify dependency map was queried
        mock_get_dependency_map.assert_called_once_with(mock_engine)
        mock_dependency_map.get_truncation_order.assert_called_once()
        mock_dependency_map.get_dependent_tables.assert_called_once_with("table1")
        
        # Verify both table1 and its dependency table2 were truncated
        truncate_calls = [
            call(text('TRUNCATE TABLE "table2" RESTART IDENTITY CASCADE')),
            call(text('TRUNCATE TABLE "table1" RESTART IDENTITY CASCADE'))
        ]
        for truncate_call in truncate_calls:
            assert truncate_call in mock_conn.execute.call_args_list
    
    def test_reset_sequences_all(self):
        """Test resetting all sequences"""
        # Set up mock engine
        mock_engine, mock_conn, mock_result = self.setup_mock_engine()
        
        # Mock the result of querying sequences
        mock_result.return_value = [("seq1",), ("seq2",), ("seq3",)]
        
        # Call reset_sequences with no specific sequences (all sequences)
        reset_sequences(mock_engine)
        
        # Verify sequences were queried
        mock_conn.execute.assert_any_call(text(
            "SELECT sequencename FROM pg_sequences "
            "WHERE schemaname = 'public'"
        ))
        
        # Verify each sequence was reset
        reset_calls = [
            call(text('ALTER SEQUENCE "seq1" RESTART WITH 1')),
            call(text('ALTER SEQUENCE "seq2" RESTART WITH 1')),
            call(text('ALTER SEQUENCE "seq3" RESTART WITH 1'))
        ]
        for reset_call in reset_calls:
            assert reset_call in mock_conn.execute.call_args_list
    
    def test_reset_sequences_specific(self):
        """Test resetting specific sequences"""
        # Set up mock engine
        mock_engine, mock_conn, _ = self.setup_mock_engine()
        
        # Call reset_sequences with specific sequences
        reset_sequences(mock_engine, ["seq1", "seq3"])
        
        # Verify only the specified sequences were reset
        reset_calls = [
            call(text('ALTER SEQUENCE "seq1" RESTART WITH 1')),
            call(text('ALTER SEQUENCE "seq3" RESTART WITH 1'))
        ]
        for reset_call in reset_calls:
            assert reset_call in mock_conn.execute.call_args_list
        
        # Verify seq2 was not reset
        assert call(text('ALTER SEQUENCE "seq2" RESTART WITH 1')) not in mock_conn.execute.call_args_list
    
    def test_verify_clean_state(self):
        """Test verifying clean state"""
        # Set up mock engine
        mock_engine, mock_conn, mock_result = self.setup_mock_engine()
        
        # Set up mock get_dependency_map
        with patch('app.database.cleanup.get_dependency_map') as mock_get_dependency_map:
            mock_dependency_map = Mock()
            mock_dependency_map.tables = ["table1", "table2"]
            mock_get_dependency_map.return_value = mock_dependency_map
            
            # Mock table count results
            def execute_side_effect(query):
                query_str = str(query)
                if "COUNT" in query_str:
                    if "table1" in query_str:
                        mock_result.scalar.return_value = 0
                    elif "table2" in query_str:
                        mock_result.scalar.return_value = 0
                elif "pg_sequences" in query_str:
                    mock_result.return_value = [("seq1", 1), ("seq2", 1)]
                elif "search_path" in query_str:
                    mock_result.scalar.return_value = "public"
                return mock_result
            
            mock_conn.execute.side_effect = execute_side_effect
            
            # Call verify_clean_state
            results = verify_clean_state(mock_engine)
            
            # Verify all checks passed
            assert results["tables_exist"] is True
            assert results["tables_empty"] is True
            assert results["sequences_reset"] is True
            assert results["settings_correct"] is True
    
    def test_verify_clean_state_issues(self):
        """Test verifying clean state with issues"""
        # Set up mock engine
        mock_engine, mock_conn, mock_result = self.setup_mock_engine()
        
        # Set up mock get_dependency_map
        with patch('app.database.cleanup.get_dependency_map') as mock_get_dependency_map:
            mock_dependency_map = Mock()
            mock_dependency_map.tables = ["table1", "table2"]
            mock_get_dependency_map.return_value = mock_dependency_map
            
            # Mock results with issues
            def execute_side_effect(query):
                query_str = str(query)
                if "COUNT" in query_str:
                    if "table1" in query_str:
                        mock_result.scalar.return_value = 0
                    elif "table2" in query_str:
                        # table2 has rows (not empty)
                        mock_result.scalar.return_value = 5
                elif "pg_sequences" in query_str:
                    # seq2 is not reset to 1
                    mock_result.return_value = [("seq1", 1), ("seq2", 10)]
                elif "search_path" in query_str:
                    # search_path doesn't include public
                    mock_result.scalar.return_value = "private"
                return mock_result
            
            mock_conn.execute.side_effect = execute_side_effect
            
            # Call verify_clean_state
            results = verify_clean_state(mock_engine)
            
            # Verify issues were detected
            assert results["tables_exist"] is True
            assert results["tables_empty"] is False
            assert results["sequences_reset"] is False
            assert results["settings_correct"] is False
    
    @patch('app.database.cleanup.truncate_tables')
    @patch('app.database.cleanup.reset_sequences')
    @patch('app.database.cleanup.verify_clean_state')
    def test_clean_database(self, mock_verify, mock_reset, mock_truncate):
        """Test clean_database function"""
        # Set up mocks
        mock_engine = Mock(spec=Engine)
        mock_verify.return_value = {"all_good": True}
        
        # Call clean_database
        result = clean_database(mock_engine)
        
        # Verify functions were called
        mock_truncate.assert_called_once_with(mock_engine)
        mock_reset.assert_called_once_with(mock_engine)
        mock_verify.assert_called_once_with(mock_engine)
        
        # Verify result
        assert result == {"all_good": True}


class TestCleanupFixtures:
    """Tests for cleanup fixture creation functions"""
    
    def test_create_cleanup_fixture(self):
        """Test creating a configurable cleanup fixture"""
        # Create mock engine and fixture
        mock_engine = Mock(spec=Engine)
        mock_engine_fixture = Mock(return_value=mock_engine)
        
        # Create cleanup fixture
        cleanup_fixture = create_cleanup_fixture(mock_engine_fixture)
        
        # Create mock request with markers
        mock_request = Mock()
        mock_request.node.get_closest_marker.side_effect = lambda marker: (
            True if marker == "clean_before" else None
        )
        
        # Set up clean_database mock
        with patch('app.database.cleanup.clean_database') as mock_clean:
            mock_clean.return_value = {"all_good": True}
            
            # Use the fixture
            fixture_gen = cleanup_fixture(mock_request)
            next(fixture_gen)  # Start the fixture
            
            # Verify engine fixture was called
            mock_engine_fixture.assert_called_once_with(mock_request)
            
            # Verify clean_database was called before the test
            mock_clean.assert_called_once_with(mock_engine)
            mock_clean.reset_mock()
            
            # Finish the fixture
            try:
                next(fixture_gen)
            except StopIteration:
                pass
            
            # Verify clean_database was not called after the test
            mock_clean.assert_not_called()
    
    def test_create_function_scoped_fixture(self):
        """Test creating a function-scoped cleanup fixture"""
        # Create mock engine and fixture
        mock_engine = Mock(spec=Engine)
        mock_engine_fixture = Mock(return_value=mock_engine)
        
        # Create function-scoped fixture
        func_fixture = create_function_scoped_cleanup_fixture(mock_engine_fixture)
        
        # Create mock request
        mock_request = Mock()
        
        # Set up clean_database mock
        with patch('app.database.cleanup.clean_database') as mock_clean:
            mock_clean.return_value = {"all_good": True}
            
            # Use the fixture
            fixture_gen = func_fixture(mock_request)
            next(fixture_gen)  # Start the fixture
            
            # Verify engine fixture was called
            mock_engine_fixture.assert_called_once_with(mock_request)
            
            # Verify clean_database was called before the test
            mock_clean.assert_called_once_with(mock_engine)
    
    def test_create_class_scoped_fixture(self):
        """Test creating a class-scoped cleanup fixture"""
        # Create mock engine and fixture
        mock_engine = Mock(spec=Engine)
        mock_engine_fixture = Mock(return_value=mock_engine)
        
        # Create class-scoped fixture
        class_fixture = create_class_scoped_cleanup_fixture(mock_engine_fixture)
        
        # Create mock request
        mock_request = Mock()
        
        # Set up clean_database mock
        with patch('app.database.cleanup.clean_database') as mock_clean:
            mock_clean.return_value = {"all_good": True}
            
            # Use the fixture
            fixture_gen = class_fixture(mock_request)
            next(fixture_gen)  # Start the fixture
            
            # Verify engine fixture was called
            mock_engine_fixture.assert_called_once_with(mock_request)
            
            # Verify clean_database was called before the test class
            mock_clean.assert_called_once_with(mock_engine)
    
    def test_create_module_scoped_fixture(self):
        """Test creating a module-scoped cleanup fixture"""
        # Create mock engine and fixture
        mock_engine = Mock(spec=Engine)
        mock_engine_fixture = Mock(return_value=mock_engine)
        
        # Create module-scoped fixture
        module_fixture = create_module_scoped_cleanup_fixture(mock_engine_fixture)
        
        # Create mock request
        mock_request = Mock()
        
        # Set up clean_database mock
        with patch('app.database.cleanup.clean_database') as mock_clean:
            mock_clean.return_value = {"all_good": True}
            
            # Use the fixture
            fixture_gen = module_fixture(mock_request)
            next(fixture_gen)  # Start the fixture
            
            # Verify engine fixture was called
            mock_engine_fixture.assert_called_once_with(mock_request)
            
            # Verify clean_database was called before the test module
            mock_clean.assert_called_once_with(mock_engine)


# Integration tests for actual database interaction
@pytest.mark.integration
class TestDatabaseCleanupIntegration:
    """Integration tests for database cleanup functionality"""
    
    @pytest.fixture
    def test_db_engine(self):
        """Create a real engine connected to the test database"""
        from sqlalchemy import create_engine
        import os
        
        # Get test database URL from environment
        test_db_url = os.environ.get("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost/photo_gallery_test")
        
        # Create engine
        engine = create_engine(test_db_url)
        
        # Verify we're connecting to a test database
        with engine.connect() as conn:
            db_name = conn.execute(text("SELECT current_database()")).scalar()
            assert "test" in db_name, f"Not a test database: {db_name}"
        
        yield engine
        
        # Close engine
        engine.dispose()
    
    def test_truncate_tables_integration(self, test_db_engine):
        """Integration test for truncate_tables"""
        # Create a sample table with data
        with test_db_engine.begin() as conn:
            # Create test table if it doesn't exist
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_truncate (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """))
            
            # Insert some data
            conn.execute(text("""
                INSERT INTO test_truncate (name) VALUES ('test1'), ('test2'), ('test3')
            """))
            
            # Verify data was inserted
            count = conn.execute(text("SELECT COUNT(*) FROM test_truncate")).scalar()
            assert count == 3, f"Expected 3 rows, got {count}"
        
        # Truncate the table
        truncate_tables(test_db_engine, ["test_truncate"])
        
        # Verify table is empty
        with test_db_engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM test_truncate")).scalar()
            assert count == 0, f"Expected 0 rows after truncation, got {count}"
    
    def test_reset_sequences_integration(self, test_db_engine):
        """Integration test for reset_sequences"""
        # Create a sample table with a sequence
        with test_db_engine.begin() as conn:
            # Create test table if it doesn't exist
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_sequence (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """))
            
            # Insert some data to advance the sequence
            conn.execute(text("""
                INSERT INTO test_sequence (name) VALUES ('test1'), ('test2'), ('test3')
            """))
            
            # Get current sequence value
            seq_value = conn.execute(text("""
                SELECT last_value FROM test_sequence_id_seq
            """)).scalar()
            assert seq_value >= 3, f"Expected sequence value >= 3, got {seq_value}"
            
            # Truncate the table
            conn.execute(text("TRUNCATE TABLE test_sequence"))
        
        # Reset the sequence
        reset_sequences(test_db_engine, ["test_sequence_id_seq"])
        
        # Verify sequence was reset
        with test_db_engine.connect() as conn:
            # Insert a new row
            conn.execute(text("INSERT INTO test_sequence (name) VALUES ('new')"))
            
            # Check ID of the new row
            new_id = conn.execute(text("SELECT id FROM test_sequence ORDER BY id LIMIT 1")).scalar()
            assert new_id == 1, f"Expected ID 1 after sequence reset, got {new_id}"
    
    def test_clean_database_integration(self, test_db_engine):
        """Integration test for clean_database"""
        # Create sample tables with data
        with test_db_engine.begin() as conn:
            # Create test tables if they don't exist
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_parent (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_child (
                    id SERIAL PRIMARY KEY,
                    parent_id INTEGER REFERENCES test_parent(id),
                    name TEXT NOT NULL
                )
            """))
            
            # Insert some data
            conn.execute(text("INSERT INTO test_parent (name) VALUES ('parent1'), ('parent2')"))
            conn.execute(text("INSERT INTO test_child (parent_id, name) VALUES (1, 'child1'), (2, 'child2')"))
        
        # Clean the database
        result = clean_database(test_db_engine)
        
        # Verify tables are empty
        with test_db_engine.connect() as conn:
            parent_count = conn.execute(text("SELECT COUNT(*) FROM test_parent")).scalar()
            child_count = conn.execute(text("SELECT COUNT(*) FROM test_child")).scalar()
            
            assert parent_count == 0, f"Expected 0 rows in test_parent, got {parent_count}"
            assert child_count == 0, f"Expected 0 rows in test_child, got {child_count}"
        
        # Verify clean state was verified
        assert result["tables_empty"] is True
    
    def test_verify_clean_state_integration(self, test_db_engine):
        """Integration test for verify_clean_state"""
        # First clean the database to ensure a clean state
        clean_database(test_db_engine)
        
        # Verify clean state
        result = verify_clean_state(test_db_engine)
        
        # Check that all verifications pass
        assert result["tables_exist"] is True, "Tables should exist"
        assert result["tables_empty"] is True, "Tables should be empty"
        assert result["sequences_reset"] is True, "Sequences should be reset"
        assert result["settings_correct"] is True, "Settings should be correct"
        
        # Now add some data to make it not clean
        with test_db_engine.begin() as conn:
            # Create test table if it doesn't exist
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_verify (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """))
            
            # Insert some data
            conn.execute(text("INSERT INTO test_verify (name) VALUES ('test')"))
        
        # Verify not clean state
        result = verify_clean_state(test_db_engine)
        
        # Check that tables_empty verification fails
        assert result["tables_empty"] is False, "Tables should not be empty"
    
    def test_cleanup_fixture_integration(self, test_db_engine):
        """Integration test for cleanup fixture"""
        # Create a fixture factory that uses our test engine
        def engine_fixture(_):
            return test_db_engine
        
        # Create cleanup fixture
        cleanup_fixture = create_cleanup_fixture(engine_fixture)
        
        # Create mock request with clean_before marker
        mock_request = Mock()
        mock_request.node.get_closest_marker.side_effect = lambda marker: (
            True if marker == "clean_before" else None
        )
        
        # Add some data to the database
        with test_db_engine.begin() as conn:
            # Create test table if it doesn't exist
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_fixture (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """))
            
            # Insert some data
            conn.execute(text("INSERT INTO test_fixture (name) VALUES ('test1'), ('test2')"))
        
        # Use the fixture
        fixture = cleanup_fixture(mock_request)
        next(fixture)  # Start the fixture
        
        # Verify database was cleaned
        with test_db_engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM test_fixture")).scalar()
            assert count == 0, f"Expected 0 rows after cleanup, got {count}"
        
        # Finish the fixture
        try:
            next(fixture)
        except StopIteration:
            pass