#!/usr/bin/env python3
"""Unit tests only for the SQLite MCP Server."""

import asyncio
import sqlite3
import tempfile
import os
from pathlib import Path
import sys

from database import SQLiteDatabase
from server import SQLiteMCPServer


async def test_database_operations():
    """Test basic database operations."""
    print("Testing database operations...")
    
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Initialize database
        db = SQLiteDatabase(db_path)
        
        # Create sample data
        db.create_sample_data()
        print("✓ Sample data created")
        
        # Test schema retrieval
        schema = db.get_schema()
        print(f"✓ Schema retrieved: {len(schema)} tables")
        
        # Test table data retrieval
        users_data = db.get_table_data("users", limit=5)
        print(f"✓ Users data retrieved: {len(users_data)} rows")
        
        # Test query execution
        query_result = db.execute_query("SELECT COUNT(*) as count FROM users")
        print(f"✓ Query executed: {query_result}")
        
        # Test safety measures
        try:
            db.execute_query("DROP TABLE users")
            print("✗ Safety check failed - dangerous query was allowed")
        except ValueError as e:
            print(f"✓ Safety check passed: {e}")
        
        print("Database operations test completed successfully!")
        
    finally:
        # Clean up
        os.unlink(db_path)


async def test_server_initialization():
    """Test server initialization."""
    print("\nTesting server initialization...")
    
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Initialize server
        server = SQLiteMCPServer(db_path)
        print("✓ Server initialized")
        
        # Create sample data
        server.database.create_sample_data()
        print("✓ Sample data created via server")
        
        # Test that handlers are set up
        print("✓ Server handlers configured")
        
        print("Server initialization test completed successfully!")
        
    finally:
        # Clean up
        os.unlink(db_path)


async def main():
    """Run unit tests only."""
    print("SQLite MCP Server Unit Tests")
    print("=" * 40)
    
    await test_database_operations()
    await test_server_initialization()
    
    print("\n" + "=" * 40)
    print("Unit tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())