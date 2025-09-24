# EA Analyzer Backend

FastAPI backend for the EA Analyzer web application.

## Features

- REST API for electrical diagram data
- Neo4j integration
- Graph data visualization endpoints
- Custom query execution

## Development

```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
