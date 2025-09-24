"""Factory for creating database clients."""

from typing import List, Optional

from .base import DatabaseClient
from .neo4j_client import Neo4jClient


class DatabaseFactory:
    """Factory for creating database clients."""

    DATABASE_REGISTRY = {
        "neo4j": Neo4jClient,
        # "postgres": PostgresClient,  # Future
        # "mysql": MySQLClient,       # Future
        # "mongodb": MongoClient,      # Future
    }

    @staticmethod
    def create_client(
        db_type: str = "neo4j",
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: str = "neo4j",
    ) -> DatabaseClient:
        """Create database client based on type."""
        db_type_lower = db_type.lower()
        
        if db_type_lower not in DatabaseFactory.DATABASE_REGISTRY:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        client_class = DatabaseFactory.DATABASE_REGISTRY[db_type_lower]
        return client_class(uri, username, password, database)

    @staticmethod
    def get_supported_types() -> List[str]:
        """Get list of supported database types."""
        return list(DatabaseFactory.DATABASE_REGISTRY.keys())