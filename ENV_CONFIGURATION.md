# Environment Configuration Guide

## Overview

The EA-Analyzer project now uses `.env` files for configuration management instead of the previous `.conf` file. This provides better integration with Docker Compose and follows standard practices for environment variable management.

## Files

### `.env` - Main Configuration File

- **Purpose**: Contains all configuration values for the project
- **Location**: Project root directory
- **Usage**: Automatically loaded by Makefile, CLI scripts, and Python code

### `.env.example` - Configuration Template

- **Purpose**: Template file showing all available configuration options
- **Usage**: Copy to `.env` and customize as needed
- **Version Control**: Included in repository as a reference

## Configuration Variables

### Data Configuration

```bash
# Path to the default data file
DATA_FILE=data/one-line-knowledge-graph.json
```

### Neo4j Configuration

```bash
# Neo4j connection settings
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
```

### Docker Configuration

```bash
# Docker Compose service configuration
NEO4J_CONTAINER_NAME=ea-analyzer-neo4j
NEO4J_IMAGE=neo4j:5.15-community
NEO4J_HTTP_PORT=7474
NEO4J_BOLT_PORT=7687
```

### Output Configuration

```bash
# Display settings
USE_COLORS=true
VERBOSE_OUTPUT=false
```

### Example Queries

```bash
# Custom example queries (semicolon-separated)
EXAMPLE_QUERIES="MATCH (t:Transformer) RETURN t.id, t.name, t.hv_kv, t.lv_kv ORDER BY t.id;MATCH (b:Breaker) RETURN b.id, b.name, b.kv_class, b.continuous_a ORDER BY b.id"
```

## Usage

### 1. **Automatic Loading**

The configuration is automatically loaded by:

- **Makefile**: Uses `include .env` to load variables
- **CLI Script**: Uses `source .env` to load variables
- **Python Code**: Uses `env_config.py` module to load variables

### 2. **Priority Order**

Configuration values are resolved in this order:

1. Command-line arguments (highest priority)
2. Environment variables from `.env` file
3. Default values (lowest priority)

### 3. **Docker Compose Integration**

Docker Compose automatically uses environment variables:

```yaml
services:
  neo4j:
    image: ${NEO4J_IMAGE:-neo4j:5.15-community}
    container_name: ${NEO4J_CONTAINER_NAME:-ea-analyzer-neo4j}
    ports:
      - "${NEO4J_HTTP_PORT:-7474}:7474"
      - "${NEO4J_BOLT_PORT:-7687}:7687"
```

## Examples

### Basic Setup

```bash
# Copy template
cp .env.example .env

# Edit configuration
nano .env

# Run with custom configuration
make run
```

### Custom Neo4j Server

```bash
# .env file
NEO4J_URI=bolt://production-server:7687
NEO4J_USERNAME=admin
NEO4J_PASSWORD=secure_password
NEO4J_DATABASE=electrical_diagrams

# Use custom server
make neo4j-store
```

### Custom Data File

```bash
# .env file
DATA_FILE=/path/to/custom-diagram.json

# Use custom data
make run
```

### Custom Example Queries

```bash
# .env file
EXAMPLE_QUERIES="MATCH (n) RETURN n LIMIT 5;MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 10"

# Run examples with custom queries
./ea-analyzer-cli.sh examples
```

## Environment-Specific Configuration

### Development

```bash
# .env.development
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=dev_password
VERBOSE_OUTPUT=true
```

### Production

```bash
# .env.production
NEO4J_URI=bolt://prod-neo4j:7687
NEO4J_USERNAME=prod_user
NEO4J_PASSWORD=secure_prod_password
NEO4J_DATABASE=production
```

### Testing

```bash
# .env.testing
NEO4J_URI=bolt://localhost:7687
NEO4J_DATABASE=test
NEO4J_PASSWORD=test_password
```

## Integration Points

### 1. **Makefile Integration**

```makefile
# Load environment variables from .env file
ifneq (,$(wildcard .env))
    include .env
    export
endif

# Use variables with defaults
NEO4J_URI ?= bolt://localhost:7687
```

### 2. **CLI Script Integration**

```bash
# Load environment variables
load_env() {
    if [ -f ".env" ]; then
        set -a
        source .env
        set +a
    fi
}
```

### 3. **Python Integration**

```python
from ea_analyzer.env_config import get_config, get_example_queries

# Get configuration
config = get_config()
neo4j_uri = config["neo4j_uri"]

# Get example queries
queries = get_example_queries()
```

## Security Considerations

### 1. **File Permissions**

```bash
# Restrict .env file permissions
chmod 600 .env
```

### 2. **Version Control**

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
echo ".env.*.local" >> .gitignore
```

### 3. **Sensitive Data**

- Never commit `.env` files with sensitive data
- Use `.env.example` for non-sensitive defaults
- Use environment-specific files for sensitive data

## Troubleshooting

### Common Issues

1. **Variables Not Loading**

   ```bash
   # Check file exists and is readable
   ls -la .env

   # Check syntax
   cat .env
   ```

2. **Docker Compose Not Using Variables**

   ```bash
   # Ensure variables are exported
   export $(cat .env | xargs)

   # Or use env_file in docker-compose.yml
   ```

3. **Python Not Loading Variables**
   ```python
   # Ensure env_config.py is imported
   from ea_analyzer.env_config import load_env_file
   load_env_file()
   ```

### Debug Mode

```bash
# Enable verbose output
echo "VERBOSE_OUTPUT=true" >> .env

# Check loaded variables
./ea-analyzer-cli.sh check
```

## Best Practices

1. **Use .env.example**: Always provide a template file
2. **Document Variables**: Include comments explaining each variable
3. **Use Defaults**: Provide sensible defaults for all variables
4. **Validate Input**: Check variable values in scripts
5. **Environment Separation**: Use different files for different environments
6. **Security First**: Never commit sensitive data to version control

This environment configuration system provides a flexible, secure, and maintainable way to manage all aspects of the EA-Analyzer project configuration.
