"""API routes for diagram operations."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import traceback

from ea_analyzer.neo4j_client import Neo4jClient
from ..dependencies import get_neo4j_client

logger = logging.getLogger(__name__)

router = APIRouter()


class DiagramSummary(BaseModel):
    """Diagram summary response model."""

    diagram_id: str
    title: str
    extracted_at: str
    index: int


class DiagramDetail(BaseModel):
    """Detailed diagram response model."""

    diagram_id: str
    title: str
    extracted_at: str
    node_counts: Dict[str, int]
    relationship_counts: Dict[str, int]
    total_nodes: int
    total_relationships: int
    metadata: Dict[str, Any]


class GraphData(BaseModel):
    """Graph data for visualization."""

    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@router.get("/", response_model=List[DiagramSummary])
async def list_diagrams(client: Neo4jClient = Depends(get_neo4j_client)):
    """List all available diagrams."""
    logger.info("Starting list_diagrams request")
    try:
        logger.info("Calling client.list_diagrams()")
        diagrams = client.list_diagrams()
        logger.info(f"Retrieved {len(diagrams)} diagrams from Neo4j")

        result = [
            DiagramSummary(
                diagram_id=diagram["diagram_id"],
                title=diagram.get("title", "Unknown"),
                extracted_at=diagram.get("extracted_at", ""),
                index=diagram["index"],
            )
            for diagram in diagrams
        ]
        logger.info(f"Successfully processed {len(result)} diagrams")
        return result
    except Exception as e:
        logger.error(f"Failed to list diagrams: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Failed to list diagrams: {str(e)}"
        )


@router.get("/{diagram_id}/summary", response_model=DiagramDetail)
async def get_diagram_summary(
    diagram_id: str, client: Neo4jClient = Depends(get_neo4j_client)
):
    """Get detailed summary of a specific diagram."""
    try:
        summary = client.get_diagram_summary_by_id(diagram_id)
        if not summary:
            raise HTTPException(
                status_code=404, detail=f"Diagram '{diagram_id}' not found"
            )

        return DiagramDetail(
            diagram_id=summary["diagram_id"],
            title=summary["metadata"].get("title", "Unknown"),
            extracted_at=summary["metadata"].get("extracted_at", ""),
            node_counts=summary["node_counts"],
            relationship_counts=summary["relationship_counts"],
            total_nodes=summary["total_nodes"],
            total_relationships=summary["total_relationships"],
            metadata=summary["metadata"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get diagram summary: {str(e)}"
        )


@router.get("/{diagram_id}/graph", response_model=GraphData)
async def get_diagram_graph(
    diagram_id: str, client: Neo4jClient = Depends(get_neo4j_client)
):
    """Get graph data for visualization."""
    logger.info(f"Starting get_diagram_graph request for diagram_id: {diagram_id}")
    try:
        # Get nodes
        logger.info("Querying nodes from Neo4j")
        nodes_query = f"""
            MATCH (n {{diagram_id: '{diagram_id}'}})
            WHERE NOT n:Metadata AND NOT n:Ontology AND NOT n:Calculations
            RETURN n.id as id, 
                   labels(n)[0] as type, 
                   n.name as name,
                   n as properties
        """
        logger.info(f"Nodes query: {nodes_query}")
        nodes_result = client.query_diagram(nodes_query)
        logger.info(f"Retrieved {len(nodes_result)} nodes")

        # Get edges
        logger.info("Querying edges from Neo4j")
        edges_query = f"""
            MATCH (from {{diagram_id: '{diagram_id}'}})-[r]->(to {{diagram_id: '{diagram_id}'}})
            RETURN from.id as from, 
                   to.id as to, 
                   type(r) as type,
                   r as properties
        """
        logger.info(f"Edges query: {edges_query}")
        edges_result = client.query_diagram(edges_query)
        logger.info(f"Retrieved {len(edges_result)} edges")

        # Get metadata
        logger.info("Querying metadata from Neo4j")
        metadata_query = f"""
            MATCH (m:Metadata {{diagram_id: '{diagram_id}'}})
            RETURN m
        """
        logger.info(f"Metadata query: {metadata_query}")
        metadata_result = client.query_diagram(metadata_query)
        logger.info(f"Retrieved {len(metadata_result)} metadata records")

        # Transform nodes for React Flow
        logger.info("Transforming nodes for React Flow")
        nodes = []
        for i, node in enumerate(nodes_result):
            try:
                # Debug logging for specific nodes
                if node["id"] in ["CAP1", "BAT", "R_50_51F"]:
                    logger.info(
                        f"Processing node {node['id']}: name={node.get('name')}, type={node['type']}"
                    )

                # Create a better label by using name, description, or device_code as fallbacks
                node_name = node.get("name")
                if not node_name:
                    # Try to use description for relay functions
                    if node["type"] == "RelayFunction":
                        node_name = node.get("description", node["id"])
                    # Try to use purpose for other components
                    elif node.get("purpose"):
                        node_name = f"{node['type']} - {node.get('purpose')}"
                    else:
                        node_name = node["id"]

                node_data = {
                    "id": node["id"],
                    "type": node["type"],
                    "data": {
                        "label": node_name,
                        "type": node["type"],
                        "properties": dict(node["properties"]),
                    },
                    "position": {
                        "x": 0,
                        "y": 0,
                    },  # Will be positioned by layout algorithm
                }
                nodes.append(node_data)
            except Exception as node_error:
                logger.error(f"Error processing node {i}: {node_error}")
                logger.error(f"Node data: {node}")
                raise

        # Transform edges for React Flow
        logger.info("Transforming edges for React Flow")
        edges = []
        for i, edge in enumerate(edges_result):
            try:
                # Handle edge properties - they might be a tuple or dict
                edge_properties = edge["properties"]
                if isinstance(edge_properties, tuple):
                    # If it's a tuple, convert to dict or use empty dict
                    edge_properties = {}
                elif not isinstance(edge_properties, dict):
                    # If it's not a dict, try to convert or use empty dict
                    try:
                        edge_properties = dict(edge_properties)
                    except (ValueError, TypeError):
                        edge_properties = {}

                edge_data = {
                    "id": f"{edge['from']}-{edge['to']}",
                    "source": edge["from"],
                    "target": edge["to"],
                    "type": edge["type"],
                    "data": {
                        "type": edge["type"],
                        "properties": edge_properties,
                    },
                }
                edges.append(edge_data)
            except Exception as edge_error:
                logger.error(f"Error processing edge {i}: {edge_error}")
                logger.error(f"Edge data: {edge}")
                raise

        metadata = dict(metadata_result[0]["m"]) if metadata_result else {}
        logger.info(
            f"Successfully processed graph data: {len(nodes)} nodes, {len(edges)} edges"
        )

        return GraphData(nodes=nodes, edges=edges, metadata=metadata)
    except Exception as e:
        logger.error(f"Failed to get graph data for diagram {diagram_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Failed to get graph data: {str(e)}"
        )


@router.delete("/{diagram_id}")
async def delete_diagram(
    diagram_id: str, client: Neo4jClient = Depends(get_neo4j_client)
):
    """Delete a specific diagram."""
    try:
        result = client.delete_diagram(diagram_id)
        return {
            "message": f"Diagram '{diagram_id}' deleted successfully",
            "deleted": result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete diagram: {str(e)}"
        )
