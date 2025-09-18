"""Graph visualization module for electrical diagrams."""

import os
from typing import Dict, List, Optional, Tuple, Any
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import networkx as nx
import numpy as np
from pathlib import Path

from .neo4j_client import Neo4jClient


class ElectricalGraphVisualizer:
    """Visualizer for electrical diagrams stored in Neo4j."""

    def __init__(self, neo4j_client: Neo4jClient):
        """Initialize the visualizer with a Neo4j client."""
        self.client = neo4j_client
        self.colors = {
            "GridSource": "#FF6B6B",  # Red
            "Transformer": "#4ECDC4",  # Teal
            "Breaker": "#45B7D1",  # Blue
            "Busbar": "#96CEB4",  # Green
            "Motor": "#FFEAA7",  # Yellow
            "RelayFunction": "#DDA0DD",  # Plum
            "Feeder": "#98D8C8",  # Mint
            "CapacitorBank": "#F7DC6F",  # Light Yellow
            "Battery": "#BB8FCE",  # Light Purple
            "default": "#95A5A6",  # Gray
        }

    def export_diagram_to_png(
        self,
        diagram_id: str,
        output_path: str,
        layout: str = "hierarchical",
        figsize: Tuple[int, int] = (16, 12),
        dpi: int = 300,
    ) -> str:
        """Export a diagram to PNG file.

        Args:
            diagram_id: The diagram ID to visualize
            output_path: Path for the output PNG file
            layout: Layout algorithm ('hierarchical', 'spring', 'circular')
            figsize: Figure size (width, height)
            dpi: DPI for the output image

        Returns:
            Path to the created PNG file
        """
        # Get diagram data from Neo4j
        nodes, edges = self._get_diagram_data(diagram_id)

        if not nodes:
            raise ValueError(f"No data found for diagram '{diagram_id}'")

        # Create NetworkX graph
        G = self._create_networkx_graph(nodes, edges)

        # Create visualization
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

        if layout == "hierarchical":
            pos = self._hierarchical_layout(G, nodes)
        elif layout == "spring":
            pos = nx.spring_layout(G, k=3, iterations=50)
        elif layout == "circular":
            pos = nx.circular_layout(G)
        else:
            pos = nx.spring_layout(G, k=3, iterations=50)

        # Draw the graph
        self._draw_graph(G, pos, ax, nodes)

        # Add title and metadata
        self._add_title_and_metadata(ax, diagram_id, nodes)

        # Save the figure
        plt.tight_layout()
        plt.savefig(
            output_path,
            dpi=dpi,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        plt.close()

        return output_path

    def _get_diagram_data(self, diagram_id: str) -> Tuple[List[Dict], List[Dict]]:
        """Get nodes and edges data for a specific diagram."""
        with self.client.driver.session(database=self.client.database) as session:
            # Get nodes
            nodes_result = session.run(
                """
                MATCH (n {diagram_id: $diagram_id})
                WHERE NOT n:Metadata AND NOT n:Ontology AND NOT n:Calculations
                RETURN n.id as id, labels(n)[0] as type, n.name as name, n
                ORDER BY labels(n)[0], n.name
                """,
                diagram_id=diagram_id,
            )
            nodes = [record.data() for record in nodes_result]

            # Get edges
            edges_result = session.run(
                """
                MATCH (from {diagram_id: $diagram_id})-[r {diagram_id: $diagram_id}]->(to {diagram_id: $diagram_id})
                RETURN from.id as from_id, type(r) as type, to.id as to_id, r.via as via, r.notes as notes
                """,
                diagram_id=diagram_id,
            )
            edges = [record.data() for record in edges_result]

        return nodes, edges

    def _create_networkx_graph(self, nodes: List[Dict], edges: List[Dict]) -> nx.Graph:
        """Create a NetworkX graph from nodes and edges data."""
        G = nx.Graph()

        # Add nodes
        for node in nodes:
            # Extract node properties, avoiding conflicts with NetworkX reserved attributes
            node_props = {}
            if "n" in node and isinstance(node["n"], dict):
                for key, value in node["n"].items():
                    if key not in ["id", "name", "type"]:  # Avoid conflicts
                        node_props[key] = value

            G.add_node(
                node["id"], node_type=node["type"], node_name=node["name"], **node_props
            )

        # Add edges
        for edge in edges:
            G.add_edge(
                edge["from_id"],
                edge["to_id"],
                edge_type=edge["type"],
                via=edge.get("via"),
                notes=edge.get("notes"),
            )

        return G

    def _hierarchical_layout(
        self, G: nx.Graph, nodes: List[Dict]
    ) -> Dict[str, Tuple[float, float]]:
        """Create a deterministic hierarchical layout optimized for electrical diagrams."""
        pos = {}

        # Group nodes by type for hierarchical positioning
        type_groups = {}
        for node in nodes:
            node_type = node["type"]
            if node_type not in type_groups:
                type_groups[node_type] = []
            type_groups[node_type].append(node["id"])

        # Sort all node lists to ensure deterministic ordering
        for node_type in type_groups:
            type_groups[node_type].sort()

        # Define hierarchy levels (top to bottom)
        hierarchy = [
            ["GridSource", "UtilitySource"],
            ["Transformer"],
            ["Busbar"],
            ["Breaker", "VB1_vacuum", "Molded_Case"],
            ["Motor", "Feeder"],
            ["RelayFunction", "ProtectiveRelay"],
            ["CapacitorBank", "Battery"],
        ]

        y_levels = {}
        for i, level_types in enumerate(hierarchy):
            y_levels[i] = len(hierarchy) - i  # Higher y for higher hierarchy

        # Position nodes deterministically
        current_x = 0
        for level, level_types in enumerate(hierarchy):
            level_nodes = []
            for node_type in level_types:
                if node_type in type_groups:
                    level_nodes.extend(type_groups[node_type])

            if level_nodes:
                # Sort level_nodes to ensure deterministic positioning
                level_nodes.sort()

                # Distribute nodes horizontally at this level
                x_positions = np.linspace(0, len(level_nodes) * 2, len(level_nodes))
                for i, node_id in enumerate(level_nodes):
                    pos[node_id] = (x_positions[i], y_levels[level])
                current_x = max(x_positions) + 2

        # Handle any remaining nodes not in hierarchy
        remaining_nodes = set(G.nodes()) - set(pos.keys())
        if remaining_nodes:
            remaining_nodes = sorted(list(remaining_nodes))  # Sort for determinism
            y_pos = 0.5
            x_positions = np.linspace(0, len(remaining_nodes) * 2, len(remaining_nodes))
            for i, node_id in enumerate(remaining_nodes):
                pos[node_id] = (x_positions[i], y_pos)

        return pos

    def _draw_graph(self, G: nx.Graph, pos: Dict, ax, nodes: List[Dict]) -> None:
        """Draw the graph with appropriate styling."""
        # Draw edges first (so they appear behind nodes)
        nx.draw_networkx_edges(
            G,
            pos,
            ax=ax,
            edge_color="#CCCCCC",
            width=1.5,
            alpha=0.7,
            arrows=True,
            arrowsize=20,
            arrowstyle="->",
        )

        # Draw nodes by type
        for node in nodes:
            node_id = node["id"]
            node_type = node["type"]
            color = self.colors.get(node_type, self.colors["default"])

            # Draw node
            nx.draw_networkx_nodes(
                G,
                pos,
                nodelist=[node_id],
                node_color=color,
                node_size=800,
                alpha=0.9,
                ax=ax,
            )

            # Add node label
            label = node.get("name") or node_id
            if len(label) > 15:
                label = label[:12] + "..."

            ax.annotate(
                label,
                xy=pos[node_id],
                xytext=(0, 15),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
            )

    def _add_title_and_metadata(self, ax, diagram_id: str, nodes: List[Dict]) -> None:
        """Add title and metadata to the plot."""
        # Get diagram metadata
        with self.client.driver.session(database=self.client.database) as session:
            metadata_result = session.run(
                """
                MATCH (m:Metadata {diagram_id: $diagram_id})
                RETURN m.title as title, m.extracted_at as extracted_at
                """,
                diagram_id=diagram_id,
            )
            metadata = metadata_result.single()

        if metadata:
            title = metadata["title"] or f"Diagram: {diagram_id}"
            ax.set_title(title, fontsize=16, fontweight="bold", pad=20)

            # Add metadata text
            info_text = f"Nodes: {len(nodes)} | Diagram ID: {diagram_id}"
            if metadata["extracted_at"]:
                info_text += f"\nExtracted: {metadata['extracted_at'][:10]}"

            ax.text(
                0.02,
                0.98,
                info_text,
                transform=ax.transAxes,
                fontsize=10,
                verticalalignment="top",
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8),
            )

        # Add legend
        self._add_legend(ax, nodes)

    def _add_legend(self, ax, nodes: List[Dict]) -> None:
        """Add a legend showing node types and colors."""
        # Get unique node types
        node_types = list(set(node["type"] for node in nodes))
        node_types.sort()

        # Create legend entries
        legend_elements = []
        for node_type in node_types[:8]:  # Limit to 8 types to avoid clutter
            color = self.colors.get(node_type, self.colors["default"])
            legend_elements.append(patches.Patch(color=color, label=node_type))

        if legend_elements:
            ax.legend(
                handles=legend_elements,
                loc="upper right",
                bbox_to_anchor=(0.98, 0.98),
                fontsize=9,
            )

    def get_available_layouts(self) -> List[str]:
        """Get list of available layout algorithms."""
        return ["hierarchical", "spring", "circular"]

    def get_node_type_colors(self) -> Dict[str, str]:
        """Get the color mapping for node types."""
        return self.colors.copy()
