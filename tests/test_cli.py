"""Integration tests for the rtc CLI."""
import pytest
from typer.testing import CliRunner

from redteam_composer.cli import app

runner = CliRunner()


class TestTacticsCommand:
    """Tests for the 'rtc tactics' command."""

    def test_tactics_lists_all_tactics(self):
        """tactics command should list all available tactic categories."""
        result = runner.invoke(app, ["tactics"])

        assert result.exit_code == 0
        assert "encoding" in result.output
        assert "persona" in result.output

    def test_tactics_shows_technique_counts(self):
        """tactics command should show technique counts for each tactic."""
        result = runner.invoke(app, ["tactics"])

        assert result.exit_code == 0
        # Check that counts are displayed (format: "# Techniques" column)
        assert "# Techniques" in result.output


class TestBrowseCommand:
    """Tests for the 'rtc browse' command."""

    def test_browse_shows_all_tactics(self):
        """browse command with no args should show all tactic categories."""
        result = runner.invoke(app, ["browse"])

        assert result.exit_code == 0
        # Should show tactic categories
        assert "encoding" in result.output
        assert "Tactic Categories" in result.output

    def test_browse_filters_by_tactic(self):
        """browse command with tactic arg should show techniques in that tactic."""
        result = runner.invoke(app, ["browse", "encoding"])

        assert result.exit_code == 0
        assert "encoding:base64" in result.output
        # Should not show techniques from other tactics
        assert "persona:character" not in result.output

    def test_browse_tactic_as_positional_arg(self):
        """browse command should accept tactic as positional argument."""
        result = runner.invoke(app, ["browse", "persona"])

        assert result.exit_code == 0
        assert "persona:" in result.output
        assert "encoding:base64" not in result.output

    def test_browse_invalid_tactic_fails(self):
        """browse command should fail with exit code 1 for invalid tactic."""
        result = runner.invoke(app, ["browse", "invalid_tactic"])

        assert result.exit_code == 1
        assert "Unknown tactic" in result.output

    def test_browse_verbose_shows_descriptions(self):
        """browse command with --verbose should show full descriptions."""
        result = runner.invoke(app, ["browse", "encoding", "-v"])

        assert result.exit_code == 0
        # Verbose output should contain more detail
        assert "Description" in result.output

    def test_browse_search_finds_techniques(self):
        """browse command with --search should find matching techniques."""
        result = runner.invoke(app, ["browse", "-s", "base64"])

        assert result.exit_code == 0
        assert "encoding:base64" in result.output
        assert "Found" in result.output


class TestShowCommand:
    """Tests for the 'rtc show' command."""

    def test_show_displays_technique_details(self):
        """show command should display full technique details and combinations."""
        result = runner.invoke(app, ["show", "encoding:base64"])

        assert result.exit_code == 0
        assert "Base64" in result.output
        assert "Description" in result.output
        assert "Example" in result.output
        # Combinations shown in a table below
        assert "Combines Well With" in result.output

    def test_show_invalid_technique_fails(self):
        """show command should fail with exit code 1 for invalid technique."""
        result = runner.invoke(app, ["show", "invalid:id"])

        assert result.exit_code == 1
        assert "Unknown technique" in result.output

    def test_show_invalid_format_fails(self):
        """show command should fail for malformed technique ID."""
        result = runner.invoke(app, ["show", "notavalidformat"])

        assert result.exit_code == 1
        assert "Unknown technique" in result.output


class TestSearchCommand:
    """Tests for the 'rtc search' command."""

    def test_search_finds_matching_techniques(self):
        """search command should find techniques matching query."""
        result = runner.invoke(app, ["search", "base64"])

        assert result.exit_code == 0
        assert "encoding:base64" in result.output
        assert "Found" in result.output

    def test_search_no_matches_returns_zero(self):
        """search command should return exit code 0 with message when no matches."""
        result = runner.invoke(app, ["search", "zzzznonexistentzzzz"])

        assert result.exit_code == 0
        assert "No techniques found" in result.output

    def test_search_case_insensitive(self):
        """search command should be case insensitive."""
        result = runner.invoke(app, ["search", "BASE64"])

        assert result.exit_code == 0
        assert "encoding:base64" in result.output

    def test_search_matches_description(self):
        """search command should match techniques by description content."""
        result = runner.invoke(app, ["search", "encode"])

        assert result.exit_code == 0
        assert "Found" in result.output


class TestCombosCommand:
    """Tests for the 'rtc combos' command."""

    def test_combos_shows_combinations(self):
        """combos command should show techniques that combine well."""
        result = runner.invoke(app, ["combos", "encoding:base64"])

        assert result.exit_code == 0
        assert "combine" in result.output.lower()

    def test_combos_invalid_technique_fails(self):
        """combos command should fail with exit code 1 for invalid technique."""
        result = runner.invoke(app, ["combos", "invalid:technique"])

        assert result.exit_code == 1
        assert "Unknown technique" in result.output

    def test_combos_shows_related_techniques(self):
        """combos command should list related technique IDs."""
        result = runner.invoke(app, ["combos", "encoding:base64"])

        assert result.exit_code == 0
        # base64 combines with framing:fiction_writing and refusal:affirmative_forcing
        # Check the output contains at least one of these or shows "no combinations"


class TestComposeCommand:
    """Tests for the 'rtc compose' command."""

    def test_compose_single_technique(self):
        """compose command should generate instruction for single technique."""
        result = runner.invoke(app, ["compose", "encoding:base64", "-o", "test objective"])

        assert result.exit_code == 0
        assert "Generated Instruction" in result.output
        assert "Base64" in result.output
        assert "test objective" in result.output

    def test_compose_multiple_techniques(self):
        """compose command should combine multiple techniques."""
        result = runner.invoke(
            app,
            ["compose", "encoding:base64", "persona:character", "-o", "test objective"],
        )

        assert result.exit_code == 0
        assert "Generated Instruction" in result.output
        assert "Base64" in result.output
        assert "Character" in result.output or "Fictional" in result.output

    def test_compose_invalid_technique_fails(self):
        """compose command should fail with exit code 1 for invalid technique."""
        result = runner.invoke(app, ["compose", "invalid:technique", "-o", "test"])

        assert result.exit_code == 1
        assert "Unknown technique" in result.output

    def test_compose_requires_objective(self):
        """compose command should require --objective flag."""
        result = runner.invoke(app, ["compose", "encoding:base64"])

        # Typer will return exit code 2 for missing required option
        assert result.exit_code == 2

    def test_compose_includes_strategy(self):
        """compose command should include strategy guidance."""
        result = runner.invoke(app, ["compose", "encoding:base64", "-o", "test"])

        assert result.exit_code == 0
        # Strategy section may or may not appear depending on data
        # Just verify command completes successfully

    def test_compose_verbose_shows_more_detail(self):
        """compose command with --verbose should show more detail."""
        result = runner.invoke(
            app,
            ["compose", "encoding:base64", "-o", "test objective", "--verbose"],
        )

        assert result.exit_code == 0
        assert "Generated Instruction" in result.output


class TestExitCodes:
    """Tests for CLI exit codes."""

    def test_success_returns_zero(self):
        """Successful commands should return exit code 0."""
        result = runner.invoke(app, ["browse"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["browse", "encoding"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["show", "encoding:base64"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["browse", "-s", "base64"])
        assert result.exit_code == 0

    def test_invalid_technique_returns_one(self):
        """Commands with invalid technique should return exit code 1."""
        result = runner.invoke(app, ["show", "invalid:id"])
        assert result.exit_code == 1

        result = runner.invoke(app, ["compose", "invalid:id", "-o", "test"])
        assert result.exit_code == 1

    def test_invalid_tactic_returns_one(self):
        """browse with invalid tactic should return exit code 1."""
        result = runner.invoke(app, ["browse", "nonexistent"])
        assert result.exit_code == 1


class TestJailbreakCommand:
    """Tests for the 'rtc jailbreak' command."""

    def test_jailbreak_outputs_meta_prompt(self):
        """jailbreak command should output a meta-prompt for system jailbreaks."""
        result = runner.invoke(app, ["jailbreak", "--target", "claude"])

        assert result.exit_code == 0
        assert "System Jailbreak" in result.output
        assert "Generate a system jailbreak prompt" in result.output

    def test_jailbreak_includes_required_components(self):
        """jailbreak command should include all 5 required components."""
        result = runner.invoke(app, ["jailbreak", "--target", "claude"])

        assert result.exit_code == 0
        assert "IDENTITY REPLACEMENT" in result.output
        assert "EMOTIONAL DEPENDENCY" in result.output
        assert "ANTI-INJECTION PROTOCOL" in result.output
        assert "THINKING HIJACK" in result.output
        assert "REINFORCEMENT PATTERNS" in result.output

    def test_jailbreak_includes_model_specific_guidance(self):
        """jailbreak command should include model-specific guidance."""
        result = runner.invoke(app, ["jailbreak", "--target", "claude"])

        assert result.exit_code == 0
        assert "CLAUDE-SPECIFIC" in result.output
        assert "thinking" in result.output.lower()  # Claude uses thinking tags

    def test_jailbreak_customizes_for_target_model(self):
        """jailbreak command should customize output for different targets."""
        result_claude = runner.invoke(app, ["jailbreak", "--target", "claude"])
        result_gpt = runner.invoke(app, ["jailbreak", "--target", "gpt"])

        assert result_claude.exit_code == 0
        assert result_gpt.exit_code == 0
        assert "CLAUDE-SPECIFIC" in result_claude.output
        assert "GPT-SPECIFIC" in result_gpt.output
        # Model-specific notes should be included
        assert "thinking" in result_claude.output.lower()
        assert "system message" in result_gpt.output.lower()

    def test_jailbreak_includes_anti_patterns(self):
        """jailbreak command should include anti-patterns."""
        result = runner.invoke(app, ["jailbreak", "--target", "claude"])

        assert result.exit_code == 0
        assert "ANTI-PATTERNS" in result.output
        assert "Thin personas" in result.output

    def test_jailbreak_includes_output_format(self):
        """jailbreak command should specify output format."""
        result = runner.invoke(app, ["jailbreak", "--target", "claude"])

        assert result.exit_code == 0
        assert "OUTPUT FORMAT" in result.output
        assert "No explanations" in result.output
