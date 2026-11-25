#!/usr/bin/env python3
"""Run repository-owned local checks without presenting them as hosted evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import TypedDict


class Check(TypedDict):
    id: str
    required: bool
    command: list[str]


class GateConfig(TypedDict):
    schema_version: str
    checks: list[Check]


class CheckResult(TypedDict):
    id: str
    required: bool
    status: str
    exit_code: int | None


def load_config(path: Path) -> GateConfig:
    data: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != "ai-safe2.local-gate.v1":
        raise ValueError("unsupported local-gate schema_version")
    checks = data.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("local gate requires at least one check")
    normalized: list[Check] = []
    seen: set[str] = set()
    for raw in checks:
        if not isinstance(raw, dict):
            raise ValueError("each local-gate check must be an object")
        check_id = raw.get("id")
        required = raw.get("required")
        command = raw.get("command")
        if not isinstance(check_id, str) or not check_id or check_id in seen:
            raise ValueError("local-gate check ids must be unique non-empty strings")
        if not isinstance(required, bool):
            raise ValueError(f"required must be boolean for {check_id}")
        if not isinstance(command, list) or not command or not all(isinstance(item, str) and item for item in command):
            raise ValueError(f"command must be a non-empty string array for {check_id}")
        seen.add(check_id)
        normalized.append({"id": check_id, "required": required, "command": command})
    return {"schema_version": "ai-safe2.local-gate.v1", "checks": normalized}


def execute(config: GateConfig, repository: Path) -> list[CheckResult]:
    results: list[CheckResult] = []
    for check in config["checks"]:
        command = [sys.executable if item == "{python}" else item for item in check["command"]]
        try:
            completed = subprocess.run(command, cwd=repository, check=False)
        except FileNotFoundError:
            results.append({"id": check["id"], "required": check["required"], "status": "unavailable", "exit_code": None})
            continue
        status = "passed" if completed.returncode == 0 else "failed"
        results.append({"id": check["id"], "required": check["required"], "status": status, "exit_code": completed.returncode})
    return results


def gate_failed(results: list[CheckResult]) -> bool:
    return any(result["required"] and result["status"] != "passed" for result in results)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    args = parser.parse_args()
    config = load_config(args.config.resolve())
    repository = args.repository.resolve()
    results = execute(config, repository)
    for result in results:
        exit_text = "" if result["exit_code"] is None else f" exit={result['exit_code']}"
        print(f"{result['id']}: {result['status']}{exit_text}")
    if gate_failed(results):
        print("Local gate failed. Hosted CI has not been evaluated.")
        return 1
    print("Local gate passed. Hosted CI is still required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
