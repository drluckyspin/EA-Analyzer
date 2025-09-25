"""LLM-based image analyzer for electrical diagrams."""

import base64
import json
import os
import re
from pathlib import Path
from typing import Any, Optional

from .models import ElectricalDiagram


def _load_prompt_from_file() -> str:
    """Load the electrical diagram analysis prompt from text file.

    Returns:
        The prompt string for LLM analysis

    Raises:
        ValueError: If the prompt file is not found or cannot be read
    """
    # Load prompt from electrical_diagram.prompt file
    prompt_file = Path(__file__).parent / "electrical_diagram.prompt"
    if not prompt_file.exists():
        raise ValueError(
            f"Prompt file not found: {prompt_file}. "
            "Please ensure the electrical_diagram.prompt file exists in the src/ea_analyzer directory."
        )

    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read().strip()
    except Exception as e:
        raise ValueError(f"Error reading prompt file: {e}") from e

    if not prompt:
        raise ValueError(
            "Prompt file is empty. Please ensure the file contains the required prompt."
        )
    return prompt


# Load the prompt from text file
PROMPT = _load_prompt_from_file()

# Simplified JSON Schema for structured output
ELECTRICAL_DIAGRAM_SCHEMA = {
    "type": "object",
    "properties": {
        "metadata": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "source_image": {"type": "string"},
                "extracted_at": {"type": "string"},
            },
            "required": ["title", "source_image", "extracted_at"],
            "additionalProperties": False,
        },
        "ontology": {
            "type": "object",
            "properties": {
                "node_types": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "attrs": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["attrs"],
                        "additionalProperties": False,
                    },
                },
                "edge_types": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "attrs": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["attrs"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["node_types", "edge_types"],
            "additionalProperties": False,
        },
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string"},
                    "name": {"type": "string"},
                    "extra_attrs": {"type": "object"},
                },
                "required": ["id", "type", "name", "extra_attrs"],
                "additionalProperties": False,
            },
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "from_": {"type": "string"},
                    "to": {"type": "string"},
                    "type": {"type": "string"},
                    "extra_attrs": {"type": "object"},
                },
                "required": ["from_", "to", "type", "extra_attrs"],
                "additionalProperties": False,
            },
        },
        "calculations": {
            "type": "object",
            "properties": {
                "short_circuit": {
                    "type": "object",
                    "properties": {
                        "first_cycle_asym_ka": {"type": "number"},
                        "one_point_five_cycles_sym_ka": {"type": "number"},
                    },
                    "additionalProperties": False,
                },
                "breaker_spec": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "kv_class": {"type": "number"},
                        "continuous_a": {"type": "number"},
                        "interrupting_ka_range": {"type": "string"},
                        "k_factor": {"type": "number"},
                    },
                    "required": [
                        "type",
                        "kv_class",
                        "continuous_a",
                        "interrupting_ka_range",
                        "k_factor",
                    ],
                    "additionalProperties": False,
                },
            },
            "required": ["short_circuit", "breaker_spec"],
            "additionalProperties": False,
        },
    },
    "required": ["metadata", "ontology", "nodes", "edges", "calculations"],
    "additionalProperties": False,
}


class LLMAnalyzer:
    """LLM-based analyzer for electrical diagram images."""

    def __init__(self, provider: str, model: str, api_key: Optional[str] = None):
        """Initialize the LLM analyzer.

        Args:
            provider: LLM provider ('openai', 'anthropic', 'gemini')
            model: Model name to use
            api_key: API key (if not provided, will use environment variable)
        """
        self.provider = provider.lower()
        self.model = model

        # Get API key from parameter or environment
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = self._get_api_key()

        if not self.api_key:
            raise ValueError(
                f"API key not found for provider '{provider}'. "
                f"Please set the appropriate environment variable."
            )

    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment variables."""
        key_mapping = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GOOGLE_API_KEY",
        }

        env_var = key_mapping.get(self.provider)
        if env_var:
            return os.environ.get(env_var)
        return None

    def analyze_image(self, image_path: Path) -> ElectricalDiagram:
        """Analyze an electrical diagram image and return structured data.

        Args:
            image_path: Path to the image file

        Returns:
            ElectricalDiagram object with parsed data

        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If analysis fails or returns invalid data
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Call the appropriate provider
        if self.provider == "openai":
            raw_json = self._call_openai(image_path)
        elif self.provider == "anthropic":
            raw_json = self._call_anthropic(image_path)
        elif self.provider == "gemini":
            raw_json = self._call_gemini(image_path)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

        # Parse and validate the JSON response
        try:
            data = self._ensure_json(raw_json)
        except Exception as e:
            raise ValueError(
                f"Model did not return valid JSON. Raw output:\n{raw_json}"
            ) from e

        # Handle case where nodes/edges are nested in ontology
        if "ontology" in data and isinstance(data["ontology"], dict):
            if "nodes" in data["ontology"] and "nodes" not in data:
                data["nodes"] = data["ontology"]["nodes"]
            if "edges" in data["ontology"] and "edges" not in data:
                data["edges"] = data["ontology"]["edges"]

        # Ensure all required edge types are present in ontology
        if "ontology" in data and "edge_types" in data["ontology"]:
            required_edge_types = [
                "CONNECTS_TO",
                "PROTECTS",
                "MEASURES",
                "CONTROLS",
                "POWERED_BY",
                "LOCATED_ON",
            ]
            for edge_type in required_edge_types:
                if edge_type not in data["ontology"]["edge_types"]:
                    data["ontology"]["edge_types"][edge_type] = {"attrs": []}

        # Validate required keys
        required_keys = ("metadata", "ontology", "nodes", "edges", "calculations")
        missing_keys = [k for k in required_keys if k not in data]
        if missing_keys:
            raise ValueError(f"Missing required keys in response: {missing_keys}")

        # Convert to ElectricalDiagram object
        try:
            return ElectricalDiagram(**data)
        except Exception as e:
            raise ValueError(
                f"Failed to create ElectricalDiagram from parsed data: {e}"
            ) from e

    def _read_image_b64(self, path: Path) -> tuple[str, str]:
        """Read image file and encode as base64."""
        data = path.read_bytes()
        # Crude mime type guess from suffix
        ext = path.suffix.lower()
        mime_mapping = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".svg": "image/svg+xml",
        }
        mime = mime_mapping.get(ext, "application/octet-stream")
        return base64.b64encode(data).decode("utf-8"), mime

    def _ensure_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from text response."""
        # Extract the first {...} block; models sometimes wrap in code fences
        fence_match = re.search(r"\{.*\}\s*$", text, flags=re.S)
        blob = fence_match.group(0) if fence_match else text
        return json.loads(blob)

    def _call_openai(self, image_path: Path) -> str:
        """Call OpenAI API for image analysis."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI package not installed. Install with: pip install openai"
            )

        client = OpenAI(api_key=self.api_key)
        b64, mime = self._read_image_b64(image_path)

        # Use the chat completions API with vision and structured output
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{b64}",
                            },
                        },
                    ],
                }
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=4000,
        )
        return response.choices[0].message.content

    def _call_anthropic(self, image_path: Path) -> str:
        """Call Anthropic API for image analysis."""
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError(
                "Anthropic package not installed. Install with: pip install anthropic"
            )

        client = Anthropic(api_key=self.api_key)
        b64, mime = self._read_image_b64(image_path)

        msg = client.messages.create(
            model=self.model,
            max_tokens=4000,
            temperature=0.0,  # Set to 0 for deterministic output
            system=(
                f"Return only valid JSON that follows this exact schema: "
                f"{json.dumps(ELECTRICAL_DIAGRAM_SCHEMA)}"
            ),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime,
                                "data": b64,
                            },
                        },
                    ],
                }
            ],
            random_seed=42,  # For determinism
        )

        # Extract text content from response
        parts = [p for p in msg.content if p.get("type") == "text"]
        return parts[0]["text"] if parts else ""

    def _call_gemini(self, image_path: Path) -> str:
        """Call Google Gemini API for image analysis."""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "Google Generative AI package not installed. "
                "Install with: pip install google-generativeai"
            )

        genai.configure(api_key=self.api_key)
        b64, mime = self._read_image_b64(image_path)

        model = genai.GenerativeModel(
            model_name=self.model,
            generation_config={
                "temperature": 0.0,  # Set to 0 for deterministic output
                "response_mime_type": "application/json",
                "response_schema": ELECTRICAL_DIAGRAM_SCHEMA,
            },
        )

        schema_json = json.dumps(ELECTRICAL_DIAGRAM_SCHEMA)
        result = model.generate_content(
            [
                {"mime_type": mime, "data": b64},
                f"{PROMPT}\n\nReturn JSON matching this schema: {schema_json}",
            ],
            safety_settings=None,  # Use defaults
        )
        return result.text


def create_analyzer(
    provider: str, model: str, api_key: Optional[str] = None
) -> LLMAnalyzer:
    """Factory function to create an LLM analyzer.

    Args:
        provider: LLM provider ('openai', 'anthropic', 'gemini')
        model: Model name to use
        api_key: API key (optional, will use environment variable if not provided)

    Returns:
        Configured LLMAnalyzer instance
    """
    return LLMAnalyzer(provider=provider, model=model, api_key=api_key)
