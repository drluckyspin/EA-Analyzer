"""Neo4j client for storing electrical diagram knowledge graphs."""

import os
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

from .models import Edge, ElectricalDiagram, Node


class Neo4jClient:
    """Client for storing electrical diagram data in Neo4j."""

    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: str = "neo4j",
    ) -> None:
        """Initialize the Neo4j client.

        Args:
            uri: Neo4j connection URI (defaults to NEO4J_URI env var or bolt://localhost:7687)
            username: Username (defaults to NEO4J_USERNAME env var or 'neo4j')
            password: Password (defaults to NEO4J_PASSWORD env var or 'password')
            database: Database name (defaults to 'neo4j')
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.database = database

        self.driver = None

    def connect(self) -> None:
        """Establish connection to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, auth=(self.username, self.password)
            )
            # Test the connection
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1")
        except ServiceUnavailable as e:
            raise ConnectionError(f"Could not connect to Neo4j at {self.uri}: {e}")

    def close(self) -> None:
        """Close the Neo4j connection."""
        if self.driver:
            self.driver.close()

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def clear_database(self) -> None:
        """Clear all nodes and relationships from the database."""
        with self.driver.session(database=self.database) as session:
            session.run("MATCH (n) DETACH DELETE n")

    def store_diagram(
        self, diagram: ElectricalDiagram, diagram_id: Optional[str] = None
    ) -> Dict[str, int]:
        """Store an electrical diagram in Neo4j with partitioning support.

        Args:
            diagram: The electrical diagram to store
            diagram_id: Unique identifier for the diagram (defaults to metadata title)

        Returns:
            Dictionary with counts of created nodes and relationships
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")

        # Generate diagram_id from metadata if not provided
        if diagram_id is None:
            import datetime

            base_id = diagram.metadata.get("title", "unknown_diagram")
            # Sanitize base_id for Neo4j
            base_id = (
                base_id.lower()
                .replace(" ", "_")
                .replace("-", "_")
                .replace("(", "")
                .replace(")", "")
                .replace("/", "_")
                .replace("\\", "_")
            )
            # Add timestamp to make it unique
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            diagram_id = f"{base_id}_{timestamp}"

        node_count = 0
        edge_count = 0

        with self.driver.session(database=self.database) as session:
            # Store metadata as a special node with diagram_id
            metadata_data = diagram.metadata.copy()
            metadata_data["diagram_id"] = diagram_id

            metadata_node = session.run(
                """
                CREATE (m:Metadata {diagram_id: $diagram_id})
                SET m += $metadata
                RETURN m
                """,
                diagram_id=diagram_id,
                metadata=metadata_data,
            ).single()

            # Store ontology information as JSON strings with diagram_id
            import json

            def convert_to_dict(obj):
                if hasattr(obj, "model_dump"):
                    return obj.model_dump()
                elif isinstance(obj, dict):
                    return {k: convert_to_dict(v) for k, v in obj.items()}
                else:
                    return obj

            node_types_data = convert_to_dict(diagram.ontology.node_types)
            edge_types_data = convert_to_dict(diagram.ontology.edge_types)

            ontology_node = session.run(
                """
                CREATE (o:Ontology {diagram_id: $diagram_id})
                SET o.node_types = $node_types,
                    o.edge_types = $edge_types
                RETURN o
                """,
                diagram_id=diagram_id,
                node_types=json.dumps(node_types_data),
                edge_types=json.dumps(edge_types_data),
            ).single()

            # Store nodes with diagram_id
            for node in diagram.nodes:
                self._create_node(session, node, diagram_id)
                node_count += 1

            # Store edges/relationships with diagram_id
            for edge in diagram.edges:
                self._create_relationship(session, edge, diagram_id)
                edge_count += 1

            # Store calculations if present with diagram_id
            if diagram.calculations:
                self._store_calculations(session, diagram.calculations, diagram_id)

        return {
            "nodes_created": node_count,
            "relationships_created": edge_count,
            "metadata_stored": 1,
            "ontology_stored": 1,
            "calculations_stored": 1 if diagram.calculations else 0,
            "diagram_id": diagram_id,
        }

    def _create_node(self, session, node: Node, diagram_id: str) -> None:
        """Create a single node in Neo4j with diagram partitioning."""
        # Prepare properties
        properties = {
            "id": node.id,
            "name": node.name,
            "diagram_id": diagram_id,
            **node.extra_attrs,
        }

        # Remove None values
        properties = {k: v for k, v in properties.items() if v is not None}

        # Sanitize node type for Neo4j label (replace spaces and special chars)
        sanitized_type = (
            node.type.replace(" ", "_")
            .replace("-", "_")
            .replace("(", "")
            .replace(")", "")
        )

        # Create the node with its type as a label
        session.run(
            f"""
            CREATE (n:{sanitized_type} {{diagram_id: $diagram_id}})
            SET n += $properties
            """,
            diagram_id=diagram_id,
            properties=properties,
        )

    def _create_relationship(self, session, edge: Edge, diagram_id: str) -> None:
        """Create a relationship between two nodes in Neo4j with diagram partitioning."""
        # Prepare relationship properties
        properties = {
            "via": edge.via,
            "notes": edge.notes,
            "diagram_id": diagram_id,
            **edge.extra_attrs,
        }

        # Remove None values
        properties = {k: v for k, v in properties.items() if v is not None}

        # Create the relationship
        session.run(
            f"""
            MATCH (from {{id: $from_id, diagram_id: $diagram_id}})
            MATCH (to {{id: $to_id, diagram_id: $diagram_id}})
            CREATE (from)-[r:{edge.type} $properties]->(to)
            """,
            from_id=edge.from_,
            to_id=edge.to,
            diagram_id=diagram_id,
            properties=properties,
        )

    def _store_calculations(self, session, calculations, diagram_id: str) -> None:
        """Store calculation results in Neo4j with diagram partitioning."""
        import json

        # Convert calculations to JSON strings
        short_circuit_data = calculations.short_circuit
        breaker_spec_data = calculations.breaker_spec

        if hasattr(breaker_spec_data, "model_dump"):
            breaker_spec_data = breaker_spec_data.model_dump()

        session.run(
            """
            CREATE (c:Calculations {diagram_id: $diagram_id})
            SET c.short_circuit = $short_circuit,
                c.breaker_spec = $breaker_spec
            """,
            diagram_id=diagram_id,
            short_circuit=json.dumps(short_circuit_data),
            breaker_spec=json.dumps(breaker_spec_data),
        )

    def get_diagram_summary(self, diagram_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a summary of the stored diagram data.

        Args:
            diagram_id: Optional diagram ID to filter by. If None, shows all diagrams.

        Returns:
            Dictionary with diagram summary data
        """
        with self.driver.session(database=self.database) as session:
            if diagram_id:
                # Get summary for specific diagram
                return self.get_diagram_summary_by_id(diagram_id)
            else:
                # Get summary for all diagrams combined
                # Get node counts by type
                node_counts = session.run(
                    """
                    MATCH (n)
                    WHERE NOT n:Metadata AND NOT n:Ontology AND NOT n:Calculations
                    RETURN labels(n)[0] as node_type, count(n) as count
                    ORDER BY count DESC
                    """
                ).data()

                # Get relationship counts by type
                rel_counts = session.run(
                    """
                    MATCH ()-[r]->()
                    RETURN type(r) as rel_type, count(r) as count
                    ORDER BY count DESC
                    """
                ).data()

                # Get metadata (most recent)
                metadata = session.run(
                    """
                    MATCH (m:Metadata)
                    RETURN m
                    ORDER BY m.extracted_at DESC
                    LIMIT 1
                    """
                ).single()

                return {
                    "node_counts": {
                        item["node_type"]: item["count"] for item in node_counts
                    },
                    "relationship_counts": {
                        item["rel_type"]: item["count"] for item in rel_counts
                    },
                    "metadata": dict(metadata["m"]) if metadata else {},
                    "total_nodes": sum(item["count"] for item in node_counts),
                    "total_relationships": sum(item["count"] for item in rel_counts),
                }

    def query_diagram(self, cypher_query: str) -> List[Dict[str, Any]]:
        """Execute a custom Cypher query on the diagram data.

        Args:
            cypher_query: The Cypher query to execute

        Returns:
            List of query results
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(cypher_query)
            return [record.data() for record in result]

    def find_connected_components(self) -> List[List[str]]:
        """Find all connected components in the electrical diagram."""
        with self.driver.session(database=self.database) as session:
            result = session.run(
                """
                MATCH (n)
                WHERE NOT n:Metadata AND NOT n:Ontology AND NOT n:Calculations
                WITH n, n.id as node_id
                CALL gds.wcc.stream('myGraph')
                YIELD nodeId, componentId
                RETURN componentId, collect(node_id) as nodes
                ORDER BY componentId
                """
            )
            return [record["nodes"] for record in result]

    def get_protection_schemes(self) -> List[Dict[str, Any]]:
        """Get all protection schemes and what they protect."""
        with self.driver.session(database=self.database) as session:
            result = session.run(
                """
                MATCH (relay:RelayFunction)-[r:PROTECTS]->(protected)
                RETURN relay.id as relay_id, 
                       relay.device_code as device_code,
                       relay.description as description,
                       protected.id as protected_id,
                       head(labels(protected)) as protected_type,
                       protected.name as protected_name,
                       r.notes as protection_notes
                ORDER BY relay.device_code, protected.name
                """
            )
            return [record.data() for record in result]

    def get_electrical_paths(
        self, from_node_id: str, to_node_id: str, diagram_id: Optional[str] = None
    ) -> List[List[str]]:
        """Find electrical paths between two nodes.

        Args:
            from_node_id: Starting node ID
            to_node_id: Ending node ID
            diagram_id: Optional diagram ID to limit search

        Returns:
            List of paths (each path is a list of node IDs)
        """
        with self.driver.session(database=self.database) as session:
            if diagram_id:
                result = session.run(
                    """
                    MATCH path = (start {id: $from_id, diagram_id: $diagram_id})-[*]-(end {id: $to_id, diagram_id: $diagram_id})
                    WHERE ALL(r in relationships(path) WHERE type(r) = 'CONNECTS_TO')
                    RETURN [node in nodes(path) | node.id] as path
                    LIMIT 10
                    """,
                    from_id=from_node_id,
                    to_id=to_node_id,
                    diagram_id=diagram_id,
                )
            else:
                result = session.run(
                    """
                    MATCH path = (start {id: $from_id})-[*]-(end {id: $to_id})
                    WHERE ALL(r in relationships(path) WHERE type(r) = 'CONNECTS_TO')
                    RETURN [node in nodes(path) | node.id] as path
                    LIMIT 10
                    """,
                    from_id=from_node_id,
                    to_id=to_node_id,
                )
            return [record["path"] for record in result]

    def list_diagrams(self) -> List[Dict[str, Any]]:
        """List all stored diagrams.

        Returns:
            List of diagram metadata dictionaries with index numbers
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(
                """
                MATCH (m:Metadata)
                RETURN m.diagram_id as diagram_id,
                       m.title as title,
                       m.extracted_at as extracted_at
                ORDER BY m.extracted_at DESC
                """
            )
            diagrams = [record.data() for record in result]

            # Deduplicate by diagram_id, keeping the first occurrence (most recent)
            seen_ids = set()
            unique_diagrams = []
            for diagram in diagrams:
                if diagram["diagram_id"] not in seen_ids:
                    seen_ids.add(diagram["diagram_id"])
                    unique_diagrams.append(diagram)

            # Add index numbers
            for i, diagram in enumerate(unique_diagrams, 1):
                diagram["index"] = i

            return unique_diagrams

    def get_diagram_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Get a diagram by its index number.

        Args:
            index: The 1-based index number

        Returns:
            Diagram metadata dictionary or None if not found
        """
        diagrams = self.list_diagrams()
        if 1 <= index <= len(diagrams):
            return diagrams[index - 1]
        return None

    def get_diagram_id_by_index(self, index: int) -> Optional[str]:
        """Get diagram ID by index number.

        Args:
            index: The 1-based index number

        Returns:
            Diagram ID or None if not found
        """
        diagram = self.get_diagram_by_index(index)
        return diagram.get("diagram_id") if diagram else None

    def resolve_diagram_identifier(self, identifier: str) -> Optional[str]:
        """Resolve a diagram identifier (index number or diagram_id) to diagram_id.

        Args:
            identifier: Either a numeric string (index) or diagram_id

        Returns:
            Resolved diagram_id or None if not found
        """
        # Check if it's a numeric index
        try:
            index = int(identifier)
            return self.get_diagram_id_by_index(index)
        except ValueError:
            # Not a number, treat as diagram_id
            diagrams = self.list_diagrams()
            for diagram in diagrams:
                if diagram.get("diagram_id") == identifier:
                    return identifier
            return None

    def delete_diagram(self, diagram_id: str) -> Dict[str, int]:
        """Delete a specific diagram and all its data.

        Args:
            diagram_id: The diagram ID to delete

        Returns:
            Dictionary with counts of deleted items
        """
        with self.driver.session(database=self.database) as session:
            # Count nodes before deletion
            node_count = session.run(
                "MATCH (n {diagram_id: $diagram_id}) RETURN count(n) as count",
                diagram_id=diagram_id,
            ).single()["count"]

            # Count relationships before deletion
            rel_count = session.run(
                "MATCH ()-[r {diagram_id: $diagram_id}]-() RETURN count(r) as count",
                diagram_id=diagram_id,
            ).single()["count"]

            # Delete all nodes and relationships for this diagram
            session.run(
                "MATCH (n {diagram_id: $diagram_id}) DETACH DELETE n",
                diagram_id=diagram_id,
            )

            return {
                "nodes_deleted": node_count,
                "relationships_deleted": rel_count,
                "diagram_id": diagram_id,
            }

    def get_diagram_summary_by_id(self, diagram_id: str) -> Dict[str, Any]:
        """Get a summary of a specific diagram.

        Args:
            diagram_id: The diagram ID to summarize

        Returns:
            Dictionary with diagram summary data
        """
        with self.driver.session(database=self.database) as session:
            # Get node counts by type for this diagram
            node_counts = session.run(
                """
                MATCH (n {diagram_id: $diagram_id})
                WHERE NOT n:Metadata AND NOT n:Ontology AND NOT n:Calculations
                RETURN labels(n)[0] as node_type, count(n) as count
                ORDER BY count DESC
                """,
                diagram_id=diagram_id,
            ).data()

            # Get relationship counts by type for this diagram
            rel_counts = session.run(
                """
                MATCH ()-[r {diagram_id: $diagram_id}]->()
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
                """,
                diagram_id=diagram_id,
            ).data()

            # Get metadata for this diagram
            metadata = session.run(
                """
                MATCH (m:Metadata {diagram_id: $diagram_id})
                RETURN m
                LIMIT 1
                """,
                diagram_id=diagram_id,
            ).single()

            return {
                "node_counts": {
                    item["node_type"]: item["count"] for item in node_counts
                },
                "relationship_counts": {
                    item["rel_type"]: item["count"] for item in rel_counts
                },
                "metadata": dict(metadata["m"]) if metadata else {},
                "total_nodes": sum(item["count"] for item in node_counts),
                "total_relationships": sum(item["count"] for item in rel_counts),
                "diagram_id": diagram_id,
            }
