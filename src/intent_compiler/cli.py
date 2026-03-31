import click
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from intent_compiler.parser import ProtocolParser
from intent_compiler.validator import ProtocolValidator, SchemaValidator
from intent_compiler.lint_config import load_config


def discover_markdown_files(paths: List[str]) -> List[Path]:
    resolved: List[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_file() and path.suffix.lower() == ".md":
            resolved.append(path)
        elif path.is_dir():
            resolved.extend([file for file in path.rglob("*.md") if file.is_file()])
    unique = sorted({file.resolve() for file in resolved})
    return unique


def _emit_typescript(artifact: Dict[str, Any]) -> str:
    fm = artifact.get("frontmatter", {})
    schema = fm.get("schema") or artifact.get("schema", {})
    version = fm.get("version") or fm.get("Version") or "unknown"
    lines = [f"// Generated from {version}"]
    if not schema:
        return "// " + "\n".join(lines)
    props = schema.get("properties", {})
    required = schema.get("required", [])
    lines.append("export interface Protocol {")
    for name, prop in props.items():
        ts_type = _json_to_ts(prop.get("type", "any"))
        if name in required:
            lines.append(f"  {name}: {ts_type};")
        else:
            lines.append(f"  {name}?: {ts_type};")
    lines.append("}")
    return "\n".join(lines)


def _json_to_ts(json_type: str) -> str:
    mapping = {
        "string": "string",
        "number": "number",
        "integer": "number",
        "boolean": "boolean",
        "array": "unknown[]",
        "object": "Record<string, unknown>",
    }
    return mapping.get(json_type, "unknown")


def _emit_prompt(artifact: Dict[str, Any]) -> str:
    fm = artifact.get("frontmatter", {})
    context = artifact.get("sections", {}).get("context", "")
    slots = artifact.get("sections", {}).get("slots", [])
    constraints = artifact.get("sections", {}).get("constraints", [])
    lines = []
    if fm.get("Model"):
        lines.append(f"Model: {fm['Model']}")
    if fm.get("Author"):
        lines.append(f"Author: {fm['Author']}")
    lines.append("")
    lines.append("## Context")
    lines.append(context)
    lines.append("")
    lines.append("## Slots")
    for slot in slots:
        name = slot.get("name", "?")
        stype = slot.get("type", "?")
        desc = slot.get("description", "")
        lines.append(f"- {{{{{name}}}}} ({stype}) — {desc}" if desc else f"- {{{{{name}}}}} ({stype})")
    lines.append("")
    lines.append("## Constraints")
    for i, c in enumerate(constraints, 1):
        lines.append(f"{i}. {c}")
    lines.append("")
    schema = fm.get("schema") or artifact.get("schema", {})
    if schema:
        lines.append("## Output Schema")
        lines.append("```json")
        lines.append(json.dumps(schema, indent=2))
        lines.append("```")
    return "\n".join(lines)


def _slot_to_dict(slot) -> Dict[str, Any]:
    if isinstance(slot, dict):
        return slot
    result = {
        "name": getattr(slot, "name", ""),
        "description": getattr(slot, "description", ""),
    }
    type_val = getattr(slot, "type", None)
    if type_val is not None:
        result["type"] = type_val.value if hasattr(type_val, "value") else str(type_val)
    else:
        result["type"] = ""
    return result


def resolve_file(file_path: str, output_format: str = "json") -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    parser = ProtocolParser()
    parsed = parser.parse_content(content)
    errors = list(parsed.get("errors", []))
    warnings = list(parsed.get("warnings", []))

    if errors:
        return {
            "file": file_path,
            "status": "error",
            "errors": errors,
            "warnings": warnings,
            "exit_code": 1,
        }

    schema = parsed.get("frontmatter", {}).get("schema")
    schema_valid = None
    if schema:
        sv = SchemaValidator()
        schema_valid = sv.validate_schema_syntax(schema)
        if not schema_valid.is_valid:
            errors.append(f"schema: {schema_valid.error}")

    artifact = {
        "frontmatter": parsed.get("frontmatter", {}),
        "sections": {
            "context": parsed.get("context", ""),
            "slots": [_slot_to_dict(s) for s in parsed.get("slots", [])],
            "constraints": parsed.get("constraints", []),
        },
    }

    if schema:
        artifact["schema"] = schema
    if schema_valid:
        artifact["schema_valid"] = schema_valid.is_valid

    return {
        "file": file_path,
        "status": "resolved",
        "warnings": warnings,
        "artifact": artifact,
        "exit_code": 0,
    }

def lint_files(paths: List[Path], strict: bool) -> Dict[str, Any]:
    validator = ProtocolValidator()
    files_output: List[Dict[str, Any]] = []
    summary = {"total": 0, "valid": 0, "errors": 0, "warnings": 0}

    for path in paths:
        result = validator.validate_protocol_file(str(path))
        errors = list(result.errors)
        warnings = list(result.warnings)

        if strict and warnings:
            errors.extend([f"(strict) {warning}" for warning in warnings])
            warnings = []

        is_valid = len(errors) == 0
        if is_valid:
            summary["valid"] += 1
        summary["total"] += 1
        summary["errors"] += len(errors)
        summary["warnings"] += len(warnings)

        files_output.append(
            {
                "file": str(path),
                "status": "valid" if is_valid else "invalid",
                "errors": errors,
                "warnings": warnings,
            }
        )

    exit_code = 0 if summary["errors"] == 0 else 1
    return {"summary": summary, "files": files_output, "exit_code": exit_code}


def _color(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"

def _ok(text: str) -> str: return _color(text, "92")
def _err(text: str) -> str: return _color(text, "91")
def _warn(text: str) -> str: return _color(text, "93")
def _dim(text: str) -> str: return _color(text, "2")
def _bold(text: str) -> str: return _color(text, "1")

def render_table(result: Dict[str, Any]) -> str:
    lines: List[str] = []
    for file_result in result["files"]:
        marker = _ok("✓") if file_result["status"] == "valid" else _err("✗")
        fname = _bold(file_result["file"])
        e_count = len(file_result["errors"])
        w_count = len(file_result["warnings"])
        e_str = _err(f"{e_count} error{'s' if e_count != 1 else ''}") if e_count else _dim("0 errors")
        w_str = _warn(f"{w_count} warning{'s' if w_count != 1 else ''}") if w_count else _dim("0 warnings")
        lines.append(f"{marker} {fname}  {e_str}  {w_str}")
        for error in file_result["errors"]:
            lines.append(f"  {_err('>')} {_err(error)}")
        for warning in file_result["warnings"]:
            lines.append(f"  {_warn('>')} {_warn(warning)}")
    summary = result["summary"]
    total = summary["total"]
    valid = summary["valid"]
    errors = summary["errors"]
    warnings = summary["warnings"]
    w_str = f"{warnings} warning{'s' if warnings != 1 else ''}"
    status = _ok(f"{valid}/{total} valid") if errors == 0 else _err(f"{errors} error{'s' if errors != 1 else ''}")
    lines.append(_dim("─" * 50))
    lines.append(f"{status} · {_warn(w_str)}")
    return "\n".join(lines)


def render_compact(result: Dict[str, Any]) -> str:
    parts: List[str] = []
    for file_result in result["files"]:
        if file_result["status"] == "valid":
            parts.append(f"{_ok('v')} {file_result['file']}")
        else:
            e = len(file_result["errors"])
            parts.append(f"{_err('x')} {file_result['file']} {_err(f'{e}e')}")
    summary = result["summary"]
    if summary["errors"] > 0:
        parts.append(_err(f"{summary['errors']}e"))
    if summary["warnings"] > 0:
        w = summary["warnings"]
        parts.append(_warn(f"{w}w"))
    parts.append(_dim(f"{summary['valid']}/{summary['total']}"))
    return " . ".join(parts)


@click.group()
def cli():
    """Deterministic Markdown → structured artifacts."""
    pass


@cli.command()
@click.argument('paths', nargs=-1, type=click.Path(exists=False))
@click.option('--strict', is_flag=True, help='Treat warnings as errors')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json', 'compact']), default='table')
@click.option('--config', 'config_path', type=click.Path(exists=False), help='Path to .intent.yaml config')
@click.option('--init-config', is_flag=True, help='Generate a .intent.yaml example config')
def lint(paths, strict, output_format, config_path, init_config):
    """Validate protocol files"""
    if init_config:
        from intent_compiler.lint_config import save_example_config
        save_example_config()
        click.echo(".intent.yaml created.")
        return

    if not paths:
        click.echo("No paths provided. Use --init-config to generate a config or provide paths.", err=True)
        sys.exit(2)

    files = discover_markdown_files(list(paths))
    if not files:
        click.echo("No .md files found", err=True)
        sys.exit(2)

    lint_result = lint_files(files, strict=strict)
    
    if output_format == "json":
        click.echo(json.dumps(lint_result, indent=2, ensure_ascii=False))
    elif output_format == "compact":
        click.echo(render_compact(lint_result))
    else:
        click.echo(render_table(lint_result))
    
    sys.exit(lint_result["exit_code"])


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--output', 'output_format', type=click.Choice(['json', 'yaml', 'typescript']), default='json')
@click.option('--out', 'out_file', type=click.Path(), help='Write output to file')
@click.option('--prompt', is_flag=True, help='Generate a structured prompt from the protocol slots')
def resolve(path, output_format, out_file, prompt):
    """Resolve a protocol file to a structured artifact"""
    result = resolve_file(path, output_format)
    
    if result.get("status") == "error":
        err_output = {
            "file": result["file"],
            "status": "error",
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", []),
        }
        output = json.dumps(err_output, indent=2, ensure_ascii=False)
        if out_file:
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(output)
        else:
            click.echo(output)
        sys.exit(1)

    if output_format == "yaml":
        import yaml
        output = yaml.dump(result.get("artifact", {}), default_flow_style=False, sort_keys=False)
    elif output_format == "typescript":
        output = _emit_typescript(result.get("artifact", {}))
    elif prompt:
        output = _emit_prompt(result.get("artifact", {}))
    else:
        output = json.dumps(result.get("artifact", {}), indent=2, ensure_ascii=False)

    if out_file:
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        click.echo(output)
    
    sys.exit(result.get("exit_code", 0))


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--mock', is_flag=True, help='Generate mock API data from schema')
@click.option('--ui', is_flag=True, help='Generate HTML UI form from schema')
@click.option('--title', default='Generated Form', help='Title for the generated UI')
@click.option('--count', default=1, type=int, help='Number of mock instances to generate')
@click.option('--seed', type=int, help='Random seed for reproducible mocks')
@click.option('--format', 'output_format', type=click.Choice(['json', 'yaml']), default='json')
@click.option('--out', 'out_file', type=click.Path(), help='Write output to file')
def generate(path, mock, ui, title, count, seed, output_format, out_file):
    """Generate code/artifacts from protocol"""
    result = resolve_file(path, "json")
    if result.get("status") == "error":
        err_output = {
            "file": result["file"],
            "status": "error",
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", []),
        }
        click.echo(json.dumps(err_output, indent=2, ensure_ascii=False), err=True)
        sys.exit(1)

    schema = result.get("artifact", {}).get("schema")
    if not schema:
        click.echo("No schema found in protocol", err=True)
        sys.exit(1)

    if mock:
        from intent_compiler.generators.mock_generator import generate_multiple_mocks
        mocks = generate_multiple_mocks(schema, count=count, seed=seed)

        if output_format == "yaml":
            import yaml
            output = yaml.dump({"mocks": mocks}, default_flow_style=False, sort_keys=False)
        else:
            output = json.dumps({"mocks": mocks}, indent=2, ensure_ascii=False)

        if out_file:
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(output)
        else:
            click.echo(output)
        return

    if ui:
        from intent_compiler.generators.ui_generator import generate_ui
        form_title = title or result.get("artifact", {}).get("frontmatter", {}).get("protocol_name", "Generated Form")
        html = generate_ui(schema, title=form_title)

        if out_file:
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(html)
        else:
            click.echo(html)
        return

    click.echo("No generator specified. Use --mock or --ui.", err=True)
    sys.exit(2)


def main():
    cli()

if __name__ == "__main__":
    main()
