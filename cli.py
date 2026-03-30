import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from validator import ProtocolValidator


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
        marker = "✓" if file_result["status"] == "valid" else "✗"
        lines.append(
            f"{marker} {file_result['file']}  errors: {len(file_result['errors'])}  warnings: {len(file_result['warnings'])}"
        )
        for error in file_result["errors"]:
            lines.append(f"  Error: {error}")
        for warning in file_result["warnings"]:
            lines.append(f"  Warning: {warning}")
    summary = result["summary"]
    lines.append(
        f"{summary['errors']} errors · {summary['warnings']} warnings · {summary['valid']}/{summary['total']} valid"
    )
    return "\n".join(lines)


def render_compact(result: Dict[str, Any]) -> str:
    lines: List[str] = []
    for file_result in result["files"]:
        if file_result["status"] == "valid":
            lines.append(f"{file_result['file']}: OK")
        else:
            first_error = file_result["errors"][0] if file_result["errors"] else "invalid"
            lines.append(f"{file_result['file']}: ERROR - {first_error}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="proto-lint")
    parser.add_argument("paths", nargs="+", help="Arquivos ou diretórios para validar")
    parser.add_argument("--strict", action="store_true", help="Warnings viram erros")
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=["table", "json", "compact"],
        default="table",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    files = discover_markdown_files(args.paths)
    if not files:
        print("Nenhum arquivo .md encontrado", file=sys.stderr)
        return 2

    lint_result = lint_files(files, strict=args.strict)

    if args.output_format == "json":
        print(json.dumps(lint_result, indent=2, ensure_ascii=False))
    elif args.output_format == "compact":
        print(render_compact(lint_result))
    else:
        print(render_table(lint_result))

    return int(lint_result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
