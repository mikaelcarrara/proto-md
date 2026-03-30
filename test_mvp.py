import unittest
from pathlib import Path

from cli import discover_markdown_files, lint_files, main
from parser import ProtocolParser
from validator import SchemaValidator


class MvpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parent
        self.protocols_dir = self.root / "protocols"
        self.valid_file = self.protocols_dir / "valid_protocol.md"
        self.invalid_file = self.protocols_dir / "invalid_protocol.md"

    def test_parser_accepts_uppercase_frontmatter_keys(self) -> None:
        content = self.valid_file.read_text(encoding="utf-8")
        result = ProtocolParser().parse_content(content)
        self.assertEqual(result["errors"], [])
        self.assertIn("schema", result["frontmatter"])

    def test_validator_rejects_invalid_enum_value(self) -> None:
        schema = {
            "type": "object",
            "properties": {"status": {"type": "string", "enum": ["ok", "ko"]}},
            "required": ["status"],
        }
        validation = SchemaValidator().validate_output({"status": "bad"}, schema)
        self.assertFalse(validation.is_valid)
        self.assertGreaterEqual(len(validation.errors), 1)

    def test_cli_lint_files_returns_errors_for_invalid_protocol(self) -> None:
        result = lint_files([self.valid_file, self.invalid_file], strict=False)
        self.assertEqual(result["summary"]["total"], 2)
        self.assertGreaterEqual(result["summary"]["errors"], 1)
        self.assertEqual(result["exit_code"], 1)

    def test_cli_main_json_output_returns_zero_for_valid_file(self) -> None:
        exit_code = main([str(self.valid_file), "--format", "json"])
        self.assertEqual(exit_code, 0)

    def test_discovery_finds_markdown_files(self) -> None:
        files = discover_markdown_files([str(self.protocols_dir)])
        names = {file.name for file in files}
        self.assertIn("valid_protocol.md", names)
        self.assertIn("invalid_protocol.md", names)


if __name__ == "__main__":
    unittest.main()
