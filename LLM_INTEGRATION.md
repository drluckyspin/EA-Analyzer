# LLM Integration for Electrical Diagram Analysis

This document describes the LLM-based image analysis functionality that has been integrated into the EA-Analyzer.

## Overview

The LLM integration allows you to analyze electrical diagram images using various Large Language Models (LLMs) with vision capabilities. The system supports multiple providers and automatically extracts structured data from one-line diagrams.

## Supported Providers

- **OpenAI**: GPT-4o, GPT-4o-mini, and other vision-capable models
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus, and other vision models
- **Google**: Gemini 2.0 Flash, Gemini 1.5 Pro, and other vision models

## Setup

### 1. Install Dependencies

The required LLM provider packages are automatically installed when you install the project:

```bash
# Install the project with all dependencies
uv sync

# Or install manually
pip install openai anthropic google-generativeai
```

### 2. Configure API Keys

Set up your API keys using environment variables. Create a `.env` file in the project root:

```bash
# Choose one or more providers
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Set default provider and model
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
```

### 3. Verify Installation

Test that everything is working:

```bash
./ea-analyzer-cli.sh check
```

## Usage

### Basic Image Analysis

Analyze an electrical diagram image and extract structured data:

```bash
# Basic analysis (uses default provider from config)
./ea-analyzer-cli.sh analyze substation.png

# Specify provider and model
./ea-analyzer-cli.sh analyze substation.png --provider openai --model gpt-4o-mini

# Save to specific output file
./ea-analyzer-cli.sh analyze substation.png --output my_diagram.json

# Analyze and immediately store in Neo4j
./ea-analyzer-cli.sh analyze substation.png --store
```

### Advanced Options

```bash
# Use Anthropic Claude
./ea-analyzer-cli.sh analyze substation.png \
  --provider anthropic \
  --model claude-3-5-sonnet-20241022 \
  --output claude_analysis.json

# Use Google Gemini
./ea-analyzer-cli.sh analyze substation.png \
  --provider gemini \
  --model gemini-2.0-flash-exp \
  --output gemini_analysis.json

# Analyze with custom API key
./ea-analyzer-cli.sh analyze substation.png \
  --provider openai \
  --api-key your_custom_key_here
```

### Programmatic Usage

You can also use the LLM analyzer directly in Python:

```python
from ea_analyzer.llm_analyzer import create_analyzer
from pathlib import Path

# Create analyzer
analyzer = create_analyzer(
    provider="openai",
    model="gpt-4o-mini",
    api_key="your-api-key"  # or None to use environment variable
)

# Analyze image
diagram = analyzer.analyze_image(Path("substation.png"))

# Access the structured data
print(f"Found {len(diagram.nodes)} nodes and {len(diagram.edges)} edges")
for node in diagram.nodes:
    print(f"Node: {node.id} ({node.type})")
```

## Output Format

The LLM analysis produces a structured JSON file with the following schema:

```json
{
  "metadata": {
    "title": "Diagram Title",
    "source_image": "path/to/image.png",
    "extracted_at": "2024-01-01T00:00:00Z"
  },
  "ontology": {
    "node_types": {...},
    "edge_types": {...}
  },
  "nodes": [
    {
      "id": "TX1",
      "type": "Transformer",
      "name": "Main Transformer",
      "hv_kv": 115,
      "lv_kv": 13.8,
      "mva_ratings": [25, 30]
    }
  ],
  "edges": [
    {
      "from": "GS_A",
      "to": "TX1",
      "type": "CONNECTS_TO",
      "via": "Cable"
    }
  ],
  "calculations": {
    "short_circuit": {...},
    "breaker_spec": {...}
  }
}
```

## Supported Node Types

- **GridSource**: Power grid sources
- **Transformer**: Power transformers
- **Breaker**: Circuit breakers and switches
- **Busbar**: Electrical busbars
- **RelayFunction**: Protection relays
- **Feeder**: Load feeders
- **CapacitorBank**: Power factor correction
- **Battery**: DC power sources
- **Meter**: Measurement devices
- **PotentialTransformer**: Voltage transformers
- **CurrentTransformer**: Current transformers
- **SurgeArrester**: Lightning protection

## Supported Edge Types

- **CONNECTS_TO**: Physical connections
- **PROTECTS**: Protection relationships
- **MEASURES**: Measurement relationships
- **CONTROLS**: Control relationships
- **POWERED_BY**: Power supply relationships
- **LOCATED_ON**: Physical location relationships

## Error Handling

The system provides comprehensive error handling:

- **Missing API Key**: Clear error message with instructions
- **Invalid Image**: File not found or unsupported format
- **LLM Errors**: Network issues, rate limits, or API errors
- **Invalid JSON**: Malformed response from LLM
- **Schema Validation**: Missing required fields in response

## Best Practices

1. **Image Quality**: Use high-resolution, clear images for best results
2. **File Formats**: Supported formats include PNG, JPG, JPEG, and SVG
3. **API Keys**: Store API keys securely in environment variables
4. **Rate Limits**: Be aware of provider rate limits for large batch processing
5. **Cost Management**: Monitor API usage and costs, especially with high-volume processing

## Troubleshooting

### Common Issues

1. **"API key not found"**: Set the appropriate environment variable
2. **"Image file not found"**: Check the file path and permissions
3. **"Model did not return valid JSON"**: The LLM response was malformed; try again
4. **Import errors**: Install the required provider packages

### Debug Mode

Enable verbose output for debugging:

```bash
./ea-analyzer-cli.sh analyze substation.png --verbose
```

### Provider-Specific Issues

- **OpenAI**: Ensure you have access to vision-capable models
- **Anthropic**: Check your API key permissions and model access
- **Google**: Verify your Google Cloud project and API enablement

## Integration with Existing Workflow

The LLM analysis integrates seamlessly with the existing EA-Analyzer workflow:

1. **Analyze**: Extract structured data from images
2. **Store**: Save to Neo4j database
3. **Query**: Use existing Cypher queries
4. **Visualize**: Generate diagrams and reports

```bash
# Complete workflow
./ea-analyzer-cli.sh analyze substation.png --store
./ea-analyzer-cli.sh neo4j summary
./ea-analyzer-cli.sh neo4j protection-schemes
```

This integration makes it easy to process electrical diagrams from images and incorporate them into your existing knowledge graph analysis workflow.
