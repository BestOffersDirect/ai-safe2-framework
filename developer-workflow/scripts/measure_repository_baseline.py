#!/usr/bin/env python3
"""Measure repository facts without turning configuration into proof of execution."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from urllib.parse import urlparse


IGNORED_PARTS = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv", "node_modules", "venv"}


def ignored(path: Path, repository: Path) -> bool:
    parts = path.relative_to(repository).parts
    return any(part in IGNORED_PARTS or part.startswith(".venv") for part in parts)


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
            text=True,
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
            text=True,
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
            text=True,
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
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return bool(result.stdout.strip())


def files_containing(repository: Path, files: list[Path], terms: tuple[str, ...]) -> list[Path]:
    matches: list[Path] = []
    for path in files:
        if path.suffix.lower() not in {".toml", ".txt", ".yaml", ".yml"}:
            continue
        try:
            content = path.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            continue
        if any(term in content for term in terms):
            matches.append(path)
    return matches


def adversarial_test_files(repository: Path, files: list[Path]) -> list[Path]:
    matches: list[Path] = []
    for path in files:
        if path.resolve() == Path(__file__).resolve():
            continue
        relative_path = path.relative_to(repository)
        is_workflow = relative_path.parts[:2] == (".github", "workflows") and path.suffix.lower() in {".yml", ".yaml"}
        is_dependency_file = path.suffix.lower() in {".toml", ".txt"}
        is_python = path.suffix.lower() == ".py"
        if not (is_workflow or is_dependency_file or is_python):
            continue
        try:
            content = path.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            continue
        dependency_signal = (is_workflow or is_dependency_file) and any(
            term in content for term in ("mutmut", "atheris", "python-afl")
        )
        import_signal = is_python and any(
            term in content
            for term in ("from hypothesis", "import hypothesis", "import atheris", "import python_afl")
        )
        hypothesis_signal = "hypothesis" in content and (is_workflow or is_dependency_file)
        if dependency_signal or import_signal or hypothesis_signal:
            matches.append(path)
    return matches


def observation(paths: list[Path], repository: Path) -> dict[str, object]:
    evidence = relative(repository, paths)
    return {"status": "observed" if evidence else "not_observed", "evidence": evidence}


def measure(repository: Path) -> dict[str, object]:
    repository = repository.resolve()
    files = repository_files(repository)
    python_files = [path for path in files if path.suffix.lower() == ".py"]
    test_python_files = [
        path
        for path in python_files
        if path.name.startswith("test_") or "tests" in path.relative_to(repository).parts
    ]
    markdown_files = [path for path in files if path.suffix.lower() == ".md"]
    workflow_files = [
        path
        for path in files
        if path.suffix.lower() in {".yml", ".yaml"}
        and path.relative_to(repository).parts[:2] == (".github", "workflows")
    ]

    codeowners = [
        repository / candidate
        for candidate in ("CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS")
        if (repository / candidate).is_file()
    ]
    pre_commit = [path for path in files if path.name in {".pre-commit-config.yaml", ".pre-commit-config.yml"}]
    type_checking = files_containing(repository, files, ("[tool.mypy]", "[tool.pyright]", "mypy", "pyright"))
    adversarial = adversarial_test_files(repository, files)

    return {
        "schema_version": "ai-safe2.repository-baseline.v1",
        "subject": {
            "repository": repository_name(repository),
            "revision": revision(repository),
            "scope": "working_tree",
            "worktree_dirty": worktree_dirty(repository),
        },
        "inventory": {
            "discovered_files": len(files),
            "python_files": len(python_files),
            "test_python_files": len(test_python_files),
            "markdown_files": len(markdown_files),
            "workflow_files": len(workflow_files),
        },
        "observations": {
            "codeowners": observation(codeowners, repository),
            "local_pre_commit": observation(pre_commit, repository),
            "type_checking": observation(type_checking, repository),
            "adversarial_testing": observation(adversarial, repository),
            "human_review_enforcement": {"status": "unknown", "evidence": []},
        },
        "limits": [
            "File presence does not prove that a check ran or passed.",
            "Repository contents do not prove branch protection or reviewer identity.",
            "A revision identifies the base commit; worktree_dirty states whether uncommitted content was also measured.",
            "Counts exclude common dependency, cache, virtual-environment, and Git directories.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = measure(args.repository)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
