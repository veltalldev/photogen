"""
app/utils/table_dependency.py - Builds a dependency graph for database tables

This module should be placed in the app/utils/ directory and provides functionality
to analyze database schema and determine the correct order for table truncation
based on foreign key constraints.

Part of the implementation for ENV-DB-2.4.3.1 (Create table dependency map)
"""
from typing import Dict, List, Set, Tuple, Optional
import logging
from sqlalchemy import inspect, MetaData, Table
from sqlalchemy.engine import Engine
from sqlalchemy.sql import text

logger = logging.getLogger(__name__)

class TableDependencyMap:
    """
    Builds and manages a dependency graph for database tables.
    Used to determine the proper order for truncating tables.
    """
    
    def __init__(self, engine: Engine, inspector=None):
        """
        Initialize the dependency map with a SQLAlchemy engine.
        
        Args:
            engine: SQLAlchemy engine connected to the database
        """
        self.engine = engine
        self.dependencies: Dict[str, Set[str]] = {}
        self.reverse_dependencies: Dict[str, Set[str]] = {}
        self.tables: List[str] = []
        self._inspector = inspector
        self._build_dependencies()
    
    def _build_dependencies(self) -> None:
        """
        Build the dependency graph by querying the database schema.
        """
        # Get all tables in the database
        if self._inspector is None:
            inspector = inspect(self.engine)
        else:
            inspector = self._inspector
        self.tables = inspector.get_table_names()
        
        # Initialize dependency dicts
        self.dependencies = {table: set() for table in self.tables}
        self.reverse_dependencies = {table: set() for table in self.tables}
        
        # Query foreign key constraints
        for table in self.tables:
            foreign_keys = inspector.get_foreign_keys(table)
            for fk in foreign_keys:
                # Get the referenced table
                referenced_table = fk['referred_table']
                
                # Add dependency: table depends on referenced_table
                self.dependencies[table].add(referenced_table)
                
                # Add reverse dependency: referenced_table is depended on by table
                self.reverse_dependencies[referenced_table].add(table)
        
        logger.debug(f"Built dependency map for {len(self.tables)} tables")
    
    def get_truncation_order(self) -> List[str]:
        """
        Determine the order in which tables should be truncated.
        
        Returns:
            List of table names in the order they should be truncated.
            The order ends with tables that have no foreign key dependencies
            ON other tables (independent tables), preceded by tables with
            dependencies that have been satisfied by later tables in the list.

            It delivers the list of recommended truncation targets as promised.
            The first table (left to right) should be dropped first.
        """
        # Create a working copy of dependencies
        remaining_deps = {table: set(deps) for table, deps in self.dependencies.items()}
        ordered_tables = []
        
        # Process tables until all are handled
        while remaining_deps:
            # Find tables with no remaining dependencies
            independent_tables = [
                table for table, deps in remaining_deps.items() if not deps
            ]
            
            if not independent_tables:
                # Circular dependency detected
                logger.error("Circular dependency detected among tables: %s", remaining_deps)
                # Break the cycle by choosing a table with the fewest dependencies
                min_deps = min(len(deps) for deps in remaining_deps.values() if deps)
                independent_tables = [
                    table for table, deps in remaining_deps.items() 
                    if len(deps) == min_deps
                ]
                logger.warning("Breaking cycle by selecting table with fewest dependencies: %s", 
                              independent_tables[0])
            
            # Add tables with no dependencies to the ordered list
            for table in independent_tables:
                ordered_tables.append(table)
                remaining_deps.pop(table)
                
                # Remove this table from the dependencies of other tables
                for deps in remaining_deps.values():
                    deps.discard(table)
        
        # Return in truncation order - parents first, then child
        # This ensures foreign key constraints won't be violated
        return list(reversed(ordered_tables))
    
    def get_dependent_tables(self, table: str) -> Set[str]:
        """
        Get all tables that depend on the specified table.
        
        Args:
            table: The table name to check for dependents
            
        Returns:
            Set of table names that depend on the specified table
        """
        if table not in self.reverse_dependencies:
            return set()
        
        result = set()
        to_process = list(self.reverse_dependencies[table])
        
        while to_process:
            current = to_process.pop()
            if current not in result:
                result.add(current)
                to_process.extend(
                    dep for dep in self.reverse_dependencies.get(current, set())
                    if dep not in result
                )
        
        return result
    
    def generate_dependency_graph(self) -> Dict[str, Dict]:
        """
        Generate a dependency graph representation for visualization or reporting.
        
        Returns:
            Dictionary representation of the dependency graph
        """
        graph = {}
        for table in self.tables:
            graph[table] = {
                "depends_on": list(self.dependencies[table]),
                "depended_by": list(self.reverse_dependencies[table])
            }
        return graph
    
    def verify_truncation_order(self, order: List[str]) -> bool:
        """
        Verify that a given truncation order satisfies all dependencies,
        accounting for circular dependencies.
        
        Args:
            order: List of table names in proposed truncation order
            
        Returns:
            True if the order is valid, False otherwise
        """
        # Ensure all tables are included
        if set(order) != set(self.tables):
            logger.error("The truncation order doesn't include all tables")
            return False
        
        # Detect circular dependencies
        circular_deps = self._find_circular_dependencies()
        logger.debug(f"Detected circular dependencies: {circular_deps}")
        
        # Create a set of processed tables
        processed = set()
        
        # Check each table in the order
        print(f"circular deps = {circular_deps}")
        for table in order:
            # Check if all dependencies have been processed
            for dependent_table in self.reverse_dependencies.get(table, set()):
                # Skip circular dependencies during verification
                if (dependent_table, table) in circular_deps:
                    logger.debug(f"Skipping circular dependency check: {dependent_table} -> {table}")
                    continue
                    
                if dependent_table not in processed and dependent_table in order:
                    print(f"found problematic table: {dependent_table}")
                    print(f"supposedly {dependent_table} depends on {table}")
                    logger.error(f"Invalid truncation order: {table} is referenced by {dependent_table}, "
                                f"but {dependent_table} hasn't been processed yet")
                    return False
            
            # Mark this table as processed
            processed.add(table)
        
        return True

    def _find_circular_dependencies(self) -> Set[Tuple[str, str]]:
        """
        Find all circular dependencies in the schema.
        
        Returns:
            Set of (table1, table2) pairs where table1 depends on table2 
            and there's a circular path back to table1
        """
        circular_deps = set()
        
        # Find self-references first (simplest form of circular dependency)
        for table in self.tables:
            if table in self.dependencies[table]:
                circular_deps.add((table, table))
        
        # Find more complex circular paths
        for start_table in self.tables:
            # Skip if we already know this table is in a cycle
            if any((start_table, other) in circular_deps for other in self.tables):
                continue
                
            # Do a depth-first search from this table
            visited = set()
            path = []
            
            def dfs(current_table):
                # If we've seen this table in the current path, we found a cycle
                if current_table in path:
                    # Extract and record the cycle
                    cycle_start = path.index(current_table)
                    cycle = path[cycle_start:] + [current_table]
                    # Add all edges in the cycle to circular_deps
                    for i in range(len(cycle) - 1):
                        circular_deps.add((cycle[i], cycle[i+1]))
                    circular_deps.add((cycle[-1], cycle[0]))  # Close the loop
                    return
                    
                # If we've processed this table before, skip it
                if current_table in visited:
                    return
                    
                # Add to path and mark as visited
                visited.add(current_table)
                path.append(current_table)
                
                # Explore dependencies
                for dep_table in self.dependencies[current_table]:
                    dfs(dep_table)
                    
                # Remove from path as we backtrack
                path.pop()
            
            # Start DFS from the current table
            dfs(start_table)
        
        return circular_deps

    def print_dependency_tree(self, output_format: str = "text") -> str:
        """
        Generate a human-readable representation of the dependency tree.
        
        Args:
            output_format: Format to output ("text" or "markdown")
            
        Returns:
            Formatted string representation of the dependency tree
        """
        if output_format == "markdown":
            output = "# Database Table Dependencies\n\n"
            for table in self.tables:
                output += f"## {table}\n\n"
                
                if self.dependencies[table]:
                    output += "### Depends on:\n"
                    for dep in sorted(self.dependencies[table]):
                        output += f"- {dep}\n"
                    output += "\n"
                
                if self.reverse_dependencies[table]:
                    output += "### Depended on by:\n"
                    for dep in sorted(self.reverse_dependencies[table]):
                        output += f"- {dep}\n"
                    output += "\n"
        else:  # text format
            output = "DATABASE TABLE DEPENDENCIES\n"
            output += "==========================\n\n"
            
            for table in self.tables:
                output += f"{table}\n"
                output += "-" * len(table) + "\n"
                
                if self.dependencies[table]:
                    output += "  Depends on:\n"
                    for dep in sorted(self.dependencies[table]):
                        output += f"    - {dep}\n"
                
                if self.reverse_dependencies[table]:
                    output += "  Depended on by:\n"
                    for dep in sorted(self.reverse_dependencies[table]):
                        output += f"    - {dep}\n"
                
                output += "\n"
        
        return output
    
    @classmethod
    def from_engine(cls, engine: Engine) -> 'TableDependencyMap':
        """
        Create a TableDependencyMap instance from a SQLAlchemy engine.
        
        Args:
            engine: SQLAlchemy engine connected to the database
            
        Returns:
            Initialized TableDependencyMap instance
        """
        return cls(engine)


def get_dependency_map(engine: Engine) -> TableDependencyMap:
    """
    Factory function to create a TableDependencyMap instance.
    
    Args:
        engine: SQLAlchemy engine connected to the database
        
    Returns:
        Initialized TableDependencyMap instance
    """
    return TableDependencyMap(engine)