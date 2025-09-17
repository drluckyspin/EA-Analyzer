"""Tests for the electrical diagram parser."""

from pathlib import Path

import pytest

from ea_analyzer.models import ElectricalDiagram
from ea_analyzer.parser import ElectricalDiagramParser


def test_parse_sample_data():
    """Test parsing the sample electrical diagram data."""
    parser = ElectricalDiagramParser()

    # Load the sample data
    sample_file = Path("data/one-line-knowledge-graph.json")
    if not sample_file.exists():
        pytest.skip("Sample data file not found")

    diagram = parser.load_from_file(sample_file)

    # Basic checks
    assert isinstance(diagram, ElectricalDiagram)
    assert len(diagram.nodes) > 0
    assert len(diagram.edges) > 0
    assert diagram.metadata is not None
    assert diagram.ontology is not None

    # Check specific nodes exist
    node_ids = [node.id for node in diagram.nodes]
    assert "GS_A" in node_ids  # Grid Source A
    assert "TX1" in node_ids  # Transformer 1
    assert "BUS1" in node_ids  # Bus 1

    # Check specific edges exist
    edge_types = [edge.type for edge in diagram.edges]
    assert "CONNECTS_TO" in edge_types
    assert "PROTECTS" in edge_types
    assert "MEASURES" in edge_types


def test_get_nodes_by_type():
    """Test filtering nodes by type."""
    parser = ElectricalDiagramParser()
    sample_file = Path("data/one-line-knowledge-graph.json")

    if not sample_file.exists():
        pytest.skip("Sample data file not found")

    diagram = parser.load_from_file(sample_file)

    # Get all transformers
    transformers = diagram.get_nodes_by_type("Transformer")
    assert len(transformers) == 2
    assert all(node.type == "Transformer" for node in transformers)

    # Get all grid sources
    grid_sources = diagram.get_nodes_by_type("GridSource")
    assert len(grid_sources) == 2
    assert all(node.type == "GridSource" for node in grid_sources)


def test_get_edges_by_type():
    """Test filtering edges by type."""
    parser = ElectricalDiagramParser()
    sample_file = Path("data/one-line-knowledge-graph.json")

    if not sample_file.exists():
        pytest.skip("Sample data file not found")

    diagram = parser.load_from_file(sample_file)

    # Get all CONNECTS_TO edges
    connects_edges = diagram.get_edges_by_type("CONNECTS_TO")
    assert len(connects_edges) > 0
    assert all(edge.type == "CONNECTS_TO" for edge in connects_edges)

    # Get all PROTECTS edges
    protects_edges = diagram.get_edges_by_type("PROTECTS")
    assert len(protects_edges) > 0
    assert all(edge.type == "PROTECTS" for edge in protects_edges)


def test_get_node_by_id():
    """Test getting a node by ID."""
    parser = ElectricalDiagramParser()
    sample_file = Path("data/one-line-knowledge-graph.json")

    if not sample_file.exists():
        pytest.skip("Sample data file not found")

    diagram = parser.load_from_file(sample_file)

    # Test existing node
    tx1 = diagram.get_node_by_id("TX1")
    assert tx1 is not None
    assert tx1.id == "TX1"
    assert tx1.type == "Transformer"

    # Test non-existing node
    non_existing = diagram.get_node_by_id("NON_EXISTING")
    assert non_existing is None


def test_get_summary():
    """Test getting diagram summary."""
    parser = ElectricalDiagramParser()
    sample_file = Path("data/one-line-knowledge-graph.json")

    if not sample_file.exists():
        pytest.skip("Sample data file not found")

    parser.load_from_file(sample_file)
    summary = parser.get_summary()

    assert "total_nodes" in summary
    assert "total_edges" in summary
    assert "node_counts" in summary
    assert "edge_counts" in summary
    assert summary["total_nodes"] > 0
    assert summary["total_edges"] > 0
