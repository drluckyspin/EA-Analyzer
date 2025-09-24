"""API routes for custom queries."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
import logging
import traceback

from ea_analyzer.neo4j_client import Neo4jClient
from ..dependencies import get_neo4j_client

logger = logging.getLogger(__name__)

router = APIRouter()


class QueryRequest(BaseModel):
    """Custom query request model."""

    query: str
    parameters: Dict[str, Any] = {}


class QueryResponse(BaseModel):
    """Query response model."""

    results: List[Dict[str, Any]]
    count: int


@router.post("/execute", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest, client: Neo4jClient = Depends(get_neo4j_client)
):
    """Execute a custom Cypher query."""
    try:
        # Basic security check - prevent dangerous operations
        dangerous_keywords = [
            "DROP",
            "DELETE",
            "CREATE",
            "MERGE",
            "SET",
            "REMOVE",
            "CALL",
            "LOAD",
            "USING",
            "PERIODIC",
            "COMMIT",
        ]

        query_upper = request.query.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise HTTPException(
                    status_code=400,
                    detail=f"Query contains potentially dangerous keyword: {keyword}. Only SELECT/MATCH queries are allowed.",
                )

        # Execute the query
        results = client.query_diagram(request.query)

        return QueryResponse(results=results, count=len(results))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to execute query: {str(e)}"
        )


@router.get("/examples", response_model=List[Dict[str, str]])
async def get_query_examples():
    """Get example queries for common operations."""
    return [
        {
            "name": "Find all transformers",
            "description": "Get all transformer nodes in the system",
            "query": "MATCH (n:Transformer) RETURN n.id, n.name, n.mva_ratings",
        },
        {
            "name": "Find protection relationships",
            "description": "Get all protection schemes",
            "query": "MATCH (r:RelayFunction)-[p:PROTECTS]->(protected) RETURN r.device_code, protected.name, p.notes",
        },
        {
            "name": "Find connected components",
            "description": "Get all nodes connected to a specific bus",
            "query": "MATCH (bus:Busbar {id: 'BUS1'})-[r]-(connected) RETURN connected.id, connected.name, type(r)",
        },
        {
            "name": "Count nodes by type",
            "description": "Get count of each node type",
            "query": "MATCH (n) WHERE NOT n:Metadata AND NOT n:Ontology AND NOT n:Calculations RETURN labels(n)[0] as type, count(n) as count ORDER BY count DESC",
        },
        {
            "name": "Find electrical paths",
            "description": "Find paths between two specific nodes",
            "query": "MATCH path = (start {id: 'SOURCE1'})-[*]-(end {id: 'LOAD1'}) RETURN [node in nodes(path) | node.id] as path LIMIT 5",
        },
    ]
