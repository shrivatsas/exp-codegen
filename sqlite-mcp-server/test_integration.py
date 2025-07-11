#!/usr/bin/env python3
"""Integration tests for the SQLite MCP Server."""

import asyncio
import json
import subprocess
import tempfile
import os
from pathlib import Path
import signal

from database import SQLiteDatabase

# Import MCP client for approach 2
try:
    from mcp.client import Client
    from mcp.client.stdio import stdio_client
    MCP_CLIENT_AVAILABLE = True
except ImportError:
    MCP_CLIENT_AVAILABLE = False
    print("Warning: MCP client library not available. Install with: pip install mcp")


async def test_mcp_protocol_direct():
    """Test MCP server using direct JSON-RPC protocol communication (Approach 1)."""
    print("Testing MCP Protocol - Direct JSON-RPC Communication...")
    
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    process = None
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
        
        # Wait for server to start
        await asyncio.sleep(1.5)
        
        # Test: Initialize connection
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
        
        # Read response with timeout
        try:
            response_line = await asyncio.wait_for(
                asyncio.create_task(asyncio.to_thread(process.stdout.readline)),
                timeout=5.0
            )
            if response_line:
                response = json.loads(response_line.strip())
                if "result" in response:
                    print("✓ Server initialized successfully")
                    print(f"  Protocol version: {response['result'].get('protocolVersion', 'unknown')}")
                else:
                    print(f"✗ Initialization failed: {response}")
            else:
                print("✗ No response received")
        except asyncio.TimeoutError:
            print("✗ Initialization timed out")
        
        print("Direct MCP protocol test completed!")
        
    except Exception as e:
        print(f"✗ Direct MCP protocol test failed: {e}")
        
    finally:
        # Clean up
        if process:
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
        
        # Use timeout for the entire client operation
        async with asyncio.timeout(10.0):
            async with stdio_client([
                "python", server_path
            ]) as (read_stream, write_stream):
                async with Client(read_stream, write_stream) as client:
                    # Initialize the client
                    await client.initialize()
                    print("✓ Client initialized successfully")
                    
                    # List available tools
                    tools_result = await client.list_tools()
                    tools = tools_result.tools
                    print(f"✓ Found {len(tools)} tools")
                    
                    # List resources
                    resources_result = await client.list_resources()
                    resources = resources_result.resources
                    print(f"✓ Found {len(resources)} resources")
                    
                    print("MCP client library test completed!")
                
    except asyncio.TimeoutError:
        print("✗ Client library test timed out")
    except Exception as e:
        print(f"✗ MCP client library test failed: {e}")
        
    finally:
        # Clean up
        os.unlink(db_path)


async def main():
    """Run integration tests."""
    print("SQLite MCP Server Integration Tests")
    print("=" * 50)
    
    await test_mcp_protocol_direct()
    await test_mcp_client_library()
    
    print("\n" + "=" * 50)
    print("Integration tests completed!")


if __name__ == "__main__":
    asyncio.run(main())