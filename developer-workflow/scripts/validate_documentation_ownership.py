#!/usr/bin/env python3
"""Validate documentation ownership, coverage, and generated mirror freshness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def safe_path(root: Path, relative: str) -> Path | None:
    value = PurePosixPath(relative)
    if value.is_absolute() or any(part in {"", ".", ".."} for part in value.parts):
        return None
    candidate = (root / Path(*value.parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def normalized_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip()


def equal_content(source: Path, target: Path, comparison: str) -> bool:
    if comparison == "semantic_json":
        source_value: object = json.loads(source.read_text(encoding="utf-8"))
        target_value: object = json.loads(target.read_text(encoding="utf-8"))
        return source_value == target_value
    return normalized_text(source) == normalized_text(target)


def markdown_files(root: Path, coverage_roots: list[str], excluded: set[str]) -> set[str]:
    found: set[str] = set()
    for relative in coverage_roots:
        candidate = safe_path(root, relative)
        if candidate is None or not candidate.exists():
            continue
        paths = [candidate] if candidate.is_file() else candidate.rglob("*.md")
        for path in paths:
            normalized = path.relative_to(root).as_posix()
            if path.suffix.lower() == ".md" and normalized not in excluded:
                found.add(normalized)
    return found


def validate(root: Path, manifest: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors = [f"schema: {error.message}" for error in Draft202012Validator(schema).iter_errors(manifest)]
    if errors:
        return sorted(errors)
    declared: set[str] = set()
    for document in manifest["documents"]:
        relative = document["path"]
        if relative in declared:
            errors.append(f"duplicate document ownership entry: {relative}")
        declared.add(relative)
        owned_path = safe_path(root, relative)
        if owned_path is None:
            errors.append(f"invalid document path: {relative}")
        elif not owned_path.is_file():
            errors.append(f"owned document does not exist: {relative}")
        if document["classification"] in {"generated", "historical_snapshot", "vendored"} and not document["notice"]:
            errors.append(f"generated, historical, or vendored document lacks notice: {relative}")

    excluded = set(manifest["coverage"]["exclude"])
    observed = markdown_files(root, manifest["coverage"]["markdown_roots"], excluded)
    for missing_path in sorted(observed - declared):
        errors.append(f"markdown document lacks ownership entry: {missing_path}")

    for mirror in manifest["mirror_sets"]:
        source_root = safe_path(root, mirror["source_root"])
        target_root = safe_path(root, mirror["target_root"])
        if source_root is None or target_root is None or not source_root.is_dir() or not target_root.is_dir():
            errors.append(f"mirror roots are invalid: {mirror['source_root']} -> {mirror['target_root']}")
            continue
        excluded_names = set(mirror["exclude"])
        for target in sorted(target_root.glob(mirror["pattern"])):
            if target.name in excluded_names or not target.is_file():
                continue
            source = source_root / target.name
            display = target.relative_to(root).as_posix()
            if not source.is_file():
                errors.append(f"generated mirror lacks source: {display}")
            elif not equal_content(source, target, mirror["comparison"]):
                errors.append(f"generated mirror is stale: {display}")
    return sorted(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    errors = validate(root, load(args.manifest), load(args.schema))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Documentation ownership and generated mirrors are current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
