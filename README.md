# proto-md

Protocol-Driven Development toolkit for Markdown-based AI protocols.

`proto-md` defines a structured way to write, parse, and validate protocol files (`.md`) so teams can ship LLM workflows with stronger correctness guarantees.

## Why proto-md

Prompt workflows often drift over time and break silently. This project introduces protocol contracts in Markdown:

- Explicit metadata (`version`, `model`, `author`, `schema`)
- Declared slots with types and constraints
- Validation gates for protocol integrity
- JSON Schema checks for model output

The goal is to make prompt workflows testable, reviewable, and CI-friendly.

## Current Status

This repository currently includes:

- `parser.py`: Markdown protocol parser with frontmatter and section extraction
- `validator.py`: JSON Schema and protocol-level validation primitives
- `cli.py`: `proto-lint` command line interface for file/directory validation
- `protocols/`: sample valid and invalid protocol files
- `test_mvp.py`: automated MVP test suite
- `SPEC_FRONTMATTER.md`: frontmatter specification
- `SPEC_PROTO_LINT.md`: linting and CI behavior specification
- `PLANO_EXECUCAO.md`: execution roadmap
- `index.html`: project landing page
- `.github/workflows/deploy-pages.yml`: GitHub Pages deployment workflow
- `.github/workflows/quality-check.yml`: quality baseline workflow (syntax, tests, CLI checks)

## Repository Layout

```text
proto-md/
├── cli.py
├── parser.py
├── protocols/
│   ├── valid_protocol.md
│   └── invalid_protocol.md
├── test_mvp.py
├── validator.py
├── SPEC_FRONTMATTER.md
├── SPEC_PROTO_LINT.md
├── PLANO_EXECUCAO.md
├── LICENSE
├── index.html
└── .github/workflows/
    ├── deploy-pages.yml
    └── quality-check.yml
```

## Quick Start

### Requirements

- Python 3.10+
- pip

### Install dependencies

```bash
pip install pyyaml jsonschema
```

### Parse a protocol

```python
from parser import ProtocolParser

content = """
---
version: 1.0.0
model: anthropic/claude-sonnet-4
author: platform-team
schema:
  type: object
  properties:
    score: { type: number, minimum: 0, maximum: 100 }
  required: [score]
---

## Context
You are a strict reviewer.

## Slots
{{code_snippet}} string — source code

## Constraints
1. Output must match schema
"""

result = ProtocolParser().parse_content(content)
print(result["errors"])
print([slot.name for slot in result["slots"]])
```

### Validate output against schema

```python
from validator import SchemaValidator

schema = {
  "type": "object",
  "properties": {
    "score": {"type": "number", "minimum": 0, "maximum": 100}
  },
  "required": ["score"]
}

output = {"score": 92}
validation = SchemaValidator().validate_output(output, schema)
print(validation.is_valid, validation.errors)
```

### Lint protocols from CLI

```bash
python cli.py protocols
python cli.py protocols --format compact
python cli.py protocols --format json
python cli.py protocols --strict
```

Exit codes:

- `0`: no errors
- `1`: validation errors found
- `2`: execution/configuration problem (for example, no `.md` file found)

### Run the MVP test suite

```bash
python -m unittest -v
```

## Protocol Format

A protocol file is expected to include:

1. Frontmatter metadata
2. `## Context` section
3. `## Slots` section with typed placeholders
4. `## Constraints` section
5. Optional `## Schema` section

Reference documents:

- `SPEC_FRONTMATTER.md`
- `SPEC_PROTO_LINT.md`

## CI and Deployment

- GitHub Pages deploy is configured in `.github/workflows/deploy-pages.yml`
- Quality checks run in `.github/workflows/quality-check.yml` for push/PR on `main`
- Pushes to `main` trigger site publication

## Roadmap

Planned milestones include:

- Full `ProtocolValidator` integration
- `proto-lint` CLI
- Strict and machine-readable output modes
- Python SDK and TypeScript SDK
- CI quality gates with robust test coverage

## License

This project is licensed under the MIT License.
See the [LICENSE](LICENSE) file for details.
