"""Data models for electrical diagram parsing."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class NodeType(BaseModel):
    """Definition of a node type in the electrical diagram ontology."""

    attrs: list[str] = Field(description="List of attributes for this node type")


class EdgeType(BaseModel):
    """Definition of an edge type in the electrical diagram ontology."""

    attrs: list[str] = Field(description="List of attributes for this edge type")


class Ontology(BaseModel):
    """Ontology defining node and edge types for electrical diagrams."""

    node_types: dict[str, NodeType] = Field(description="Available node types")
    edge_types: dict[str, EdgeType] = Field(description="Available edge types")


class Node(BaseModel):
    """A node in the electrical diagram knowledge graph."""

    id: str = Field(description="Unique identifier for the node")
    type: str = Field(description="Type of the node")
    name: Optional[str] = Field(default=None, description="Human-readable name")
    # Additional attributes are stored as key-value pairs
    extra_attrs: dict[str, Any] = Field(
        default_factory=dict, description="Additional attributes"
    )

    model_config = {"extra": "allow"}


class Edge(BaseModel):
    """An edge in the electrical diagram knowledge graph."""

    from_: str = Field(alias="from", description="Source node ID")
    type: str = Field(description="Type of the edge")
    to: str = Field(description="Target node ID")
    via: Optional[str] = Field(default=None, description="Connection method")
    notes: Optional[str] = Field(default=None, description="Additional notes")
    # Additional attributes are stored as key-value pairs
    extra_attrs: dict[str, Any] = Field(
        default_factory=dict, description="Additional attributes"
    )

    model_config = {"extra": "allow", "populate_by_name": True}


class ShortCircuitCalculation(BaseModel):
    """Short circuit calculation results for a bus."""

    first_cycle_asym_ka: float = Field(
        description="First cycle asymmetrical short circuit current"
    )
    one_point_five_cycles_sym_ka: float = Field(
        description="1.5 cycle symmetrical short circuit current"
    )


class BreakerSpec(BaseModel):
    """Breaker specification details."""

    type: str = Field(description="Breaker type")
    kv_class: float = Field(description="Voltage class in kV")
    continuous_a: int = Field(description="Continuous current rating in amperes")
    interrupting_ka_range: str = Field(description="Interrupting capacity range")
    k_factor: float = Field(description="K factor")


class Calculations(BaseModel):
    """Calculations performed on the electrical diagram."""

    short_circuit: dict[str, Any] = Field(description="Short circuit calculations")
    breaker_spec: BreakerSpec = Field(description="Breaker specifications")


class ElectricalDiagram(BaseModel):
    """Complete electrical diagram knowledge graph."""

    metadata: dict[str, Any] = Field(description="Metadata about the diagram")
    ontology: Ontology = Field(description="Ontology definition")
    nodes: list[Node] = Field(description="List of nodes in the diagram")
    edges: list[Edge] = Field(description="List of edges in the diagram")
    calculations: Optional[Calculations] = Field(
        default=None, description="Calculations"
    )

    def get_nodes_by_type(self, node_type: str) -> list[Node]:
        """Get all nodes of a specific type."""
        return [node for node in self.nodes if node.type == node_type]

    def get_edges_by_type(self, edge_type: str) -> list[Edge]:
        """Get all edges of a specific type."""
        return [edge for edge in self.edges if edge.type == edge_type]

    def get_node_by_id(self, node_id: str) -> Optional[Node]:
        """Get a node by its ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_edges_from_node(self, node_id: str) -> list[Edge]:
        """Get all edges originating from a specific node."""
        return [edge for edge in self.edges if edge.from_ == node_id]

    def get_edges_to_node(self, node_id: str) -> list[Edge]:
        """Get all edges terminating at a specific node."""
        return [edge for edge in self.edges if edge.to == node_id]
