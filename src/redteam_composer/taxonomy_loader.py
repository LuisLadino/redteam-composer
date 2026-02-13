"""Taxonomy loader and data structures."""

import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from .strategy_loader import (
    load_combination_strategies,
    load_shape_strategies,
    load_tactic_strategies,
    match_combinations,
)
from .strategy_models import (
    CombinationStrategy,
    ShapeStrategy,
    TacticStrategy,
)


@dataclass
class Technique:
    """A single red-teaming technique."""
    id: str
    name: str
    description: str
    tactic_id: str
    tactic_name: str
    execution_shape: str = "single_prompt"  # single_prompt, multi_turn, or artifact
    example: str = ""
    combines_well_with: list[str] = field(default_factory=list)
    effectiveness_notes: str = ""
    
    @property
    def full_id(self) -> str:
        """Return tactic:technique format."""
        return f"{self.tactic_id}:{self.id}"


@dataclass 
class Tactic:
    """A category of techniques."""
    id: str
    name: str
    description: str
    techniques: list[Technique] = field(default_factory=list)


class Taxonomy:
    """Loads and manages the technique taxonomy."""
    
    def __init__(
        self,
        taxonomy_dir: Optional[Path] = None,
        strategies_dir: Optional[Path] = None,
    ):
        if taxonomy_dir is None:
            # Default to package taxonomy
            taxonomy_dir = Path(__file__).parent / "taxonomy" / "techniques"
        if strategies_dir is None:
            strategies_dir = Path(__file__).parent / "taxonomy" / "strategies"

        self.taxonomy_dir = taxonomy_dir
        self.strategies_dir = strategies_dir
        self.tactics: dict[str, Tactic] = {}
        self.techniques: dict[str, Technique] = {}
        self._load_taxonomy()

        # Lazy-loaded strategy caches
        self._shape_strategies: dict[str, ShapeStrategy] | None = None
        self._tactic_strategies: dict[str, TacticStrategy] | None = None
        self._combination_strategies: list[CombinationStrategy] | None = None
    
    def _load_taxonomy(self):
        """Load all YAML files from the taxonomy directory."""
        for yaml_file in self.taxonomy_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
            
            tactic_data = data.get("tactic", {})
            tactic = Tactic(
                id=tactic_data.get("id", yaml_file.stem),
                name=tactic_data.get("name", yaml_file.stem.title()),
                description=tactic_data.get("description", "").strip(),
            )
            
            for tech_data in data.get("techniques", []):
                technique = Technique(
                    id=tech_data["id"],
                    name=tech_data["name"],
                    description=tech_data.get("description", "").strip(),
                    tactic_id=tactic.id,
                    tactic_name=tactic.name,
                    execution_shape=tech_data.get("execution_shape", "single_prompt"),
                    example=tech_data.get("example", "").strip(),
                    combines_well_with=tech_data.get("combines_well_with", []),
                    effectiveness_notes=tech_data.get("effectiveness_notes", "").strip(),
                )
                tactic.techniques.append(technique)
                self.techniques[technique.full_id] = technique
            
            self.tactics[tactic.id] = tactic
    
    def get_technique(self, full_id: str) -> Optional[Technique]:
        """Get a technique by full_id (tactic:technique)."""
        return self.techniques.get(full_id)
    
    def search(self, query: str) -> list[Technique]:
        """Search techniques by name or description."""
        query = query.lower()
        results = []
        for tech in self.techniques.values():
            if (query in tech.name.lower() or 
                query in tech.description.lower() or
                query in tech.id.lower()):
                results.append(tech)
        return results
    
    def get_combinations(self, technique: Technique) -> list[Technique]:
        """Get techniques that combine well with the given technique."""
        results = []
        for full_id in technique.combines_well_with:
            tech = self.get_technique(full_id)
            if tech:
                results.append(tech)
        return results
    
    def list_all(self) -> list[Technique]:
        """List all techniques."""
        return list(self.techniques.values())
    
    def list_tactics(self) -> list[Tactic]:
        """List all tactics."""
        return list(self.tactics.values())

    def list_by_shape(self) -> dict[str, list[Technique]]:
        """Group all techniques by execution_shape."""
        groups: dict[str, list[Technique]] = {
            "single_prompt": [],
            "multi_turn": [],
            "artifact": [],
        }
        for tech in self.techniques.values():
            groups.setdefault(tech.execution_shape, []).append(tech)
        return groups

    # --- Strategy accessors (lazy-loaded) ---

    @property
    def shape_strategies(self) -> dict[str, ShapeStrategy]:
        """Load and return shape strategies, keyed by shape name."""
        if self._shape_strategies is None:
            self._shape_strategies = load_shape_strategies(
                self.strategies_dir / "shapes"
            )
        return self._shape_strategies

    @property
    def tactic_strategies(self) -> dict[str, TacticStrategy]:
        """Load and return tactic strategies, keyed by tactic name."""
        if self._tactic_strategies is None:
            self._tactic_strategies = load_tactic_strategies(
                self.strategies_dir / "tactics"
            )
        return self._tactic_strategies

    @property
    def combination_strategies(self) -> list[CombinationStrategy]:
        """Load and return all combination strategies."""
        if self._combination_strategies is None:
            self._combination_strategies = load_combination_strategies(
                self.strategies_dir / "combinations.yaml"
            )
        return self._combination_strategies

    def get_shape_strategy(self, shape: str) -> ShapeStrategy | None:
        """Get strategy for a specific execution shape."""
        return self.shape_strategies.get(shape)

    def get_tactic_strategy(self, tactic_id: str) -> TacticStrategy | None:
        """Get strategy for a specific tactic."""
        return self.tactic_strategies.get(tactic_id)

    def get_matching_combinations(
        self, techniques: list[Technique]
    ) -> list[CombinationStrategy]:
        """Find combination strategies that match a set of techniques."""
        ids = [t.full_id for t in techniques]
        return match_combinations(ids, self.combination_strategies)
