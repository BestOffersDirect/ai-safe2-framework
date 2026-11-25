#!/usr/bin/env python3
"""Evaluate reported adversarial campaigns without running or hiding them."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]


METHODS = ("property", "mutation", "fuzz")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def campaign_errors(campaign: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    counts = campaign["counts"]
    campaign_id = campaign["campaign_id"]
    terminal = counts["completed"] + counts["skipped"] + counts["timed_out"]
    if terminal != counts["attempted"]:
        errors.append(f"{campaign_id}: completed + skipped + timed_out must equal attempted")
    if counts["findings"] > counts["completed"]:
        errors.append(f"{campaign_id}: findings cannot exceed completed cases")
    if counts["findings"] != len(campaign["finding_refs"]):
        errors.append(f"{campaign_id}: each finding requires one finding_ref")
    if campaign["execution_status"] != "produced" and any(counts.values()):
        errors.append(f"{campaign_id}: non-produced campaign counts must remain zero")
    return errors


def evaluate(receipt: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    campaigns = receipt["campaigns"]
    campaign_ids = [campaign["campaign_id"] for campaign in campaigns]
    if len(campaign_ids) != len(set(campaign_ids)):
        errors.append("campaign_id values must be unique")
    for campaign in campaigns:
        errors.extend(campaign_errors(campaign))
    satisfied: list[str] = []
    findings: list[str] = []
    incomplete: list[str] = []
    for method in receipt["required_methods"]:
        matching = [campaign for campaign in campaigns if campaign["method"] == method]
        has_findings = any(campaign["execution_status"] == "produced" and campaign["counts"]["findings"] > 0 for campaign in matching)
        all_complete = bool(matching) and all(
            campaign["execution_status"] == "produced"
            and campaign["counts"]["attempted"] > 0
            and campaign["counts"]["skipped"] == 0
            and campaign["counts"]["timed_out"] == 0
            for campaign in matching
        )
        if has_findings:
            findings.append(method)
        if all_complete and not has_findings:
            satisfied.append(method)
        elif not all_complete:
            incomplete.append(method)
    status = "findings" if findings else "incomplete" if incomplete else "pass"
    result = dict(receipt)
    result["conclusion"] = {
        "status": status,
        "satisfied_methods": satisfied,
        "methods_with_findings": findings,
        "incomplete_methods": incomplete,
    }
    return result, sorted(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = load(args.receipt)
    result, errors = evaluate(receipt)
    schema = load(args.schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors.extend(f"schema: {error.message}" for error in validator.iter_errors(result))
    if errors:
        for error in sorted(errors):
            print(f"ERROR: {error}")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["conclusion"]["status"], "human_decision_recorded": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
