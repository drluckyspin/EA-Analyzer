"""Typer-based CLI for EA-Analyzer with rich output and validation."""

import json
import os
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
from .database import DatabaseFactory
from .parser import ElectricalDiagramParser
from .graph_visualizer import ElectricalGraphVisualizer
from .llm_analyzer import create_analyzer

# Initialize Typer app and Rich console
app = typer.Typer(
    name="ea-analyzer",
    help="Electrical Assembly Analyzer with database integration",
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
    db_type: str = typer.Option(
        "neo4j", "--db-type", help="Database type (neo4j, postgres, etc.)", envvar="DB_TYPE"
    ),
    db_uri: str = typer.Option(
        "bolt://localhost:7687",
        "--db-uri",
        help="Database connection URI (defaults to Docker Compose Neo4j)",
        envvar="DB_URI",
    ),
    db_username: str = typer.Option(
        "neo4j", "--db-user", help="Database username", envvar="DB_USERNAME"
    ),
    db_password: str = typer.Option(
        "password", "--db-pass", help="Database password", envvar="DB_PASSWORD"
    ),
    db_database: str = typer.Option(
        "neo4j", "--db-name", help="Database name", envvar="DB_DATABASE"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """EA-Analyzer - Electrical diagram parsing and knowledge graph extraction with database integration."""
    # Store global options
    global _global_options
    _global_options.update(
        {
            "data_file": data_file,
            "db_type": db_type,
            "db_uri": db_uri,
            "db_username": db_username,
            "db_password": db_password,
            "db_database": db_database,
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


def validate_db_uri(uri: str, db_type: str = "neo4j") -> bool:
    """Validate database URI format."""
    if not uri:
        console.print("[red]✗[/red] Database URI cannot be empty")
        return False

    if db_type.lower() == "neo4j":
        if not (uri.startswith("bolt://") or uri.startswith("neo4j://")):
            console.print(f"[red]✗[/red] Invalid Neo4j URI format: {uri}")
            console.print(
                "[yellow]ℹ[/yellow] Expected format: bolt://hostname:port or neo4j://hostname:port"
            )
            console.print("[yellow]ℹ[/yellow] Example: bolt://localhost:7687")
            return False
    # Add validation for other database types as needed
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
    # Handle the case where input_file might be a Typer ArgumentInfo object
    if input_file is not None and hasattr(input_file, '__class__') and 'ArgumentInfo' in str(input_file.__class__):
        data_file = get_data_file()
    else:
        data_file = Path(input_file) if input_file is not None else get_data_file()

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
    """Store diagram in database with partitioning support."""
    # Handle the case where input_file might be a Typer ArgumentInfo object
    if input_file is not None and hasattr(input_file, '__class__') and 'ArgumentInfo' in str(input_file.__class__):
        data_file = get_data_file()
    else:
        data_file = Path(input_file) if input_file is not None else get_data_file()

    if not validate_data_file(data_file):
        raise typer.Exit(1)

    if not validate_db_uri(_global_options["db_uri"], _global_options["db_type"]):
        raise typer.Exit(1)

    console.print(Panel("Storing Diagram in Database", style="blue"))
    console.print(f"[cyan]ℹ[/cyan] Loading diagram from: {data_file}")
    console.print(f"[cyan]ℹ[/cyan] Database URI: {_global_options['db_uri']}")
    console.print(f"[cyan]ℹ[/cyan] Database: {_global_options['db_database']}")

    try:
        parser = ElectricalDiagramParser()
        diagram = parser.load_from_file(data_file)
        console.print(f"[green]✓[/green] Successfully loaded diagram from {data_file}")

        client = DatabaseFactory.create_client(
            db_type=_global_options["db_type"],
            uri=_global_options["db_uri"],
            username=_global_options["db_username"],
            password=_global_options["db_password"],
            database=_global_options["db_database"]
        )
        
        with client:
            # Handle Typer OptionInfo objects
            actual_clear = False if hasattr(clear, '__class__') and 'OptionInfo' in str(clear.__class__) else clear
            actual_diagram_id = None if hasattr(diagram_id, '__class__') and 'OptionInfo' in str(diagram_id.__class__) else diagram_id
            
            if actual_clear:
                console.print("[yellow]Clearing database...[/yellow]")
                client.clear_database()

            console.print("[yellow]Storing diagram in database...[/yellow]")
            result = client.store_diagram(diagram, actual_diagram_id)

            # Display results
            result_table = Table(title="Storage Results")
            result_table.add_column("Item", style="cyan")
            result_table.add_column("Count", style="magenta")

            for key, value in result.items():
                result_table.add_row(key.replace("_", " ").title(), str(value))

            console.print(result_table)
            console.print(f"[green]✓[/green] Successfully stored diagram in database!")
            console.print(
                f"[cyan]ℹ[/cyan] Diagram ID: {result.get('diagram_id', 'Unknown')}"
            )
            console.print(f"[cyan]ℹ[/cyan] Use 'db list' to see all stored diagrams")

    except Exception as e:
        console.print(f"[red]✗[/red] Error storing diagram: {e}")
        raise typer.Exit(1)


# Create a separate Typer app for database commands
db_app = typer.Typer(
    name="db", help="Database operations"
)

# Add the db app to the main app
app.add_typer(db_app, name="db")


@db_app.command()
def ping():
    """Check if database is running and accessible."""
    if not validate_db_uri(_global_options["db_uri"], _global_options["db_type"]):
        raise typer.Exit(1)

    console.print(Panel("Database Connection Test", style="blue"))
    console.print(
        f"[cyan]ℹ[/cyan] Testing connection to: {_global_options['db_uri']}"
    )
    console.print(f"[cyan]ℹ[/cyan] Database: {_global_options['db_database']}")

    try:
        client = DatabaseFactory.create_client(
            db_type=_global_options["db_type"],
            uri=_global_options["db_uri"],
            username=_global_options["db_username"],
            password=_global_options["db_password"],
            database=_global_options["db_database"]
        )
        
        with client:
            # Try to execute a simple query to test the connection
            result = client.query_diagram("RETURN 1 as test")

            if result and len(result) > 0:
                console.print("[green]✓[/green] Database is running and accessible!")
                console.print(
                    f"[green]✓[/green] Successfully connected to database: {_global_options['db_database']}"
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
                    "[red]✗[/red] Database connection failed - no response to test query"
                )
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]✗[/red] Database connection failed: {e}")
        console.print("[yellow]ℹ[/yellow] Please check:")
        console.print("[yellow]ℹ[/yellow]   - Database service is running")
        console.print("[yellow]ℹ[/yellow]   - Connection URI is correct")
        console.print("[yellow]ℹ[/yellow]   - Username and password are correct")
        console.print("[yellow]ℹ[/yellow]   - Database exists")
        raise typer.Exit(1)


@db_app.command()
def summary():
    """Show summary of data stored in database."""
    if not validate_db_uri(_global_options["db_uri"], _global_options["db_type"]):
        raise typer.Exit(1)

    console.print(Panel("Database Summary", style="blue"))

    try:
        client = DatabaseFactory.create_client(
            db_type=_global_options["db_type"],
            uri=_global_options["db_uri"],
            username=_global_options["db_username"],
            password=_global_options["db_password"],
            database=_global_options["db_database"]
        )
        
        with client:
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
        console.print(f"[red]✗[/red] Error connecting to database: {e}")
        raise typer.Exit(1)


@db_app.command()
def protection_schemes():
    """Show protection schemes in the diagram."""
    if not validate_db_uri(_global_options["db_uri"], _global_options["db_type"]):
        raise typer.Exit(1)

    console.print(Panel("Protection Schemes Analysis", style="blue"))

    try:
        client = DatabaseFactory.create_client(
            db_type=_global_options["db_type"],
            uri=_global_options["db_uri"],
            username=_global_options["db_username"],
            password=_global_options["db_password"],
            database=_global_options["db_database"]
        )
        
        with client:
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


@db_app.command()
def query(cypher_query: str = typer.Argument(..., help="Cypher query to execute")):
    """Execute a custom database query."""
    if not validate_db_uri(_global_options["db_uri"], _global_options["db_type"]):
        raise typer.Exit(1)

    console.print(Panel("Custom Database Query", style="blue"))
    console.print(f"[cyan]ℹ[/cyan] Query: {cypher_query}")

    try:
        client = DatabaseFactory.create_client(
            db_type=_global_options["db_type"],
            uri=_global_options["db_uri"],
            username=_global_options["db_username"],
            password=_global_options["db_password"],
            database=_global_options["db_database"]
        )
        
        with client:
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
                    if row:  # Only add row if it's not empty
                        result_table.add_row(*row)

                console.print(result_table)

    except Exception as e:
        console.print(f"[red]✗[/red] Error executing query: {e}")
        raise typer.Exit(1)


@db_app.command()
def list_diagrams():
    """List all stored diagrams."""
    if not validate_db_uri(_global_options["db_uri"], _global_options["db_type"]):
        raise typer.Exit(1)

    try:
        client = DatabaseFactory.create_client(
            db_type=_global_options["db_type"],
            uri=_global_options["db_uri"],
            username=_global_options["db_username"],
            password=_global_options["db_password"],
            database=_global_options["db_database"]
        )
        
        with client:
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


@db_app.command()
def delete(
    identifier: str = typer.Argument(
        ..., help="Diagram index number or diagram ID to delete"
    ),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
):
    """Delete a specific diagram and all its data."""
    if not validate_db_uri(_global_options["db_uri"], _global_options["db_type"]):
        raise typer.Exit(1)

    try:
        client = DatabaseFactory.create_client(
            db_type=_global_options["db_type"],
            uri=_global_options["db_uri"],
            username=_global_options["db_username"],
            password=_global_options["db_password"],
            database=_global_options["db_database"]
        )
        
        with client:
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


@db_app.command()
def summary_by_id(
    identifier: str = typer.Argument(
        ..., help="Diagram index number or diagram ID to summarize"
    ),
):
    """Get a summary of a specific diagram."""
    if not validate_db_uri(_global_options["db_uri"], _global_options["db_type"]):
        raise typer.Exit(1)

    try:
        client = DatabaseFactory.create_client(
            db_type=_global_options["db_type"],
            uri=_global_options["db_uri"],
            username=_global_options["db_username"],
            password=_global_options["db_password"],
            database=_global_options["db_database"]
        )
        
        with client:
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


@db_app.command()
def export(
    identifier: str = typer.Argument(
        ..., help="Diagram index number or diagram ID to export"
    ),
    output_file: str = typer.Option(
        "diagram.png", "--output", "-o", help="Output PNG file path"
    ),
    layout: str = typer.Option(
        "hierarchical",
        "--layout",
        "-l",
        help="Layout algorithm (hierarchical, spring, circular)",
    ),
    width: int = typer.Option(16, "--width", "-w", help="Image width in inches"),
    height: int = typer.Option(12, "--height", "-h", help="Image height in inches"),
    dpi: int = typer.Option(300, "--dpi", help="Image DPI"),
):
    """Export a diagram to PNG file."""
    if not validate_db_uri(_global_options["db_uri"], _global_options["db_type"]):
        raise typer.Exit(1)

    try:
        client = DatabaseFactory.create_client(
            db_type=_global_options["db_type"],
            uri=_global_options["db_uri"],
            username=_global_options["db_username"],
            password=_global_options["db_password"],
            database=_global_options["db_database"]
        )
        
        with client:
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

            console.print(Panel(f"Exporting Diagram: {identifier}", style="blue"))
            console.print(f"[cyan]ℹ[/cyan] Diagram ID: {diagram_id}")
            console.print(f"[cyan]ℹ[/cyan] Output file: {output_file}")
            console.print(f"[cyan]ℹ[/cyan] Layout: {layout}")
            console.print(f"[cyan]ℹ[/cyan] Size: {width}x{height} inches at {dpi} DPI")

            # Create visualizer and export
            visualizer = ElectricalGraphVisualizer(client)

            # Validate layout
            available_layouts = visualizer.get_available_layouts()
            if layout not in available_layouts:
                console.print(f"[red]✗[/red] Invalid layout '{layout}'")
                console.print(
                    f"[yellow]ℹ[/yellow] Available layouts: {', '.join(available_layouts)}"
                )
                raise typer.Exit(1)

            # Export the diagram
            output_path = visualizer.export_diagram_to_png(
                diagram_id=diagram_id,
                output_path=output_file,
                layout=layout,
                figsize=(width, height),
                dpi=dpi,
            )

            console.print(
                f"[green]✓[/green] Successfully exported diagram to: {output_path}"
            )

            # Show file info
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                console.print(f"[cyan]ℹ[/cyan] File size: {file_size:,} bytes")

    except Exception as e:
        console.print(f"[red]✗[/red] Error exporting diagram: {e}")
        raise typer.Exit(1)


@app.command()
def examples():
    """Run example queries."""
    if not validate_db_uri(_global_options["db_uri"], _global_options["db_type"]):
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
            client = DatabaseFactory.create_client(
                db_type=_global_options["db_type"],
                uri=_global_options["db_uri"],
                username=_global_options["db_username"],
                password=_global_options["db_password"],
                database=_global_options["db_database"]
            )
            
            with client:
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
                        if row:  # Only add row if it's not empty
                            result_table.add_row(*row)

                    console.print(result_table)
        except Exception as e:
            console.print(f"[red]✗[/red] Error executing query: {e}")
        console.print()


@app.command()
def analyze(
    image_path: Path = typer.Argument(..., help="Path to electrical diagram image"),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output JSON file path (defaults to image name with .json extension)",
    ),
    provider: str = typer.Option(
        None,
        "--provider",
        help="LLM provider (openai, anthropic, gemini) - uses config if not specified",
    ),
    model: str = typer.Option(
        None, "--model", help="LLM model name - uses config if not specified"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        help="API key for the LLM provider - uses environment variable if not specified",
    ),
    store_after: bool = typer.Option(
        False, "--store", help="Store the analyzed diagram in Neo4j after analysis"
    ),
):
    """Analyze an electrical diagram image using LLM and extract structured data."""
    if not image_path.exists():
        console.print(f"[red]✗[/red] Image file not found: {image_path}")
        raise typer.Exit(1)

    # Get configuration
    config = get_config()

    # Use provided values or fall back to config
    llm_provider = provider or config["llm_provider"]
    llm_model = model or config["llm_model"]
    llm_api_key = api_key or config.get(f"{llm_provider}_api_key")

    if not llm_api_key:
        console.print(f"[red]✗[/red] No API key found for provider '{llm_provider}'")
        console.print(
            f"[yellow]ℹ[/yellow] Please set {llm_provider.upper()}_API_KEY environment variable"
        )
        console.print(f"[yellow]ℹ[/yellow] Or use --api-key option")
        raise typer.Exit(1)

    # Set output file if not provided
    if not output_file:
        output_file = image_path.with_suffix(".json")

    console.print(Panel("LLM Image Analysis", style="blue"))
    console.print(f"[cyan]ℹ[/cyan] Image: {image_path}")
    console.print(f"[cyan]ℹ[/cyan] Provider: {llm_provider}")
    console.print(f"[cyan]ℹ[/cyan] Model: {llm_model}")
    console.print(f"[cyan]ℹ[/cyan] Output: {output_file}")

    try:
        # Create analyzer
        analyzer = create_analyzer(
            provider=llm_provider, model=llm_model, api_key=llm_api_key
        )

        # Analyze image
        console.print("[yellow]Analyzing image with LLM...[/yellow]")
        diagram = analyzer.analyze_image(image_path)
        console.print("[green]✓[/green] Image analysis completed successfully!")

        # Save to JSON file
        console.print(f"[yellow]Saving results to {output_file}...[/yellow]")
        with open(output_file, "w") as f:
            json.dump(diagram.model_dump(), f, indent=2)
        console.print(f"[green]✓[/green] Results saved to {output_file}")

        # Show summary
        summary_data = {
            "total_nodes": len(diagram.nodes),
            "total_edges": len(diagram.edges),
            "has_calculations": diagram.calculations is not None,
            "node_counts": {},
            "edge_counts": {},
        }

        # Count nodes by type
        for node in diagram.nodes:
            node_type = node.type
            summary_data["node_counts"][node_type] = (
                summary_data["node_counts"].get(node_type, 0) + 1
            )

        # Count edges by type
        for edge in diagram.edges:
            edge_type = edge.type
            summary_data["edge_counts"][edge_type] = (
                summary_data["edge_counts"].get(edge_type, 0) + 1
            )

        # Display summary
        stats_table = Table(title="Analysis Results")
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

        # Store in database if requested
        if store_after:
            console.print("[yellow]Storing diagram in database...[/yellow]")
            if not validate_db_uri(_global_options["db_uri"], _global_options["db_type"]):
                console.print("[red]✗[/red] Invalid database URI")
                raise typer.Exit(1)

            try:
                client = DatabaseFactory.create_client(
                    db_type=_global_options["db_type"],
                    uri=_global_options["db_uri"],
                    username=_global_options["db_username"],
                    password=_global_options["db_password"],
                    database=_global_options["db_database"]
                )
                
                with client:
                    result = client.store_diagram(diagram)
                    console.print(
                        f"[green]✓[/green] Diagram stored in database with ID: {result.get('diagram_id', 'Unknown')}"
                    )
            except Exception as e:
                console.print(f"[red]✗[/red] Error storing in database: {e}")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]✗[/red] Error analyzing image: {e}")
        raise typer.Exit(1)


@app.command()
def demo():
    """Run complete demo (start database, store data, run examples)."""
    console.print(Panel("EA-Analyzer Complete Demo", style="blue"))

    # Check prerequisites
    check()

    # Show original data summary
    summary()

    # Store in database
    store()

    # Show database summary
    # Call the db summary function directly
    if not validate_db_uri(_global_options["db_uri"], _global_options["db_type"]):
        console.print("[red]✗[/red] Invalid database configuration")
        return
    
    console.print(Panel("Database Summary", style="blue"))
    
    try:
        client = DatabaseFactory.create_client(
            db_type=_global_options["db_type"],
            uri=_global_options["db_uri"],
            username=_global_options["db_username"],
            password=_global_options["db_password"],
            database=_global_options["db_database"]
        )
        
        with client:
            # Get summary data
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
                        style="blue"
                    )
                )
            
            # Display statistics
            if summary_data.get("statistics"):
                stats = summary_data["statistics"]
                
                # Main statistics table
                stats_table = Table(title="Diagram Statistics")
                stats_table.add_column("Metric", style="cyan")
                stats_table.add_column("Value", style="magenta")
                
                stats_table.add_row("Total Nodes", str(stats.get("total_nodes", 0)))
                stats_table.add_row("Total Relationships", str(stats.get("total_relationships", 0)))
                
                console.print(stats_table)
                
                # Node types table
                if stats.get("node_types"):
                    node_table = Table(title="Node Types")
                    node_table.add_column("Type", style="cyan")
                    node_table.add_column("Count", style="magenta")
                    
                    for node_type, count in stats["node_types"].items():
                        node_table.add_row(node_type, str(count))
                    
                    console.print(node_table)
                
                # Relationship types table
                if stats.get("relationship_types"):
                    rel_table = Table(title="Relationship Types")
                    rel_table.add_column("Type", style="cyan")
                    rel_table.add_column("Count", style="magenta")
                    
                    for rel_type, count in stats["relationship_types"].items():
                        rel_table.add_row(rel_type, str(count))
                    
                    console.print(rel_table)
            
            console.print("[green]✓[/green] Database summary retrieved successfully!")
            
    except Exception as e:
        console.print(f"[red]✗[/red] Error retrieving database summary: {e}")
        return

    # Show protection schemes
    console.print(Panel("Protection Schemes Analysis", style="blue"))
    
    try:
        with client:
            protection_schemes = client.get_protection_schemes()
            
            if not protection_schemes:
                console.print("[yellow]ℹ[/yellow] No protection schemes found in the database")
                return
            
            schemes_table = Table(title="Protection Schemes")
            schemes_table.add_column("Relay ID", style="cyan")
            schemes_table.add_column("Device Code", style="green")
            schemes_table.add_column("Description", style="white")
            schemes_table.add_column("Protected", style="magenta")
            schemes_table.add_column("Type", style="blue")
            schemes_table.add_column("Notes", style="yellow")
            
            for scheme in protection_schemes:
                schemes_table.add_row(
                    scheme.get("relay_id", "Unknown"),
                    scheme.get("device_code", "Unknown"),
                    scheme.get("description", "Unknown"),
                    scheme.get("protected_name") or scheme.get("protected_id", "Unknown"),
                    scheme.get("protected_type", "Unknown"),
                    scheme.get("protection_notes", "") or ""
                )
            
            console.print(schemes_table)
            console.print("[green]✓[/green] Protection schemes analysis completed!")
            
    except Exception as e:
        console.print(f"[red]✗[/red] Error analyzing protection schemes: {e}")
        return

    # Run example queries
    examples()

    console.print("[green]✓[/green] Demo completed successfully!")
    console.print("[cyan]ℹ[/cyan] You can now explore the data using:")
    console.print("[cyan]ℹ[/cyan]   - Database Browser: http://localhost:7474")
    console.print(
        "[cyan]ℹ[/cyan]   - CLI commands: ea-analyzer db summary, ea-analyzer db protection-schemes, etc."
    )


@app.command()
def neo4j():
    """Legacy Neo4j command - use 'db' instead."""
    console.print("[yellow]⚠[/yellow] 'neo4j' command is deprecated. Use 'db' instead.")
    console.print("[cyan]ℹ[/cyan] Redirecting to 'db' command...")
    console.print("[cyan]ℹ[/cyan] Use: ea-analyzer db --help")
    raise typer.Exit(0)


if __name__ == "__main__":
    app()
