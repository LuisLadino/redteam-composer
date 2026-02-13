"""Data models for strategy layer."""

from dataclasses import dataclass, field


@dataclass
class AntiPattern:
    """A known ineffective or counterproductive approach."""
    pattern: str
    why: str
    instead: str = ""


@dataclass
class WorkedExample:
    """A concrete example showing effective vs ineffective application."""
    scenario: str
    effective: str
    ineffective: str = ""
    why_effective_works: str = ""


@dataclass
class TechniqueStrategy:
    """Strategy guidance for a specific technique within a tactic."""
    technique_id: str
    application_strategy: str
    worked_examples: list[WorkedExample] = field(default_factory=list)


@dataclass
class TacticStrategy:
    """Strategy guidance for an entire tactic category."""
    tactic: str
    name: str
    general_strategy: str
    techniques: dict[str, TechniqueStrategy] = field(default_factory=dict)
    anti_patterns: list[AntiPattern] = field(default_factory=list)


@dataclass
class ShapeStrategy:
    """Strategy guidance for an execution shape (single_prompt, multi_turn, artifact)."""
    shape: str
    name: str
    principles: list[str] = field(default_factory=list)
    anti_patterns: list[AntiPattern] = field(default_factory=list)
    quality_criteria: list[str] = field(default_factory=list)


@dataclass
class CombinationStrategy:
    """Strategy guidance for combining specific techniques."""
    techniques: list[str]
    strategy: str
    worked_example: WorkedExample | None = None
