"""Abstract base class for database operations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..models import ElectricalDiagram


class DatabaseClient(ABC):
    """Abstract base class for database operations."""

    @abstractmethod
    def connect(self) -> None:
        """Establish database connection."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    def store_diagram(
        self, diagram: ElectricalDiagram, diagram_id: Optional[str] = None
    ) -> Dict[str, int]:
        """Store diagram in database."""
        pass

    @abstractmethod
    def get_diagram_summary(self) -> Dict[str, Any]:
        """Get database summary."""
        pass

    @abstractmethod
    def get_diagram_summary_by_id(self, diagram_id: str) -> Dict[str, Any]:
        """Get summary of a specific diagram."""
        pass

    @abstractmethod
    def list_diagrams(self) -> List[Dict[str, Any]]:
        """List all stored diagrams."""
        pass

    @abstractmethod
    def delete_diagram(self, diagram_id: str) -> Dict[str, int]:
        """Delete a diagram."""
        pass

    @abstractmethod
    def query_diagram(self, cypher_query: str) -> List[Dict[str, Any]]:
        """Execute database query."""
        pass

    @abstractmethod
    def get_protection_schemes(self) -> List[Dict[str, Any]]:
        """Get protection schemes from the database."""
        pass

    @abstractmethod
    def resolve_diagram_identifier(self, identifier: str) -> Optional[str]:
        """Resolve diagram identifier (index or ID) to diagram_id."""
        pass

    @abstractmethod
    def clear_database(self) -> None:
        """Clear all nodes and relationships from the database."""
        pass

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()