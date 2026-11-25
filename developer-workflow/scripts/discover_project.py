#!/usr/bin/env python3
"""Create a read-only project map from observable repository files."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


IGNORED_PARTS = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__", "node_modules", "venv"}
LANGUAGES = {
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".cs": "C#",
    ".go": "Go",
    ".java": "Java",
    ".js": "JavaScript",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".php": "PHP",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".swift": "Swift",
    ".ts": "TypeScript",
    ".tsx": "TypeScript"
}
ECOSYSTEM_FILES = {
    "Android or Gradle": {"build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"},
    "JavaScript or TypeScript": {"package.json", "pnpm-lock.yaml", "yarn.lock"},
    "Python": {"pyproject.toml", "requirements.txt", "Pipfile", "poetry.lock", "uv.lock"},
    "Rust": {"Cargo.toml", "Cargo.lock"},
    "Go": {"go.mod", "go.sum"},
    "Ruby": {"Gemfile", "Gemfile.lock"},
    "Unity": {"ProjectVersion.txt"},
    "Godot": {"project.godot"}
}
REVIEW_SIGNALS = {
    "authentication": {"auth", "authentication", "authorization", "oauth", "identity"},
    "payments": {"payment", "payments", "billing", "checkout", "settlement"},
    "policy": {"policy", "policies", "ruleset", "rules"},
    "secrets": {"secret", "secrets", "credential", "credentials", "keys"},
    "data": {"database", "db", "migration", "migrations", "storage"},
    "delivery": {"deploy", "deployment", "release", "infra", "infrastructure", "workflows"},
    "agent tools": {"agent", "agents", "mcp", "tools"}
}


def ignored(path: Path, repository: Path) -> bool:
    return any(
        part in IGNORED_PARTS or part.startswith(".venv")
        for part in path.relative_to(repository).parts
    )


def repository_files(repository: Path) -> list[Path]:
    return sorted(
        path
        for path in repository.rglob("*")
        if path.is_file() and not ignored(path, repository)
    )


def relative(repository: Path, paths: list[Path]) -> list[str]:
    return sorted(path.relative_to(repository).as_posix() for path in paths)


def is_git_root(repository: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "-c", f"safe.directory={repository.as_posix()}", "-C", str(repository), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
    return Path(result.stdout.strip()).resolve() == repository.resolve()


def revision(repository: Path) -> str | None:
    if not is_git_root(repository):
        return None
    try:
        result = subprocess.run(
            ["git", "-c", f"safe.directory={repository.as_posix()}", "-C", str(repository), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def repository_name(repository: Path) -> str:
    if not is_git_root(repository):
        return repository.name
    try:
        result = subprocess.run(
            ["git", "-c", f"safe.directory={repository.as_posix()}", "-C", str(repository), "config", "--get", "remote.origin.url"],
            check=True,
            capture_output=True,
            text=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return repository.name
    remote = result.stdout.strip()
    if not remote:
        return repository.name
    if ":" in remote and "://" not in remote:
        remote = remote.rsplit(":", 1)[-1]
    else:
        remote = urlparse(remote).path
    name = Path(remote).name
    return name.removesuffix(".git") or repository.name


def worktree_dirty(repository: Path) -> bool | None:
    if not is_git_root(repository):
        return None
    try:
        result = subprocess.run(
            ["git", "-c", f"safe.directory={repository.as_posix()}", "-C", str(repository), "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return bool(result.stdout.strip())


def ecosystem_evidence(repository: Path, files: list[Path]) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for name, filenames in ECOSYSTEM_FILES.items():
        matches = [path for path in files if path.name in filenames]
        if matches:
            results.append({"name": name, "evidence": relative(repository, matches)})
    return results


def review_candidates(repository: Path, files: list[Path]) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    directories = sorted({path.parent for path in files if path.parent != repository})
    for directory in directories:
        tokens = {part.lower() for part in directory.relative_to(repository).parts}
        signals = sorted(name for name, terms in REVIEW_SIGNALS.items() if tokens & terms)
        if signals:
            candidates.append({"path": directory.relative_to(repository).as_posix(), "signals": signals})
    return candidates


def discover(repository: Path) -> dict[str, object]:
    repository = repository.resolve()
    files = repository_files(repository)
    language_counts = Counter(
        LANGUAGES[path.suffix.lower()]
        for path in files
        if path.suffix.lower() in LANGUAGES
    )
    workflows = [
        path for path in files
        if path.suffix.lower() in {".yml", ".yaml"}
        and path.relative_to(repository).parts[:2] == (".github", "workflows")
    ]
    instruction_names = {"AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md", "SECURITY.md", "copilot-instructions.md"}
    instructions = [path for path in files if path.name in instruction_names]
    documentation = [
        path for path in files
        if path.name.lower() == "readme.md"
        and len(path.relative_to(repository).parts) <= 3
    ]
    return {
        "schema_version": "ai-safe2.project-map.v1",
        "subject": {
            "repository": repository_name(repository),
            "revision": revision(repository),
            "scope": "working_tree",
            "worktree_dirty": worktree_dirty(repository)
        },
        "languages": [
            {"name": name, "file_count": count}
            for name, count in sorted(language_counts.items())
        ],
        "ecosystems": ecosystem_evidence(repository, files),
        "automation": relative(repository, workflows),
        "instructions": relative(repository, instructions),
        "documentation": relative(repository, documentation),
        "review_candidates": review_candidates(repository, files),
        "unknowns": [
            "Repository files do not establish deployed architecture or runtime data flows.",
            "A human must confirm trust boundaries, owners, external services, and sensitive data.",
            "Hosted branch protection, required reviewers, and secret configuration require separate evidence."
        ],
        "limits": [
            "Path names identify review candidates, not confirmed risk or control coverage.",
            "Detected configuration files do not prove that an ecosystem is built, tested, or deployed.",
            "A revision identifies the base commit; worktree_dirty states whether uncommitted content was also mapped.",
            "The project map cannot authorize work or lower the route selected by policy."
        ]
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = discover(args.repository)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
