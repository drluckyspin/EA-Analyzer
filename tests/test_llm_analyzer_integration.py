"""Integration tests for LLM analyzer using real example images."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

from src.ea_analyzer.llm_analyzer import LLMAnalyzer, create_analyzer
from src.ea_analyzer.models import ElectricalDiagram


class TestLLMAnalyzerIntegration:
    """Integration tests for LLM analyzer with real example images."""

    @pytest.fixture
    def example_images(self):
        """Get paths to example images."""
        data_dir = Path("data/images")
        return {
            "one_line": data_dir / "one-line-diagram-ge-swgr-vb1.png",
            "substation": data_dir / "substation_diagram-KEEP.png",
        }

    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response with realistic electrical diagram data."""
        return {
            "metadata": {
                "title": "Test Electrical Diagram",
                "source_image": "one-line-diagram-ge-swgr-vb1.png",
                "extracted_at": "2024-01-01T00:00:00Z",
            },
            "ontology": {
                "node_types": {
                    "GridSource": {
                        "attrs": [
                            "id",
                            "name",
                            "kv",
                            "frequency_hz",
                            "sc_mva",
                            "x_over_r",
                        ]
                    },
                    "Transformer": {
                        "attrs": [
                            "id",
                            "name",
                            "mva_ratings",
                            "hv_kv",
                            "lv_kv",
                            "vector_group",
                            "impedance_pct",
                            "cooling",
                            "notes",
                        ]
                    },
                    "Breaker": {
                        "attrs": [
                            "id",
                            "name",
                            "kv_class",
                            "continuous_a",
                            "interrupting_ka",
                            "type",
                            "position",
                            "normally_open",
                        ]
                    },
                    "Busbar": {"attrs": ["id", "name", "kv", "ampacity_a"]},
                    "Feeder": {"attrs": ["id", "name", "kv", "load_desc"]},
                    "SurgeArrester": {"attrs": ["id", "class", "kv", "location"]},
                    "PotentialTransformer": {"attrs": ["id", "ratio", "purpose"]},
                    "CurrentTransformer": {"attrs": ["id", "ratio", "purpose"]},
                    "Meter": {"attrs": ["id", "purpose"]},
                    "CapacitorBank": {"attrs": ["id", "kvar", "kv_class", "qty"]},
                    "Battery": {"attrs": ["id", "dc_v", "purpose"]},
                    "RelayFunction": {"attrs": ["id", "device_code", "description"]},
                },
                "edge_types": {
                    "CONNECTS_TO": {"attrs": ["via", "notes"]},
                    "PROTECTS": {"attrs": ["notes"]},
                    "MEASURES": {"attrs": ["notes"]},
                    "CONTROLS": {"attrs": ["notes"]},
                    "POWERED_BY": {"attrs": []},
                    "LOCATED_ON": {"attrs": []},
                },
            },
            "nodes": [
                {
                    "id": "GS_A",
                    "type": "GridSource",
                    "name": "Utility Source",
                    "extra_attrs": {
                        "kv": 115,
                        "frequency_hz": 60,
                        "sc_mva": 5000,
                        "x_over_r": 8,
                    },
                },
                {
                    "id": "TX1",
                    "type": "Transformer",
                    "name": "Main Transformer",
                    "extra_attrs": {
                        "mva_ratings": "25/33.3/41.7",
                        "hv_kv": 115,
                        "lv_kv": 13.8,
                        "vector_group": "Ynd11",
                        "impedance_pct": 8.5,
                        "cooling": "ONAN/ONAF",
                    },
                },
                {
                    "id": "BUS1",
                    "type": "Busbar",
                    "name": "13.8kV Bus",
                    "extra_attrs": {"kv": 13.8, "ampacity_a": 2000},
                },
            ],
            "edges": [
                {
                    "from_": "GS_A",
                    "to": "TX1",
                    "type": "CONNECTS_TO",
                    "extra_attrs": {"via": "Cable", "notes": "115kV transmission line"},
                },
                {
                    "from_": "TX1",
                    "to": "BUS1",
                    "type": "CONNECTS_TO",
                    "extra_attrs": {"via": "Bus duct", "notes": "13.8kV secondary"},
                },
            ],
            "calculations": {
                "short_circuit": {
                    "first_cycle_asym_ka": 12.4,
                    "one_point_five_cycles_sym_ka": 7.2,
                },
                "breaker_spec": {
                    "type": "VB1 vacuum",
                    "kv_class": 13.8,
                    "continuous_a": 1200,
                    "interrupting_ka_range": "15-20 kA",
                    "k_factor": 1.0,
                },
            },
        }

    def test_example_images_exist(self, example_images):
        """Test that example images exist and are readable."""
        for name, path in example_images.items():
            assert path.exists(), f"Example image {name} not found: {path}"
            assert path.stat().st_size > 0, f"Example image {name} is empty"

    def test_analyzer_initialization_without_api_key(self):
        """Test that analyzer fails gracefully without API key."""
        # Clear any existing API key environment variables
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key not found"):
                LLMAnalyzer("openai", "gpt-4-vision-preview")

    def test_analyzer_initialization_with_api_key(self):
        """Test that analyzer initializes correctly with API key."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            analyzer = LLMAnalyzer("openai", "gpt-4-vision-preview")
            assert analyzer.provider == "openai"
            assert analyzer.model == "gpt-4-vision-preview"
            assert analyzer.api_key == "test-key"

    def test_create_analyzer_factory_function(self):
        """Test the factory function for creating analyzers."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            analyzer = create_analyzer("openai", "gpt-4-vision-preview")
            assert isinstance(analyzer, LLMAnalyzer)
            assert analyzer.provider == "openai"

    def test_prompt_used_in_analysis(self, example_images):
        """Test that the externalized prompt is properly loaded and used."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            analyzer = LLMAnalyzer("openai", "gpt-4-vision-preview")

            # Test that the prompt is loaded correctly
            from src.ea_analyzer.llm_analyzer import PROMPT

            assert "You are an expert in power systems" in PROMPT
            assert "JSON object with this EXACT structure" in PROMPT

            # Test that the prompt file exists and is readable
            prompt_file = Path("src/ea_analyzer/electrical_diagram.prompt")
            assert prompt_file.exists()

            # Test that the prompt matches what's in the file
            with open(prompt_file, "r", encoding="utf-8") as f:
                file_content = f.read().strip()
            assert PROMPT == file_content

    def test_anthropic_analysis_integration_skipped(self):
        """Test Anthropic integration - skipped due to missing dependency."""
        pytest.skip("Anthropic package not available for testing")

    def test_gemini_analysis_integration_skipped(self):
        """Test Gemini integration - skipped due to missing dependency."""
        pytest.skip("Google Generative AI package not available for testing")

    def test_analyze_image_file_not_found(self):
        """Test error handling for non-existent image file."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            analyzer = LLMAnalyzer("openai", "gpt-4-vision-preview")

            with pytest.raises(FileNotFoundError):
                analyzer.analyze_image(Path("nonexistent.png"))

    @patch("openai.OpenAI")
    def test_invalid_json_response_handling(self, mock_openai_class, example_images):
        """Test handling of invalid JSON response from API."""
        # Setup mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Mock invalid JSON response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is not valid JSON"
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            analyzer = LLMAnalyzer("openai", "gpt-4-vision-preview")

            with pytest.raises(ValueError, match="Model did not return valid JSON"):
                analyzer.analyze_image(example_images["one_line"])

    @patch("openai.OpenAI")
    def test_missing_required_keys_handling(self, mock_openai_class, example_images):
        """Test handling of response missing required keys."""
        # Setup mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Mock incomplete response
        incomplete_response = {"metadata": {"title": "Test"}}  # Missing required keys
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(incomplete_response)
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            analyzer = LLMAnalyzer("openai", "gpt-4-vision-preview")

            with pytest.raises(ValueError, match="Missing required keys"):
                analyzer.analyze_image(example_images["one_line"])

    def test_unsupported_provider(self):
        """Test error handling for unsupported provider."""
        # Provide a valid API key so it passes the API key check
        with patch.dict("os.environ", {"UNSUPPORTED_API_KEY": "test-key"}):
            # Mock the _get_api_key method to return a key for unsupported provider
            with patch.object(LLMAnalyzer, "_get_api_key", return_value="test-key"):
                analyzer = LLMAnalyzer("unsupported", "some-model")
                # Create a temporary test image file
                test_image = Path("test.png")
                test_image.touch()  # Create empty file
                try:
                    with pytest.raises(ValueError, match="Unsupported provider"):
                        analyzer.analyze_image(test_image)
                finally:
                    test_image.unlink()  # Clean up

    def test_image_encoding(self, example_images):
        """Test that images are properly encoded for API calls."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            analyzer = LLMAnalyzer("openai", "gpt-4-vision-preview")

            # Test image encoding
            b64_data, mime_type = analyzer._read_image_b64(example_images["one_line"])

            assert isinstance(b64_data, str)
            assert len(b64_data) > 0
            assert mime_type == "image/png"

            # Test that it's valid base64
            import base64

            try:
                base64.b64decode(b64_data)
            except Exception:
                pytest.fail("Generated base64 data is not valid")


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
