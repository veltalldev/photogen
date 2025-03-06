"""
tests/unit/utils/test_table_dependency.py - Tests for the table dependency map functionality

This test file should be placed in the tests/unit/utils/ directory and verifies
the functionality of the TableDependencyMap class.

Part of the implementation for ENV-DB-2.4.3.1 (Create table dependency map)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, ForeignKey
from sqlalchemy.engine import Engine

from app.utils.table_dependency import TableDependencyMap, get_dependency_map


class TestTableDependencyMap:
    """Tests for TableDependencyMap class"""
    
    def setup_mock_inspector(self):
        """Set up a mock inspector with a sample database schema"""
        mock_inspector = Mock()
        
        # Define tables
        tables = ["users", "posts", "comments", "tags", "post_tags"]
        mock_inspector.get_table_names.return_value = tables
        
        # Define foreign keys
        foreign_keys = {
            "users": [],  # No foreign keys
            "posts": [
                {"referred_table": "users"}  # posts.user_id -> users.id
            ],
            "comments": [
                {"referred_table": "users"},  # comments.user_id -> users.id
                {"referred_table": "posts"}   # comments.post_id -> posts.id
            ],
            "tags": [],  # No foreign keys
            "post_tags": [
                {"referred_table": "posts"},  # post_tags.post_id -> posts.id
                {"referred_table": "tags"}    # post_tags.tag_id -> tags.id
            ]
        }
        
        mock_inspector.get_foreign_keys = lambda table: foreign_keys.get(table, [])
        return mock_inspector
    
    @patch('sqlalchemy.inspect')
    def test_build_dependencies(self, mock_inspect):
        """Test that dependencies are correctly built from database schema"""
        # Set up mock inspector
        mock_inspect.return_value = self.setup_mock_inspector()
        
        # Create dependency map with mock engine
        engine = Mock(spec=Engine)
        dependency_map = TableDependencyMap(engine)
        
        # Verify tables
        assert set(dependency_map.tables) == {"users", "posts", "comments", "tags", "post_tags"}
        
        # Verify dependencies
        assert dependency_map.dependencies["users"] == set()
        assert dependency_map.dependencies["posts"] == {"users"}
        assert dependency_map.dependencies["comments"] == {"users", "posts"}
        assert dependency_map.dependencies["tags"] == set()
        assert dependency_map.dependencies["post_tags"] == {"posts", "tags"}
        
        # Verify reverse dependencies
        assert dependency_map.reverse_dependencies["users"] == {"posts", "comments"}
        assert dependency_map.reverse_dependencies["posts"] == {"comments", "post_tags"}
        assert dependency_map.reverse_dependencies["comments"] == set()
        assert dependency_map.reverse_dependencies["tags"] == {"post_tags"}
        assert dependency_map.reverse_dependencies["post_tags"] == set()
    
    @patch('sqlalchemy.inspect')
    def test_get_truncation_order(self, mock_inspect):
        """Test that truncation order is correctly determined"""
        # Set up mock inspector
        mock_inspect.return_value = self.setup_mock_inspector()
        
        # Create dependency map with mock engine
        engine = Mock(spec=Engine)
        dependency_map = TableDependencyMap(engine)
        
        # Get truncation order
        order = dependency_map.get_truncation_order()
        
        # Verify order guarantees
        # 1. Comments should come before posts and users
        # 2. Post_tags should come before posts and tags
        # 3. Posts should come before users
        
        # Convert to indices for easier comparison
        indices = {table: i for i, table in enumerate(order)}
        
        # Check constraints
        assert indices["comments"] < indices["posts"]
        assert indices["comments"] < indices["users"]
        assert indices["post_tags"] < indices["posts"]
        assert indices["post_tags"] < indices["tags"]
        assert indices["posts"] < indices["users"]
        
        # Verify complete order
        expected_order = ["comments", "post_tags", "posts", "tags", "users"]
        assert set(order) == set(expected_order)  # All tables should be included
        
        # Verify the order is valid
        assert dependency_map.verify_truncation_order(order)
    
    @patch('sqlalchemy.inspect')
    def test_get_dependent_tables(self, mock_inspect):
        """Test that dependent tables are correctly identified"""
        # Set up mock inspector
        mock_inspect.return_value = self.setup_mock_inspector()
        
        # Create dependency map with mock engine
        engine = Mock(spec=Engine)
        dependency_map = TableDependencyMap(engine)
        
        # Verify dependent tables
        assert dependency_map.get_dependent_tables("users") == {"posts", "comments"}
        assert dependency_map.get_dependent_tables("posts") == {"comments", "post_tags"}
        assert dependency_map.get_dependent_tables("comments") == set()
        assert dependency_map.get_dependent_tables("tags") == {"post_tags"}
        assert dependency_map.get_dependent_tables("post_tags") == set()
        
        # Check for non-existent table
        assert dependency_map.get_dependent_tables("non_existent") == set()
    
    @patch('sqlalchemy.inspect')
    def test_generate_dependency_graph(self, mock_inspect):
        """Test that dependency graph is correctly generated"""
        # Set up mock inspector
        mock_inspect.return_value = self.setup_mock_inspector()
        
        # Create dependency map with mock engine
        engine = Mock(spec=Engine)
        dependency_map = TableDependencyMap(engine)
        
        # Generate dependency graph
        graph = dependency_map.generate_dependency_graph()
        
        # Verify graph structure
        assert set(graph.keys()) == {"users", "posts", "comments", "tags", "post_tags"}
        
        # Check a few entries
        assert graph["users"]["depends_on"] == []
        assert set(graph["users"]["depended_by"]) == {"posts", "comments"}
        
        assert set(graph["comments"]["depends_on"]) == {"users", "posts"}
        assert graph["comments"]["depended_by"] == []
    
    @patch('sqlalchemy.inspect')
    def test_verify_truncation_order(self, mock_inspect):
        """Test truncation order verification"""
        # Set up mock inspector
        mock_inspect.return_value = self.setup_mock_inspector()
        
        # Create dependency map with mock engine
        engine = Mock(spec=Engine)
        dependency_map = TableDependencyMap(engine)
        
        # Valid order: child tables before parent tables
        valid_order = ["comments", "post_tags", "posts", "tags", "users"]
        assert dependency_map.verify_truncation_order(valid_order)
        
        # Invalid order: parent table before child table
        invalid_order = ["users", "posts", "comments", "tags", "post_tags"]
        assert not dependency_map.verify_truncation_order(invalid_order)
        
        # Missing table
        incomplete_order = ["comments", "posts", "tags", "users"]
        assert not dependency_map.verify_truncation_order(incomplete_order)
    
    @patch('sqlalchemy.inspect')
    def test_print_dependency_tree(self, mock_inspect):
        """Test dependency tree printing"""
        # Set up mock inspector
        mock_inspect.return_value = self.setup_mock_inspector()
        
        # Create dependency map with mock engine
        engine = Mock(spec=Engine)
        dependency_map = TableDependencyMap(engine)
        
        # Get text representation
        text_output = dependency_map.print_dependency_tree("text")
        
        # Basic checks
        assert "DATABASE TABLE DEPENDENCIES" in text_output
        assert "users" in text_output
        assert "posts" in text_output
        assert "Depends on:" in text_output
        assert "Depended on by:" in text_output
        
        # Get markdown representation
        md_output = dependency_map.print_dependency_tree("markdown")
        
        # Basic checks
        assert "# Database Table Dependencies" in md_output
        assert "## users" in md_output
        assert "### Depends on:" in md_output
        assert "### Depended on by:" in md_output
    
    @patch('sqlalchemy.inspect')
    def test_factory_function(self, mock_inspect):
        """Test factory function for creating dependency map"""
        # Set up mock inspector
        mock_inspect.return_value = self.setup_mock_inspector()
        
        # Create dependency map with mock engine using factory function
        engine = Mock(spec=Engine)
        dependency_map = get_dependency_map(engine)
        
        # Verify it's the correct type
        assert isinstance(dependency_map, TableDependencyMap)
        
        # Verify dependencies were built
        assert len(dependency_map.tables) > 0


def test_with_circular_dependencies():
    """Test handling of circular dependencies"""
    # Create a mock inspector with circular dependencies
    mock_inspector = Mock()
    
    # Define tables with circular dependencies
    tables = ["a", "b", "c"]
    mock_inspector.get_table_names.return_value = tables
    
    # Define circular foreign keys: a -> b -> c -> a
    foreign_keys = {
        "a": [{"referred_table": "c"}],  # a depends on c
        "b": [{"referred_table": "a"}],  # b depends on a
        "c": [{"referred_table": "b"}]   # c depends on b
    }
    
    mock_inspector.get_foreign_keys = lambda table: foreign_keys.get(table, [])
    
    # Create dependency map
    with patch('sqlalchemy.inspect', return_value=mock_inspector):
        engine = Mock(spec=Engine)
        dependency_map = TableDependencyMap(engine)
        
        # Try to get truncation order
        order = dependency_map.get_truncation_order()
        
        # Verify we got an order despite circular dependencies
        assert len(order) == 3
        assert set(order) == {"a", "b", "c"}
        
        # Verify the order is not valid (due to circular dependencies)
        assert not dependency_map.verify_truncation_order(order)


def test_real_photo_gallery_schema():
    """
    Integration test with a mock of the actual Photo Gallery schema.
    This tests the dependency map with our specific schema structure.
    """
    # Mock inspector with Photo Gallery schema
    mock_inspector = Mock()
    
    # Define tables based on Photo Gallery schema
    tables = [
        "photos", "albums", "album_photos", "shared_links",
        "generation_sessions", "generation_steps", "step_alternatives",
        "models", "prompt_templates", "application_settings"
    ]
    
    mock_inspector.get_table_names.return_value = tables
    
    # Define foreign keys based on schema
    foreign_keys = {
        "photos": [
            {"referred_table": "photos"}  # source_image_id -> photos.id
        ],
        "albums": [
            {"referred_table": "photos"}  # cover_photo_id -> photos.id
        ],
        "album_photos": [
            {"referred_table": "albums"},  # album_id -> albums.id
            {"referred_table": "photos"}   # photo_id -> photos.id
        ],
        "shared_links": [
            {"referred_table": "photos"},  # photo_id -> photos.id
            {"referred_table": "albums"}   # album_id -> albums.id
        ],
        "generation_sessions": [
            {"referred_table": "photos"}  # source_image_id -> photos.id
        ],
        "generation_steps": [
            {"referred_table": "generation_sessions"},  # session_id -> generation_sessions.id
            {"referred_table": "generation_steps"},     # parent_id -> generation_steps.id
            {"referred_table": "photos"}                # selected_image_id -> photos.id
        ],
        "step_alternatives": [
            {"referred_table": "generation_steps"},  # step_id -> generation_steps.id
            {"referred_table": "photos"}             # image_id -> photos.id
        ],
        "models": [],  # No foreign keys
        "prompt_templates": [],  # No foreign keys
        "application_settings": []  # No foreign keys
    }
    
    mock_inspector.get_foreign_keys = lambda table: foreign_keys.get(table, [])
    
    # Create dependency map
    with patch('sqlalchemy.inspect', return_value=mock_inspector):
        engine = Mock(spec=Engine)
        dependency_map = TableDependencyMap(engine)
        
        # Get truncation order
        order = dependency_map.get_truncation_order()
        
        # Verify all tables are included
        assert set(order) == set(tables)
        
        # Print the order for debugging
        print(f"Truncation order: {order}")
        
        # Verify order is valid
        assert dependency_map.verify_truncation_order(order)
        
        # Verify specific ordering constraints
        indices = {table: i for i, table in enumerate(order)}
        
        # Check some key relationships
        assert indices["step_alternatives"] < indices["generation_steps"]
        assert indices["generation_steps"] < indices["generation_sessions"]
        assert indices["album_photos"] < indices["albums"]
        assert indices["album_photos"] < indices["photos"]
        assert indices["shared_links"] < indices["albums"]
        assert indices["shared_links"] < indices["photos"]