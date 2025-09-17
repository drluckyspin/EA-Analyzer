#!/usr/bin/env python3
"""Example script demonstrating Neo4j integration for electrical diagrams."""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ea_analyzer.neo4j_client import Neo4jClient
from ea_analyzer.parser import ElectricalDiagramParser


def main():
    """Demonstrate Neo4j integration."""
    # Path to the sample data
    data_file = Path(__file__).parent.parent / "data" / "one-line-knowledge-graph.json"

    if not data_file.exists():
        print(f"Error: Data file not found at {data_file}")
        return

    # Neo4j connection settings
    # You can set these as environment variables or modify here
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")

    print("=== Electrical Diagram Neo4j Integration Example ===")
    print(f"Neo4j URI: {neo4j_uri}")
    print(f"Database: {neo4j_database}")
    print()

    try:
        # Load the electrical diagram
        print("1. Loading electrical diagram from JSON...")
        parser = ElectricalDiagramParser()
        diagram = parser.load_from_file(data_file)
        print(
            f"   ✓ Loaded diagram with {len(diagram.nodes)} nodes and {len(diagram.edges)} edges"
        )

        # Connect to Neo4j and store the diagram
        print("\n2. Connecting to Neo4j and storing diagram...")
        with Neo4jClient(
            uri=neo4j_uri,
            username=neo4j_username,
            password=neo4j_password,
            database=neo4j_database,
        ) as client:
            # Clear existing data (optional)
            print("   Clearing existing data...")
            client.clear_database()

            # Store the diagram
            print("   Storing diagram...")
            result = client.store_diagram(diagram)

            print("   ✓ Storage completed!")
            print(f"   - Nodes created: {result['nodes_created']}")
            print(f"   - Relationships created: {result['relationships_created']}")
            print(f"   - Metadata stored: {result['metadata_stored']}")
            print(f"   - Ontology stored: {result['ontology_stored']}")
            print(f"   - Calculations stored: {result['calculations_stored']}")

            # Get and display summary
            print("\n3. Retrieving diagram summary from Neo4j...")
            summary = client.get_diagram_summary()
            print(f"   Total nodes: {summary['total_nodes']}")
            print(f"   Total relationships: {summary['total_relationships']}")

            # Show node type breakdown
            print("\n   Node types:")
            for node_type, count in summary["node_counts"].items():
                print(f"     - {node_type}: {count}")

            # Show relationship type breakdown
            print("\n   Relationship types:")
            for rel_type, count in summary["relationship_counts"].items():
                print(f"     - {rel_type}: {count}")

            # Query protection schemes
            print("\n4. Querying protection schemes...")
            protection_schemes = client.get_protection_schemes()
            if protection_schemes:
                print("   Protection schemes found:")
                for scheme in protection_schemes:
                    print(
                        f"     - {scheme['relay_id']} ({scheme['device_code']}): {scheme['description']}"
                    )
                    print(
                        f"       Protects: {scheme['protected_name']} ({scheme['protected_type']})"
                    )
            else:
                print("   No protection schemes found")

            # Example custom query
            print("\n5. Running custom Cypher query...")
            custom_query = """
            MATCH (t:Transformer)
            RETURN t.id as transformer_id, t.name as name, t.hv_kv as hv_kv, t.lv_kv as lv_kv
            ORDER BY t.id
            """
            transformers = client.query_diagram(custom_query)
            print("   Transformers found:")
            for tx in transformers:
                print(
                    f"     - {tx['transformer_id']}: {tx['name']} ({tx['hv_kv']}kV/{tx['lv_kv']}kV)"
                )

        print("\n✓ Example completed successfully!")
        print("\nYou can now use the CLI commands to interact with the data:")
        print("  ea-analyze neo4j summary")
        print("  ea-analyze neo4j protection-schemes")
        print("  ea-analyze neo4j query 'MATCH (n) RETURN n LIMIT 5'")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure Neo4j is running and accessible at the specified URI.")
        print(
            "You can start Neo4j with: docker run -p 7474:7474 -p 7687:7687 neo4j:latest"
        )


if __name__ == "__main__":
    main()
