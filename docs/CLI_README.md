# EA-Analyzer CLI

A modern Python-based command-line interface for the Electrical Assembly Analyzer with Neo4j integration, built with Typer and Rich.

## Features

- **Modern Python CLI**: Built with Typer for excellent user experience
- **Rich Output**: Beautiful tables, panels, and colored output with Rich
- **Docker Compose Integration**: Neo4j runs automatically via Docker Compose
- **Data Management**: Store and query electrical diagrams in Neo4j
- **Analysis Tools**: Built-in protection scheme analysis and custom queries
- **Automatic Validation**: Comprehensive input validation with helpful error messages
- **Type Safety**: Full type hints and automatic type checking
- **Configuration**: Flexible configuration via environment variables or command-line options

## Prerequisites

- **Docker and Docker Compose**: Required for Neo4j database
- **Python 3.9+**: Required for the CLI application
- **uv package manager**: For dependency management

## Quick Start

### 1. Make the script executable

```bash
chmod +x ea-analyzer-cli.sh
```

### 2. Check prerequisites

```bash
./ea-analyzer-cli.sh check
```

### 3. Run the complete demo

```bash
./ea-analyzer-cli.sh demo
```

### 4. Direct Python CLI (Alternative)

You can also use the Python CLI directly:

```bash
uv run -m ea_analyzer.typer_cli check
uv run -m ea_analyzer.typer_cli summary
uv run -m ea_analyzer.typer_cli --help
```

## Commands

### System Commands

#### `check`

Check prerequisites and system status

```bash
./ea-analyzer-cli.sh check
```

### Data Commands

#### `summary`

Show diagram summary from JSON file

```bash
./ea-analyzer-cli.sh summary
./ea-analyzer-cli.sh summary path/to/custom.json
```

#### `store`

Store diagram in Neo4j database

```bash
./ea-analyzer-cli.sh store
./ea-analyzer-cli.sh store --clear
./ea-analyzer-cli.sh store path/to/custom.json
```

### Neo4j Commands (via Docker Compose)

All Neo4j commands automatically start the Neo4j Docker container if it's not running.

#### `neo4j ping`

Check if Neo4j is running and accessible

```bash
./ea-analyzer-cli.sh neo4j ping
```

#### `neo4j summary`

Show summary of data stored in Neo4j

```bash
./ea-analyzer-cli.sh neo4j summary
```

#### `neo4j protection-schemes`

Show protection schemes analysis

```bash
./ea-analyzer-cli.sh neo4j protection-schemes
```

#### `neo4j query QUERY`

Run custom Cypher query

```bash
./ea-analyzer-cli.sh neo4j query "MATCH (t:Transformer) RETURN t.name, t.hv_kv, t.lv_kv"
```

### Analysis Commands

#### `examples`

Run predefined example queries

```bash
./ea-analyzer-cli.sh examples
```

#### `demo`

Run complete demo (store data, run examples)

```bash
./ea-analyzer-cli.sh demo
```

## Configuration

### Environment Variables

Set these environment variables to customize the behavior:

```bash
export DATA_FILE="path/to/your/data.json"
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="your_password"
export NEO4J_DATABASE="neo4j"
```

### Environment File

Create a `.env` file in your project directory:

```bash
# .env file
DATA_FILE=data/one-line-knowledge-graph.json
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
```

### Command Line Options

Override settings using command line options:

```bash
./ea-analyzer-cli.sh --data-file custom-data.json store
./ea-analyzer-cli.sh --neo4j-uri bolt://remote-server:7687 neo4j summary
```

### Advanced Usage

For more advanced usage, you can use the Python CLI directly with full Typer features:

```bash
# Get detailed help for any command
uv run -m ea_analyzer.typer_cli --help
uv run -m ea_analyzer.typer_cli neo4j --help
uv run -m ea_analyzer.typer_cli store --help

# Use with custom options
uv run -m ea_analyzer.typer_cli --data-file custom.json --verbose summary
uv run -m ea_analyzer.typer_cli --neo4j-uri bolt://remote:7687 neo4j query "MATCH (n) RETURN n LIMIT 5"
```

## Example Workflows

### 1. Complete Analysis Workflow

```bash
# Check system (includes Docker check)
./ea-analyzer-cli.sh check

# Test Neo4j connection (starts Docker container if needed)
./ea-analyzer-cli.sh neo4j ping

# Show data summary
./ea-analyzer-cli.sh summary

# Store data in Neo4j (starts Docker container if needed)
./ea-analyzer-cli.sh store

# Analyze protection schemes
./ea-analyzer-cli.sh neo4j protection-schemes

# Run custom queries
./ea-analyzer-cli.sh neo4j query "MATCH (n:Transformer) RETURN n.name, n.hv_kv, n.lv_kv"
```

### 2. Quick Demo

```bash
# Run everything automatically
./ea-analyzer-cli.sh demo
```

### 3. Custom Data Analysis

```bash
# Use custom data file
./ea-analyzer-cli.sh --data-file my-diagram.json store

# Query specific components
./ea-analyzer-cli.sh neo4j query "MATCH (b:Breaker) WHERE b.kv_class > 10 RETURN b.name, b.kv_class"
```

### 4. Advanced Python CLI Usage

```bash
# Get detailed help
uv run -m ea_analyzer.typer_cli --help
uv run -m ea_analyzer.typer_cli neo4j --help

# Use with verbose output
uv run -m ea_analyzer.typer_cli --verbose summary

# Custom Neo4j connection
uv run -m ea_analyzer.typer_cli --neo4j-uri bolt://remote:7687 neo4j summary
```

## Example Queries

The CLI includes several built-in example queries:

### Transformers

```cypher
MATCH (t:Transformer) RETURN t.id, t.name, t.hv_kv, t.lv_kv ORDER BY t.id
```

### Breakers

```cypher
MATCH (b:Breaker) RETURN b.id, b.name, b.kv_class, b.continuous_a ORDER BY b.id
```

### Protection Schemes

```cypher
MATCH (r:RelayFunction)-[rel:PROTECTS]->(p)
RETURN r.device_code, r.description, p.name, p.type ORDER BY r.device_code
```

### Bus Connections

```cypher
MATCH (bus:Busbar)-[r:CONNECTS_TO]-(comp)
RETURN bus.name, comp.type, comp.name, r.via ORDER BY bus.name, comp.type
```

### Power Sources

```cypher
MATCH (n) WHERE n:GridSource OR n:Transformer
RETURN n.type, n.name, n.kv ORDER BY n.type, n.name
```

## Troubleshooting

### Common Issues

1. **Neo4j Connection Failed**

   ```bash
   # Check if Docker and Neo4j are running
   ./ea-analyzer-cli.sh check

   # Test Neo4j connection (starts Docker container if needed)
   ./ea-analyzer-cli.sh neo4j ping

   # Start services manually if needed
   make start

   # Use custom Neo4j URI
   ./ea-analyzer-cli.sh --neo4j-uri bolt://your-neo4j-server:7687 neo4j ping
   ```

2. **Data File Not Found**

   ```bash
   # Check if data file exists
   ls -la data/one-line-knowledge-graph.json

   # Use custom data file
   ./ea-analyzer-cli.sh --data-file /path/to/your/data.json summary
   ```

3. **Invalid JSON File**

   ```bash
   # Validate JSON file
   python3 -m json.tool your-file.json

   # The CLI will show helpful error messages for invalid JSON
   ./ea-analyzer-cli.sh --data-file invalid.json summary
   ```

4. **Permission Denied**

   ```bash
   # Make script executable
   chmod +x ea-analyzer-cli.sh
   ```

5. **Missing Dependencies**

   ```bash
   # Install dependencies
   uv sync

   # Check prerequisites
   ./ea-analyzer-cli.sh check
   ```

### Debug Mode

Enable verbose output using the `--verbose` flag:

```bash
./ea-analyzer-cli.sh --verbose summary
uv run -m ea_analyzer.typer_cli --verbose summary
```

### Getting Help

The CLI provides comprehensive help for all commands:

```bash
# General help
./ea-analyzer-cli.sh --help

# Help for specific commands
uv run -m ea_analyzer.typer_cli summary --help
uv run -m ea_analyzer.typer_cli neo4j --help
uv run -m ea_analyzer.typer_cli store --help
```

## Integration with Other Tools

### Neo4j Browser

After storing data, you can explore it in Neo4j Browser:

- URL: http://localhost:7474
- Username: neo4j
- Password: password

### Python Scripts

The CLI can be integrated into Python scripts:

```python
import subprocess

# Run CLI commands from Python
result = subprocess.run(['./ea-analyzer-cli.sh', 'neo4j', 'summary'],
                       capture_output=True, text=True)
print(result.stdout)
```

### CI/CD Pipelines

Use the CLI in automated workflows:

```yaml
# GitHub Actions example
- name: Analyze Electrical Diagram
  run: |
    ./ea-analyzer-cli.sh check
    ./ea-analyzer-cli.sh start-neo4j
    ./ea-analyzer-cli.sh store
    ./ea-analyzer-cli.sh protection
```

## Advanced Usage

### Custom Query Files

Create query files for complex analysis:

```bash
# Create query file
cat > transformer_analysis.cypher << EOF
MATCH (t:Transformer)
OPTIONAL MATCH (t)-[r:CONNECTS_TO]-(connected)
RETURN t.name, t.hv_kv, t.lv_kv,
       collect(connected.name) as connections
ORDER BY t.name
EOF

# Run query from file
./ea-analyzer-cli.sh query "$(cat transformer_analysis.cypher)"
```

### Batch Processing

Process multiple data files:

```bash
for file in data/*.json; do
    echo "Processing $file"
    ./ea-analyzer-cli.sh --data-file "$file" store
done
```

### Monitoring

Monitor Neo4j status:

```bash
# Check if Neo4j is running
docker ps | grep neo4j-ea-analyzer

# View Neo4j logs
docker logs neo4j-ea-analyzer
```

## Contributing

To add new commands or features to the CLI:

1. Add new command function to `src/ea_analyzer/typer_cli.py`
2. Update the bash wrapper if needed
3. Update this README with documentation
4. Test with various data files and configurations

## License

This CLI is part of the EA-Analyzer project and follows the same MIT license.
