"""SQLite MCP Server implementation."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from pathlib import Path

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.server.lowlevel import NotificationOptions
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

from database import SQLiteDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLiteMCPServer:
    """SQLite MCP Server that provides database access through MCP protocol."""
    
    def __init__(self, db_path: str):
        """Initialize the SQLite MCP Server.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.database = SQLiteDatabase(db_path)
        self.server = Server("sqlite-mcp-server")
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Set up MCP server handlers."""
        
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List available resources (database schema and tables)."""
            resources = []
            
            # Add database schema resource
            resources.append(
                Resource(
                    uri="sqlite://schema",
                    name="Database Schema",
                    description="Complete database schema with table definitions",
                    mimeType="application/json"
                )
            )
            
            # Add individual table resources
            try:
                schema = self.database.get_schema()
                for table in schema:
                    resources.append(
                        Resource(
                            uri=f"sqlite://table/{table['name']}",
                            name=f"Table: {table['name']}",
                            description=f"Data from the {table['name']} table",
                            mimeType="application/json"
                        )
                    )
            except Exception as e:
                logger.error(f"Error getting schema: {e}")
            
            return resources
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a specific resource by URI."""
            try:
                if uri == "sqlite://schema":
                    schema = self.database.get_schema()
                    return json.dumps(schema, indent=2)
                
                elif uri.startswith("sqlite://table/"):
                    table_name = uri.split("/")[-1]
                    data = self.database.get_table_data(table_name, limit=50)
                    return json.dumps(data, indent=2)
                
                else:
                    raise ValueError(f"Unknown resource URI: {uri}")
            
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                return json.dumps({"error": str(e)})
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="execute_query",
                    description="Execute a read-only SQL query on the database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The SQL query to execute (SELECT only)"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_table_schema",
                    description="Get the schema for a specific table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "The name of the table to get schema for"
                            }
                        },
                        "required": ["table_name"]
                    }
                ),
                Tool(
                    name="list_tables",
                    description="List all tables in the database",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_table_data",
                    description="Get data from a specific table with optional limit",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "The name of the table to get data from"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of rows to return (default: 100)",
                                "default": 100
                            }
                        },
                        "required": ["table_name"]
                    }
                ),
                Tool(
                    name="create_sample_data",
                    description="Create sample data for demonstration purposes",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            try:
                if name == "execute_query":
                    query = arguments.get("query", "")
                    if not query:
                        raise ValueError("Query is required")
                    
                    results = self.database.execute_query(query)
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(results, indent=2, default=str)
                        )
                    ]
                
                elif name == "get_table_schema":
                    table_name = arguments.get("table_name", "")
                    if not table_name:
                        raise ValueError("Table name is required")
                    
                    schema = self.database.get_schema()
                    table_schema = next(
                        (table for table in schema if table['name'] == table_name), 
                        None
                    )
                    
                    if not table_schema:
                        raise ValueError(f"Table '{table_name}' not found")
                    
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(table_schema, indent=2)
                        )
                    ]
                
                elif name == "list_tables":
                    schema = self.database.get_schema()
                    table_names = [table['name'] for table in schema]
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(table_names, indent=2)
                        )
                    ]
                
                elif name == "get_table_data":
                    table_name = arguments.get("table_name", "")
                    limit = arguments.get("limit", 100)
                    
                    if not table_name:
                        raise ValueError("Table name is required")
                    
                    data = self.database.get_table_data(table_name, limit)
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(data, indent=2, default=str)
                        )
                    ]
                
                elif name == "create_sample_data":
                    self.database.create_sample_data()
                    return [
                        TextContent(
                            type="text",
                            text="Sample data created successfully"
                        )
                    ]
                
                else:
                    raise ValueError(f"Unknown tool: {name}")
            
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [
                    TextContent(
                        type="text",
                        text=f"Error: {str(e)}"
                    )
                ]
    
    async def run(self) -> None:
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="sqlite-mcp-server",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities=None
                    )
                )
            )


def main() -> None:
    """Main entry point for the SQLite MCP Server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SQLite MCP Server")
    parser.add_argument(
        "--db-path",
        default="./database.db",
        help="Path to the SQLite database file (default: ./database.db)"
    )
    parser.add_argument(
        "--create-sample",
        action="store_true",
        help="Create sample data on startup"
    )
    
    args = parser.parse_args()
    
    # Create server instance
    server = SQLiteMCPServer(args.db_path)
    
    # Create sample data if requested
    if args.create_sample:
        server.database.create_sample_data()
        logger.info("Sample data created")
    
    # Run the server
    logger.info(f"Starting SQLite MCP Server with database: {args.db_path}")
    asyncio.run(server.run())


if __name__ == "__main__":
    main()