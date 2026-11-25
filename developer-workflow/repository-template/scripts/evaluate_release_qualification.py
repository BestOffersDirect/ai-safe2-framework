#!/usr/bin/env python3
"""Evaluate release evidence without making the human release decision."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def evaluate(record: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    revision = record["candidate"]["revision"]
    errors: list[str] = []
    mandatory = {
        "local-gate", "hosted-ci", "clean-game-canary", "security-review",
        "placeholder-resolution", "package-integrity",
    }
    omitted = mandatory - set(record["required_capabilities"])
    if omitted:
        errors.append("release policy omits mandatory capabilities: " + ", ".join(sorted(omitted)))
    seen: set[tuple[str, str]] = set()
    produced: set[str] = set()
    for item in record["evidence"]:
        key = (item["capability"], item["producer"])
        if key in seen:
            errors.append(f"duplicate release evidence for capability and producer: {key[0]} / {key[1]}")
        seen.add(key)
        if item["status"] == "produced" and not item["evidence_ref"]:
            errors.append(f"produced release evidence lacks evidence_ref: {item['capability']}")
        if item["status"] == "produced" and item["subject_revision"] == revision:
            produced.add(item["capability"])
    missing = sorted((mandatory | set(record["required_capabilities"])) - produced)
    result = dict(record)
    result["missing_capabilities"] = missing
    result["outcome"] = "hold" if missing else "ready_for_human_release_decision"
    result["human_authority"] = {
        "release_decision_recorded": False,
        "release_owner": None,
        "release_at": None,
        "rationale": None,
    }
    return result, sorted(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result, errors = evaluate(load(args.record))
    validator = Draft202012Validator(load(args.schema), format_checker=FormatChecker())
    errors.extend(f"schema: {error.message}" for error in validator.iter_errors(result))
    if errors:
        for error in sorted(errors):
            print(f"ERROR: {error}")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"outcome": result["outcome"], "release_authorized": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
