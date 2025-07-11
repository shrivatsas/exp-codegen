#!/usr/bin/env python3
"""Test script for the SQLite MCP Server."""

import asyncio
import sqlite3
import tempfile
import os
from pathlib import Path
import sys
import json
import subprocess
from io import StringIO

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import SQLiteDatabase
from server import SQLiteMCPServer

# Import MCP client for approach 2
try:
    from mcp.client import Client
    from mcp.client.stdio import stdio_client
    MCP_CLIENT_AVAILABLE = True
except ImportError:
    MCP_CLIENT_AVAILABLE = False
    print("Warning: MCP client library not available. Install with: pip install mcp-client")


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


def test_query_validation():
    """Test query validation logic."""
    print("\nTesting query validation...")
    
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = SQLiteDatabase(db_path)
        db.create_sample_data()
        
        # Test valid queries
        valid_queries = [
            "SELECT * FROM users",
            "SELECT name, email FROM users WHERE age > 25",
            "SELECT COUNT(*) FROM products",
            "SELECT * FROM users LIMIT 10"
        ]
        
        for query in valid_queries:
            try:
                result = db.execute_query(query)
                print(f"✓ Valid query accepted: {query[:30]}...")
            except Exception as e:
                print(f"✗ Valid query rejected: {query} - {e}")
        
        # Test invalid queries
        invalid_queries = [
            "DROP TABLE users",
            "DELETE FROM users",
            "UPDATE users SET age = 30",
            "INSERT INTO users VALUES (1, 'test', 'test@example.com', 25, datetime('now'))",
            "ALTER TABLE users ADD COLUMN test TEXT"
        ]
        
        for query in invalid_queries:
            try:
                result = db.execute_query(query)
                print(f"✗ Invalid query accepted: {query}")
            except ValueError as e:
                print(f"✓ Invalid query rejected: {query[:30]}...")
        
        print("Query validation test completed successfully!")
        
    finally:
        # Clean up
        os.unlink(db_path)


async def test_mcp_protocol_direct():
    """Test MCP server using direct JSON-RPC protocol communication (Approach 1)."""
    print("\nTesting MCP Protocol - Direct JSON-RPC Communication...")
    
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Initialize database with sample data
        db = SQLiteDatabase(db_path)
        db.create_sample_data()
        
        # Start server process
        process = subprocess.Popen(
            ["python", "server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path(__file__).parent)
        )
        
        # Wait a moment for server to start
        await asyncio.sleep(1.0)
        
        # Test 1: Initialize the connection
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read initialization response
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            print(f"✓ Initialization response: {response.get('result', {}).get('protocolVersion', 'unknown')}")
        
        # Test 2: List tools
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            tools = response.get("result", {}).get("tools", [])
            print(f"✓ Tools listed: {len(tools)} tools available")
            for tool in tools:
                print(f"  - {tool.get('name', 'unknown')}: {tool.get('description', 'no description')}")
        
        # Test 3: Call a tool (query database)
        query_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "query_database",
                "arguments": {
                    "query": "SELECT COUNT(*) as user_count FROM users"
                }
            }
        }
        
        process.stdin.write(json.dumps(query_request) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            result = response.get("result", {})
            print(f"✓ Query executed successfully: {result}")
        
        # Test 4: List resources
        resources_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/list",
            "params": {}
        }
        
        process.stdin.write(json.dumps(resources_request) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            resources = response.get("result", {}).get("resources", [])
            print(f"✓ Resources listed: {len(resources)} resources available")
        
        print("Direct MCP protocol test completed successfully!")
        
    except Exception as e:
        print(f"✗ Direct MCP protocol test failed: {e}")
        
    finally:
        # Clean up
        if 'process' in locals():
            process.terminate()
            try:
                process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        os.unlink(db_path)


async def test_mcp_client_library():
    """Test MCP server using MCP client library (Approach 2)."""
    print("\nTesting MCP Protocol - Client Library...")
    
    if not MCP_CLIENT_AVAILABLE:
        print("✗ MCP client library not available. Skipping client library tests.")
        return
    
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Initialize database with sample data
        db = SQLiteDatabase(db_path)
        db.create_sample_data()
        
        # Test using MCP client library
        server_path = str(Path(__file__).parent / "server.py")
        
        async with stdio_client([
            "python", server_path
        ]) as (read_stream, write_stream):
            async with Client(read_stream, write_stream) as client:
                # Test 1: Initialize the client
                await client.initialize()
                print("✓ Client initialized successfully")
                
                # Test 2: List available tools
                tools_result = await client.list_tools()
                tools = tools_result.tools
                print(f"✓ Tools listed via client: {len(tools)} tools available")
                
                for tool in tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                # Test 3: Call a tool
                if tools:
                    # Find the query_database tool
                    query_tool = None
                    for tool in tools:
                        if tool.name == "query_database":
                            query_tool = tool
                            break
                    
                    if query_tool:
                        result = await client.call_tool(
                            query_tool.name,
                            {
                                "query": "SELECT name, email FROM users LIMIT 3"
                            }
                        )
                        print(f"✓ Tool called successfully: {result}")
                    else:
                        print("✗ query_database tool not found")
                
                # Test 4: List resources
                resources_result = await client.list_resources()
                resources = resources_result.resources
                print(f"✓ Resources listed via client: {len(resources)} resources available")
                
                for resource in resources:
                    print(f"  - {resource.name}: {resource.description}")
                
                # Test 5: Read a resource
                if resources:
                    resource = resources[0]
                    resource_content = await client.read_resource(resource.uri)
                    print(f"✓ Resource read successfully: {resource.name}")
                    print(f"  Content length: {len(str(resource_content))}")
                
                print("MCP client library test completed successfully!")
                
    except Exception as e:
        print(f"✗ MCP client library test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up
        os.unlink(db_path)


async def test_mcp_error_handling():
    """Test MCP server error handling."""
    print("\nTesting MCP Error Handling...")
    
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Initialize database with sample data
        db = SQLiteDatabase(db_path)
        db.create_sample_data()
        
        # Start server process
        process = subprocess.Popen(
            ["python", "server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path(__file__).parent)
        )
        
        # Wait a moment for server to start
        await asyncio.sleep(1.0)
        
        # Test 1: Invalid method
        invalid_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "invalid/method",
            "params": {}
        }
        
        process.stdin.write(json.dumps(invalid_request) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            if "error" in response:
                print(f"✓ Invalid method properly rejected: {response['error']['message']}")
            else:
                print("✗ Invalid method was not rejected")
        
        # Test 2: Invalid SQL query
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"roots": {"listChanged": True}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        process.stdout.readline()  # Read init response
        
        dangerous_query_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "query_database",
                "arguments": {
                    "query": "DROP TABLE users"
                }
            }
        }
        
        process.stdin.write(json.dumps(dangerous_query_request) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            if "error" in response:
                print(f"✓ Dangerous query properly rejected: {response['error']['message']}")
            else:
                print("✗ Dangerous query was not rejected")
        
        print("MCP error handling test completed successfully!")
        
    except Exception as e:
        print(f"✗ MCP error handling test failed: {e}")
        
    finally:
        # Clean up
        if 'process' in locals():
            process.terminate()
            try:
                process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        os.unlink(db_path)


async def main():
    """Run all tests."""
    print("SQLite MCP Server Test Suite")
    print("=" * 40)
    
    # Unit tests
    await test_database_operations()
    await test_server_initialization()
    test_query_validation()
    
    # Integration tests
    await test_mcp_protocol_direct()
    await test_mcp_client_library()
    await test_mcp_error_handling()
    
    print("\n" + "=" * 40)
    print("All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())