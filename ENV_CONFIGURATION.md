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

### LLM Configuration

```bash
# LLM Provider API Keys (set only the one you use)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# LLM Provider Settings
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
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

### LLM Image Analysis

```bash
# .env file with OpenAI configuration
OPENAI_API_KEY=sk-proj-your-actual-api-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

# Analyze electrical diagram images
./ea-analyzer-cli.sh analyze substation.png
```

### Multiple LLM Providers

```bash
# .env file with multiple providers
OPENAI_API_KEY=sk-proj-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GOOGLE_API_KEY=your-google-api-key

# Use specific provider
./ea-analyzer-cli.sh analyze substation.png --provider anthropic --model claude-3-5-sonnet-20241022
```

## Environment-Specific Configuration

### Development

```bash
# .env.development
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=dev_password
VERBOSE_OUTPUT=true

# LLM Configuration for development
OPENAI_API_KEY=sk-proj-dev-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
```

### Production

```bash
# .env.production
NEO4J_URI=bolt://prod-neo4j:7687
NEO4J_USERNAME=prod_user
NEO4J_PASSWORD=secure_prod_password
NEO4J_DATABASE=production

# LLM Configuration for production
OPENAI_API_KEY=sk-proj-prod-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
```

### Testing

```bash
# .env.testing
NEO4J_URI=bolt://localhost:7687
NEO4J_DATABASE=test
NEO4J_PASSWORD=test_password

# LLM Configuration for testing (optional)
# OPENAI_API_KEY=sk-proj-test-key-here
# LLM_PROVIDER=openai
# LLM_MODEL=gpt-4o-mini
```

## LLM Configuration Details

### Supported Providers

| Provider  | Environment Variable | Default Model                | Description                                  |
| --------- | -------------------- | ---------------------------- | -------------------------------------------- |
| OpenAI    | `OPENAI_API_KEY`     | `gpt-4o-mini`                | GPT-4o, GPT-4o-mini, and other vision models |
| Anthropic | `ANTHROPIC_API_KEY`  | `claude-3-5-sonnet-20241022` | Claude 3.5 Sonnet, Claude 3 Opus             |
| Google    | `GOOGLE_API_KEY`     | `gemini-2.0-flash-exp`       | Gemini 2.0, Gemini 1.5 Pro                   |

### Model Configuration

```bash
# Set default provider and model
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

# Override via command line
./ea-analyzer-cli.sh analyze image.png --provider anthropic --model claude-3-5-sonnet-20241022
```

### API Key Management

```bash
# Single provider setup
OPENAI_API_KEY=sk-proj-your-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

# Multiple providers setup
OPENAI_API_KEY=sk-proj-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GOOGLE_API_KEY=your-google-api-key

# Use any provider
./ea-analyzer-cli.sh analyze image.png --provider anthropic
```

### Security Best Practices

```bash
# Restrict API key file permissions
chmod 600 .env

# Use environment-specific files
cp .env.example .env.production
# Edit .env.production with production keys

# Never commit API keys to version control
echo ".env" >> .gitignore
echo ".env.*" >> .gitignore
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

4. **LLM API Key Issues**

   ```bash
   # Check API key is set
   echo $OPENAI_API_KEY

   # Test LLM configuration
   ./ea-analyzer-cli.sh analyze --help

   # Check specific provider
   ./ea-analyzer-cli.sh analyze image.png --provider openai --api-key your-key
   ```

5. **LLM Provider Not Found**

   ```bash
   # Check provider name (case-sensitive)
   LLM_PROVIDER=openai  # not OpenAI

   # Check model name
   LLM_MODEL=gpt-4o-mini  # not gpt-4o-mini-vision
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
7. **LLM API Key Security**:
   - Use different API keys for different environments
   - Monitor API usage and costs
   - Rotate keys regularly
   - Use least-privilege access
8. **Provider Selection**: Choose the most cost-effective provider for your use case
9. **Model Selection**: Use appropriate models for your accuracy vs. cost requirements
10. **Error Handling**: Implement proper error handling for API failures and rate limits

## Complete .env Template

```bash
# EA-Analyzer Environment Configuration
# Copy this file to .env and update with your actual values

# Data file path
DATA_FILE=data/one-line-knowledge-graph.json

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j

# LLM Provider API Keys (set only the one you use)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

# Display Configuration
USE_COLORS=true
VERBOSE_OUTPUT=false

# Example Queries (optional)
EXAMPLE_QUERIES="MATCH (n:Transformer) RETURN n.name;MATCH (b:Breaker) RETURN b.id, b.name"
```

This environment configuration system provides a flexible, secure, and maintainable way to manage all aspects of the EA-Analyzer project configuration, including the new LLM integration features.
