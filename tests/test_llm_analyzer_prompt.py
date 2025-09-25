"""Test the externalized prompt system for LLM analyzer."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.ea_analyzer.llm_analyzer import LLMAnalyzer, PROMPT, _load_prompt_from_file


class TestExternalizedPrompt:
    """Test the externalized prompt functionality."""

    def test_prompt_file_exists(self):
        """Test that the prompt file exists and is readable."""
        prompt_file = Path("src/ea_analyzer/electrical_diagram.prompt")
        assert prompt_file.exists(), f"Prompt file not found: {prompt_file}"
        assert prompt_file.stat().st_size > 0, "Prompt file is empty"

    def test_prompt_loading(self):
        """Test that the prompt loads correctly from file."""
        prompt = _load_prompt_from_file()

        # Basic validation
        assert isinstance(prompt, str), "Prompt should be a string"
        assert len(prompt) > 1000, "Prompt should be substantial"
        assert prompt.strip() == prompt, (
            "Prompt should not have leading/trailing whitespace"
        )

    def test_prompt_content_structure(self):
        """Test that the prompt contains expected sections."""
        expected_sections = [
            "You are an expert in power systems",
            "JSON object with this EXACT structure",
            "GridSource",
            "Transformer",
            "Breaker",
            "Busbar",
            "Feeder",
            "Key Rules:",
            "Return only valid JSON",
        ]

        for section in expected_sections:
            assert section in PROMPT, f"Prompt should contain '{section}'"

    def test_prompt_json_structure(self):
        """Test that the prompt contains a valid JSON example structure."""
        # Check for key JSON structure elements
        json_elements = [
            '"metadata"',
            '"ontology"',
            '"node_types"',
            '"edge_types"',
            '"nodes"',
            '"edges"',
            '"calculations"',
        ]

        for element in json_elements:
            assert element in PROMPT, f"Prompt should contain JSON element '{element}'"

    def test_prompt_node_types(self):
        """Test that the prompt includes all expected node types."""
        expected_node_types = [
            "GridSource",
            "Transformer",
            "Breaker",
            "Busbar",
            "Feeder",
            "SurgeArrester",
            "PotentialTransformer",
            "CurrentTransformer",
            "Meter",
            "CapacitorBank",
            "Battery",
            "RelayFunction",
        ]

        for node_type in expected_node_types:
            assert node_type in PROMPT, f"Prompt should include node type '{node_type}'"

    def test_prompt_edge_types(self):
        """Test that the prompt includes all expected edge types."""
        expected_edge_types = [
            "CONNECTS_TO",
            "PROTECTS",
            "MEASURES",
            "CONTROLS",
            "POWERED_BY",
            "LOCATED_ON",
        ]

        for edge_type in expected_edge_types:
            assert edge_type in PROMPT, f"Prompt should include edge type '{edge_type}'"

    def test_prompt_rules_section(self):
        """Test that the prompt includes the key rules section."""
        rules_content = [
            "Each component must have a unique",
            "Use consistent IDs",
            "All breakers: type",
            "Put all component attributes in the",
            "Preserve numeric values exactly",
            "If a value is unreadable or missing",
            "Include short-circuit values",
            "Extract all visible components",
        ]

        for rule in rules_content:
            assert rule in PROMPT, f"Prompt should include rule: '{rule}'"

    def test_prompt_consistency_with_original(self):
        """Test that the externalized prompt is consistent with expected structure."""
        # Test that the prompt has the right overall structure
        assert PROMPT.startswith("You are an expert in power systems"), (
            "Prompt should start with expert introduction"
        )
        assert PROMPT.endswith(
            "Return only valid JSON matching this exact structure."
        ), "Prompt should end with JSON instruction"

        # Test that it contains the example JSON structure
        assert '"id": "GS_A"' in PROMPT, "Should contain example node ID"
        assert '"type": "GridSource"' in PROMPT, "Should contain example node type"
        assert '"from_": "GS_A"' in PROMPT, "Should contain example edge"

    def test_llm_analyzer_imports_prompt(self):
        """Test that LLMAnalyzer can import the prompt successfully."""
        # This tests that the module-level PROMPT is loaded correctly
        assert PROMPT is not None, "PROMPT should be loaded at module level"
        assert len(PROMPT) > 0, "PROMPT should not be empty"

    def test_prompt_file_missing_error(self):
        """Test error handling when prompt file is missing."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(ValueError, match="Prompt file not found"):
                _load_prompt_from_file()

    def test_prompt_file_empty_error(self):
        """Test error handling when prompt file is empty."""
        with patch("builtins.open", mock_open(read_data="")):
            with pytest.raises(ValueError, match="Prompt file is empty"):
                _load_prompt_from_file()

    def test_prompt_file_read_error(self):
        """Test error handling when prompt file cannot be read."""
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            with pytest.raises(ValueError, match="Error reading prompt file"):
                _load_prompt_from_file()


def mock_open(read_data):
    """Helper function to mock file opening."""
    from unittest.mock import mock_open as _mock_open

    return _mock_open(read_data=read_data)


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
