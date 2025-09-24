"""Environment configuration loader for EA-Analyzer."""

import os
from pathlib import Path
from typing import Optional


def load_env_file(env_file: Optional[Path] = None) -> None:
    """Load environment variables from .env file.

    Args:
        env_file: Path to .env file. If None, looks for .env in project root.
    """
    if env_file is None:
        # Look for .env file in project root
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env"

    if not env_file.exists():
        return

    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Parse KEY=VALUE pairs
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                # Set environment variable if not already set
                if key not in os.environ:
                    os.environ[key] = value


def get_config() -> dict[str, str]:
    """Get configuration values from environment variables.

    Returns:
        Dictionary of configuration values with defaults.
    """
    # Load .env file if it exists
    load_env_file()

    return {
        "data_file": os.getenv("DATA_FILE", "data/one-line-knowledge-graph.json"),
        # Database configuration with backward compatibility
        "db_type": os.getenv("DB_TYPE", os.getenv("NEO4J_TYPE", "neo4j")),
        "db_uri": os.getenv("DB_URI", os.getenv("NEO4J_URI", "bolt://localhost:7687")),
        "db_username": os.getenv("DB_USERNAME", os.getenv("NEO4J_USERNAME", "neo4j")),
        "db_password": os.getenv("DB_PASSWORD", os.getenv("NEO4J_PASSWORD", "password")),
        "db_database": os.getenv("DB_DATABASE", os.getenv("NEO4J_DATABASE", "neo4j")),
        # Legacy Neo4j variables for backward compatibility
        "neo4j_uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "neo4j_username": os.getenv("NEO4J_USERNAME", "neo4j"),
        "neo4j_password": os.getenv("NEO4J_PASSWORD", "password"),
        "neo4j_database": os.getenv("NEO4J_DATABASE", "neo4j"),
        "use_colors": os.getenv("USE_COLORS", "true").lower() == "true",
        "verbose_output": os.getenv("VERBOSE_OUTPUT", "false").lower() == "true",
        # LLM Configuration
        "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
        "llm_model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        "google_api_key": os.getenv("GOOGLE_API_KEY"),
    }


def get_example_queries() -> list[str]:
    """Get example queries from environment variables.

    Returns:
        List of example Cypher queries.
    """
    load_env_file()

    queries_str = os.getenv("EXAMPLE_QUERIES", "")
    if not queries_str:
        return []

    # Split by semicolon and clean up
    queries = [q.strip() for q in queries_str.split(";") if q.strip()]
    return queries
