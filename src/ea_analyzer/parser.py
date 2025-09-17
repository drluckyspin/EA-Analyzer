"""Parser for electrical diagram knowledge graphs."""

import json
from pathlib import Path
from typing import Any, Optional

from .models import Edge, ElectricalDiagram, Node


class ElectricalDiagramParser:
    """Parser for electrical diagram knowledge graphs from JSON files."""

    def __init__(self) -> None:
        self.diagram: Optional[ElectricalDiagram] = None

    def load_from_file(self, file_path: Path) -> ElectricalDiagram:
        """Load an electrical diagram from a JSON file."""
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        return self.parse_data(data)

    def parse_data(self, data: dict[str, Any]) -> ElectricalDiagram:
        """Parse electrical diagram data from a dictionary."""
        # Parse nodes
        nodes = []
        for node_data in data.get("nodes", []):
            # Create a copy to avoid modifying the original
            node_data_copy = node_data.copy()
            node_id = node_data_copy.pop("id")
            node_type = node_data_copy.pop("type")
            node_name = node_data_copy.pop("name", None)

            # All remaining data becomes extra attributes
            extra_attrs = node_data_copy

            node = Node(
                id=node_id, type=node_type, name=node_name, extra_attrs=extra_attrs
            )
            nodes.append(node)

        # Parse edges
        edges = []
        for edge_data in data.get("edges", []):
            # Create a copy to avoid modifying the original
            edge_data_copy = edge_data.copy()
            from_id = edge_data_copy.pop("from")
            edge_type = edge_data_copy.pop("type")
            to_id = edge_data_copy.pop("to")
            via = edge_data_copy.pop("via", None)
            notes = edge_data_copy.pop("notes", None)

            # All remaining data becomes extra attributes
            extra_attrs = edge_data_copy

            edge_data = {
                "from": from_id,
                "type": edge_type,
                "to": to_id,
                "via": via,
                "notes": notes,
                "extra_attrs": extra_attrs,
            }
            edge = Edge(**edge_data)
            edges.append(edge)

        # Create the diagram
        diagram = ElectricalDiagram(
            metadata=data.get("metadata", {}),
            ontology=data.get("ontology", {}),
            nodes=nodes,
            edges=edges,
            calculations=data.get("calculations"),
        )

        self.diagram = diagram
        return diagram

    def save_to_file(self, file_path: Path) -> None:
        """Save the current diagram to a JSON file."""
        if self.diagram is None:
            raise ValueError("No diagram loaded")

        # Convert back to dictionary format
        data: dict[str, Any] = {
            "metadata": self.diagram.metadata,
            "ontology": self.diagram.ontology.model_dump(),
            "nodes": [],
            "edges": [],
            "calculations": self.diagram.calculations.model_dump()
            if self.diagram.calculations
            else None,
        }

        # Convert nodes
        for node in self.diagram.nodes:
            node_data = {"id": node.id, "type": node.type, **node.extra_attrs}
            if node.name is not None:
                node_data["name"] = node.name
            data["nodes"].append(node_data)

        # Convert edges
        for edge in self.diagram.edges:
            edge_data = {
                "from": edge.from_,
                "type": edge.type,
                "to": edge.to,
                **edge.extra_attrs,
            }
            if edge.via is not None:
                edge_data["via"] = edge.via
            if edge.notes is not None:
                edge_data["notes"] = edge.notes
            data["edges"].append(edge_data)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the electrical diagram."""
        if self.diagram is None:
            return {"error": "No diagram loaded"}

        # Count nodes by type
        node_counts: dict[str, int] = {}
        for node in self.diagram.nodes:
            node_counts[node.type] = node_counts.get(node.type, 0) + 1

        # Count edges by type
        edge_counts: dict[str, int] = {}
        for edge in self.diagram.edges:
            edge_counts[edge.type] = edge_counts.get(edge.type, 0) + 1

        return {
            "metadata": self.diagram.metadata,
            "total_nodes": len(self.diagram.nodes),
            "total_edges": len(self.diagram.edges),
            "node_counts": node_counts,
            "edge_counts": edge_counts,
            "has_calculations": self.diagram.calculations is not None,
        }
