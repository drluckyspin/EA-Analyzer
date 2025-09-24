"""Dependencies for FastAPI application."""

import logging
import traceback
from fastapi import HTTPException, Depends
from ea_analyzer.neo4j_client import Neo4jClient
from ea_analyzer.env_config import get_config

logger = logging.getLogger(__name__)


def get_neo4j_client() -> Neo4jClient:
    """Dependency to get Neo4j client."""
    logger.info("Creating Neo4j client...")
    try:
        config = get_config()
        logger.info(
            f"Neo4j config - URI: {config.get('neo4j_uri')}, Database: {config.get('neo4j_database')}"
        )

        client = Neo4jClient(
            uri=config["neo4j_uri"],
            username=config["neo4j_username"],
            password=config["neo4j_password"],
            database=config["neo4j_database"],
        )
        logger.info("Neo4j client created, attempting connection...")
        client.connect()
        logger.info("Neo4j connection successful")
        return client
    except Exception as e:
        logger.error(f"Failed to create/connect Neo4j client: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Failed to connect to Neo4j: {str(e)}"
        )
