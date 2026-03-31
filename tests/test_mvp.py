import pytest
from pathlib import Path
from click.testing import CliRunner

from intent_compiler.cli import cli, discover_markdown_files
from intent_compiler.parser import ProtocolParser
from intent_compiler.validator import SchemaValidator


@pytest.fixture
def protocols_dir():
    # Caminho ajustável agora que test_mvp está em /tests e protocolos na raiz
    return Path(__file__).resolve().parent.parent / "protocols"


@pytest.fixture
def valid_file(protocols_dir):
    return protocols_dir / "valid_protocol.md"


@pytest.fixture
def invalid_file(protocols_dir):
    return protocols_dir / "invalid_protocol.md"


def test_parser_accepts_uppercase_frontmatter_keys(valid_file):
    content = valid_file.read_text(encoding="utf-8")
    result = ProtocolParser().parse_content(content)
    assert result["errors"] == []
    assert "schema" in result["frontmatter"]


def test_validator_rejects_invalid_enum_value():
    schema = {
        "type": "object",
        "properties": {"status": {"type": "string", "enum": ["ok", "ko"]}},
        "required": ["status"],
    }
    validation = SchemaValidator().validate_output({"status": "bad"}, schema)
    assert not validation.is_valid
    assert len(validation.errors) >= 1


def test_cli_lint_files_returns_errors_for_invalid_protocol(valid_file, invalid_file):
    runner = CliRunner()
    result = runner.invoke(cli, ["lint", str(valid_file), str(invalid_file), "--format", "json"])
    # CliRunner captura de exit_code
    assert result.exit_code == 1


def test_cli_main_json_output_returns_zero_for_valid_file(valid_file):
    runner = CliRunner()
    result = runner.invoke(cli, ["lint", str(valid_file), "--format", "json"])
    assert result.exit_code == 0


def test_discovery_finds_markdown_files(protocols_dir):
    files = discover_markdown_files([str(protocols_dir)])
    names = {f.name for f in files}
    assert "valid_protocol.md" in names
    assert "invalid_protocol.md" in names
