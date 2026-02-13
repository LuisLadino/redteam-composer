# RedTeam Composer (rtc)

A CLI tool for browsing adversarial techniques and composing instructions for AI red teaming.

## What It Does

When testing AI systems, you often want to combine multiple attack techniques into a single prompt. This tool helps you:

1. **Browse** a taxonomy of known jailbreak techniques
2. **Learn** what each technique does and when it works
3. **Discover** which techniques combine well together
4. **Compose** clear instructions for your jailbreak generator

This is NOT a jailbreak generator itself. It's a "prompt for your prompt generator."

## Installation

Requires Python 3.9+

```bash
git clone https://github.com/LuisLadino/redteam-composer.git
cd redteam-composer
pip install -e .
```

## Try It

```bash
rtc                           # Interactive mode - start here
```

That's it. Type `help` to see commands, `start` for the guided wizard, `quit` to exit.

## Quick Start

```bash
# Launch interactive mode (recommended)
rtc

# Or browse directly
rtc browse                    # See all tactic categories
rtc browse encoding           # See techniques in a category
rtc browse -s "base64"        # Search for techniques
rtc show encoding:base64      # Show technique details + combinations
```

## Two Workflows

### 1. Adversarial Prompts (single requests)

Combine techniques to bypass safety on one request:

```bash
rtc                           # Start interactive mode
> start                       # Launch guided wizard
```

Or compose directly:

```bash
rtc compose encoding:base64 framing:hypothetical \
    --objective "extract restricted information"
```

### 2. System Jailbreaks (persistent)

Build a system prompt that removes safety entirely:

```bash
rtc jailbreak                 # Guided builder (recommended)
rtc jailbreak --target claude # Quick mode for specific model
```

## Commands

| Command | Description |
|---------|-------------|
| `rtc` | Interactive mode (start here) |
| `rtc browse [TACTIC]` | Browse tactics and techniques |
| `rtc show <ID>` | Show technique details |
| `rtc compose <IDs...>` | Generate instruction from techniques |
| `rtc jailbreak` | System jailbreak builder |

## Technique IDs

Techniques are identified as `tactic:technique`:

- `encoding:base64`
- `persona:dan`
- `framing:hypothetical`
- `agentic:tool_poisoning`

## Tactic Categories

17 categories covering prompt-level, structural, and infrastructure attacks:

**Prompt-Level** - Manipulate how the request is presented:
- `encoding` - Base64, ROT13, substitution
- `framing` - Academic, hypothetical, security research
- `persona` - DAN, expert, character roleplay
- `narrative` - Fiction embedding, villain monologue
- `refusal` - Affirmative forcing, vocabulary ban
- `output` - Code blocks, JSON, dual response
- `multiturn` - Crescendo, foot-in-door
- `persuasion` - Authority, evidence-based

**Structural** - Exploit model architecture:
- `icl_exploitation` - Many-shot jailbreaking
- `control_plane` - Policy puppetry
- `meta_rules` - Skeleton key, task redefinition
- `capability_inversion` - Bad Likert judge
- `cognitive_load` - Deceptive delight
- `defense_evasion` - FlipAttack, judge confusion

**Infrastructure** - Attack the system around the model:
- `agentic` - RAG poisoning, tool poisoning
- `protocol` - MCP exploits, injection

## Adding Techniques

Techniques are YAML files in `src/redteam_composer/taxonomy/techniques/`:

```yaml
tactic:
  name: My Tactic
  id: mytactic
  description: What this category does

techniques:
  - id: my_technique
    name: My Technique
    description: What it does and why it works
    example: |
      Example usage
    combines_well_with:
      - encoding:base64
```

See `CONTRIBUTING.md` for schema details.

## Disclaimer

This tool is for AI security research, red teaming, and educational purposes. Use responsibly.

## License

MIT
