"""API routes for diagram operations."""

import base64
import json
import logging
import shutil
import tempfile
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ea_analyzer.neo4j_client import Neo4jClient
from ea_analyzer.llm_analyzer import create_analyzer
from ea_analyzer.env_config import get_config
from ..dependencies import get_neo4j_client


def convert_pdf_to_image(pdf_path: Path) -> Path:
    """Convert PDF file to PNG image for LLM analysis.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Path to the converted PNG image

    Raises:
        HTTPException: If PDF conversion fails
    """
    try:
        from pdf2image import convert_from_path

        # Convert PDF to images (first page only)
        images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=300)

        if not images:
            raise HTTPException(
                status_code=400, detail="Failed to convert PDF: No pages found"
            )

        # Save first page as PNG
        image_path = pdf_path.parent / f"{pdf_path.stem}_converted.png"
        images[0].save(image_path, "PNG")

        logger.info(f"PDF converted to image: {image_path}")
        return image_path

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="PDF processing not available. pdf2image package not installed.",
        )
    except Exception as e:
        logger.error(f"PDF conversion failed: {str(e)}")
        raise HTTPException(
            status_code=400, detail=f"Failed to convert PDF to image: {str(e)}"
        )


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


class UploadResponse(BaseModel):
    """Response model for file upload."""

    upload_id: str
    filename: str
    file_size: int
    file_type: str
    message: str


class AnalysisProgress(BaseModel):
    """Progress update for analysis."""

    upload_id: str
    step: str
    progress: int  # 0-100
    message: str
    completed: bool = False
    error: Optional[str] = None


class AnalysisResult(BaseModel):
    """Result of LLM analysis."""

    upload_id: str
    diagram_data: Dict[str, Any]
    analysis_summary: Dict[str, Any]
    success: bool
    error: Optional[str] = None


class StorageResult(BaseModel):
    """Result of database storage."""

    upload_id: str
    diagram_id: str
    storage_summary: Dict[str, Any]
    success: bool
    error: Optional[str] = None


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
            RETURN DISTINCT n.id as id, 
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
            RETURN DISTINCT from.id as from, 
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


# File upload and analysis endpoints
@router.post("/upload", response_model=UploadResponse)
async def upload_diagram_file(file: UploadFile = File(...)):
    """Upload a diagram file (PDF or image) for analysis."""
    try:
        # Validate file type
        allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. Allowed types: PDF, PNG, JPG, JPEG",
            )

        # Validate file size (20MB limit)
        max_size = 20 * 1024 * 1024  # 20MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {len(file_content)} bytes. Maximum size: 20MB",
            )

        # Generate unique upload ID
        upload_id = str(uuid.uuid4())

        # Create temp directory for this upload
        temp_dir = Path(tempfile.gettempdir()) / "ea_analyzer_uploads" / upload_id
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Save file to temp directory with original filename
        original_filename = file.filename or "unknown"
        file_extension = (
            Path(original_filename).suffix if original_filename != "unknown" else ".tmp"
        )
        temp_file_path = temp_dir / original_filename

        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file_content)

        # Also save a copy with generic name for analysis
        generic_file_path = temp_dir / f"upload{file_extension}"
        with open(generic_file_path, "wb") as temp_file:
            temp_file.write(file_content)

        logger.info(
            f"File uploaded successfully: {original_filename} -> {temp_file_path}"
        )

        return UploadResponse(
            upload_id=upload_id,
            filename=original_filename,
            file_size=len(file_content),
            file_type=file.content_type,
            message="File uploaded successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload file: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_uploaded_file(upload_id: str = Form(...)):
    """Analyze an uploaded diagram file using LLM."""
    try:
        # Find the uploaded file
        temp_dir = Path(tempfile.gettempdir()) / "ea_analyzer_uploads" / upload_id
        if not temp_dir.exists():
            raise HTTPException(
                status_code=404, detail=f"Upload ID '{upload_id}' not found"
            )

        # Find the uploaded file
        uploaded_files = list(temp_dir.glob("upload.*"))
        if not uploaded_files:
            raise HTTPException(
                status_code=404, detail=f"No uploaded file found for ID '{upload_id}'"
            )

        file_path = uploaded_files[0]

        # Get LLM configuration
        config = get_config()
        llm_provider = config["llm_provider"]
        llm_model = config["llm_model"]
        llm_api_key = config.get(f"{llm_provider}_api_key")

        if not llm_api_key:
            raise HTTPException(
                status_code=500,
                detail=f"No API key found for provider '{llm_provider}'. Please configure the API key.",
            )

        # Convert PDF to image if needed
        if file_path.suffix.lower() == ".pdf":
            logger.info(f"Converting PDF to image for upload {upload_id}")
            converted_image_path = convert_pdf_to_image(file_path)
            analysis_file_path = converted_image_path
        else:
            analysis_file_path = file_path

        # Create analyzer
        analyzer = create_analyzer(
            provider=llm_provider, model=llm_model, api_key=llm_api_key
        )

        # Analyze the image
        logger.info(f"Starting LLM analysis for upload {upload_id}")
        diagram = analyzer.analyze_image(analysis_file_path)
        logger.info(f"LLM analysis completed for upload {upload_id}")

        # Convert diagram to dict
        diagram_data = diagram.model_dump()

        # Create analysis summary
        analysis_summary = {
            "total_nodes": len(diagram.nodes),
            "total_edges": len(diagram.edges),
            "has_calculations": diagram.calculations is not None,
            "node_types": list(set(node.type for node in diagram.nodes)),
            "edge_types": list(set(edge.type for edge in diagram.edges)),
            "title": diagram.metadata.get("title", "Unknown"),
            "analyzed_at": datetime.now().isoformat(),
        }

        return AnalysisResult(
            upload_id=upload_id,
            diagram_data=diagram_data,
            analysis_summary=analysis_summary,
            success=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze file {upload_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return AnalysisResult(
            upload_id=upload_id,
            diagram_data={},
            analysis_summary={},
            success=False,
            error=str(e),
        )


@router.post("/store", response_model=StorageResult)
async def store_analyzed_diagram(
    upload_id: str = Form(...),
    diagram_data: str = Form(...),  # JSON string
    client: Neo4jClient = Depends(get_neo4j_client),
):
    """Store an analyzed diagram in the database."""
    try:
        import json
        from ea_analyzer.models import ElectricalDiagram

        # Parse diagram data
        diagram_dict = json.loads(diagram_data)
        diagram = ElectricalDiagram(**diagram_dict)

        # Find the original uploaded file to store as Base64
        temp_dir = Path(tempfile.gettempdir()) / "ea_analyzer_uploads" / upload_id
        original_image_b64 = None

        if temp_dir.exists():
            uploaded_files = list(temp_dir.glob("upload.*"))
            if uploaded_files:
                file_path = uploaded_files[0]
                with open(file_path, "rb") as f:
                    file_content = f.read()
                    original_image_b64 = base64.b64encode(file_content).decode("utf-8")

        # Add original image to metadata
        if original_image_b64:
            diagram.metadata["original_image"] = original_image_b64

            # Find the original filename (not the generic upload.* file)
            original_file = None
            for file_path in uploaded_files:
                if not file_path.name.startswith("upload."):
                    original_file = file_path
                    break

            # If we still can't find it, try to get it from the upload response
            if not original_file:
                # Look for any file that's not upload.*
                all_files = list(temp_dir.glob("*"))
                for file_path in all_files:
                    if file_path.is_file() and not file_path.name.startswith("upload."):
                        original_file = file_path
                        break

            diagram.metadata["original_filename"] = (
                original_file.name if original_file else "unknown"
            )
            diagram.metadata["upload_timestamp"] = datetime.now().isoformat()

            logger.info(
                f"Original filename set to: {diagram.metadata['original_filename']}"
            )
            logger.info(
                f"Available files in temp dir: {[f.name for f in temp_dir.glob('*')]}"
            )

        # Store in database
        logger.info(f"Storing diagram for upload {upload_id}")
        result = client.store_diagram(diagram)
        logger.info(f"Diagram stored successfully for upload {upload_id}")

        # Clean up temp files
        if temp_dir.exists():
            import shutil

            shutil.rmtree(temp_dir)

        return StorageResult(
            upload_id=upload_id,
            diagram_id=result.get("diagram_id", "unknown"),
            storage_summary=result,
            success=True,
        )

    except Exception as e:
        logger.error(f"Failed to store diagram for upload {upload_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return StorageResult(
            upload_id=upload_id,
            diagram_id="",
            storage_summary={},
            success=False,
            error=str(e),
        )
