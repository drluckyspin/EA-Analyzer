"""Typer-based CLI for EA-Analyzer with rich output and validation."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from .env_config import get_config
from .neo4j_client import Neo4jClient
from .parser import ElectricalDiagramParser

# Initialize Typer app and Rich console
app = typer.Typer(
    name="ea-analyzer",
    help="Electrical Assembly Analyzer with Neo4j integration",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()

# Global state for options
_global_options = {}


@app.callback()
def main(
    data_file: Optional[Path] = typer.Option(
        None, "--data-file", "-f", help="Path to JSON data file", envvar="DATA_FILE"
    ),
    neo4j_uri: str = typer.Option(
        "bolt://localhost:7687",
        "--neo4j-uri",
        help="Neo4j connection URI (defaults to Docker Compose Neo4j)",
        envvar="NEO4J_URI",
    ),
    neo4j_username: str = typer.Option(
        "neo4j", "--neo4j-user", help="Neo4j username", envvar="NEO4J_USERNAME"
    ),
    neo4j_password: str = typer.Option(
        "password", "--neo4j-pass", help="Neo4j password", envvar="NEO4J_PASSWORD"
    ),
    neo4j_database: str = typer.Option(
        "neo4j", "--neo4j-db", help="Neo4j database name", envvar="NEO4J_DATABASE"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """EA-Analyzer - Electrical diagram parsing and knowledge graph extraction with Neo4j via Docker Compose."""
    # Store global options
    global _global_options
    _global_options.update(
        {
            "data_file": data_file,
            "neo4j_uri": neo4j_uri,
            "neo4j_username": neo4j_username,
            "neo4j_password": neo4j_password,
            "neo4j_database": neo4j_database,
            "verbose": verbose,
        }
    )


def get_data_file() -> Path:
    """Get the data file path from global options or config."""
    data_file = _global_options.get("data_file")
    if data_file:
        return data_file

    config = get_config()
    return Path(config["data_file"])


def validate_data_file(file_path: Path) -> bool:
    """Validate data file exists and is valid JSON."""
    if not file_path.exists():
        console.print(f"[red]✗[/red] Data file not found: {file_path}")
        console.print(
            "[yellow]ℹ[/yellow] Please check the file path or create the file first"
        )
        return False

    if not file_path.is_file():
        console.print(f"[red]✗[/red] Path is not a file: {file_path}")
        return False

    try:
        with open(file_path, "r") as f:
            json.load(f)
    except json.JSONDecodeError as e:
        console.print(f"[red]✗[/red] Data file is not valid JSON: {file_path}")
        console.print(f"[yellow]ℹ[/yellow] Error: {e}")
        return False
    except Exception as e:
        console.print(f"[red]✗[/red] Error reading file: {e}")
        return False

    return True


def validate_neo4j_uri(uri: str) -> bool:
    """Validate Neo4j URI format."""
    if not uri:
        console.print("[red]✗[/red] Neo4j URI cannot be empty")
        return False

    if not (uri.startswith("bolt://") or uri.startswith("neo4j://")):
        console.print(f"[red]✗[/red] Invalid Neo4j URI format: {uri}")
        console.print(
            "[yellow]ℹ[/yellow] Expected format: bolt://hostname:port or neo4j://hostname:port"
        )
        console.print("[yellow]ℹ[/yellow] Example: bolt://localhost:7687")
        return False

    return True


@app.command()
def check():
    """Check prerequisites and system status."""
    console.print(Panel("Checking Prerequisites", style="blue"))

    # Check Python
    try:
        result = subprocess.run(
            [sys.executable, "--version"], capture_output=True, text=True
        )
        console.print(f"[green]✓[/green] Python found: {result.stdout.strip()}")
    except Exception as e:
        console.print(f"[red]✗[/red] Python not found: {e}")
        raise typer.Exit(1)

    # Check uv
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        console.print(f"[green]✓[/green] uv found: {result.stdout.strip()}")
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] uv not found: {e}")

    # Check Docker
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        console.print(f"[green]✓[/green] Docker found: {result.stdout.strip()}")
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] Docker not found: {e}")
        console.print("[yellow]ℹ[/yellow] Neo4j operations will require manual setup")

    console.print("[green]✓[/green] Prerequisites check completed")


@app.command()
def summary(input_file: Optional[Path] = typer.Argument(None, help="Input JSON file")):
    """Show diagram summary from JSON file."""
    data_file = input_file or get_data_file()

    if not validate_data_file(data_file):
        raise typer.Exit(1)

    console.print(Panel("Diagram Summary", style="blue"))
    console.print(f"[cyan]ℹ[/cyan] Loading diagram from: {data_file}")

    try:
        parser = ElectricalDiagramParser()
        parser.load_from_file(data_file)
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
        raise typer.Exit(1)


@app.command()
def store(
    input_file: Optional[Path] = typer.Argument(None, help="Input JSON file"),
    clear: bool = typer.Option(False, "--clear", help="Clear database before storing"),
    diagram_id: Optional[str] = typer.Option(
        None, "--diagram-id", help="Custom diagram ID (defaults to title-based ID)"
    ),
):
    """Store diagram in Neo4j database with partitioning support."""
    data_file = input_file or get_data_file()

    if not validate_data_file(data_file):
        raise typer.Exit(1)

    if not validate_neo4j_uri(_global_options["neo4j_uri"]):
        raise typer.Exit(1)

    console.print(Panel("Storing Diagram in Neo4j", style="blue"))
    console.print(f"[cyan]ℹ[/cyan] Loading diagram from: {data_file}")
    console.print(f"[cyan]ℹ[/cyan] Neo4j URI: {_global_options['neo4j_uri']}")
    console.print(f"[cyan]ℹ[/cyan] Database: {_global_options['neo4j_database']}")

    try:
        parser = ElectricalDiagramParser()
        diagram = parser.load_from_file(data_file)
        console.print(f"[green]✓[/green] Successfully loaded diagram from {data_file}")

        with Neo4jClient(
            uri=_global_options["neo4j_uri"],
            username=_global_options["neo4j_username"],
            password=_global_options["neo4j_password"],
            database=_global_options["neo4j_database"],
        ) as client:
            if clear:
                console.print("[yellow]Clearing database...[/yellow]")
                client.clear_database()

            console.print("[yellow]Storing diagram in Neo4j...[/yellow]")
            result = client.store_diagram(diagram, diagram_id)

            # Display results
            result_table = Table(title="Storage Results")
            result_table.add_column("Item", style="cyan")
            result_table.add_column("Count", style="magenta")

            for key, value in result.items():
                result_table.add_row(key.replace("_", " ").title(), str(value))

            console.print(result_table)
            console.print(f"[green]✓[/green] Successfully stored diagram in Neo4j!")
            console.print(
                f"[cyan]ℹ[/cyan] Diagram ID: {result.get('diagram_id', 'Unknown')}"
            )
            console.print(f"[cyan]ℹ[/cyan] Use 'neo4j list' to see all stored diagrams")

    except Exception as e:
        console.print(f"[red]✗[/red] Error storing diagram: {e}")
        raise typer.Exit(1)


# Create a separate Typer app for Neo4j commands
neo4j_app = typer.Typer(
    name="neo4j", help="Neo4j database operations (via Docker Compose)"
)

# Add the neo4j app to the main app
app.add_typer(neo4j_app, name="neo4j")


@neo4j_app.command()
def ping():
    """Check if Neo4j is running and accessible (via Docker Compose)."""
    if not validate_neo4j_uri(_global_options["neo4j_uri"]):
        raise typer.Exit(1)

    console.print(Panel("Neo4j Connection Test", style="blue"))
    console.print(
        f"[cyan]ℹ[/cyan] Testing connection to: {_global_options['neo4j_uri']}"
    )
    console.print(f"[cyan]ℹ[/cyan] Database: {_global_options['neo4j_database']}")

    try:
        with Neo4jClient(
            uri=_global_options["neo4j_uri"],
            username=_global_options["neo4j_username"],
            password=_global_options["neo4j_password"],
            database=_global_options["neo4j_database"],
        ) as client:
            # Try to execute a simple query to test the connection
            result = client.query_diagram("RETURN 1 as test")

            if result and len(result) > 0:
                console.print("[green]✓[/green] Neo4j is running and accessible!")
                console.print(
                    f"[green]✓[/green] Successfully connected to database: {_global_options['neo4j_database']}"
                )

                # Get some basic database info
                try:
                    db_info = client.query_diagram(
                        "CALL db.info() YIELD name, address RETURN name, address LIMIT 1"
                    )
                    if db_info:
                        console.print(
                            f"[cyan]ℹ[/cyan] Database name: {db_info[0].get('name', 'Unknown')}"
                        )
                        console.print(
                            f"[cyan]ℹ[/cyan] Database address: {db_info[0].get('address', 'Unknown')}"
                        )
                except Exception:
                    # If db.info() fails, that's okay, we still have a working connection
                    pass
            else:
                console.print(
                    "[red]✗[/red] Neo4j connection failed - no response to test query"
                )
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]✗[/red] Neo4j connection failed: {e}")
        console.print("[yellow]ℹ[/yellow] Please check:")
        console.print("[yellow]ℹ[/yellow]   - Neo4j Docker container is running")
        console.print("[yellow]ℹ[/yellow]   - Connection URI is correct")
        console.print("[yellow]ℹ[/yellow]   - Username and password are correct")
        console.print("[yellow]ℹ[/yellow]   - Database exists")
        raise typer.Exit(1)


@neo4j_app.command()
def summary():
    """Show summary of data stored in Neo4j (via Docker Compose)."""
    if not validate_neo4j_uri(_global_options["neo4j_uri"]):
        raise typer.Exit(1)

    console.print(Panel("Neo4j Database Summary", style="blue"))

    try:
        with Neo4jClient(
            uri=_global_options["neo4j_uri"],
            username=_global_options["neo4j_username"],
            password=_global_options["neo4j_password"],
            database=_global_options["neo4j_database"],
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
        raise typer.Exit(1)


@neo4j_app.command()
def protection_schemes():
    """Show protection schemes in the diagram (via Docker Compose)."""
    if not validate_neo4j_uri(_global_options["neo4j_uri"]):
        raise typer.Exit(1)

    console.print(Panel("Protection Schemes Analysis", style="blue"))

    try:
        with Neo4jClient(
            uri=_global_options["neo4j_uri"],
            username=_global_options["neo4j_username"],
            password=_global_options["neo4j_password"],
            database=_global_options["neo4j_database"],
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
        raise typer.Exit(1)


@neo4j_app.command()
def query(cypher_query: str = typer.Argument(..., help="Cypher query to execute")):
    """Execute a custom Cypher query (via Docker Compose)."""
    if not validate_neo4j_uri(_global_options["neo4j_uri"]):
        raise typer.Exit(1)

    console.print(Panel("Custom Cypher Query", style="blue"))
    console.print(f"[cyan]ℹ[/cyan] Query: {cypher_query}")

    try:
        with Neo4jClient(
            uri=_global_options["neo4j_uri"],
            username=_global_options["neo4j_username"],
            password=_global_options["neo4j_password"],
            database=_global_options["neo4j_database"],
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
        raise typer.Exit(1)


@neo4j_app.command()
def list():
    """List all stored diagrams."""
    if not validate_neo4j_uri(_global_options["neo4j_uri"]):
        raise typer.Exit(1)

    try:
        with Neo4jClient(
            uri=_global_options["neo4j_uri"],
            username=_global_options["neo4j_username"],
            password=_global_options["neo4j_password"],
            database=_global_options["neo4j_database"],
        ) as client:
            console.print(Panel("Stored Diagrams", style="blue"))

            diagrams = client.list_diagrams()

            if diagrams:
                table = Table(title="Available Diagrams")
                table.add_column("Index", style="cyan")
                table.add_column("Title", style="green")
                table.add_column("Source", style="yellow")
                table.add_column("Extracted", style="magenta")
                table.add_column("Diagram ID", style="dim")

                for diagram in diagrams:
                    table.add_row(
                        str(diagram.get("index", "?")),
                        diagram.get("title", "Unknown"),
                        diagram.get("source", "Unknown"),
                        diagram.get("extracted_at", "Unknown"),
                        diagram.get("diagram_id", "Unknown")[:50] + "..."
                        if len(diagram.get("diagram_id", "")) > 50
                        else diagram.get("diagram_id", "Unknown"),
                    )

                console.print(table)
                console.print(f"[green]✓[/green] Found {len(diagrams)} diagram(s)")
                console.print(
                    "[cyan]ℹ[/cyan] Use index numbers (1, 2, 3...) or full diagram IDs for commands"
                )
            else:
                console.print("[yellow]ℹ[/yellow] No diagrams found in database")

    except Exception as e:
        console.print(f"[red]✗[/red] Error listing diagrams: {e}")
        raise typer.Exit(1)


@neo4j_app.command()
def delete(
    identifier: str = typer.Argument(
        ..., help="Diagram index number or diagram ID to delete"
    ),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
):
    """Delete a specific diagram and all its data."""
    if not validate_neo4j_uri(_global_options["neo4j_uri"]):
        raise typer.Exit(1)

    try:
        with Neo4jClient(
            uri=_global_options["neo4j_uri"],
            username=_global_options["neo4j_username"],
            password=_global_options["neo4j_password"],
            database=_global_options["neo4j_database"],
        ) as client:
            # Resolve identifier to diagram_id
            diagram_id = client.resolve_diagram_identifier(identifier)

            if not diagram_id:
                console.print(f"[red]✗[/red] Diagram '{identifier}' not found")
                console.print(
                    "[yellow]ℹ[/yellow] Use 'neo4j list' to see available diagrams"
                )
                console.print(
                    "[yellow]ℹ[/yellow] Use index numbers (1, 2, 3...) or full diagram IDs"
                )
                raise typer.Exit(1)

            # Confirmation prompt
            if not confirm:
                console.print(
                    f"[yellow]⚠[/yellow] This will permanently delete diagram '{diagram_id}' and all its data"
                )
                if not typer.confirm("Are you sure you want to continue?"):
                    console.print("[yellow]ℹ[/yellow] Operation cancelled")
                    raise typer.Exit(0)

            console.print(Panel(f"Deleting Diagram: {diagram_id}", style="red"))

            result = client.delete_diagram(diagram_id)

            # Display results
            result_table = Table(title="Deletion Results")
            result_table.add_column("Item", style="cyan")
            result_table.add_column("Count", style="magenta")

            for key, value in result.items():
                if key != "diagram_id":
                    result_table.add_row(key.replace("_", " ").title(), str(value))

            console.print(result_table)
            console.print(
                f"[green]✓[/green] Successfully deleted diagram '{diagram_id}'"
            )

    except Exception as e:
        console.print(f"[red]✗[/red] Error deleting diagram: {e}")
        raise typer.Exit(1)


@neo4j_app.command()
def summary_by_id(
    identifier: str = typer.Argument(
        ..., help="Diagram index number or diagram ID to summarize"
    ),
):
    """Get a summary of a specific diagram."""
    if not validate_neo4j_uri(_global_options["neo4j_uri"]):
        raise typer.Exit(1)

    try:
        with Neo4jClient(
            uri=_global_options["neo4j_uri"],
            username=_global_options["neo4j_username"],
            password=_global_options["neo4j_password"],
            database=_global_options["neo4j_database"],
        ) as client:
            # Resolve identifier to diagram_id
            diagram_id = client.resolve_diagram_identifier(identifier)

            if not diagram_id:
                console.print(f"[red]✗[/red] Diagram '{identifier}' not found")
                console.print(
                    "[yellow]ℹ[/yellow] Use 'neo4j list' to see available diagrams"
                )
                console.print(
                    "[yellow]ℹ[/yellow] Use index numbers (1, 2, 3...) or full diagram IDs"
                )
                raise typer.Exit(1)

            console.print(Panel(f"Diagram Summary: {identifier}", style="blue"))

            summary = client.get_diagram_summary_by_id(diagram_id)

            if not summary.get("metadata"):
                console.print(f"[red]✗[/red] Diagram '{identifier}' not found")
                console.print(
                    "[yellow]ℹ[/yellow] Use 'neo4j list' to see available diagrams"
                )
                raise typer.Exit(1)

            # Display metadata
            metadata = summary["metadata"]
            console.print(Panel("Diagram Metadata", style="green"))
            console.print(f"[cyan]ℹ[/cyan] Title: {metadata.get('title', 'Unknown')}")
            console.print(f"[cyan]ℹ[/cyan] Source: {metadata.get('source', 'Unknown')}")
            console.print(
                f"[cyan]ℹ[/cyan] Extracted: {metadata.get('extracted_at', 'Unknown')}"
            )

            # Display statistics
            stats_table = Table(title="Diagram Statistics")
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="green")

            stats_table.add_row("Total Nodes", str(summary["total_nodes"]))
            stats_table.add_row(
                "Total Relationships", str(summary["total_relationships"])
            )

            console.print(stats_table)

            # Display node types
            if summary["node_counts"]:
                node_table = Table(title="Node Types")
                node_table.add_column("Type", style="cyan")
                node_table.add_column("Count", style="green")

                for node_type, count in summary["node_counts"].items():
                    node_table.add_row(node_type, str(count))

                console.print(node_table)

            # Display relationship types
            if summary["relationship_counts"]:
                rel_table = Table(title="Relationship Types")
                rel_table.add_column("Type", style="cyan")
                rel_table.add_column("Count", style="green")

                for rel_type, count in summary["relationship_counts"].items():
                    rel_table.add_row(rel_type, str(count))

                console.print(rel_table)

    except Exception as e:
        console.print(f"[red]✗[/red] Error getting diagram summary: {e}")
        raise typer.Exit(1)


@app.command()
def examples():
    """Run example queries."""
    if not validate_neo4j_uri(_global_options["neo4j_uri"]):
        raise typer.Exit(1)

    console.print(Panel("Example Queries", style="blue"))

    # Default queries
    queries = [
        "MATCH (t:Transformer) RETURN t.id, t.name, t.hv_kv, t.lv_kv ORDER BY t.id",
        "MATCH (b:Breaker) RETURN b.id, b.name, b.kv_class, b.continuous_a ORDER BY b.id",
        "MATCH (r:RelayFunction)-[rel:PROTECTS]->(p) RETURN r.device_code, r.description, p.name, p.type ORDER BY r.device_code",
        "MATCH (bus:Busbar)-[r:CONNECTS_TO]-(comp) RETURN bus.name, head(labels(comp)) as type, comp.name, r.via ORDER BY bus.name, type",
        "MATCH (n) WHERE n:GridSource OR n:Transformer RETURN head(labels(n)) as type, n.name, n.kv ORDER BY type, n.name",
    ]

    query_names = [
        "Transformers",
        "Breakers",
        "Protection Schemes",
        "Bus Connections",
        "Power Sources and Transformers",
    ]

    for i, (query, name) in enumerate(zip(queries, query_names), 1):
        console.print(f"[cyan]ℹ[/cyan] Query {i}: {name}")
        # Call the neo4j query command directly
        try:
            with Neo4jClient(
                uri=_global_options["neo4j_uri"],
                username=_global_options["neo4j_username"],
                password=_global_options["neo4j_password"],
                database=_global_options["neo4j_database"],
            ) as client:
                results = client.query_diagram(query)

                if not results:
                    console.print("[yellow]No results found.[/yellow]")
                    continue

                # Display results in a table format
                if results:
                    # Get column names from the first result
                    columns = list(results[0].keys())

                    result_table = Table(title=f"Query {i} Results: {name}")
                    for col in columns:
                        result_table.add_column(col, style="cyan")

                    for result in results:
                        row = [str(result.get(col, "")) for col in columns]
                        result_table.add_row(*row)

                    console.print(result_table)
        except Exception as e:
            console.print(f"[red]✗[/red] Error executing query: {e}")
        console.print()


@app.command()
def demo():
    """Run complete demo (start Neo4j, store data, run examples)."""
    console.print(Panel("EA-Analyzer Complete Demo", style="blue"))

    # Check prerequisites
    check()

    # Show original data summary
    summary()

    # Store in Neo4j
    store()

    # Show Neo4j summary
    neo4j_app.get_command("summary")()

    # Show protection schemes
    neo4j_app.get_command("protection_schemes")()

    # Run example queries
    examples()

    console.print("[green]✓[/green] Demo completed successfully!")
    console.print("[cyan]ℹ[/cyan] You can now explore the data using:")
    console.print("[cyan]ℹ[/cyan]   - Neo4j Browser: http://localhost:7474")
    console.print(
        "[cyan]ℹ[/cyan]   - CLI commands: ea-analyzer neo4j summary, ea-analyzer neo4j protection-schemes, etc."
    )


if __name__ == "__main__":
    app()
