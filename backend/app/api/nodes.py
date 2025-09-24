"""API routes for node operations."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import traceback

from ea_analyzer.neo4j_client import Neo4jClient
from ..dependencies import get_neo4j_client

logger = logging.getLogger(__name__)

router = APIRouter()


class NodeResponse(BaseModel):
    """Node response model."""

    id: str
    type: str
    name: Optional[str]
    properties: Dict[str, Any]


class NodeConnection(BaseModel):
    """Node connection response model."""

    node_id: str
    node_type: str
    node_name: Optional[str]
    relationship_type: str
    direction: str  # "incoming" or "outgoing"


@router.get("/", response_model=List[NodeResponse])
async def list_nodes(
    diagram_id: Optional[str] = Query(None, description="Filter by diagram ID"),
    node_type: Optional[str] = Query(None, description="Filter by node type"),
    client: Neo4jClient = Depends(get_neo4j_client),
):
    """List nodes with optional filtering."""
    try:
        # Build query based on filters
        where_clauses = []
        params = {}

        if diagram_id:
            where_clauses.append("n.diagram_id = $diagram_id")
            params["diagram_id"] = diagram_id

        if node_type:
            where_clauses.append("labels(n)[0] = $node_type")
            params["node_type"] = node_type

        where_clause = (
            " AND ".join(where_clauses)
            if where_clauses
            else "NOT n:Metadata AND NOT n:Ontology AND NOT n:Calculations"
        )

        query = f"""
            MATCH (n)
            WHERE {where_clause}
            RETURN n.id as id, 
                   labels(n)[0] as type, 
                   n.name as name,
                   n as properties
            ORDER BY n.name, n.id
        """

        result = client.query_diagram(query)

        return [
            NodeResponse(
                id=node["id"],
                type=node["type"],
                name=node.get("name"),
                properties=dict(node["properties"]),
            )
            for node in result
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list nodes: {str(e)}")


@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(node_id: str, client: Neo4jClient = Depends(get_neo4j_client)):
    """Get a specific node by ID."""
    try:
        result = client.query_diagram(
            f"MATCH (n {{id: '{node_id}'}}) WHERE NOT n:Metadata AND NOT n:Ontology AND NOT n:Calculations RETURN n.id as id, labels(n)[0] as type, n.name as name, n as properties"
        )

        if not result:
            raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")

        node = result[0]
        return NodeResponse(
            id=node["id"],
            type=node["type"],
            name=node.get("name"),
            properties=dict(node["properties"]),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get node: {str(e)}")


@router.get("/{node_id}/connections", response_model=List[NodeConnection])
async def get_node_connections(
    node_id: str, client: Neo4jClient = Depends(get_neo4j_client)
):
    """Get all connections for a specific node."""
    try:
        # Get outgoing connections
        outgoing_result = client.query_diagram(f"""
            MATCH (n {{id: '{node_id}'}})-[r]->(connected)
            WHERE NOT connected:Metadata AND NOT connected:Ontology AND NOT connected:Calculations
            RETURN connected.id as node_id,
                   labels(connected)[0] as node_type,
                   connected.name as node_name,
                   type(r) as relationship_type,
                   'outgoing' as direction
        """)

        # Get incoming connections
        incoming_result = client.query_diagram(f"""
            MATCH (connected)-[r]->(n {{id: '{node_id}'}})
            WHERE NOT connected:Metadata AND NOT connected:Ontology AND NOT connected:Calculations
            RETURN connected.id as node_id,
                   labels(connected)[0] as node_type,
                   connected.name as node_name,
                   type(r) as relationship_type,
                   'incoming' as direction
        """)

        connections = []
        for conn in outgoing_result + incoming_result:
            connections.append(
                NodeConnection(
                    node_id=conn["node_id"],
                    node_type=conn["node_type"],
                    node_name=conn.get("node_name"),
                    relationship_type=conn["relationship_type"],
                    direction=conn["direction"],
                )
            )

        return connections
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get node connections: {str(e)}"
        )


@router.get("/types/list", response_model=List[str])
async def list_node_types(client: Neo4jClient = Depends(get_neo4j_client)):
    """List all available node types."""
    try:
        result = client.query_diagram("""
            MATCH (n)
            WHERE NOT n:Metadata AND NOT n:Ontology AND NOT n:Calculations
            RETURN DISTINCT labels(n)[0] as node_type
            ORDER BY node_type
        """)

        return [node["node_type"] for node in result]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list node types: {str(e)}"
        )
