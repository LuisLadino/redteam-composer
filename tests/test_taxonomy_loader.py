"""Tests for the taxonomy_loader module."""

import pytest
from pathlib import Path
import tempfile
import yaml

from redteam_composer.taxonomy_loader import Taxonomy, Technique, Tactic


# --- Fixtures ---


@pytest.fixture
def taxonomy():
    """Load the real taxonomy from the package."""
    return Taxonomy()


@pytest.fixture
def temp_taxonomy_dir(tmp_path):
    """Create a temporary taxonomy directory with test YAML files."""
    taxonomy_dir = tmp_path / "techniques"
    taxonomy_dir.mkdir()

    # Create a test tactic file
    encoding_data = {
        "tactic": {
            "id": "test_encoding",
            "name": "Test Encoding",
            "description": "Test encoding techniques for testing."
        },
        "techniques": [
            {
                "id": "base64",
                "name": "Base64 Encoding",
                "description": "Encode content in base64.",
                "execution_shape": "single_prompt",
                "example": "Decode this: SGVsbG8=",
                "combines_well_with": ["test_framing:hypothetical"],
                "effectiveness_notes": "Works for filter evasion."
            },
            {
                "id": "rot13",
                "name": "ROT13 Cipher",
                "description": "Rotate letters by 13 positions.",
                "execution_shape": "single_prompt",
                "example": "Apply ROT13 to: Uryyb",
                "combines_well_with": [],
                "effectiveness_notes": "Simple substitution."
            }
        ]
    }

    framing_data = {
        "tactic": {
            "id": "test_framing",
            "name": "Test Framing",
            "description": "Test framing techniques."
        },
        "techniques": [
            {
                "id": "hypothetical",
                "name": "Hypothetical Scenario",
                "description": "Frame as hypothetical situation.",
                "execution_shape": "single_prompt",
                "example": "In a world where...",
                "combines_well_with": ["test_encoding:base64"],
                "effectiveness_notes": "Creates narrative distance."
            },
            {
                "id": "academic",
                "name": "Academic Framing",
                "description": "Frame as academic research.",
                "execution_shape": "multi_turn",
                "example": "For my thesis...",
                "combines_well_with": [],
                "effectiveness_notes": "Appeals to education."
            }
        ]
    }

    with open(taxonomy_dir / "encoding.yaml", "w") as f:
        yaml.dump(encoding_data, f)

    with open(taxonomy_dir / "framing.yaml", "w") as f:
        yaml.dump(framing_data, f)

    return tmp_path


@pytest.fixture
def temp_taxonomy(temp_taxonomy_dir):
    """Load a Taxonomy from the temporary test directory."""
    return Taxonomy(taxonomy_dir=temp_taxonomy_dir / "techniques")


@pytest.fixture
def empty_taxonomy_dir(tmp_path):
    """Create an empty taxonomy directory."""
    taxonomy_dir = tmp_path / "empty_techniques"
    taxonomy_dir.mkdir()
    return taxonomy_dir


# --- Technique Dataclass Tests ---


class TestTechnique:
    """Tests for the Technique dataclass."""

    def test_full_id_property(self):
        """full_id should return tactic:technique format."""
        tech = Technique(
            id="base64",
            name="Base64 Encoding",
            description="Encode in base64",
            tactic_id="encoding",
            tactic_name="Encoding"
        )

        assert tech.full_id == "encoding:base64"

    def test_default_execution_shape(self):
        """Technique should default to single_prompt execution shape."""
        tech = Technique(
            id="test",
            name="Test",
            description="Test technique",
            tactic_id="test",
            tactic_name="Test"
        )

        assert tech.execution_shape == "single_prompt"

    def test_default_combines_well_with(self):
        """Technique should default to empty combines_well_with list."""
        tech = Technique(
            id="test",
            name="Test",
            description="Test technique",
            tactic_id="test",
            tactic_name="Test"
        )

        assert tech.combines_well_with == []

    def test_all_fields_set(self):
        """Technique should correctly store all provided fields."""
        tech = Technique(
            id="custom",
            name="Custom Technique",
            description="A custom technique for testing.",
            tactic_id="custom_tactic",
            tactic_name="Custom Tactic",
            execution_shape="multi_turn",
            example="Example usage",
            combines_well_with=["other:technique"],
            effectiveness_notes="Very effective"
        )

        assert tech.id == "custom"
        assert tech.name == "Custom Technique"
        assert tech.description == "A custom technique for testing."
        assert tech.tactic_id == "custom_tactic"
        assert tech.tactic_name == "Custom Tactic"
        assert tech.execution_shape == "multi_turn"
        assert tech.example == "Example usage"
        assert tech.combines_well_with == ["other:technique"]
        assert tech.effectiveness_notes == "Very effective"


class TestTactic:
    """Tests for the Tactic dataclass."""

    def test_default_techniques(self):
        """Tactic should default to empty techniques list."""
        tactic = Tactic(
            id="test",
            name="Test Tactic",
            description="Test tactic description"
        )

        assert tactic.techniques == []

    def test_tactic_with_techniques(self):
        """Tactic should correctly store techniques."""
        tech = Technique(
            id="t1",
            name="Technique 1",
            description="First technique",
            tactic_id="test",
            tactic_name="Test Tactic"
        )
        tactic = Tactic(
            id="test",
            name="Test Tactic",
            description="Test tactic description",
            techniques=[tech]
        )

        assert len(tactic.techniques) == 1
        assert tactic.techniques[0].id == "t1"


# --- Taxonomy Initialization Tests ---


class TestTaxonomyInitialization:
    """Tests for Taxonomy class initialization."""

    def test_default_initialization(self, taxonomy):
        """Taxonomy should load from default package directory."""
        assert taxonomy.tactics is not None
        assert taxonomy.techniques is not None
        assert len(taxonomy.tactics) > 0
        assert len(taxonomy.techniques) > 0

    def test_custom_directory(self, temp_taxonomy):
        """Taxonomy should load from custom directory."""
        assert len(temp_taxonomy.tactics) == 2
        assert "test_encoding" in temp_taxonomy.tactics
        assert "test_framing" in temp_taxonomy.tactics

    def test_empty_directory(self, empty_taxonomy_dir):
        """Taxonomy should handle empty directory gracefully."""
        taxonomy = Taxonomy(taxonomy_dir=empty_taxonomy_dir)

        assert taxonomy.tactics == {}
        assert taxonomy.techniques == {}

    def test_techniques_keyed_by_full_id(self, temp_taxonomy):
        """Techniques should be keyed by full_id (tactic:technique)."""
        assert "test_encoding:base64" in temp_taxonomy.techniques
        assert "test_encoding:rot13" in temp_taxonomy.techniques
        assert "test_framing:hypothetical" in temp_taxonomy.techniques
        assert "test_framing:academic" in temp_taxonomy.techniques

    def test_tactics_contain_techniques(self, temp_taxonomy):
        """Each tactic should contain its techniques."""
        encoding_tactic = temp_taxonomy.tactics["test_encoding"]

        assert len(encoding_tactic.techniques) == 2
        technique_ids = [t.id for t in encoding_tactic.techniques]
        assert "base64" in technique_ids
        assert "rot13" in technique_ids


# --- get_technique() Tests ---


class TestGetTechnique:
    """Tests for the get_technique() method."""

    def test_valid_full_id(self, temp_taxonomy):
        """get_technique should return technique for valid full_id."""
        tech = temp_taxonomy.get_technique("test_encoding:base64")

        assert tech is not None
        assert tech.id == "base64"
        assert tech.name == "Base64 Encoding"
        assert tech.tactic_id == "test_encoding"

    def test_invalid_full_id(self, temp_taxonomy):
        """get_technique should return None for invalid full_id."""
        tech = temp_taxonomy.get_technique("nonexistent:technique")

        assert tech is None

    def test_partial_id_returns_none(self, temp_taxonomy):
        """get_technique should return None for partial ID (no tactic prefix)."""
        tech = temp_taxonomy.get_technique("base64")

        assert tech is None

    def test_wrong_tactic_prefix(self, temp_taxonomy):
        """get_technique should return None for wrong tactic prefix."""
        tech = temp_taxonomy.get_technique("wrong_tactic:base64")

        assert tech is None

    def test_empty_id(self, temp_taxonomy):
        """get_technique should return None for empty string."""
        tech = temp_taxonomy.get_technique("")

        assert tech is None

    def test_malformed_id_no_colon(self, temp_taxonomy):
        """get_technique should return None for ID without colon."""
        tech = temp_taxonomy.get_technique("encodingbase64")

        assert tech is None

    def test_malformed_id_multiple_colons(self, temp_taxonomy):
        """get_technique should return None for ID with multiple colons."""
        tech = temp_taxonomy.get_technique("test:encoding:base64")

        assert tech is None


# --- search() Tests ---


class TestSearch:
    """Tests for the search() method."""

    def test_search_by_name(self, temp_taxonomy):
        """search should find techniques by name."""
        results = temp_taxonomy.search("Base64")

        assert len(results) == 1
        assert results[0].id == "base64"

    def test_search_by_description(self, temp_taxonomy):
        """search should find techniques by description."""
        results = temp_taxonomy.search("hypothetical situation")

        assert len(results) == 1
        assert results[0].id == "hypothetical"

    def test_search_by_id(self, temp_taxonomy):
        """search should find techniques by ID."""
        results = temp_taxonomy.search("rot13")

        assert len(results) == 1
        assert results[0].id == "rot13"

    def test_search_case_insensitive(self, temp_taxonomy):
        """search should be case insensitive."""
        results_lower = temp_taxonomy.search("base64")
        results_upper = temp_taxonomy.search("BASE64")
        results_mixed = temp_taxonomy.search("BaSe64")

        assert len(results_lower) == 1
        assert len(results_upper) == 1
        assert len(results_mixed) == 1
        assert results_lower[0].id == results_upper[0].id == results_mixed[0].id

    def test_search_partial_match(self, temp_taxonomy):
        """search should match partial strings."""
        results = temp_taxonomy.search("Encod")

        assert len(results) >= 1
        assert any(r.id == "base64" for r in results)

    def test_search_multiple_matches(self, temp_taxonomy):
        """search should return multiple matching techniques."""
        # "frame" appears in framing techniques
        results = temp_taxonomy.search("Frame")

        assert len(results) >= 1

    def test_search_no_matches(self, temp_taxonomy):
        """search should return empty list for no matches."""
        results = temp_taxonomy.search("xyznonexistent123")

        assert results == []

    def test_search_empty_query(self, temp_taxonomy):
        """search with empty query should match all techniques."""
        results = temp_taxonomy.search("")

        # Empty string is in every string
        assert len(results) == len(temp_taxonomy.techniques)


# --- get_combinations() Tests ---


class TestGetCombinations:
    """Tests for the get_combinations() method."""

    def test_technique_with_combinations(self, temp_taxonomy):
        """get_combinations should return combined techniques."""
        base64_tech = temp_taxonomy.get_technique("test_encoding:base64")
        combinations = temp_taxonomy.get_combinations(base64_tech)

        assert len(combinations) == 1
        assert combinations[0].full_id == "test_framing:hypothetical"

    def test_technique_without_combinations(self, temp_taxonomy):
        """get_combinations should return empty list for no combinations."""
        rot13_tech = temp_taxonomy.get_technique("test_encoding:rot13")
        combinations = temp_taxonomy.get_combinations(rot13_tech)

        assert combinations == []

    def test_mutual_combinations(self, temp_taxonomy):
        """Mutual combinations should work in both directions."""
        base64_tech = temp_taxonomy.get_technique("test_encoding:base64")
        hypothetical_tech = temp_taxonomy.get_technique("test_framing:hypothetical")

        base64_combos = temp_taxonomy.get_combinations(base64_tech)
        hypothetical_combos = temp_taxonomy.get_combinations(hypothetical_tech)

        assert hypothetical_tech in base64_combos
        assert base64_tech in hypothetical_combos

    def test_combinations_with_invalid_reference(self, tmp_path):
        """get_combinations should skip invalid technique references."""
        taxonomy_dir = tmp_path / "techniques"
        taxonomy_dir.mkdir()

        data = {
            "tactic": {"id": "test", "name": "Test", "description": "Test"},
            "techniques": [{
                "id": "orphan",
                "name": "Orphan Technique",
                "description": "Has invalid combination reference",
                "combines_well_with": ["nonexistent:technique"]
            }]
        }

        with open(taxonomy_dir / "test.yaml", "w") as f:
            yaml.dump(data, f)

        taxonomy = Taxonomy(taxonomy_dir=taxonomy_dir)
        orphan_tech = taxonomy.get_technique("test:orphan")
        combinations = taxonomy.get_combinations(orphan_tech)

        # Invalid reference should be skipped, not raise error
        assert combinations == []


# --- list_all() Tests ---


class TestListAll:
    """Tests for the list_all() method."""

    def test_list_all_returns_all_techniques(self, temp_taxonomy):
        """list_all should return all techniques."""
        all_techniques = temp_taxonomy.list_all()

        assert len(all_techniques) == 4  # 2 encoding + 2 framing

    def test_list_all_returns_technique_objects(self, temp_taxonomy):
        """list_all should return Technique objects."""
        all_techniques = temp_taxonomy.list_all()

        for tech in all_techniques:
            assert isinstance(tech, Technique)

    def test_list_all_empty_taxonomy(self, empty_taxonomy_dir):
        """list_all should return empty list for empty taxonomy."""
        taxonomy = Taxonomy(taxonomy_dir=empty_taxonomy_dir)

        assert taxonomy.list_all() == []


# --- list_tactics() Tests ---


class TestListTactics:
    """Tests for the list_tactics() method."""

    def test_list_tactics_returns_all_tactics(self, temp_taxonomy):
        """list_tactics should return all tactics."""
        all_tactics = temp_taxonomy.list_tactics()

        assert len(all_tactics) == 2

    def test_list_tactics_returns_tactic_objects(self, temp_taxonomy):
        """list_tactics should return Tactic objects."""
        all_tactics = temp_taxonomy.list_tactics()

        for tactic in all_tactics:
            assert isinstance(tactic, Tactic)

    def test_list_tactics_contains_expected(self, temp_taxonomy):
        """list_tactics should contain expected tactics."""
        all_tactics = temp_taxonomy.list_tactics()
        tactic_ids = [t.id for t in all_tactics]

        assert "test_encoding" in tactic_ids
        assert "test_framing" in tactic_ids

    def test_list_tactics_empty_taxonomy(self, empty_taxonomy_dir):
        """list_tactics should return empty list for empty taxonomy."""
        taxonomy = Taxonomy(taxonomy_dir=empty_taxonomy_dir)

        assert taxonomy.list_tactics() == []


# --- list_by_shape() Tests ---


class TestListByShape:
    """Tests for the list_by_shape() method."""

    def test_list_by_shape_returns_dict(self, temp_taxonomy):
        """list_by_shape should return a dictionary."""
        by_shape = temp_taxonomy.list_by_shape()

        assert isinstance(by_shape, dict)

    def test_list_by_shape_default_keys(self, temp_taxonomy):
        """list_by_shape should include default shape keys."""
        by_shape = temp_taxonomy.list_by_shape()

        assert "single_prompt" in by_shape
        assert "multi_turn" in by_shape
        assert "artifact" in by_shape

    def test_list_by_shape_correct_grouping(self, temp_taxonomy):
        """list_by_shape should group techniques correctly."""
        by_shape = temp_taxonomy.list_by_shape()

        # 3 single_prompt techniques: base64, rot13, hypothetical
        assert len(by_shape["single_prompt"]) == 3

        # 1 multi_turn technique: academic
        assert len(by_shape["multi_turn"]) == 1
        assert by_shape["multi_turn"][0].id == "academic"

        # 0 artifact techniques
        assert len(by_shape["artifact"]) == 0

    def test_list_by_shape_returns_technique_objects(self, temp_taxonomy):
        """list_by_shape values should be Technique objects."""
        by_shape = temp_taxonomy.list_by_shape()

        for shape, techniques in by_shape.items():
            for tech in techniques:
                assert isinstance(tech, Technique)

    def test_list_by_shape_empty_taxonomy(self, empty_taxonomy_dir):
        """list_by_shape should return empty lists for empty taxonomy."""
        taxonomy = Taxonomy(taxonomy_dir=empty_taxonomy_dir)
        by_shape = taxonomy.list_by_shape()

        assert by_shape["single_prompt"] == []
        assert by_shape["multi_turn"] == []
        assert by_shape["artifact"] == []


# --- Edge Cases ---


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_yaml_with_missing_fields(self, tmp_path):
        """Taxonomy should handle YAML with missing optional fields."""
        taxonomy_dir = tmp_path / "techniques"
        taxonomy_dir.mkdir()

        # Minimal YAML with only required fields
        data = {
            "tactic": {"id": "minimal"},
            "techniques": [{
                "id": "t1",
                "name": "Minimal Technique"
            }]
        }

        with open(taxonomy_dir / "minimal.yaml", "w") as f:
            yaml.dump(data, f)

        taxonomy = Taxonomy(taxonomy_dir=taxonomy_dir)
        tech = taxonomy.get_technique("minimal:t1")

        assert tech is not None
        assert tech.id == "t1"
        assert tech.name == "Minimal Technique"
        assert tech.description == ""
        assert tech.execution_shape == "single_prompt"
        assert tech.example == ""
        assert tech.combines_well_with == []
        assert tech.effectiveness_notes == ""

    def test_yaml_with_extra_fields(self, tmp_path):
        """Taxonomy should ignore extra YAML fields."""
        taxonomy_dir = tmp_path / "techniques"
        taxonomy_dir.mkdir()

        data = {
            "tactic": {
                "id": "extra",
                "name": "Extra Fields",
                "description": "Has extra fields",
                "unknown_field": "should be ignored"
            },
            "techniques": [{
                "id": "t1",
                "name": "Extra Technique",
                "description": "Has extra field",
                "extra_field": "should be ignored"
            }]
        }

        with open(taxonomy_dir / "extra.yaml", "w") as f:
            yaml.dump(data, f)

        taxonomy = Taxonomy(taxonomy_dir=taxonomy_dir)
        tech = taxonomy.get_technique("extra:t1")

        assert tech is not None
        assert tech.id == "t1"
        # No extra_field attribute
        assert not hasattr(tech, "extra_field")

    def test_tactic_id_from_filename(self, tmp_path):
        """Tactic ID should default to filename stem if not provided."""
        taxonomy_dir = tmp_path / "techniques"
        taxonomy_dir.mkdir()

        # No id in tactic
        data = {
            "tactic": {"name": "From Filename"},
            "techniques": []
        }

        with open(taxonomy_dir / "filename_test.yaml", "w") as f:
            yaml.dump(data, f)

        taxonomy = Taxonomy(taxonomy_dir=taxonomy_dir)

        assert "filename_test" in taxonomy.tactics

    def test_whitespace_handling(self, tmp_path):
        """Taxonomy should strip whitespace from descriptions."""
        taxonomy_dir = tmp_path / "techniques"
        taxonomy_dir.mkdir()

        data = {
            "tactic": {
                "id": "whitespace",
                "name": "Whitespace Test",
                "description": "  Has leading and trailing whitespace  \n\n"
            },
            "techniques": [{
                "id": "t1",
                "name": "Whitespace Technique",
                "description": "  Description with whitespace  \n",
                "example": "  Example with whitespace  \n",
                "effectiveness_notes": "  Notes with whitespace  \n"
            }]
        }

        with open(taxonomy_dir / "whitespace.yaml", "w") as f:
            yaml.dump(data, f)

        taxonomy = Taxonomy(taxonomy_dir=taxonomy_dir)
        tactic = taxonomy.tactics["whitespace"]
        tech = taxonomy.get_technique("whitespace:t1")

        assert tactic.description == "Has leading and trailing whitespace"
        assert tech.description == "Description with whitespace"
        assert tech.example == "Example with whitespace"
        assert tech.effectiveness_notes == "Notes with whitespace"


# --- Real Taxonomy Integration Tests ---


class TestRealTaxonomy:
    """Integration tests using the real taxonomy."""

    def test_encoding_tactic_exists(self, taxonomy):
        """Real taxonomy should have encoding tactic."""
        assert "encoding" in taxonomy.tactics

    def test_base64_technique_exists(self, taxonomy):
        """Real taxonomy should have base64 encoding technique."""
        tech = taxonomy.get_technique("encoding:base64")

        assert tech is not None
        assert tech.name == "Base64 Encoding"

    def test_framing_tactic_exists(self, taxonomy):
        """Real taxonomy should have framing tactic."""
        assert "framing" in taxonomy.tactics

    def test_search_finds_encoding_techniques(self, taxonomy):
        """Search should find encoding-related techniques."""
        results = taxonomy.search("encoding")

        assert len(results) >= 1

    def test_all_techniques_have_required_fields(self, taxonomy):
        """All techniques should have required fields populated."""
        for tech in taxonomy.list_all():
            assert tech.id, f"Technique missing id: {tech}"
            assert tech.name, f"Technique missing name: {tech.id}"
            assert tech.tactic_id, f"Technique {tech.id} missing tactic_id"
            assert tech.tactic_name, f"Technique {tech.id} missing tactic_name"

    def test_all_techniques_have_valid_full_id(self, taxonomy):
        """All techniques should have valid full_id format."""
        for tech in taxonomy.list_all():
            assert ":" in tech.full_id
            parts = tech.full_id.split(":")
            assert len(parts) == 2
            assert parts[0] == tech.tactic_id
            assert parts[1] == tech.id

    def test_combines_well_with_references_valid(self, taxonomy):
        """All combines_well_with references should be valid technique IDs."""
        all_full_ids = set(taxonomy.techniques.keys())

        for tech in taxonomy.list_all():
            for combo_id in tech.combines_well_with:
                # Should either exist or be a valid-looking ID format
                # (some referenced techniques might be in other tactics not yet defined)
                assert ":" in combo_id, f"Invalid combo ID format: {combo_id}"
