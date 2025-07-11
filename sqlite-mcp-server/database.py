"""SQLite database operations for the MCP server."""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from pathlib import Path


class SQLiteDatabase:
    """Handles SQLite database operations with safety measures."""
    
    def __init__(self, db_path: str):
        """Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._ensure_database_exists()
    
    def _ensure_database_exists(self) -> None:
        """Ensure the database file exists and is accessible."""
        if not self.db_path.exists():
            # Create an empty database file
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("SELECT 1")  # Simple query to initialize the database
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory for dict-like access."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_schema(self) -> List[Dict[str, Any]]:
        """Get the database schema information.
        
        Returns:
            List of table schema information
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    name,
                    sql
                FROM sqlite_master 
                WHERE type='table' 
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            
            tables = []
            for row in cursor.fetchall():
                table_name = row['name']
                table_sql = row['sql']
                
                # Get column information
                columns_cursor = conn.execute(f"PRAGMA table_info({table_name})")
                columns = [
                    {
                        'name': col[1],
                        'type': col[2],
                        'not_null': bool(col[3]),
                        'default_value': col[4],
                        'primary_key': bool(col[5])
                    }
                    for col in columns_cursor.fetchall()
                ]
                
                tables.append({
                    'name': table_name,
                    'sql': table_sql,
                    'columns': columns
                })
            
            return tables
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a SQL query with safety checks.
        
        Args:
            query: The SQL query to execute
            params: Optional parameters for the query
            
        Returns:
            List of query results as dictionaries
            
        Raises:
            ValueError: If the query is not allowed (e.g., not a SELECT)
        """
        # Basic safety check - only allow SELECT queries
        query_stripped = query.strip().upper()
        if not query_stripped.startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed for safety")
        
        # Check for dangerous patterns
        dangerous_patterns = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
        for pattern in dangerous_patterns:
            if pattern in query_stripped:
                raise ValueError(f"Query contains dangerous pattern: {pattern}")
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params or ())
            rows = cursor.fetchall()
            
            # Convert rows to dictionaries
            return [dict(row) for row in rows]
    
    def get_table_data(self, table_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get data from a specific table with a limit.
        
        Args:
            table_name: Name of the table
            limit: Maximum number of rows to return
            
        Returns:
            List of table data as dictionaries
        """
        # Sanitize table name to prevent SQL injection
        if not table_name.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Invalid table name")
        
        query = f"SELECT * FROM {table_name} LIMIT ?"
        return self.execute_query(query, (limit,))
    
    def create_sample_data(self) -> None:
        """Create sample data for demonstration purposes."""
        with self.get_connection() as conn:
            # Create a sample users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    age INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create a sample products table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    category TEXT,
                    in_stock BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert sample data
            conn.executemany("""
                INSERT OR IGNORE INTO users (name, email, age) VALUES (?, ?, ?)
            """, [
                ('John Doe', 'john@example.com', 30),
                ('Jane Smith', 'jane@example.com', 25),
                ('Bob Johnson', 'bob@example.com', 35),
                ('Alice Brown', 'alice@example.com', 28)
            ])
            
            conn.executemany("""
                INSERT OR IGNORE INTO products (name, price, category, in_stock) VALUES (?, ?, ?, ?)
            """, [
                ('Laptop', 999.99, 'Electronics', True),
                ('Mouse', 29.99, 'Electronics', True),
                ('Keyboard', 79.99, 'Electronics', False),
                ('Desk Chair', 199.99, 'Furniture', True),
                ('Monitor', 299.99, 'Electronics', True)
            ])
            
            conn.commit()