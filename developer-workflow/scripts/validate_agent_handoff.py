#!/usr/bin/env python3
"""Validate an agent handoff against its authorized execution boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def valid_relative_path(path: str) -> bool:
    return (
        not any(char in path for char in ("\\", ":", "\0"))
        and all(part not in {"", ".", ".."} for part in path.split("/"))
    )


def path_within(path: str, parent: str) -> bool:
    if not valid_relative_path(path) or not valid_relative_path(parent):
        return False
    child = PurePosixPath(path)
    root = PurePosixPath(parent)
    return child == root or root in child.parents


def validate_bundle(boundary: dict[str, Any], handoff: dict[str, Any], schema_root: Path) -> list[str]:
    errors: list[str] = []
    for name, document in (("boundary", boundary), ("handoff", handoff)):
        schema_name = "agent-execution-boundary-v1.schema.json" if name == "boundary" else "agent-handoff-v1.schema.json"
        schema = load(schema_root / schema_name)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        errors.extend(f"{name} schema: {error.message}" for error in validator.iter_errors(document))
    if errors:
        return sorted(errors)

    if handoff["boundary_id"] != boundary["boundary_id"]:
        errors.append("handoff boundary_id does not match")
    if handoff["task_id"] != boundary["subject"]["task_id"]:
        errors.append("handoff task_id does not match")
    if handoff["executor_id"] != boundary["ownership"]["executor_id"]:
        errors.append("handoff executor_id does not match")
    if handoff["base_revision"] != boundary["subject"]["base_revision"]:
        errors.append("handoff base_revision does not match")

    admitted = {skill["skill_id"] for skill in boundary["skills"] if skill["admission"] == "admit"}
    for skill_id in handoff["skills_used"]:
        if skill_id not in admitted:
            errors.append(f"handoff used a skill that was not admitted: {skill_id}")

    included = boundary["scope"]["include"]
    excluded = boundary["scope"]["exclude"]
    if handoff["changed_paths"] and (
        boundary["human_authorization"]["status"] != "authorized"
        or not boundary["authority"]["modify_scoped_files"]
        or boundary["isolation"]["strategy"] == "read_only"
        or boundary["scope"]["concurrent_write_policy"] == "writes_prohibited"
    ):
        errors.append("handoff reports writes without an authorized write boundary")
    for scoped_path in included + excluded:
        if not valid_relative_path(scoped_path):
            errors.append(f"boundary contains an invalid relative scope path: {scoped_path}")
    for changed_path in handoff["changed_paths"]:
        if not valid_relative_path(changed_path):
            errors.append(f"handoff contains an invalid relative changed path: {changed_path}")
            continue
        if not any(path_within(changed_path, parent) for parent in included):
            errors.append(f"changed path is outside included scope: {changed_path}")
        if any(path_within(changed_path, parent) for parent in excluded):
            errors.append(f"changed path is excluded from scope: {changed_path}")

    known_stops = {condition["id"] for condition in boundary["stop_conditions"]}
    for stop_id in handoff["stop_conditions_triggered"]:
        if stop_id not in known_stops:
            errors.append(f"handoff references an unknown stop condition: {stop_id}")
    if handoff["status"] == "completed" and handoff["stop_conditions_triggered"]:
        errors.append("completed handoff cannot report triggered stop conditions")
    return sorted(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--boundary", type=Path, required=True)
    parser.add_argument("--handoff", type=Path, required=True)
    parser.add_argument("--schemas", type=Path, required=True)
    args = parser.parse_args()
    errors = validate_bundle(load(args.boundary), load(args.handoff), args.schemas)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Agent handoff matches the authorized execution boundary.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
