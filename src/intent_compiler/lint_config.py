import yaml
import re
from pathlib import Path
from typing import Optional
from intent_compiler.validator import DEFAULT_LINT_CONFIG, LintConfig, LintRule

CONFIG_FILE = ".intent.yaml"

def load_config(config_path: Optional[str] = None) -> LintConfig:
    path = Path(config_path) if config_path else Path.cwd() / CONFIG_FILE
    if not path.exists():
        return DEFAULT_LINT_CONFIG
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if not raw:
            return DEFAULT_LINT_CONFIG
        rules_raw = raw.get("rules", [])
        rules = []
        for r in rules_raw:
            if isinstance(r, dict):
                rules.append(LintRule(
                    id=str(r.get("id", "UNKN")),
                    severity=str(r.get("severity", "warning")),
                    message=str(r.get("message", "")),
                ))
        fail_on = str(raw.get("fail_on", "error"))
        return LintConfig(rules=rules, fail_on=fail_on)
    except Exception:
        return DEFAULT_LINT_CONFIG

def save_example_config(path: str = CONFIG_FILE) -> None:
    example = {
        "lint": {
            "fail_on": "error",
            "rules": [
                {"id": "PM001", "severity": "error", "message": "Frontmatter required"},
                {"id": "PM002", "severity": "error", "message": "Required field missing: {field}"},
                {"id": "PM003", "severity": "error", "message": "Slots used but not declared: {slots}"},
                {"id": "PM004", "severity": "error", "message": "Invalid schema: {reason}"},
                {"id": "PM005", "severity": "warning", "message": "Slots declared but not used: {slots}"},
                {"id": "PM006", "severity": "warning", "message": "Version does not follow semver"},
                {"id": "PM007", "severity": "warning", "message": "Model not specified"},
            ],
        }
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(example, f, default_flow_style=False, sort_keys=False)
