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

    def store_diagram(self, diagram: ElectricalDiagram) -> Dict[str, int]:
        """Store an electrical diagram in Neo4j.

        Args:
            diagram: The electrical diagram to store

        Returns:
            Dictionary with counts of created nodes and relationships
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")

        node_count = 0
        edge_count = 0

        with self.driver.session(database=self.database) as session:
            # Store metadata as a special node
            metadata_node = session.run(
                """
                CREATE (m:Metadata)
                SET m += $metadata
                RETURN m
                """,
                metadata=diagram.metadata,
            ).single()

            # Store ontology information as JSON strings
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
                CREATE (o:Ontology)
                SET o.node_types = $node_types,
                    o.edge_types = $edge_types
                RETURN o
                """,
                node_types=json.dumps(node_types_data),
                edge_types=json.dumps(edge_types_data),
            ).single()

            # Store nodes
            for node in diagram.nodes:
                self._create_node(session, node)
                node_count += 1

            # Store edges/relationships
            for edge in diagram.edges:
                self._create_relationship(session, edge)
                edge_count += 1

            # Store calculations if present
            if diagram.calculations:
                self._store_calculations(session, diagram.calculations)

        return {
            "nodes_created": node_count,
            "relationships_created": edge_count,
            "metadata_stored": 1,
            "ontology_stored": 1,
            "calculations_stored": 1 if diagram.calculations else 0,
        }

    def _create_node(self, session, node: Node) -> None:
        """Create a single node in Neo4j."""
        # Prepare properties
        properties = {"id": node.id, "name": node.name, **node.extra_attrs}

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
            CREATE (n:{sanitized_type})
            SET n += $properties
            """,
            properties=properties,
        )

    def _create_relationship(self, session, edge: Edge) -> None:
        """Create a relationship between two nodes in Neo4j."""
        # Prepare relationship properties
        properties = {"via": edge.via, "notes": edge.notes, **edge.extra_attrs}

        # Remove None values
        properties = {k: v for k, v in properties.items() if v is not None}

        # Create the relationship
        session.run(
            f"""
            MATCH (from {{id: $from_id}})
            MATCH (to {{id: $to_id}})
            CREATE (from)-[r:{edge.type} $properties]->(to)
            """,
            from_id=edge.from_,
            to_id=edge.to,
            properties=properties,
        )

    def _store_calculations(self, session, calculations) -> None:
        """Store calculation results in Neo4j."""
        import json

        # Convert calculations to JSON strings
        short_circuit_data = calculations.short_circuit
        breaker_spec_data = calculations.breaker_spec

        if hasattr(breaker_spec_data, "model_dump"):
            breaker_spec_data = breaker_spec_data.model_dump()

        session.run(
            """
            CREATE (c:Calculations)
            SET c.short_circuit = $short_circuit,
                c.breaker_spec = $breaker_spec
            """,
            short_circuit=json.dumps(short_circuit_data),
            breaker_spec=json.dumps(breaker_spec_data),
        )

    def get_diagram_summary(self) -> Dict[str, Any]:
        """Get a summary of the stored diagram data."""
        with self.driver.session(database=self.database) as session:
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

            # Get metadata
            metadata = session.run(
                """
                MATCH (m:Metadata)
                RETURN m
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
        self, from_node_id: str, to_node_id: str
    ) -> List[List[str]]:
        """Find electrical paths between two nodes.

        Args:
            from_node_id: Starting node ID
            to_node_id: Ending node ID

        Returns:
            List of paths (each path is a list of node IDs)
        """
        with self.driver.session(database=self.database) as session:
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
