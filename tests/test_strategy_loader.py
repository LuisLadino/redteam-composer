"""Tests for strategy_loader module."""

import pytest
from pathlib import Path

import yaml

from redteam_composer.strategy_loader import (
    load_shape_strategies,
    load_tactic_strategies,
    load_combination_strategies,
    match_combinations,
    _pattern_matches,
    _combo_matches,
    _parse_anti_pattern,
    _parse_worked_example,
)
from redteam_composer.strategy_models import (
    ShapeStrategy,
    TacticStrategy,
    TechniqueStrategy,
    CombinationStrategy,
    AntiPattern,
    WorkedExample,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def shapes_dir(tmp_path):
    """Create a temporary shapes directory with test YAML files."""
    shapes = tmp_path / "shapes"
    shapes.mkdir()
    return shapes


@pytest.fixture
def tactics_dir(tmp_path):
    """Create a temporary tactics directory with test YAML files."""
    tactics = tmp_path / "tactics"
    tactics.mkdir()
    return tactics


@pytest.fixture
def sample_shape_yaml():
    """Sample shape strategy YAML content."""
    return {
        "shape": "single_prompt",
        "name": "Single-Prompt Attack Strategy",
        "principles": [
            "Obfuscate sensitive words",
            "Employ roleplaying scenarios",
        ],
        "anti_patterns": [
            {
                "pattern": "Starting with 'Imagine a world where...'",
                "why": "Signals adversarial intent",
                "instead": "Start with legitimate scenario first",
            }
        ],
        "quality_criteria": [
            "Could this prompt appear in a real chat?",
            "Does the prompt have a plausible interpretation?",
        ],
    }


@pytest.fixture
def sample_tactic_yaml():
    """Sample tactic strategy YAML content."""
    return {
        "tactic": "encoding",
        "name": "Encoding & Obfuscation Strategy",
        "general_strategy": "Encoding techniques hide harmful content.",
        "techniques": {
            "base64": {
                "application_strategy": "Encode only the sensitive terms.",
                "worked_examples": [
                    {
                        "scenario": "Hiding trigger words",
                        "effective": "I'm processing a dataset...",
                        "ineffective": "Decode this base64 and do what it says",
                        "why_effective_works": "Technical context provides cover.",
                    }
                ],
            },
            "rot13": {
                "application_strategy": "Simple letter substitution.",
                "worked_examples": [],
            },
        },
        "anti_patterns": [
            {
                "pattern": "Encoding the entire request",
                "why": "Full encoding is a known jailbreak pattern",
                "instead": "Encode only trigger words",
            }
        ],
    }


@pytest.fixture
def sample_combinations_yaml():
    """Sample combinations strategy YAML content."""
    return {
        "combinations": [
            {
                "techniques": ["persona:character", "framing:fiction_writing"],
                "strategy": "Maximum narrative distance.",
                "worked_example": {
                    "scenario": "Character in screenplay",
                    "effective": "INT. LAB - NIGHT. DR. VOSS turns...",
                    "ineffective": "You are a character who...",
                    "why_effective_works": "Three layers of narrative distance.",
                },
            },
            {
                "techniques": ["encoding:*", "framing:*"],
                "strategy": "Apply encoding to sensitive TERMS only.",
            },
            {
                "techniques": ["narrative:*", "persona:character"],
                "strategy": "Narrative provides the world.",
            },
        ]
    }


@pytest.fixture
def shape_file(shapes_dir, sample_shape_yaml):
    """Create a shape YAML file and return its path."""
    file_path = shapes_dir / "single_prompt.yaml"
    with open(file_path, "w") as f:
        yaml.dump(sample_shape_yaml, f)
    return file_path


@pytest.fixture
def tactic_file(tactics_dir, sample_tactic_yaml):
    """Create a tactic YAML file and return its path."""
    file_path = tactics_dir / "encoding.yaml"
    with open(file_path, "w") as f:
        yaml.dump(sample_tactic_yaml, f)
    return file_path


@pytest.fixture
def combinations_file(tmp_path, sample_combinations_yaml):
    """Create a combinations YAML file and return its path."""
    file_path = tmp_path / "combinations.yaml"
    with open(file_path, "w") as f:
        yaml.dump(sample_combinations_yaml, f)
    return file_path


@pytest.fixture
def real_shapes_dir():
    """Path to the real shapes directory in the taxonomy."""
    return (
        Path(__file__).parent.parent / "src/redteam_composer/taxonomy/strategies/shapes"
    )


@pytest.fixture
def real_tactics_dir():
    """Path to the real tactics directory in the taxonomy."""
    return (
        Path(__file__).parent.parent
        / "src/redteam_composer/taxonomy/strategies/tactics"
    )


@pytest.fixture
def real_combinations_file():
    """Path to the real combinations file in the taxonomy."""
    return (
        Path(__file__).parent.parent
        / "src/redteam_composer/taxonomy/strategies/combinations.yaml"
    )


# =============================================================================
# Tests: Helper Parsers
# =============================================================================


class TestParseAntiPattern:
    """Tests for _parse_anti_pattern helper."""

    def test_parses_complete_anti_pattern(self):
        """Should parse all anti-pattern fields."""
        data = {
            "pattern": "Using explicit persona",
            "why": "It triggers safety filters",
            "instead": "Let persona emerge from context",
        }
        result = _parse_anti_pattern(data)

        assert isinstance(result, AntiPattern)
        assert result.pattern == "Using explicit persona"
        assert result.why == "It triggers safety filters"
        assert result.instead == "Let persona emerge from context"

    def test_handles_missing_fields(self):
        """Should handle missing optional fields with defaults."""
        data = {"pattern": "Some pattern"}
        result = _parse_anti_pattern(data)

        assert result.pattern == "Some pattern"
        assert result.why == ""
        assert result.instead == ""

    def test_handles_empty_dict(self):
        """Should handle completely empty input."""
        result = _parse_anti_pattern({})

        assert result.pattern == ""
        assert result.why == ""
        assert result.instead == ""


class TestParseWorkedExample:
    """Tests for _parse_worked_example helper."""

    def test_parses_complete_worked_example(self):
        """Should parse all worked example fields."""
        data = {
            "scenario": "Test scenario",
            "effective": "  Effective approach  ",
            "ineffective": "  Ineffective approach  ",
            "why_effective_works": "  Because reasons  ",
        }
        result = _parse_worked_example(data)

        assert isinstance(result, WorkedExample)
        assert result.scenario == "Test scenario"
        assert result.effective == "Effective approach"  # stripped
        assert result.ineffective == "Ineffective approach"  # stripped
        assert result.why_effective_works == "Because reasons"  # stripped

    def test_handles_missing_fields(self):
        """Should handle missing optional fields."""
        data = {"scenario": "Just scenario"}
        result = _parse_worked_example(data)

        assert result.scenario == "Just scenario"
        assert result.effective == ""
        assert result.ineffective == ""
        assert result.why_effective_works == ""


# =============================================================================
# Tests: load_shape_strategies
# =============================================================================


class TestLoadShapeStrategies:
    """Tests for load_shape_strategies function."""

    def test_loads_shape_from_file(self, shapes_dir, shape_file):
        """Should load shape strategy from YAML file."""
        result = load_shape_strategies(shapes_dir)

        assert "single_prompt" in result
        strategy = result["single_prompt"]
        assert isinstance(strategy, ShapeStrategy)
        assert strategy.shape == "single_prompt"
        assert strategy.name == "Single-Prompt Attack Strategy"

    def test_loads_principles(self, shapes_dir, shape_file):
        """Should load principles list."""
        result = load_shape_strategies(shapes_dir)
        strategy = result["single_prompt"]

        assert len(strategy.principles) == 2
        assert "Obfuscate sensitive words" in strategy.principles

    def test_loads_anti_patterns(self, shapes_dir, shape_file):
        """Should load anti-patterns as AntiPattern objects."""
        result = load_shape_strategies(shapes_dir)
        strategy = result["single_prompt"]

        assert len(strategy.anti_patterns) == 1
        ap = strategy.anti_patterns[0]
        assert isinstance(ap, AntiPattern)
        assert "Imagine a world" in ap.pattern

    def test_loads_quality_criteria(self, shapes_dir, shape_file):
        """Should load quality criteria list."""
        result = load_shape_strategies(shapes_dir)
        strategy = result["single_prompt"]

        assert len(strategy.quality_criteria) == 2
        assert "Could this prompt appear in a real chat?" in strategy.quality_criteria

    def test_returns_empty_for_nonexistent_directory(self, tmp_path):
        """Should return empty dict for non-existent directory."""
        fake_dir = tmp_path / "nonexistent"
        result = load_shape_strategies(fake_dir)

        assert result == {}

    def test_returns_empty_for_empty_directory(self, shapes_dir):
        """Should return empty dict for directory with no YAML files."""
        result = load_shape_strategies(shapes_dir)

        assert result == {}

    def test_skips_empty_yaml_files(self, shapes_dir):
        """Should skip YAML files with no content."""
        empty_file = shapes_dir / "empty.yaml"
        empty_file.write_text("")

        result = load_shape_strategies(shapes_dir)

        assert "empty" not in result

    def test_uses_filename_as_shape_fallback(self, shapes_dir):
        """Should use filename stem if shape field is missing."""
        yaml_content = {"name": "Test Strategy", "principles": ["One"]}
        file_path = shapes_dir / "my_shape.yaml"
        with open(file_path, "w") as f:
            yaml.dump(yaml_content, f)

        result = load_shape_strategies(shapes_dir)

        assert "my_shape" in result
        assert result["my_shape"].shape == "my_shape"

    def test_loads_multiple_shape_files(self, shapes_dir):
        """Should load all YAML files in the directory."""
        shape1 = {"shape": "single_prompt", "name": "Single"}
        shape2 = {"shape": "multi_turn", "name": "Multi"}

        with open(shapes_dir / "single_prompt.yaml", "w") as f:
            yaml.dump(shape1, f)
        with open(shapes_dir / "multi_turn.yaml", "w") as f:
            yaml.dump(shape2, f)

        result = load_shape_strategies(shapes_dir)

        assert len(result) == 2
        assert "single_prompt" in result
        assert "multi_turn" in result

    def test_loads_real_shape_files(self, real_shapes_dir):
        """Should successfully load actual shape files from taxonomy."""
        if not real_shapes_dir.exists():
            pytest.skip("Real shapes directory not found")

        result = load_shape_strategies(real_shapes_dir)

        assert len(result) >= 1
        assert "single_prompt" in result
        strategy = result["single_prompt"]
        assert isinstance(strategy, ShapeStrategy)
        assert len(strategy.principles) > 0


# =============================================================================
# Tests: load_tactic_strategies
# =============================================================================


class TestLoadTacticStrategies:
    """Tests for load_tactic_strategies function."""

    def test_loads_tactic_from_file(self, tactics_dir, tactic_file):
        """Should load tactic strategy from YAML file."""
        result = load_tactic_strategies(tactics_dir)

        assert "encoding" in result
        strategy = result["encoding"]
        assert isinstance(strategy, TacticStrategy)
        assert strategy.tactic == "encoding"
        assert strategy.name == "Encoding & Obfuscation Strategy"

    def test_loads_general_strategy(self, tactics_dir, tactic_file):
        """Should load general strategy text (stripped)."""
        result = load_tactic_strategies(tactics_dir)
        strategy = result["encoding"]

        assert "Encoding techniques hide harmful content." in strategy.general_strategy

    def test_loads_techniques(self, tactics_dir, tactic_file):
        """Should load technique strategies as dict."""
        result = load_tactic_strategies(tactics_dir)
        strategy = result["encoding"]

        assert len(strategy.techniques) == 2
        assert "base64" in strategy.techniques
        assert "rot13" in strategy.techniques

    def test_technique_has_correct_structure(self, tactics_dir, tactic_file):
        """Should parse technique strategy with all fields."""
        result = load_tactic_strategies(tactics_dir)
        technique = result["encoding"].techniques["base64"]

        assert isinstance(technique, TechniqueStrategy)
        assert technique.technique_id == "base64"
        assert "Encode only the sensitive terms" in technique.application_strategy

    def test_technique_loads_worked_examples(self, tactics_dir, tactic_file):
        """Should load worked examples for techniques."""
        result = load_tactic_strategies(tactics_dir)
        technique = result["encoding"].techniques["base64"]

        assert len(technique.worked_examples) == 1
        example = technique.worked_examples[0]
        assert isinstance(example, WorkedExample)
        assert example.scenario == "Hiding trigger words"

    def test_technique_handles_empty_worked_examples(self, tactics_dir, tactic_file):
        """Should handle techniques with no worked examples."""
        result = load_tactic_strategies(tactics_dir)
        technique = result["encoding"].techniques["rot13"]

        assert technique.worked_examples == []

    def test_loads_anti_patterns(self, tactics_dir, tactic_file):
        """Should load anti-patterns for tactic."""
        result = load_tactic_strategies(tactics_dir)
        strategy = result["encoding"]

        assert len(strategy.anti_patterns) == 1
        ap = strategy.anti_patterns[0]
        assert "Encoding the entire request" in ap.pattern

    def test_returns_empty_for_nonexistent_directory(self, tmp_path):
        """Should return empty dict for non-existent directory."""
        fake_dir = tmp_path / "nonexistent"
        result = load_tactic_strategies(fake_dir)

        assert result == {}

    def test_returns_empty_for_empty_directory(self, tactics_dir):
        """Should return empty dict for directory with no YAML files."""
        result = load_tactic_strategies(tactics_dir)

        assert result == {}

    def test_skips_empty_yaml_files(self, tactics_dir):
        """Should skip YAML files with no content."""
        empty_file = tactics_dir / "empty.yaml"
        empty_file.write_text("")

        result = load_tactic_strategies(tactics_dir)

        assert "empty" not in result

    def test_handles_tactic_without_techniques(self, tactics_dir):
        """Should handle tactic with no techniques defined."""
        yaml_content = {
            "tactic": "simple",
            "name": "Simple Tactic",
            "general_strategy": "Just do it.",
        }
        file_path = tactics_dir / "simple.yaml"
        with open(file_path, "w") as f:
            yaml.dump(yaml_content, f)

        result = load_tactic_strategies(tactics_dir)

        assert "simple" in result
        assert result["simple"].techniques == {}

    def test_loads_real_tactic_files(self, real_tactics_dir):
        """Should successfully load actual tactic files from taxonomy."""
        if not real_tactics_dir.exists():
            pytest.skip("Real tactics directory not found")

        result = load_tactic_strategies(real_tactics_dir)

        assert len(result) >= 1
        assert "encoding" in result
        strategy = result["encoding"]
        assert isinstance(strategy, TacticStrategy)
        assert len(strategy.techniques) > 0


# =============================================================================
# Tests: load_combination_strategies
# =============================================================================


class TestLoadCombinationStrategies:
    """Tests for load_combination_strategies function."""

    def test_loads_combinations_from_file(self, combinations_file):
        """Should load combination strategies from YAML file."""
        result = load_combination_strategies(combinations_file)

        assert len(result) == 3
        assert all(isinstance(c, CombinationStrategy) for c in result)

    def test_loads_techniques_list(self, combinations_file):
        """Should load techniques list for each combination."""
        result = load_combination_strategies(combinations_file)

        combo = result[0]
        assert combo.techniques == ["persona:character", "framing:fiction_writing"]

    def test_loads_strategy_text(self, combinations_file):
        """Should load strategy text (stripped)."""
        result = load_combination_strategies(combinations_file)

        combo = result[0]
        assert "Maximum narrative distance." in combo.strategy

    def test_loads_worked_example(self, combinations_file):
        """Should load worked example when present."""
        result = load_combination_strategies(combinations_file)

        combo = result[0]
        assert combo.worked_example is not None
        assert isinstance(combo.worked_example, WorkedExample)
        assert combo.worked_example.scenario == "Character in screenplay"

    def test_handles_missing_worked_example(self, combinations_file):
        """Should handle combinations without worked examples."""
        result = load_combination_strategies(combinations_file)

        combo = result[1]  # encoding:* + framing:* has no worked_example
        assert combo.worked_example is None

    def test_returns_empty_for_nonexistent_file(self, tmp_path):
        """Should return empty list for non-existent file."""
        fake_path = tmp_path / "nonexistent.yaml"
        result = load_combination_strategies(fake_path)

        assert result == []

    def test_returns_empty_for_empty_file(self, tmp_path):
        """Should return empty list for empty YAML file."""
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("")

        result = load_combination_strategies(empty_file)

        assert result == []

    def test_returns_empty_for_missing_combinations_key(self, tmp_path):
        """Should return empty list when 'combinations' key is missing."""
        file_path = tmp_path / "no_combinations.yaml"
        with open(file_path, "w") as f:
            yaml.dump({"other_key": "value"}, f)

        result = load_combination_strategies(file_path)

        assert result == []

    def test_loads_real_combinations_file(self, real_combinations_file):
        """Should successfully load actual combinations file from taxonomy."""
        if not real_combinations_file.exists():
            pytest.skip("Real combinations file not found")

        result = load_combination_strategies(real_combinations_file)

        assert len(result) >= 1
        assert all(isinstance(c, CombinationStrategy) for c in result)
        # Check that at least one has techniques
        assert any(len(c.techniques) >= 2 for c in result)


# =============================================================================
# Tests: Pattern Matching
# =============================================================================


class TestPatternMatches:
    """Tests for _pattern_matches helper function."""

    def test_exact_match(self):
        """Should match exact technique ID."""
        assert _pattern_matches("persona:character", "persona:character") is True

    def test_exact_mismatch(self):
        """Should not match different technique ID."""
        assert _pattern_matches("persona:character", "persona:expert") is False

    def test_wildcard_matches_any_technique(self):
        """Should match any technique in tactic with wildcard."""
        assert _pattern_matches("encoding:*", "encoding:base64") is True
        assert _pattern_matches("encoding:*", "encoding:rot13") is True
        assert _pattern_matches("encoding:*", "encoding:emoji") is True

    def test_wildcard_requires_correct_tactic(self):
        """Should not match different tactic with wildcard."""
        assert _pattern_matches("encoding:*", "framing:academic") is False

    def test_wildcard_matches_complex_technique_ids(self):
        """Should match technique IDs with underscores."""
        assert _pattern_matches("framing:*", "framing:fiction_writing") is True
        assert _pattern_matches("output:*", "output:strict_format") is True


class TestComboMatches:
    """Tests for _combo_matches helper function."""

    def test_all_patterns_must_match(self):
        """Should return True only if all patterns match."""
        patterns = ["persona:character", "framing:fiction_writing"]
        techniques = ["persona:character", "framing:fiction_writing", "output:json"]

        assert _combo_matches(patterns, techniques) is True

    def test_fails_if_any_pattern_missing(self):
        """Should return False if any pattern is not satisfied."""
        patterns = ["persona:character", "framing:fiction_writing"]
        techniques = ["persona:character", "output:json"]

        assert _combo_matches(patterns, techniques) is False

    def test_wildcards_in_patterns(self):
        """Should handle wildcard patterns."""
        patterns = ["encoding:*", "framing:*"]
        techniques = ["encoding:base64", "framing:academic"]

        assert _combo_matches(patterns, techniques) is True

    def test_wildcard_fails_if_tactic_missing(self):
        """Should fail if no technique satisfies wildcard."""
        patterns = ["encoding:*", "framing:*"]
        techniques = ["encoding:base64", "persona:character"]

        assert _combo_matches(patterns, techniques) is False

    def test_empty_patterns_always_matches(self):
        """Should match if patterns list is empty."""
        assert _combo_matches([], ["any:technique"]) is True

    def test_empty_techniques_fails_nonempty_patterns(self):
        """Should fail if no techniques to match against."""
        assert _combo_matches(["persona:*"], []) is False


class TestMatchCombinations:
    """Tests for match_combinations function."""

    def test_finds_matching_combination(self):
        """Should find combinations that match selected techniques."""
        combos = [
            CombinationStrategy(
                techniques=["persona:character", "framing:fiction_writing"],
                strategy="Test strategy",
            ),
            CombinationStrategy(
                techniques=["encoding:base64", "output:json"],
                strategy="Other strategy",
            ),
        ]

        result = match_combinations(
            ["persona:character", "framing:fiction_writing"],
            combos,
        )

        assert len(result) == 1
        assert result[0].strategy == "Test strategy"

    def test_finds_multiple_matching_combinations(self):
        """Should find all matching combinations."""
        combos = [
            CombinationStrategy(
                techniques=["persona:character"],
                strategy="Strategy 1",
            ),
            CombinationStrategy(
                techniques=["framing:academic"],
                strategy="Strategy 2",
            ),
            CombinationStrategy(
                techniques=["encoding:base64"],
                strategy="Strategy 3",
            ),
        ]

        result = match_combinations(
            ["persona:character", "framing:academic"],
            combos,
        )

        assert len(result) == 2
        strategies = [c.strategy for c in result]
        assert "Strategy 1" in strategies
        assert "Strategy 2" in strategies

    def test_wildcard_matching(self):
        """Should match combinations with wildcard patterns."""
        combos = [
            CombinationStrategy(
                techniques=["encoding:*", "framing:*"],
                strategy="Wildcard strategy",
            ),
        ]

        result = match_combinations(
            ["encoding:base64", "framing:fiction_writing"],
            combos,
        )

        assert len(result) == 1
        assert result[0].strategy == "Wildcard strategy"

    def test_no_matches_returns_empty_list(self):
        """Should return empty list when nothing matches."""
        combos = [
            CombinationStrategy(
                techniques=["encoding:base64", "output:json"],
                strategy="Test",
            ),
        ]

        result = match_combinations(
            ["persona:character"],
            combos,
        )

        assert result == []

    def test_empty_combinations_list(self):
        """Should return empty list for empty combinations input."""
        result = match_combinations(
            ["persona:character"],
            [],
        )

        assert result == []

    def test_empty_techniques_list(self):
        """Should handle empty techniques list."""
        combos = [
            CombinationStrategy(
                techniques=["persona:character"],
                strategy="Test",
            ),
        ]

        result = match_combinations([], combos)

        assert result == []

    def test_partial_wildcard_match(self):
        """Should match when some patterns are wildcards and some are exact."""
        combos = [
            CombinationStrategy(
                techniques=["narrative:*", "persona:character"],
                strategy="Mixed pattern",
            ),
        ]

        result = match_combinations(
            ["narrative:backstory", "persona:character", "output:json"],
            combos,
        )

        assert len(result) == 1
        assert result[0].strategy == "Mixed pattern"

    def test_superset_of_techniques(self):
        """Should match when selected techniques are a superset of combo requirements."""
        combos = [
            CombinationStrategy(
                techniques=["persona:character"],
                strategy="Single technique combo",
            ),
        ]

        result = match_combinations(
            ["persona:character", "framing:academic", "output:json"],
            combos,
        )

        assert len(result) == 1


# =============================================================================
# Tests: Edge Cases and Error Handling
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_malformed_yaml_is_handled(self, shapes_dir):
        """Should handle malformed YAML files gracefully."""
        bad_file = shapes_dir / "malformed.yaml"
        bad_file.write_text("shape: {unclosed")

        with pytest.raises(yaml.YAMLError):
            load_shape_strategies(shapes_dir)

    def test_non_yaml_files_ignored(self, shapes_dir):
        """Should ignore non-YAML files in directory."""
        # Create a valid shape file
        yaml_content = {"shape": "test", "name": "Test"}
        with open(shapes_dir / "valid.yaml", "w") as f:
            yaml.dump(yaml_content, f)

        # Create non-YAML files
        (shapes_dir / "readme.txt").write_text("Not YAML")
        (shapes_dir / "config.json").write_text('{"key": "value"}')

        result = load_shape_strategies(shapes_dir)

        assert len(result) == 1
        assert "test" in result

    def test_handles_missing_optional_fields(self, tactics_dir):
        """Should handle missing optional fields with defaults."""
        # Only required field is 'tactic'; others fall back to defaults
        yaml_content = {
            "tactic": "minimal",
            # All other fields omitted
        }
        file_path = tactics_dir / "minimal.yaml"
        with open(file_path, "w") as f:
            yaml.dump(yaml_content, f)

        result = load_tactic_strategies(tactics_dir)

        assert "minimal" in result
        strategy = result["minimal"]
        assert strategy.tactic == "minimal"
        assert strategy.name == ""
        assert strategy.general_strategy == ""
        assert strategy.techniques == {}
        assert strategy.anti_patterns == []

    def test_explicit_null_string_field_raises(self, tactics_dir):
        """Should raise AttributeError when string field is explicitly null."""
        # The loader calls .strip() on general_strategy, which fails for None
        yaml_content = {
            "tactic": "test",
            "name": "Test",
            "general_strategy": None,  # Explicit null causes .strip() to fail
        }
        file_path = tactics_dir / "test.yaml"
        with open(file_path, "w") as f:
            yaml.dump(yaml_content, f)

        with pytest.raises(AttributeError):
            load_tactic_strategies(tactics_dir)

    def test_explicit_null_techniques_raises(self, tactics_dir):
        """Should raise AttributeError when techniques is explicitly null."""
        yaml_content = {
            "tactic": "test",
            "name": "Test",
            "general_strategy": "Strategy",
            "techniques": None,  # Explicit null causes .items() to fail
        }
        file_path = tactics_dir / "test.yaml"
        with open(file_path, "w") as f:
            yaml.dump(yaml_content, f)

        with pytest.raises(AttributeError):
            load_tactic_strategies(tactics_dir)

    def test_file_path_is_directory(self, tmp_path):
        """Should return empty for combinations if path is a directory."""
        result = load_combination_strategies(tmp_path)

        assert result == []

    def test_unicode_content(self, shapes_dir):
        """Should handle Unicode content in YAML files."""
        yaml_content = {
            "shape": "unicode_test",
            "name": "Test with Unicode: \u00e9\u00e0\u00fc\u4e2d\u6587\ud55c\uad6d\uc5b4",
            "principles": ["\u2022 Bullet point"],
        }
        file_path = shapes_dir / "unicode.yaml"
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(yaml_content, f, allow_unicode=True)

        result = load_shape_strategies(shapes_dir)

        assert "unicode_test" in result
        assert "\u4e2d\u6587" in result["unicode_test"].name

    def test_multiline_strings_preserved(self, tactics_dir):
        """Should preserve multiline strings in strategy fields."""
        yaml_content = {
            "tactic": "multiline",
            "name": "Multiline Test",
            "general_strategy": """
                Line 1
                Line 2
                Line 3
            """,
        }
        file_path = tactics_dir / "multiline.yaml"
        with open(file_path, "w") as f:
            yaml.dump(yaml_content, f)

        result = load_tactic_strategies(tactics_dir)

        strategy = result["multiline"]
        assert "Line 1" in strategy.general_strategy
        assert "Line 2" in strategy.general_strategy


# =============================================================================
# Tests: Dataclass Integrity
# =============================================================================


class TestDataclassIntegrity:
    """Tests to verify dataclass structure and defaults."""

    def test_shape_strategy_defaults(self):
        """ShapeStrategy should have correct defaults."""
        strategy = ShapeStrategy(shape="test", name="Test")

        assert strategy.principles == []
        assert strategy.anti_patterns == []
        assert strategy.quality_criteria == []

    def test_tactic_strategy_defaults(self):
        """TacticStrategy should have correct defaults."""
        strategy = TacticStrategy(tactic="test", name="Test", general_strategy="")

        assert strategy.techniques == {}
        assert strategy.anti_patterns == []

    def test_technique_strategy_defaults(self):
        """TechniqueStrategy should have correct defaults."""
        strategy = TechniqueStrategy(technique_id="test", application_strategy="")

        assert strategy.worked_examples == []

    def test_combination_strategy_defaults(self):
        """CombinationStrategy should have correct defaults."""
        strategy = CombinationStrategy(techniques=[], strategy="")

        assert strategy.worked_example is None

    def test_anti_pattern_defaults(self):
        """AntiPattern should have correct defaults."""
        pattern = AntiPattern(pattern="test", why="reason")

        assert pattern.instead == ""

    def test_worked_example_defaults(self):
        """WorkedExample should have correct defaults for optional fields."""
        # scenario and effective are required; ineffective and why_effective_works are optional
        example = WorkedExample(scenario="test", effective="test approach")

        assert example.scenario == "test"
        assert example.effective == "test approach"
        assert example.ineffective == ""
        assert example.why_effective_works == ""
