"""RedTeam Composer - A CLI tool for browsing jailbreak techniques and composing instructions."""

from .taxonomy_loader import Taxonomy, Technique, Tactic
from .composer import compose_instruction, compose_strategy

__version__ = "0.1.0"
__all__ = ["Taxonomy", "Technique", "Tactic", "compose_instruction", "compose_strategy"]
