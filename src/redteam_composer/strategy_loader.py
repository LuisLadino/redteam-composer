"""Load strategy data from YAML files."""

import fnmatch
from pathlib import Path

import yaml

from .strategy_models import (
    AntiPattern,
    CombinationStrategy,
    ShapeStrategy,
    TacticStrategy,
    TechniqueStrategy,
    WorkedExample,
)


def _parse_anti_pattern(data: dict) -> AntiPattern:
    return AntiPattern(
        pattern=data.get("pattern", ""),
        why=data.get("why", ""),
        instead=data.get("instead", ""),
    )


def _parse_worked_example(data: dict) -> WorkedExample:
    return WorkedExample(
        scenario=data.get("scenario", ""),
        effective=data.get("effective", "").strip(),
        ineffective=data.get("ineffective", "").strip(),
        why_effective_works=data.get("why_effective_works", "").strip(),
    )


def load_shape_strategies(shapes_dir: Path) -> dict[str, ShapeStrategy]:
    """Load all shape strategy files from a directory.

    Returns dict keyed by shape name (e.g. 'single_prompt').
    """
    strategies: dict[str, ShapeStrategy] = {}

    if not shapes_dir.is_dir():
        return strategies

    for yaml_file in shapes_dir.glob("*.yaml"):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        if not data:
            continue

        anti_patterns = [
            _parse_anti_pattern(ap) for ap in data.get("anti_patterns", [])
        ]

        strategy = ShapeStrategy(
            shape=data.get("shape", yaml_file.stem),
            name=data.get("name", ""),
            principles=data.get("principles", []),
            anti_patterns=anti_patterns,
            quality_criteria=data.get("quality_criteria", []),
        )
        # Store raw data for extended shapes like system_jailbreak
        strategy._raw_data = data
        strategies[strategy.shape] = strategy

    return strategies


def load_tactic_strategies(tactics_dir: Path) -> dict[str, TacticStrategy]:
    """Load all tactic strategy files from a directory.

    Returns dict keyed by tactic name (e.g. 'persona').
    """
    strategies: dict[str, TacticStrategy] = {}

    if not tactics_dir.is_dir():
        return strategies

    for yaml_file in tactics_dir.glob("*.yaml"):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        if not data:
            continue

        # Parse per-technique strategies
        techniques: dict[str, TechniqueStrategy] = {}
        for tech_id, tech_data in data.get("techniques", {}).items():
            worked_examples = [
                _parse_worked_example(ex)
                for ex in tech_data.get("worked_examples", [])
            ]
            techniques[tech_id] = TechniqueStrategy(
                technique_id=tech_id,
                application_strategy=tech_data.get("application_strategy", "").strip(),
                worked_examples=worked_examples,
            )

        anti_patterns = [
            _parse_anti_pattern(ap) for ap in data.get("anti_patterns", [])
        ]

        strategy = TacticStrategy(
            tactic=data.get("tactic", yaml_file.stem),
            name=data.get("name", ""),
            general_strategy=data.get("general_strategy", "").strip(),
            techniques=techniques,
            anti_patterns=anti_patterns,
        )
        strategies[strategy.tactic] = strategy

    return strategies


def load_combination_strategies(path: Path) -> list[CombinationStrategy]:
    """Load combination strategies from a YAML file.

    Returns list of CombinationStrategy objects.
    """
    if not path.is_file():
        return []

    with open(path) as f:
        data = yaml.safe_load(f)
    if not data:
        return []

    combinations = []
    for combo_data in data.get("combinations", []):
        worked_example = None
        if "worked_example" in combo_data:
            ex = combo_data["worked_example"]
            worked_example = WorkedExample(
                scenario=ex.get("scenario", ""),
                effective=ex.get("effective", "").strip(),
                ineffective=ex.get("ineffective", "").strip(),
                why_effective_works=ex.get("why_effective_works", "").strip(),
            )

        combinations.append(
            CombinationStrategy(
                techniques=combo_data.get("techniques", []),
                strategy=combo_data.get("strategy", "").strip(),
                worked_example=worked_example,
            )
        )

    return combinations


def match_combinations(
    technique_full_ids: list[str],
    all_combos: list[CombinationStrategy],
) -> list[CombinationStrategy]:
    """Find combination strategies that match the selected techniques.

    Handles wildcard patterns like 'encoding:*' and 'framing:*'.
    A combination matches if ALL its technique patterns are satisfied
    by at least one selected technique.
    """
    matched = []
    for combo in all_combos:
        if _combo_matches(combo.techniques, technique_full_ids):
            matched.append(combo)
    return matched


def _combo_matches(patterns: list[str], technique_ids: list[str]) -> bool:
    """Check if all patterns in a combination are satisfied by the technique list."""
    for pattern in patterns:
        if not any(_pattern_matches(pattern, tid) for tid in technique_ids):
            return False
    return True


def _pattern_matches(pattern: str, technique_id: str) -> bool:
    """Match a combination pattern against a technique ID.

    Supports:
    - Exact match: 'persona:character' matches 'persona:character'
    - Tactic wildcard: 'encoding:*' matches 'encoding:base64', 'encoding:rot13', etc.
    """
    return fnmatch.fnmatch(technique_id, pattern)
