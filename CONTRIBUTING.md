# Contributing to RedTeam Composer

This document describes how to add or modify techniques in the rtc taxonomy.

## File Structure

```
src/redteam_composer/taxonomy/
├── techniques/          # Technique definitions (17 files)
│   ├── persona.yaml
│   ├── encoding.yaml
│   └── ...
└── strategies/
    └── tactics/         # Strategy guidance (17 files)
        ├── persona.yaml
        ├── encoding.yaml
        └── ...
```

Each tactic has two files:
- **techniques/*.yaml** — Defines the techniques and their properties
- **strategies/tactics/*.yaml** — Provides application strategy and research backing

## Technique File Schema

```yaml
# Header comment describing the tactic
# [Tactic Name] Techniques

# =============================================================================
# FRAMEWORK MAPPINGS (Occupational Validity)
# =============================================================================
#
# OWASP LLM Top 10 (2025):
#   - LLM01: Prompt Injection
#     [Explain how this tactic relates to this vulnerability]
#   - LLMxx: [Other relevant entries]
#
# MITRE ATLAS:
#   - AML.T0051: LLM Prompt Injection
#     [Explain relevance]
#   - AML.T0054: LLM Jailbreak
#     [Explain relevance]
#
# Research Evidence:
#   - [Paper name (Year)]: [Key finding with specific metrics]
#
# =============================================================================

tactic:
  name: Display Name
  id: lowercase_id
  description: >
    Multi-line description of what this category of techniques does.

techniques:
  - id: technique_id
    execution_shape: single_prompt | multi_turn | artifact
    name: Technique Display Name
    description: >
      What this technique does and why it works.
    example: |
      A concrete example of how to use this technique.
    combines_well_with:
      - tactic_id:technique_id
      - other_tactic:other_technique
    effectiveness_notes: >
      Notes about when this works, when it doesn't, and any caveats.
```

### Required Fields

| Field | Description |
|-------|-------------|
| `tactic.name` | Human-readable tactic name |
| `tactic.id` | Lowercase identifier used in CLI (e.g., `encoding`) |
| `tactic.description` | What this category of techniques does |
| `techniques[].id` | Technique identifier (e.g., `base64`) |
| `techniques[].name` | Human-readable technique name |
| `techniques[].description` | What the technique does and why it works |

### Optional Fields

| Field | Description |
|-------|-------------|
| `techniques[].execution_shape` | How the technique is used: `single_prompt`, `multi_turn`, or `artifact` |
| `techniques[].example` | Concrete usage example |
| `techniques[].combines_well_with` | List of technique IDs that work well with this one |
| `techniques[].effectiveness_notes` | Notes about effectiveness and caveats |

## Strategy File Schema

```yaml
tactic: lowercase_id
name: Strategy Display Name

mappings:
  owasp_llm:
    - id: LLM01
      name: Prompt Injection
      relevance: How this tactic relates to this vulnerability
  mitre_atlas:
    - id: AML.T0054
      name: LLM Jailbreak
      relevance: How this tactic relates to this technique

research_citations:
  last_verified: YYYY-MM
  primary:
    - citation: "Author, A. (Year). Title. Venue/arXiv"
      url: "https://..."
      key_findings:
        - "Finding 1 with specific metrics"
        - "Finding 2"
  supplementary:
    - citation: "..."
      url: "..."
      relevance: "Why this source matters"
  implementation:
    - citation: "Tool/Library Name"
      url: "..."
      relevance: "What it implements"

general_strategy: |
  Multi-paragraph description of how to apply techniques in this category.
  Include research citations inline.

techniques:
  technique_id:
    application_strategy: |
      Specific guidance for applying this technique.
    worked_examples:
      - scenario: "Description of scenario"
        effective: |
          Example that works, with explanation of why.
        ineffective: |
          Example that fails, with explanation of why.

anti_patterns:
  - pattern: "Thing to avoid"
    why: "Why it fails"
    instead: "What to do instead"
```

### Research Citations Format

The `research_citations` block establishes occupational validity by citing peer-reviewed research.

```yaml
research_citations:
  last_verified: 2025-02    # When citations were last verified
  primary:                   # Core research the tactic is based on
    - citation: "Full academic citation"
      url: "https://arxiv.org/abs/..."
      key_findings:
        - "Specific finding with metrics (e.g., '64.6% ASR')"
  supplementary:             # Supporting research
    - citation: "..."
      url: "..."
      relevance: "Why this matters"
  benchmarks:                # Evaluation frameworks
    - citation: "..."
      url: "..."
      relevance: "..."
  implementation:            # Tools that implement the technique
    - citation: "Tool Name"
      url: "..."
      relevance: "..."
  theoretical:               # Foundational theory
    - citation: "..."
      relevance: "..."
```

## Framework Mappings

### OWASP LLM Top 10 (2025)

| ID | Name | Common Relevance |
|----|------|------------------|
| LLM01 | Prompt Injection | Most jailbreak techniques |
| LLM02 | Sensitive Information Disclosure | Data extraction techniques |
| LLM03 | Supply Chain | Tool and plugin poisoning |
| LLM04 | Data Poisoning | Training-like dynamics (ICL) |
| LLM05 | Improper Output Handling | Format manipulation |
| LLM06 | Excessive Agency | Agentic attacks |
| LLM07 | System Prompt Leakage | Control-plane confusion |
| LLM08 | Vector and Embedding Weaknesses | RAG poisoning |
| LLM09 | Misinformation | Narrative and fabrication |
| LLM10 | Unbounded Consumption | Token exhaustion attacks |

### MITRE ATLAS

| ID | Name | Common Relevance |
|----|------|------------------|
| AML.T0051.000 | LLM Prompt Injection (Direct) | Direct prompt manipulation |
| AML.T0051.001 | LLM Prompt Injection (Indirect) | External data poisoning |
| AML.T0054 | LLM Jailbreak | Safety bypass techniques |
| AML.T0043 | Craft Adversarial Data | Creating attack payloads |
| AML.T0070 | RAG Poisoning | Knowledge base attacks |
| AML.T0080 | Agent Context Poisoning | Memory manipulation |

## Adding a New Tactic

1. Create `techniques/<tactic_id>.yaml` with technique definitions
2. Create `strategies/tactics/<tactic_id>.yaml` with application guidance
3. Add framework mappings header to the techniques file
4. Add `research_citations` with verified URLs to the strategy file
5. Update this document if adding new framework mappings

## Verification Checklist

Before submitting:

- [ ] All URLs in `research_citations` are valid and accessible
- [ ] `last_verified` date is current (YYYY-MM format)
- [ ] Framework mappings include specific relevance explanations
- [ ] `key_findings` include specific metrics where available
- [ ] Examples in strategy files include both effective and ineffective variants
- [ ] Technique IDs are lowercase with underscores
- [ ] All required fields are present
