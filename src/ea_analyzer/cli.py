"""Command-line interface for EA Parsing."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .env_config import get_config, get_example_queries
from .neo4j_client import Neo4jClient
from .parser import ElectricalDiagramParser

console = Console()


@click.group()
@click.version_option()
@click.option(
    "--data-file",
    "data_file",
    type=click.Path(path_type=Path),
    envvar="DATA_FILE",
    help="Default input JSON file (overrides env if provided)",
)
@click.pass_context
def main(ctx: click.Context, data_file: Optional[Path]) -> None:
    """EA Parsing - Electrical diagram parsing and knowledge graph extraction."""
    ctx.ensure_object(dict)
    ctx.obj["data_file"] = data_file


@main.command()
@click.argument("input_file", required=False, type=click.Path(path_type=Path))
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), help="Output file path"
)
@click.pass_context
def parse(
    ctx: click.Context, input_file: Optional[Path], output: Optional[Path]
) -> None:
    """Parse an electrical diagram JSON file."""
    parser = ElectricalDiagramParser()

    try:
        chosen = (
            input_file or ctx.obj.get("data_file") or Path(get_config()["data_file"])
        )  # type: ignore[arg-type]
        if not chosen or not Path(chosen).exists():
            raise FileNotFoundError(f"Input file not found: {chosen}")
        parser.load_from_file(Path(chosen))
        console.print(f"[green]✓[/green] Successfully loaded diagram from {chosen}")

        if output:
            parser.save_to_file(output)
            console.print(f"[green]✓[/green] Saved diagram to {output}")

    except Exception as e:
        console.print(f"[red]✗[/red] Error parsing file: {e}")
        raise click.Abort()


@main.command()
@click.argument("input_file", required=False, type=click.Path(path_type=Path))
@click.pass_context
def summary(ctx: click.Context, input_file: Optional[Path]) -> None:
    """Show a summary of an electrical diagram."""
    parser = ElectricalDiagramParser()

    try:
        chosen = (
            input_file or ctx.obj.get("data_file") or Path(get_config()["data_file"])
        )  # type: ignore[arg-type]
        if not chosen or not Path(chosen).exists():
            raise FileNotFoundError(f"Input file not found: {chosen}")
        parser.load_from_file(Path(chosen))
        summary_data = parser.get_summary()

        # Display metadata
        if "metadata" in summary_data:
            metadata = summary_data["metadata"]
            console.print(
                Panel(
                    f"[bold]Title:[/bold] {metadata.get('title', 'N/A')}\n"
                    f"[bold]Source:[/bold] {metadata.get('source_image', 'N/A')}\n"
                    f"[bold]Extracted:[/bold] {metadata.get('extracted_at', 'N/A')}",
                    title="Diagram Metadata",
                    border_style="blue",
                )
            )

        # Display statistics
        stats_table = Table(title="Diagram Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="magenta")

        stats_table.add_row("Total Nodes", str(summary_data["total_nodes"]))
        stats_table.add_row("Total Edges", str(summary_data["total_edges"]))
        stats_table.add_row(
            "Has Calculations", "Yes" if summary_data["has_calculations"] else "No"
        )

        console.print(stats_table)

        # Display node counts
        if summary_data["node_counts"]:
            node_table = Table(title="Node Types")
            node_table.add_column("Type", style="cyan")
            node_table.add_column("Count", style="magenta")

            for node_type, count in sorted(summary_data["node_counts"].items()):
                node_table.add_row(node_type, str(count))

            console.print(node_table)

        # Display edge counts
        if summary_data["edge_counts"]:
            edge_table = Table(title="Edge Types")
            edge_table.add_column("Type", style="cyan")
            edge_table.add_column("Count", style="magenta")

            for edge_type, count in sorted(summary_data["edge_counts"].items()):
                edge_table.add_row(edge_type, str(count))

            console.print(edge_table)

    except Exception as e:
        console.print(f"[red]✗[/red] Error loading file: {e}")
        raise click.Abort()


@main.command()
@click.argument("input_file", required=False, type=click.Path(path_type=Path))
@click.option("--node-type", help="Filter by node type")
@click.option("--edge-type", help="Filter by edge type")
@click.pass_context
def list_items(
    ctx: click.Context,
    input_file: Optional[Path],
    node_type: Optional[str],
    edge_type: Optional[str],
) -> None:
    """List nodes and edges in the diagram."""
    parser = ElectricalDiagramParser()

    try:
        chosen = (
            input_file or ctx.obj.get("data_file") or Path(get_config()["data_file"])
        )  # type: ignore[arg-type]
        if not chosen or not Path(chosen).exists():
            raise FileNotFoundError(f"Input file not found: {chosen}")
        diagram = parser.load_from_file(Path(chosen))

        if node_type:
            nodes = diagram.get_nodes_by_type(node_type)
            console.print(f"[bold]Nodes of type '{node_type}':[/bold]")
            for node in nodes:
                console.print(f"  {node.id}: {node.name or 'No name'}")
        else:
            console.print("[bold]All Nodes:[/bold]")
            for node in diagram.nodes:
                console.print(f"  {node.id} ({node.type}): {node.name or 'No name'}")

        if edge_type:
            edges = diagram.get_edges_by_type(edge_type)
            console.print(f"\n[bold]Edges of type '{edge_type}':[/bold]")
            for edge in edges:
                console.print(f"  {edge.from_} -> {edge.to}")
        else:
            console.print("\n[bold]All Edges:[/bold]")
            for edge in diagram.edges:
                console.print(f"  {edge.from_} --[{edge.type}]--> {edge.to}")

    except Exception as e:
        console.print(f"[red]✗[/red] Error loading file: {e}")
        raise click.Abort()


@main.group()
def neo4j() -> None:
    """Neo4j database operations."""
    pass


@neo4j.command()
@click.argument("input_file", required=False, type=click.Path(path_type=Path))
@click.option("--uri", help="Neo4j connection URI")
@click.option("--username", help="Neo4j username")
@click.option("--password", help="Neo4j password")
@click.option("--database", help="Neo4j database name")
@click.option("--clear", is_flag=True, help="Clear database before storing")
@click.pass_context
def store(
    ctx: click.Context,
    input_file: Optional[Path],
    uri: Optional[str],
    username: Optional[str],
    password: Optional[str],
    database: Optional[str],
    clear: bool,
) -> None:
    """Store an electrical diagram in Neo4j."""
    parser = ElectricalDiagramParser()

    # Get configuration from environment
    config = get_config()

    # Use provided values or fall back to environment config
    uri = uri or config["neo4j_uri"]
    username = username or config["neo4j_username"]
    password = password or config["neo4j_password"]
    database = database or config["neo4j_database"]

    try:
        # Load the diagram
        chosen = (
            input_file or ctx.obj.get("data_file") or Path(get_config()["data_file"])
        )  # type: ignore[arg-type]
        if not chosen or not Path(chosen).exists():
            raise FileNotFoundError(f"Input file not found: {chosen}")
        diagram = parser.load_from_file(Path(chosen))
        console.print(f"[green]✓[/green] Successfully loaded diagram from {chosen}")

        # Connect to Neo4j and store
        with Neo4jClient(
            uri=uri, username=username, password=password, database=database
        ) as client:
            if clear:
                console.print("[yellow]Clearing database...[/yellow]")
                client.clear_database()

            console.print("[yellow]Storing diagram in Neo4j...[/yellow]")
            result = client.store_diagram(diagram)

            # Display results
            result_table = Table(title="Storage Results")
            result_table.add_column("Item", style="cyan")
            result_table.add_column("Count", style="magenta")

            for key, value in result.items():
                result_table.add_row(key.replace("_", " ").title(), str(value))

            console.print(result_table)
            console.print("[green]✓[/green] Successfully stored diagram in Neo4j!")

    except Exception as e:
        console.print(f"[red]✗[/red] Error storing diagram: {e}")
        raise click.Abort()


@neo4j.command()
@click.option("--uri", help="Neo4j connection URI")
@click.option("--username", help="Neo4j username")
@click.option("--password", help="Neo4j password")
@click.option("--database", help="Neo4j database name")
def summary(
    uri: Optional[str],
    username: Optional[str],
    password: Optional[str],
    database: Optional[str],
) -> None:
    """Show a summary of the stored diagram in Neo4j."""
    # Get configuration from environment
    config = get_config()

    # Use provided values or fall back to environment config
    uri = uri or config["neo4j_uri"]
    username = username or config["neo4j_username"]
    password = password or config["neo4j_password"]
    database = database or config["neo4j_database"]

    try:
        with Neo4jClient(
            uri=uri, username=username, password=password, database=database
        ) as client:
            summary_data = client.get_diagram_summary()

            # Display metadata
            if summary_data.get("metadata"):
                metadata = summary_data["metadata"]
                console.print(
                    Panel(
                        f"[bold]Title:[/bold] {metadata.get('title', 'N/A')}\n"
                        f"[bold]Source:[/bold] {metadata.get('source_image', 'N/A')}\n"
                        f"[bold]Extracted:[/bold] {metadata.get('extracted_at', 'N/A')}",
                        title="Diagram Metadata",
                        border_style="blue",
                    )
                )

            # Display statistics
            stats_table = Table(title="Diagram Statistics")
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="magenta")

            stats_table.add_row("Total Nodes", str(summary_data["total_nodes"]))
            stats_table.add_row(
                "Total Relationships", str(summary_data["total_relationships"])
            )

            console.print(stats_table)

            # Display node counts
            if summary_data["node_counts"]:
                node_table = Table(title="Node Types")
                node_table.add_column("Type", style="cyan")
                node_table.add_column("Count", style="magenta")

                for node_type, count in sorted(summary_data["node_counts"].items()):
                    node_table.add_row(node_type, str(count))

                console.print(node_table)

            # Display relationship counts
            if summary_data["relationship_counts"]:
                rel_table = Table(title="Relationship Types")
                rel_table.add_column("Type", style="cyan")
                rel_table.add_column("Count", style="magenta")

                for rel_type, count in sorted(
                    summary_data["relationship_counts"].items()
                ):
                    rel_table.add_row(rel_type, str(count))

                console.print(rel_table)

    except Exception as e:
        console.print(f"[red]✗[/red] Error connecting to Neo4j: {e}")
        raise click.Abort()


@neo4j.command()
@click.option("--uri", help="Neo4j connection URI")
@click.option("--username", help="Neo4j username")
@click.option("--password", help="Neo4j password")
@click.option("--database", help="Neo4j database name")
def protection_schemes(
    uri: Optional[str],
    username: Optional[str],
    password: Optional[str],
    database: Optional[str],
) -> None:
    """Show protection schemes in the diagram."""
    # Get configuration from environment
    config = get_config()

    # Use provided values or fall back to environment config
    uri = uri or config["neo4j_uri"]
    username = username or config["neo4j_username"]
    password = password or config["neo4j_password"]
    database = database or config["neo4j_database"]

    try:
        with Neo4jClient(
            uri=uri, username=username, password=password, database=database
        ) as client:
            schemes = client.get_protection_schemes()

            if not schemes:
                console.print("[yellow]No protection schemes found.[/yellow]")
                return

            protection_table = Table(title="Protection Schemes")
            protection_table.add_column("Relay ID", style="cyan")
            protection_table.add_column("Device Code", style="green")
            protection_table.add_column("Description", style="white")
            protection_table.add_column("Protected", style="magenta")
            protection_table.add_column("Type", style="blue")
            protection_table.add_column("Notes", style="yellow")

            for scheme in schemes:
                protection_table.add_row(
                    scheme["relay_id"],
                    scheme["device_code"],
                    scheme["description"],
                    scheme["protected_name"] or scheme["protected_id"],
                    scheme["protected_type"],
                    scheme["protection_notes"] or "",
                )

            console.print(protection_table)

    except Exception as e:
        console.print(f"[red]✗[/red] Error querying protection schemes: {e}")
        raise click.Abort()


@neo4j.command()
@click.argument("cypher_query")
@click.option("--uri", help="Neo4j connection URI")
@click.option("--username", help="Neo4j username")
@click.option("--password", help="Neo4j password")
@click.option("--database", help="Neo4j database name")
def query(
    cypher_query: str,
    uri: Optional[str],
    username: Optional[str],
    password: Optional[str],
    database: Optional[str],
) -> None:
    """Execute a custom Cypher query."""
    # Get configuration from environment
    config = get_config()

    # Use provided values or fall back to environment config
    uri = uri or config["neo4j_uri"]
    username = username or config["neo4j_username"]
    password = password or config["neo4j_password"]
    database = database or config["neo4j_database"]

    try:
        with Neo4jClient(
            uri=uri, username=username, password=password, database=database
        ) as client:
            results = client.query_diagram(cypher_query)

            if not results:
                console.print("[yellow]No results found.[/yellow]")
                return

            # Display results in a table format
            if results:
                # Get column names from the first result
                columns = list(results[0].keys())

                result_table = Table(title="Query Results")
                for col in columns:
                    result_table.add_column(col, style="cyan")

                for result in results:
                    row = [str(result.get(col, "")) for col in columns]
                    result_table.add_row(*row)

                console.print(result_table)

    except Exception as e:
        console.print(f"[red]✗[/red] Error executing query: {e}")
        raise click.Abort()


if __name__ == "__main__":
    main()
