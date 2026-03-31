import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from parser import ProtocolParser
from validator import ProtocolValidator, SchemaValidator
from lint_config import load_config


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
        import json
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


def resolve_files(paths: List[Path], output_format: str) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    for path in paths:
        result = resolve_file(str(path), output_format)
        results.append(result)
    return {"files": results, "exit_code": 0 if all(r["exit_code"] == 0 for r in results) else 1}


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


def _color(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"

COLOR_RESET  = "\033[0m"
COLOR_RED    = "91"
COLOR_GREEN  = "92"
COLOR_YELLOW = "93"
COLOR_GRAY   = "90"
COLOR_DIM    = "2"

def _ok(text: str) -> str: return _color(text, COLOR_GREEN)
def _err(text: str) -> str: return _color(text, COLOR_RED)
def _warn(text: str) -> str: return _color(text, COLOR_YELLOW)
def _dim(text: str) -> str: return _color(text, COLOR_DIM)
def _bold(text: str) -> str: return _color(text, "1")
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="proto")
    sub = parser.add_subparsers(dest="command", required=True)

    lint = sub.add_parser("lint", help="Validate protocol files")
    lint.add_argument("paths", nargs="*", help="Files or directories to validate")
    lint.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    lint.add_argument(
        "--format",
        dest="output_format",
        choices=["table", "json", "compact"],
        default="table",
    )
    lint.add_argument(
        "--config",
        dest="config_path",
        type=str,
        default=None,
        help="Path to .intent.yaml config (default: .intent.yaml in cwd)",
    )
    lint.add_argument(
        "--init-config",
        action="store_true",
        help="Generate a .intent.yaml example config",
    )

    resolve = sub.add_parser("resolve", help="Resolve a protocol file to a structured artifact")
    resolve.add_argument("path", help="Protocol file to resolve")
    resolve.add_argument(
        "--output",
        dest="output_format",
        choices=["json", "yaml", "typescript"],
        default="json",
    )
    resolve.add_argument(
        "--out",
        dest="out_file",
        type=str,
        default=None,
        help="Write output to file (default: stdout)",
    )
    resolve.add_argument(
        "--prompt",
        action="store_true",
        help="Generate a structured prompt from the protocol slots",
    )

    generate = sub.add_parser("generate", help="Generate code/artifacts from protocol")
    generate.add_argument("path", help="Protocol file to use as base")
    generate.add_argument(
        "--mock",
        action="store_true",
        help="Generate mock API data from schema",
    )
    generate.add_argument(
        "--ui",
        action="store_true",
        help="Generate HTML UI form from schema",
    )
    generate.add_argument(
        "--title",
        type=str,
        default="Generated Form",
        help="Title for the generated UI (default: 'Generated Form')",
    )
    generate.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of mock instances to generate (default: 1)",
    )
    generate.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible mocks",
    )
    generate.add_argument(
        "--format",
        dest="output_format",
        choices=["json", "yaml"],
        default="json",
    )
    generate.add_argument(
        "--out",
        dest="out_file",
        type=str,
        default=None,
        help="Write output to file (default: stdout)",
    )

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "lint":
        if args.init_config:
            from lint_config import save_example_config
            save_example_config()
            print(".intent.yaml created.")
            return 0

        if not args.paths:
            print("No paths provided. Use --init-config to generate a config or provide paths.", file=sys.stderr)
            return 2

        if args.config_path:
            from pathlib import Path
            if not Path(args.config_path).exists():
                print(f"Config not found: {args.config_path}", file=sys.stderr)
                return 2

        files = discover_markdown_files(args.paths)
        if not files:
            print("No .md files found", file=sys.stderr)
            return 2
        lint_result = lint_files(files, strict=args.strict)
        if args.output_format == "json":
            print(json.dumps(lint_result, indent=2, ensure_ascii=False))
        elif args.output_format == "compact":
            print(render_compact(lint_result))
        else:
            print(render_table(lint_result))
        return int(lint_result["exit_code"])

    elif args.command == "resolve":
        result = resolve_file(args.path, args.output_format)
        if result.get("status") == "error":
            err_output = {
                "file": result["file"],
                "status": "error",
                "errors": result.get("errors", []),
                "warnings": result.get("warnings", []),
            }
            output = json.dumps(err_output, indent=2, ensure_ascii=False)
            if args.out_file:
                with open(args.out_file, "w", encoding="utf-8") as f:
                    f.write(output)
            else:
                print(output)
            return 1

        if args.output_format == "yaml":
            try:
                import yaml
                output = yaml.dump(result.get("artifact", {}), default_flow_style=False, sort_keys=False)
            except ImportError:
                print("yaml library required for YAML output: pip install pyyaml", file=sys.stderr)
                return 2
        elif args.output_format == "typescript":
            output = _emit_typescript(result.get("artifact", {}))
        elif args.prompt:
            output = _emit_prompt(result.get("artifact", {}))
        else:
            output = json.dumps(result.get("artifact", {}), indent=2, ensure_ascii=False)

        if args.out_file:
            with open(args.out_file, "w", encoding="utf-8") as f:
                f.write(output)
        else:
            print(output)
        return result.get("exit_code", 0)

    elif args.command == "generate":
        result = resolve_file(args.path, "json")
        if result.get("status") == "error":
            err_output = {
                "file": result["file"],
                "status": "error",
                "errors": result.get("errors", []),
                "warnings": result.get("warnings", []),
            }
            print(json.dumps(err_output, indent=2, ensure_ascii=False), file=sys.stderr)
            return 1

        schema = result.get("artifact", {}).get("schema")
        if not schema:
            print("No schema found in protocol", file=sys.stderr)
            return 1

        if args.mock:
            from mock_generator import generate_multiple_mocks
            mocks = generate_multiple_mocks(schema, count=args.count, seed=args.seed)

            if args.output_format == "yaml":
                try:
                    import yaml
                    output = yaml.dump({"mocks": mocks}, default_flow_style=False, sort_keys=False)
                except ImportError:
                    print("yaml library required for YAML output: pip install pyyaml", file=sys.stderr)
                    return 2
            else:
                output = json.dumps({"mocks": mocks}, indent=2, ensure_ascii=False)

            if args.out_file:
                with open(args.out_file, "w", encoding="utf-8") as f:
                    f.write(output)
            else:
                print(output)
            return 0

        if args.ui:
            from ui_generator import generate_ui
            title = args.title or result.get("artifact", {}).get("frontmatter", {}).get("protocol_name", "Generated Form")
            html = generate_ui(schema, title=title)

            if args.out_file:
                with open(args.out_file, "w", encoding="utf-8") as f:
                    f.write(html)
            else:
                print(html)
            return 0

        print("No generator specified. Use --mock or --ui.", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
