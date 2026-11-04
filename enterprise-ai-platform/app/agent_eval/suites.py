from pathlib import Path
from typing import Any

import yaml


def load_suite(path: str | Path) -> dict[str, Any]:
    suite = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(suite, dict) or not isinstance(suite.get("cases"), list):
        raise ValueError("Suite must be a YAML mapping with a cases list")
    ids: set[str] = set()
    for case in suite["cases"]:
        if not all(key in case for key in ("id", "input")):
            raise ValueError("Every case requires id and input")
        if case["id"] in ids:
            raise ValueError(f"Duplicate case id: {case['id']}")
        ids.add(case["id"])
    suite.setdefault("name", Path(path).stem)
    suite.setdefault("version", "1.0")
    suite.setdefault("type", "standard")
    return suite
