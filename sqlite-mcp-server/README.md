# SQLite MCP Server

A Model Context Protocol (MCP) server that provides safe, read-only access to SQLite databases. This server allows Large Language Models (LLMs) to explore database schemas, execute SELECT queries, and analyze data through the MCP protocol.

## Features

- **Safe Database Access**: Only allows read-only SELECT queries with built-in safety validation
- **Schema Exploration**: Provides complete database schema information as MCP resources
- **Table Data Access**: Allows querying individual tables with configurable limits
- **Sample Data Creation**: Can create sample data for demonstration purposes
- **Error Handling**: Comprehensive error handling with informative messages

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install mcp
```

## Usage

### Basic Usage

```bash
python -m sqlite_mcp_server.server --db-path ./my_database.db
```

### Create Sample Data

```bash
python -m sqlite_mcp_server.server --db-path ./demo.db --create-sample
```

### Command Line Options

- `--db-path`: Path to the SQLite database file (default: `./database.db`)
- `--create-sample`: Create sample data on startup

## MCP Resources

The server provides the following MCP resources:

- `sqlite://schema`: Complete database schema with table definitions
- `sqlite://table/{table_name}`: Data from individual tables (limited to 50 rows)

## MCP Tools

The server provides these tools for LLM interaction:

### `execute_query`
Execute a read-only SQL query on the database.

**Parameters:**
- `query` (string): The SQL query to execute (SELECT only)

**Example:**
```json
{
  "query": "SELECT * FROM users WHERE age > 25 LIMIT 10"
}
```

### `get_table_schema`
Get the schema for a specific table.

**Parameters:**
- `table_name` (string): The name of the table

**Example:**
```json
{
  "table_name": "users"
}
```

### `list_tables`
List all tables in the database.

**Parameters:** None

### `get_table_data`
Get data from a specific table with optional limit.

**Parameters:**
- `table_name` (string): The name of the table
- `limit` (integer, optional): Maximum number of rows to return (default: 100)

**Example:**
```json
{
  "table_name": "products",
  "limit": 25
}
```

### `create_sample_data`
Create sample data for demonstration purposes.

**Parameters:** None

## Safety Features

- **Query Validation**: Only SELECT queries are allowed
- **Pattern Detection**: Blocks dangerous SQL patterns (DROP, DELETE, UPDATE, etc.)
- **Table Name Sanitization**: Validates table names to prevent SQL injection
- **Row Limits**: Configurable limits to prevent excessive data retrieval
- **Error Handling**: Comprehensive error catching and reporting

## Sample Data

When using `--create-sample`, the server creates two sample tables:

### Users Table
- `id`: Primary key
- `name`: User name
- `email`: Unique email address
- `age`: User age
- `created_at`: Timestamp

### Products Table
- `id`: Primary key
- `name`: Product name
- `price`: Product price
- `category`: Product category
- `in_stock`: Boolean availability
- `created_at`: Timestamp

## Integration with MCP Clients

This server is designed to work with MCP-compatible clients. The server communicates via stdio using the MCP protocol, making it suitable for integration with various LLM applications and tools.

## Error Handling

The server includes comprehensive error handling:

- Invalid queries are rejected with descriptive error messages
- Database connection issues are handled gracefully
- Tool parameter validation ensures proper input
- All errors are logged for debugging purposes

## Development

The server is structured with separate modules:

- `database.py`: SQLite database operations and safety measures
- `server.py`: MCP server implementation and tool handlers
- `__init__.py`: Package initialization

## License

This project is provided as-is for educational and demonstration purposes.