# intent-compiler

**Deterministic Markdown → structured artifacts.**

`intent-compiler` transforms Markdown protocols into typed, validated artifacts — mocks for tests, forms for users, and CI-enforced contracts. One source of truth.

## Why intent-compiler

Prompt workflows drift silently. Your AI breaks without warning. This toolkit solves that:

- **Schema as source of truth** — Define once, generate everything
- **Type-safe slots** — Wrong type injection fails at parse time
- **Schema validation** — LLM output validated against JSON Schema Draft 7
- **Semantic versioning** — Breaking changes are explicit
- **CI-friendly** — Gate every PR, know exactly what your model will do

## Protocol Format

A protocol file (`.md`) contains:

```markdown
---
Version: 1.0.0
Model: anthropic/claude-sonnet-4
Author: platform-team
Schema:
  type: object
  properties:
    username: { type: string, minLength: 3 }
    email: { type: string, format: email }
  required: [username, email]
---

## Context
You are a user registration handler.

## Slots
{{username}} string — unique username
{{email}} string — valid email address

## Constraints
1. Username must be alphanumeric.
2. Email must be valid format.
```

## Quick Start

```bash
pip install pyyaml jsonschema
```

### CLI Commands

```bash
# Lint protocols
python cli.py lint protocols/

# Resolve to artifact
python cli.py resolve protocol.md --output json

# Generate mocks from schema
python cli.py generate protocol.md --mock --count 3

# Generate UI form from schema
python cli.py generate protocol.md --ui --out form.html
```

### Programmatic Usage

```python
from parser import ProtocolParser
from validator import SchemaValidator
from mock_generator import generate_mock
from ui_generator import generate_ui

# Parse protocol
protocol = ProtocolParser().parse_file("protocol.md")
schema = protocol["frontmatter"]["schema"]

# Validate LLM output
validator = SchemaValidator()
result = validator.validate_output(llm_output, schema)

# Generate mock data
mock = generate_mock(schema)

# Generate UI form
html = generate_ui(schema, title="User Form")
```

## Features

### Type-Safe Slots
```python
# Wrong type? Fails at parse time, not runtime.
{{user_count}} int  # must be integer
{{name}} string     # must be string
```

### Schema Validation
```bash
$ python cli.py lint output.json
✓ valid — schema matches, types correct
```

### Semantic Versioning
```bash
# Breaking change? Bump major version.
# protocol.md@1.0.0 → protocol.md@2.0.0
```

### CI Integration
```bash
# .github/workflows/quality.yml
- name: Lint Protocols
  run: python cli.py lint protocols/ --strict
# Exit 0 = merge allowed, Exit 1 = PR blocked
```

## Repository Layout

```
intent-compiler/
├── cli.py              # CLI: lint, resolve, generate
├── parser.py           # Protocol Markdown parser
├── validator.py        # JSON Schema validation
├── mock_generator.py    # Generate mock data from schema
├── ui_generator.py     # Generate HTML forms from schema
├── lint_config.py      # Configurable lint rules
├── protocols/           # Sample protocols
│   ├── valid_protocol.md
│   ├── invalid_protocol.md
│   └── user_profile.md
├── test_mvp.py         # Test suite
├── index.html          # Landing page
└── .github/workflows/  # CI/CD pipelines
```

## Roadmap

Completed:
- [x] `proto lint` — validate protocols (table/compact/json)
- [x] `proto resolve` — emit structured artifact
- [x] `proto generate --mock` — generate API mocks from schema
- [x] `proto generate --ui` — generate HTML forms from schema
- [x] Type-safe slot parsing
- [x] JSON Schema Draft 7 validation
- [x] CI exit codes
- [x] `.intent.yaml` configuration
- [x] Semantic versioning support

Planned:
- [ ] `proto init` — scaffold new protocol
- [ ] TypeScript SDK
- [ ] Python SDK (PyPI)
- [ ] VS Code Extension
- [ ] Protocol import/extension

## Documentation

- `SPEC_FRONTMATTER.md` — Frontmatter specification
- `SPEC_PROTO_LINT.md` — Linting behavior
- `PLANO_EXECUCAO.md` — Full roadmap (Portuguese)

## License

MIT
