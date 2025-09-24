"""API routes for edge/relationship operations."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import traceback

from ea_analyzer.neo4j_client import Neo4jClient
from ..dependencies import get_neo4j_client

logger = logging.getLogger(__name__)

router = APIRouter()


class EdgeResponse(BaseModel):
    """Edge response model."""

    id: str
    from_node: str
    to_node: str
    type: str
    properties: Dict[str, Any]


class EdgeTypeCount(BaseModel):
    """Edge type count response model."""

    type: str
    count: int


@router.get("/", response_model=List[EdgeResponse])
async def list_edges(
    diagram_id: Optional[str] = Query(None, description="Filter by diagram ID"),
    edge_type: Optional[str] = Query(None, description="Filter by edge type"),
    client: Neo4jClient = Depends(get_neo4j_client),
):
    """List edges with optional filtering."""
    try:
        # Build query based on filters
        where_clauses = []
        params = {}

        if diagram_id:
            where_clauses.append("r.diagram_id = $diagram_id")
            params["diagram_id"] = diagram_id

        if edge_type:
            where_clauses.append("type(r) = $edge_type")
            params["edge_type"] = edge_type

        where_clause = " AND ".join(where_clauses) if where_clauses else "true"

        query = f"""
            MATCH (from)-[r]->(to)
            WHERE {where_clause}
            RETURN from.id as from_node,
                   to.id as to_node,
                   type(r) as type,
                   r as properties
            ORDER BY type(r), from.id, to.id
        """

        result = client.query_diagram(query)

        edges = []
        for i, edge in enumerate(result):
            edges.append(
                EdgeResponse(
                    id=f"{edge['from_node']}-{edge['to_node']}-{i}",
                    from_node=edge["from_node"],
                    to_node=edge["to_node"],
                    type=edge["type"],
                    properties=dict(edge["properties"]),
                )
            )

        return edges
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list edges: {str(e)}")


@router.get("/types/list", response_model=List[EdgeTypeCount])
async def list_edge_types(client: Neo4jClient = Depends(get_neo4j_client)):
    """List all available edge types with counts."""
    try:
        result = client.query_diagram("""
            MATCH ()-[r]->()
            RETURN type(r) as type, count(r) as count
            ORDER BY count DESC, type
        """)

        return [
            EdgeTypeCount(type=edge["type"], count=edge["count"]) for edge in result
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list edge types: {str(e)}"
        )


@router.get("/protection-schemes", response_model=List[Dict[str, Any]])
async def get_protection_schemes(client: Neo4jClient = Depends(get_neo4j_client)):
    """Get all protection schemes and what they protect."""
    try:
        result = client.get_protection_schemes()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get protection schemes: {str(e)}"
        )


@router.get("/paths/{from_node_id}/{to_node_id}", response_model=List[List[str]])
async def get_paths(
    from_node_id: str,
    to_node_id: str,
    diagram_id: Optional[str] = Query(None, description="Filter by diagram ID"),
    client: Neo4jClient = Depends(get_neo4j_client),
):
    """Find electrical paths between two nodes."""
    try:
        paths = client.get_electrical_paths(from_node_id, to_node_id, diagram_id)
        return paths
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find paths: {str(e)}")
