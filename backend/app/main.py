"""FastAPI backend for EA Analyzer web application."""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import sys
import logging
import traceback
from datetime import datetime

# Add the src directory to the path so we can import ea_analyzer modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

from ea_analyzer.neo4j_client import Neo4jClient
from ea_analyzer.env_config import get_config
from .api import diagrams, nodes, edges, queries
from .dependencies import get_neo4j_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("backend.log")],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting EA Analyzer API...")
    logger.info(f"Python path: {sys.path}")
    logger.info(f"Working directory: {os.getcwd()}")
    try:
        config = get_config()
        logger.info(f"Loaded configuration: {list(config.keys())}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        logger.error(traceback.format_exc())
    yield
    # Shutdown
    logger.info("Shutting down EA Analyzer API...")


app = FastAPI(
    title="EA Analyzer API",
    description="REST API for electrical diagram analysis and visualization",
    version="1.0.0",
    lifespan=lifespan,
)


# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")

    try:
        response = await call_next(request)
        process_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
        return response
    except Exception as e:
        process_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Request failed after {process_time:.3f}s: {str(e)}")
        logger.error(traceback.format_exc())
        raise


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://frontend:3000",
    ],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routers
app.include_router(diagrams.router, prefix="/api/diagrams", tags=["diagrams"])
app.include_router(nodes.router, prefix="/api/nodes", tags=["nodes"])
app.include_router(edges.router, prefix="/api/edges", tags=["edges"])
app.include_router(queries.router, prefix="/api/queries", tags=["queries"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "EA Analyzer API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.info("Health check requested")
    try:
        # Test Neo4j connection
        config = get_config()
        client = Neo4jClient(
            uri=config["neo4j_uri"],
            username=config["neo4j_username"],
            password=config["neo4j_password"],
            database=config["neo4j_database"],
        )
        client.connect()
        client.close()

        return {
            "status": "healthy",
            "neo4j": "connected",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "neo4j": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
