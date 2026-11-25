from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    path = ROOT / "scripts" / "validate_workflow.py"
    spec = importlib.util.spec_from_file_location("validate_workflow", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def decision_record():
    return {
        "schema_version": "ai-safe2.decision-record.v1",
        "decision_id": "pr-1@abc123",
        "subject": {"identifier": "pr-1", "revision": "abc123"},
        "route": "enhanced",
        "outcome": "hold",
        "required_evidence": ["targeted-validation", "semantic-review"],
        "evidence": [],
        "risks": [],
        "human_authority": {"required": True, "decision_owner": None, "decision_at": None, "rationale": None},
        "replay": {"policy_digest": "sha256:policy", "configuration_digest": "sha256:config", "producer_versions": {}},
    }


def ci_observation():
    return {
        "schema_version": "ai-safe2.ci-execution-observation.v1",
        "receipt_id": "ci-pr-44@abc123",
        "subject": {
            "identifier": "pr-44",
            "revision": "abc123",
            "capability": "device-privacy-tests",
        },
        "runner": {
            "provider": "github-actions",
            "image": "ubuntu-24.04",
            "operating_system": "Linux",
            "architecture": "x86_64",
            "environment_facts": {"hardware_acceleration": True, "api_level": 36},
        },
        "required_phases": ["environment_preflight", "build", "test", "postprocess"],
        "phases": [
            {"name": name, "status": "passed", "exit_code": 0, "failure_class": None, "failure_reason": None}
            for name in ("environment_preflight", "build", "test", "postprocess")
        ],
        "test_results": {
            "status": "passed",
            "minimum_required": 1,
            "discovered": 128,
            "executed": 128,
            "passed": 128,
            "failed": 0,
            "skipped": 0,
        },
        "artifacts": [{"name": "device-test-report", "digest": "sha256:example"}],
        "limitations": [],
    }


def test_package_contracts_validate():
    module = load_validator()
    assert module.validate_package(ROOT) == []


def test_repository_baseline_is_schema_valid_and_preserves_unknown_review_state(tmp_path):
    repository = tmp_path / "sample"
    repository.mkdir()
    (repository / "CODEOWNERS").write_text("* @maintainer\n", encoding="utf-8")
    (repository / "pyproject.toml").write_text("[tool.mypy]\nstrict = true\n", encoding="utf-8")
    (repository / "src").mkdir()
    (repository / "src" / "service.py").write_text("value: int = 1\n", encoding="utf-8")
    (repository / "tests").mkdir()
    (repository / "tests" / "test_service.py").write_text("def test_value(): pass\n", encoding="utf-8")
    (repository / "issue.yml").write_text("prompt: State the hypothesis\n", encoding="utf-8")
    (repository / ".venv-custom" / "Lib").mkdir(parents=True)
    adversarial_import = "import " + "hypothesis\n"
    (repository / ".venv-custom" / "Lib" / "dependency.py").write_text(adversarial_import, encoding="utf-8")

    module = load_script("measure_repository_baseline.py")
    result = module.measure(repository)
    schema = json.loads((ROOT / "schemas" / "repository-baseline-v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(result)

    assert result["inventory"]["python_files"] == 2
    assert result["inventory"]["test_python_files"] == 1
    assert result["observations"]["codeowners"]["status"] == "observed"
    assert result["observations"]["local_pre_commit"]["status"] == "not_observed"
    assert result["observations"]["type_checking"]["status"] == "observed"
    assert result["observations"]["adversarial_testing"]["status"] == "not_observed"
    assert result["observations"]["human_review_enforcement"]["status"] == "unknown"
    assert result["subject"]["scope"] == "working_tree"
    assert result["subject"]["worktree_dirty"] is None


def test_project_discovery_is_read_only_schema_valid_and_non_authoritative(tmp_path):
    repository = tmp_path / "sample-game"
    repository.mkdir()
    (repository / "pyproject.toml").write_text("[project]\nname = 'sample'\n", encoding="utf-8")
    (repository / "AGENTS.md").write_text("Review instructions.\n", encoding="utf-8")
    (repository / "README.md").write_text("# Sample\n", encoding="utf-8")
    (repository / ".github" / "workflows").mkdir(parents=True)
    (repository / ".github" / "workflows" / "ci.yml").write_text("name: CI\n", encoding="utf-8")
    (repository / "src" / "payments").mkdir(parents=True)
    (repository / "src" / "payments" / "service.py").write_text("value: int = 1\n", encoding="utf-8")
    before = sorted(path.relative_to(repository).as_posix() for path in repository.rglob("*") if path.is_file())

    module = load_script("discover_project.py")
    result = module.discover(repository)
    schema = json.loads((ROOT / "schemas" / "project-map-v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(result)
    after = sorted(path.relative_to(repository).as_posix() for path in repository.rglob("*") if path.is_file())

    assert before == after
    assert result["subject"]["scope"] == "working_tree"
    assert result["subject"]["worktree_dirty"] is None
    assert {item["name"] for item in result["languages"]} == {"Python"}
    assert result["ecosystems"] == [{"name": "Python", "evidence": ["pyproject.toml"]}]
    assert result["automation"] == [".github/workflows/ci.yml"]
    assert result["instructions"] == ["AGENTS.md"]
    assert {item["path"] for item in result["review_candidates"]} >= {"src/payments"}
    assert any("cannot authorize" in limit for limit in result["limits"])


def test_local_gate_config_is_valid_and_required_failures_block(tmp_path):
    schema = json.loads((ROOT / "schemas" / "local-gate-v1.schema.json").read_text(encoding="utf-8"))
    config = json.loads((ROOT / "local-gate.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(config)

    module = load_script("run_local_gate.py")
    fixture = {
        "schema_version": "ai-safe2.local-gate.v1",
        "checks": [
            {"id": "passes", "required": True, "command": ["{python}", "-c", "raise SystemExit(0)"]},
            {"id": "optional-missing", "required": False, "command": ["missing-local-gate-command"]},
            {"id": "required-failure", "required": True, "command": ["{python}", "-c", "raise SystemExit(3)"]}
        ]
    }
    config_path = tmp_path / "local-gate.json"
    config_path.write_text(json.dumps(fixture), encoding="utf-8")
    loaded = module.load_config(config_path)
    results = module.execute(loaded, tmp_path)

    assert [result["status"] for result in results] == ["passed", "unavailable", "failed"]
    assert module.gate_failed(results) is True


def test_local_gate_scripts_match_documented_strict_type_boundary():
    config = json.loads((ROOT / "local-gate.json").read_text(encoding="utf-8"))
    type_check = next(check for check in config["checks"] if check["id"] == "discovery-types")
    assert type_check["required"] is True
    for script in ("measure_repository_baseline.py", "discover_project.py", "run_local_gate.py", "validate_agent_handoff.py", "attach_evidence.py", "evaluate_adversarial_assurance.py", "validate_documentation_ownership.py", "evaluate_release_qualification.py"):
        assert f"scripts/{script}" in type_check["command"]


def test_local_gate_template_preserves_contract_and_runner_parity():
    release_schema = json.loads((ROOT / "schemas" / "local-gate-v1.schema.json").read_text(encoding="utf-8"))
    template_schema = json.loads(
        (ROOT / "repository-template" / ".ai-safe2" / "schemas" / "local-gate-v1.schema.json").read_text(encoding="utf-8")
    )
    template_config = json.loads(
        (ROOT / "repository-template" / ".ai-safe2" / "local-gate.json").read_text(encoding="utf-8")
    )
    assert release_schema == template_schema
    Draft202012Validator(release_schema).validate(template_config)
    assert template_config["checks"] == [
        {
            "id": "workflow-contracts",
            "required": True,
            "command": ["{python}", "scripts/validate_workflow.py", "--root", "."]
        },
        {
            "id": "documentation-ownership",
            "required": True,
            "command": ["{python}", "scripts/validate_documentation_ownership.py", "--root", ".", "--manifest", ".ai-safe2/documentation-ownership.json", "--schema", ".ai-safe2/schemas/documentation-ownership-v1.schema.json"]
        }
    ]
    assert (ROOT / "scripts" / "run_local_gate.py").read_text(encoding="utf-8").rstrip() == (
        ROOT / "repository-template" / "scripts" / "run_local_gate.py"
    ).read_text(encoding="utf-8").rstrip()


def execution_boundary():
    return {
        "schema_version": "ai-safe2.agent-execution-boundary.v1",
        "boundary_id": "boundary-1",
        "plan_ref": "evidence/development-plan.json",
        "subject": {"task_id": "task-1", "base_revision": "abc123"},
        "ownership": {"accountable_human": "maintainer", "executor_id": "codex-worker-1", "executor_type": "agent"},
        "scope": {"include": ["developer-workflow"], "exclude": ["developer-workflow/evidence/private"], "concurrent_write_policy": "isolated_worktree"},
        "isolation": {"strategy": "worktree", "reference": "feat/example"},
        "tools": [{"tool_id": "local-files", "permissions": ["read", "write"], "data_boundary": "local", "secrets_required": False, "rationale": "Edit the authorized package."}],
        "skills": [{
            "skill_id": "superpowers",
            "source": "https://github.com/obra/superpowers",
            "pin": "commit:abc123",
            "license": "MIT",
            "trust_gate": {"status": "produced", "evidence_ref": "evidence/superpowers-safe2.json"},
            "external_review": {"status": "not_requested", "evidence_ref": None},
            "admission": "admit",
            "decision_owner": "maintainer"
        }],
        "budgets": {"max_parallel_workers": 2, "max_subagent_depth": 1, "max_elapsed_minutes": 120, "max_tool_calls": 100},
        "stop_conditions": [{"id": "scope-change", "trigger": "Required work falls outside included paths.", "action": "escalate"}],
        "authority": {"modify_scoped_files": True, "merge": False, "release": False, "deploy": False, "policy_change": False, "exception": False, "risk_acceptance": False},
        "human_authorization": {"status": "authorized", "owner": "maintainer", "authorized_at": "2026-11-23T20:00:00Z"},
        "limitations": ["Authorization applies only to the named task, revision, scope, tools, and budgets."]
    }


def agent_handoff():
    return {
        "schema_version": "ai-safe2.agent-handoff.v1",
        "handoff_id": "handoff-1",
        "boundary_id": "boundary-1",
        "task_id": "task-1",
        "base_revision": "abc123",
        "result_revision": "def456",
        "executor_id": "codex-worker-1",
        "status": "partial",
        "changed_paths": ["developer-workflow/docs/guide.md"],
        "skills_used": ["superpowers"],
        "evidence_refs": ["evidence/tests.json"],
        "findings": [],
        "assumptions": [],
        "unknowns": ["Hosted CI has not run."],
        "conflicts": [],
        "residual_risks": ["The handoff is an executor-produced claim."],
        "stop_conditions_triggered": [],
        "next_action": "Run hosted checks and build the development receipt.",
        "authority": {"completion_verified": False, "merge": False, "release": False, "deploy": False, "risk_acceptance": False},
        "limitations": ["This handoff does not prove completion or approval."]
    }


def test_execution_boundary_and_handoff_validate_together():
    module = load_script("validate_agent_handoff.py")
    assert module.validate_bundle(execution_boundary(), agent_handoff(), ROOT / "schemas") == []


def test_execution_boundary_rejects_unscoped_changes_unadmitted_skills_and_false_completion():
    module = load_script("validate_agent_handoff.py")
    boundary = execution_boundary()
    handoff = agent_handoff()
    handoff["changed_paths"] = ["NEXUS/payments/service.py"]
    handoff["skills_used"] = ["unreviewed-skill"]
    handoff["status"] = "completed"
    handoff["stop_conditions_triggered"] = ["scope-change"]
    errors = module.validate_bundle(boundary, handoff, ROOT / "schemas")
    assert "changed path is outside included scope: NEXUS/payments/service.py" in errors
    assert "handoff used a skill that was not admitted: unreviewed-skill" in errors
    assert "completed handoff cannot report triggered stop conditions" in errors


def test_execution_boundary_cannot_admit_skill_without_native_gate_and_owner():
    boundary = execution_boundary()
    boundary["skills"][0]["trust_gate"] = {"status": "unavailable", "evidence_ref": None}
    boundary["skills"][0]["decision_owner"] = None
    schema = json.loads((ROOT / "schemas" / "agent-execution-boundary-v1.schema.json").read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(boundary))
    assert errors


def test_execution_boundary_rejects_produced_skill_evidence_without_reference():
    boundary = execution_boundary()
    boundary["skills"][0]["trust_gate"]["evidence_ref"] = None
    schema = json.loads((ROOT / "schemas" / "agent-execution-boundary-v1.schema.json").read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(boundary))
    assert errors


def test_agent_handoff_rejects_path_traversal_and_base_revision_mismatch():
    module = load_script("validate_agent_handoff.py")
    handoff = agent_handoff()
    handoff["base_revision"] = "wrong-base"
    handoff["changed_paths"] = ["developer-workflow/../NEXUS/service.py"]
    errors = module.validate_bundle(execution_boundary(), handoff, ROOT / "schemas")
    assert "handoff base_revision does not match" in errors
    assert "handoff contains an invalid relative changed path: developer-workflow/../NEXUS/service.py" in errors


def test_agent_boundary_contracts_are_exported_without_drift():
    for schema_name in (
        "agent-execution-boundary-v1.schema.json",
        "agent-handoff-v1.schema.json",
    ):
        release_schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
        template_schema = json.loads(
            (ROOT / "repository-template" / ".ai-safe2" / "schemas" / schema_name).read_text(encoding="utf-8")
        )
        assert release_schema == template_schema
    assert (ROOT / "scripts" / "validate_agent_handoff.py").read_text(encoding="utf-8").rstrip() == (
        ROOT / "repository-template" / "scripts" / "validate_agent_handoff.py"
    ).read_text(encoding="utf-8").rstrip()


def evidence_envelope(module, *, revision="abc123", status="produced"):
    envelope = {
        "schema_version": "ai-safe2.evidence-envelope.v1",
        "evidence_id": "review-1",
        "subject": {"type": "repository_change", "identifier": "pr-1", "revision": revision, "scope": ["src/"]},
        "producer": {"adapter_id": "codex-review", "name": "Codex review", "version": "1.2.3", "capabilities": ["semantic-review"], "model": "model-family"},
        "execution": {"status": status, "started_at": "2026-11-23T20:00:00Z", "completed_at": "2026-11-23T20:01:00Z", "policy_digest": "sha256:policy", "failure_reason": None},
        "observations": [],
        "findings": [],
        "limitations": ["Reviewer output is advisory."],
        "artifacts": [],
    }
    envelope["integrity"] = {"content_digest": module.canonical_digest(envelope), "signature": None}
    return envelope


def test_evidence_bridge_attaches_valid_revision_bound_envelope_without_deciding():
    module = load_script("attach_evidence.py")
    record, errors = module.attach(decision_record(), [evidence_envelope(module)])
    assert errors == []
    assert record["outcome"] == "hold"
    assert record["evidence"] == [{
        "evidence_id": "review-1",
        "capability": "semantic-review",
        "status": "produced",
        "subject_revision": "abc123",
        "producer": "codex-review",
    }]
    assert record["replay"]["producer_versions"]["codex-review"] == "1.2.3"


def test_evidence_bridge_rejects_stale_revision_and_tampered_digest():
    module = load_script("attach_evidence.py")
    stale = evidence_envelope(module, revision="old-revision")
    _, errors = module.attach(decision_record(), [stale])
    assert "review-1: subject revision does not match decision record" in errors
    stale["producer"]["version"] = "tampered"
    schema = json.loads((ROOT / "schemas" / "evidence-envelope-v1.schema.json").read_text(encoding="utf-8"))
    assert "integrity: content_digest does not match canonical envelope content" in module.validate_envelope(stale, schema)


def test_attachment_checks_policy_and_preserves_recorded_human_decisions():
    module = load_script("attach_evidence.py")
    record = decision_record()
    envelope = evidence_envelope(module)
    record["replay"]["policy_digest"] = "sha256:different"
    _, errors = module.attach(record, [envelope])
    assert any("policy digest does not match" in error for error in errors)
    record["outcome"] = "deferred"
    unchanged, errors = module.attach(record, [envelope])
    assert unchanged == record
    assert "refusing to alter a recorded human decision" in errors


def test_handoff_rejects_writes_without_authority():
    module = load_script("validate_agent_handoff.py")
    boundary = execution_boundary()
    boundary["authority"]["modify_scoped_files"] = False
    assert "handoff reports writes without an authorized write boundary" in module.validate_bundle(
        boundary, agent_handoff(), ROOT / "schemas"
    )


def test_evidence_bridge_rejects_duplicate_identity_and_producer_version_conflicts():
    module = load_script("attach_evidence.py")
    first = evidence_envelope(module)
    second = evidence_envelope(module)
    second["producer"]["version"] = "2.0.0"
    second["producer"]["capabilities"] = ["security-diff"]
    second["integrity"] = {"content_digest": module.canonical_digest(second), "signature": None}
    _, errors = module.attach(decision_record(), [first, second])
    assert "review-1: duplicate evidence_id has conflicting content" in errors
    assert "codex-review: conflicting producer versions in attached evidence" in errors


def test_review_provenance_records_dependence_without_claiming_independence():
    record = {
        "schema_version": "ai-safe2.review-provenance.v1",
        "review_evidence_id": "review-1",
        "subject": {"identifier": "pr-1", "revision": "abc123", "scope": ["src/"]},
        "producer": {"kind": "model", "adapter_id": "codex-review", "provider": "openai", "model_family": "gpt", "operator_id": None},
        "inputs": {"context_refs": ["revision:abc123"], "prior_review_evidence_ids": [], "implementation_evidence_ids": ["handoff-1"]},
        "relationship_to_change_author": "unknown",
        "dependence_assessment": {"status": "not_assessed", "known_overlaps": ["unknown"], "assessor": None, "basis": "No evidence established reviewer separation."},
        "limitations": ["This record does not establish independent assurance."]
    }
    schema = json.loads((ROOT / "schemas" / "review-provenance-v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(record)
    assert "independent" not in schema["properties"]["dependence_assessment"]["properties"]["status"]["enum"]

    record["dependence_assessment"] = {
        "status": "separation_observed",
        "known_overlaps": ["provider"],
        "assessor": None,
        "basis": "Unsupported claim."
    }
    assert list(Draft202012Validator(schema).iter_errors(record))


def test_evidence_bridge_contracts_are_exported_without_drift():
    assert json.loads((ROOT / "schemas" / "review-provenance-v1.schema.json").read_text(encoding="utf-8")) == json.loads(
        (ROOT / "repository-template" / ".ai-safe2" / "schemas" / "review-provenance-v1.schema.json").read_text(encoding="utf-8")
    )
    assert (ROOT / "scripts" / "attach_evidence.py").read_text(encoding="utf-8").rstrip() == (
        ROOT / "repository-template" / "scripts" / "attach_evidence.py"
    ).read_text(encoding="utf-8").rstrip()


def adversarial_receipt():
    campaigns = []
    for method in ("property", "mutation", "fuzz"):
        campaigns.append({
            "campaign_id": f"{method}-critical-parser",
            "method": method,
            "target": "Critical parser authorization boundary",
            "tool": {"name": f"example-{method}-tool", "version": "1.0.0"},
            "execution_status": "produced",
            "started_at": "2026-11-23T20:00:00Z",
            "completed_at": "2026-11-23T20:01:00Z",
            "counts": {"attempted": 100, "completed": 100, "findings": 0, "skipped": 0, "timed_out": 0},
            "finding_refs": [],
            "artifact_refs": [f"evidence/{method}.json"],
            "failure_reason": None,
            "limitations": ["This campaign covers only the named parser boundary."]
        })
    return {
        "schema_version": "ai-safe2.adversarial-assurance-receipt.v1",
        "receipt_id": "adversarial-pr-1@abc123",
        "subject": {"identifier": "pr-1", "revision": "abc123", "scope": ["src/parser.py"]},
        "required_methods": ["property", "mutation", "fuzz"],
        "campaigns": campaigns,
        "conclusion": {"status": "incomplete", "satisfied_methods": [], "methods_with_findings": [], "incomplete_methods": ["property", "mutation", "fuzz"]},
        "authority": {"completion_verified": False, "merge": False, "release": False, "risk_acceptance": False},
        "limitations": ["Tool-native artifacts require separate retention and review."]
    }


def test_adversarial_assurance_pass_requires_complete_nonempty_campaigns():
    module = load_script("evaluate_adversarial_assurance.py")
    result, errors = module.evaluate(adversarial_receipt())
    assert errors == []
    assert result["conclusion"] == {
        "status": "pass",
        "satisfied_methods": ["property", "mutation", "fuzz"],
        "methods_with_findings": [],
        "incomplete_methods": [],
    }
    schema = json.loads((ROOT / "schemas" / "adversarial-assurance-receipt-v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(result)


def test_adversarial_assurance_preserves_findings_and_unavailable_tools():
    module = load_script("evaluate_adversarial_assurance.py")
    receipt = adversarial_receipt()
    receipt["campaigns"][1]["counts"]["findings"] = 1
    receipt["campaigns"][1]["finding_refs"] = ["evidence/surviving-mutant-1.json"]
    unavailable = receipt["campaigns"][2]
    unavailable["execution_status"] = "unavailable"
    unavailable["started_at"] = None
    unavailable["completed_at"] = None
    unavailable["counts"] = {"attempted": 0, "completed": 0, "findings": 0, "skipped": 0, "timed_out": 0}
    unavailable["failure_reason"] = "Fuzzer is not installed on this runner."
    result, errors = module.evaluate(receipt)
    assert errors == []
    assert result["conclusion"]["status"] == "findings"
    assert result["conclusion"]["methods_with_findings"] == ["mutation"]
    assert result["conclusion"]["incomplete_methods"] == ["fuzz"]


def test_adversarial_assurance_rejects_impossible_or_hidden_counts():
    module = load_script("evaluate_adversarial_assurance.py")
    receipt = adversarial_receipt()
    campaign = receipt["campaigns"][0]
    campaign["counts"] = {"attempted": 10, "completed": 8, "findings": 9, "skipped": 0, "timed_out": 0}
    _, errors = module.evaluate(receipt)
    assert any("must equal attempted" in error for error in errors)
    assert any("findings cannot exceed completed" in error for error in errors)

    duplicate = adversarial_receipt()
    duplicate["campaigns"].append(dict(duplicate["campaigns"][0]))
    _, duplicate_errors = module.evaluate(duplicate)
    assert "campaign_id values must be unique" in duplicate_errors


def test_adversarial_assurance_contracts_are_exported_without_drift():
    assert json.loads((ROOT / "schemas" / "adversarial-assurance-receipt-v1.schema.json").read_text(encoding="utf-8")) == json.loads(
        (ROOT / "repository-template" / ".ai-safe2" / "schemas" / "adversarial-assurance-receipt-v1.schema.json").read_text(encoding="utf-8")
    )
    assert (ROOT / "scripts" / "evaluate_adversarial_assurance.py").read_text(encoding="utf-8").rstrip() == (
        ROOT / "repository-template" / "scripts" / "evaluate_adversarial_assurance.py"
    ).read_text(encoding="utf-8").rstrip()


def test_documentation_ownership_covers_package_and_export_template():
    module = load_script("validate_documentation_ownership.py")
    schema = json.loads((ROOT / "schemas" / "documentation-ownership-v1.schema.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "documentation-ownership.json").read_text(encoding="utf-8"))
    assert module.validate(ROOT, manifest, schema) == []

    template_manifest = json.loads(
        (ROOT / "repository-template" / ".ai-safe2" / "documentation-ownership.json").read_text(encoding="utf-8")
    )
    assert module.validate(ROOT / "repository-template", template_manifest, schema) == []


def test_documentation_ownership_detects_unowned_markdown_and_stale_mirror(tmp_path):
    module = load_script("validate_documentation_ownership.py")
    schema = json.loads((ROOT / "schemas" / "documentation-ownership-v1.schema.json").read_text(encoding="utf-8"))
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "owned.md").write_text("# Owned\n", encoding="utf-8")
    (tmp_path / "docs" / "unowned.md").write_text("# Unowned\n", encoding="utf-8")
    (tmp_path / "source").mkdir()
    (tmp_path / "target").mkdir()
    (tmp_path / "source" / "mirror.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "target" / "mirror.py").write_text("value = 2\n", encoding="utf-8")
    manifest = {
        "schema_version": "ai-safe2.documentation-ownership.v1",
        "documents": [{
            "path": "docs/owned.md", "classification": "canonical", "owner": "maintainer",
            "canonical_sources": [], "freshness": "manual_review", "status": "current", "notice": None
        }],
        "mirror_sets": [{
            "source_root": "source", "target_root": "target", "pattern": "*.py", "exclude": [],
            "comparison": "normalized_text", "owner": "maintainer", "notice": "Generated mirror."
        }],
        "coverage": {"markdown_roots": ["docs"], "exclude": []}
    }
    errors = module.validate(tmp_path, manifest, schema)
    assert "markdown document lacks ownership entry: docs/unowned.md" in errors
    assert "generated mirror is stale: target/mirror.py" in errors


def test_documentation_ownership_contracts_are_exported_without_drift():
    assert json.loads((ROOT / "schemas" / "documentation-ownership-v1.schema.json").read_text(encoding="utf-8")) == json.loads(
        (ROOT / "repository-template" / ".ai-safe2" / "schemas" / "documentation-ownership-v1.schema.json").read_text(encoding="utf-8")
    )
    assert (ROOT / "scripts" / "validate_documentation_ownership.py").read_text(encoding="utf-8").rstrip() == (
        ROOT / "repository-template" / "scripts" / "validate_documentation_ownership.py"
    ).read_text(encoding="utf-8").rstrip()


def test_adapters_cannot_authorize():
    manifests = json.loads((ROOT / "adapters" / "manifests.json").read_text(encoding="utf-8"))
    assert manifests
    assert all("authorize" not in manifest["authority"] for manifest in manifests)


def test_game_profile_contains_authority_and_economy_lenses():
    profile = json.loads((ROOT / "profiles" / "game.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schemas" / "product-profile-v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(profile)
    assert "client-server-authority" in profile["lenses"]
    assert "economy-inventory-purchase-entitlements" in profile["lenses"]
    assert profile["maturity"] == "preview"
    assert profile["canary"]["status"] == "local_fixture"


def test_profile_catalog_does_not_present_unqualified_profiles_as_bundled():
    catalog = json.loads((ROOT / "profiles" / "catalog.json").read_text(encoding="utf-8"))
    bundled = [item["profile_id"] for item in catalog["profiles"] if item["availability"] == "bundled_preview"]
    assert bundled == ["game"]
    assert all(item["path"] is None for item in catalog["profiles"] if item["availability"] == "planned")

    schema = json.loads((ROOT / "schemas" / "product-profile-v1.schema.json").read_text(encoding="utf-8"))
    template_profile = json.loads(
        (ROOT / "repository-template" / ".ai-safe2" / "profiles" / "game.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(template_profile)


def test_required_provider_failure_cannot_be_pass():
    workflow = json.loads(
        (ROOT / "repository-template" / ".ai-safe2" / "workflow.json").read_text(encoding="utf-8")
    )
    assert workflow["invariants"]["provider_failure_is_not_pass"] is True
    assert workflow["routes"]["critical"]["security_review"] == "required"


def test_game_change_routing():
    path = ROOT / "scripts" / "classify_change.py"
    spec = importlib.util.spec_from_file_location("classify_change", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    profile = json.loads((ROOT / "profiles" / "game.json").read_text(encoding="utf-8"))
    assert module.classify(["docs/guide.md"], profile)["route"] == "standard"
    assert module.classify(["src/gameplay/player.cs"], profile)["route"] == "enhanced"
    assert module.classify(["src/multiplayer/authority.cs"], profile)["route"] == "critical"


def test_terminal_decision_requires_human_record():
    schema = json.loads((ROOT / "schemas" / "decision-record-v1.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    record = decision_record()
    record["outcome"] = "approved"
    with pytest.raises(ValidationError):
        validator.validate(record)
    record["human_authority"] = {
        "required": True,
        "decision_owner": "release-owner",
        "decision_at": "2026-10-09T04:00:00Z",
        "rationale": "Required evidence was reviewed.",
    }
    validator.validate(record)


def test_evidence_evaluator_is_revision_bound_and_cannot_authorize():
    module = load_script("evaluate_decision.py")
    record = decision_record()
    record["evidence"] = [
        {"evidence_id": "e1", "capability": "targeted-validation", "status": "produced", "subject_revision": "abc123", "producer": "pytest"},
        {"evidence_id": "e2", "capability": "semantic-review", "status": "produced", "subject_revision": "old-revision", "producer": "reviewer"},
    ]
    assert module.evaluate(record)["outcome"] == "hold"
    record["evidence"][1]["subject_revision"] = "abc123"
    evaluated = module.evaluate(record)
    assert evaluated["outcome"] == "ready_for_human_decision"
    assert evaluated["human_authority"]["decision_owner"] is None


def test_failed_or_unavailable_evidence_never_satisfies_requirement():
    module = load_script("evaluate_decision.py")
    record = decision_record()
    record["evidence"] = [
        {"evidence_id": "e1", "capability": capability, "status": status, "subject_revision": "abc123", "producer": "provider"}
        for capability, status in (("targeted-validation", "failed"), ("semantic-review", "unavailable"))
    ]
    assert module.evaluate(record)["outcome"] == "hold"


def test_template_classifier_matches_release_classifier(tmp_path):
    paths_file = tmp_path / "paths.txt"
    paths_file.write_text("docs/guide.md\nsrc/multiplayer/authority.cs\n", encoding="utf-8")
    outputs = []
    for script in (ROOT / "scripts" / "classify_change.py", ROOT / "repository-template" / "scripts" / "classify_change.py"):
        output = tmp_path / f"{script.parent.name}.json"
        subprocess.run(
            [sys.executable, str(script), "--profile", str(ROOT / "profiles" / "game.json"), "--paths-file", str(paths_file), "--output", str(output)],
            check=True,
        )
        outputs.append(json.loads(output.read_text(encoding="utf-8")))
    assert outputs[0] == outputs[1]
    assert outputs[0]["route"] == "critical"


def test_template_explainer_matches_release_and_describes_boundaries(tmp_path):
    workflow = ROOT / "repository-template" / ".ai-safe2" / "workflow.json"
    profile = ROOT / "repository-template" / ".ai-safe2" / "profiles" / "game.json"
    outputs = []
    for script in (
        ROOT / "scripts" / "explain_workflow.py",
        ROOT / "repository-template" / "scripts" / "explain_workflow.py",
    ):
        output = tmp_path / f"{script.parent.name}-workflow.md"
        subprocess.run(
            [
                sys.executable,
                str(script),
                "--workflow",
                str(workflow),
                "--profile",
                str(profile),
                "--output",
                str(output),
            ],
            check=True,
        )
        outputs.append(output.read_text(encoding="utf-8"))
    assert outputs[0] == outputs[1]
    assert "## What changed" in outputs[0]
    assert "## Current preview boundary" in outputs[0]
    assert "## CI execution evidence boundary" in outputs[0]
    assert "wrapper exit code" in outputs[0]
    assert "Superpowers" in outputs[0]
    assert "Codex Security" in outputs[0]
    assert "cannot merge, release, deploy, or" in outputs[0]
    assert "a CLI decision-routing result, a human decision record" in outputs[0]


def test_required_decision_tools_match_template():
    for name in ("build_cli_decision_request.py", "build_decision_record.py", "evaluate_decision.py"):
        assert (ROOT / "scripts" / name).read_text(encoding="utf-8").rstrip() == (
            ROOT / "repository-template" / "scripts" / name
        ).read_text(encoding="utf-8").rstrip()
    assert json.loads((ROOT / "schemas" / "decision-record-v1.schema.json").read_text(encoding="utf-8")) == json.loads(
        (ROOT / "repository-template" / ".ai-safe2" / "schemas" / "decision-record-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )


def test_ci_execution_receipt_is_revision_bound_and_schema_valid():
    module = load_script("evaluate_ci_execution.py")
    receipt = module.evaluate(ci_observation())
    assert receipt["subject"]["revision"] == "abc123"
    assert receipt["outcome"] == "produced"
    assert receipt["failure"] == {"class": None, "phase": None, "reason": None}
    schema = json.loads((ROOT / "schemas" / "ci-execution-receipt-v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(receipt)
    unsigned = {key: value for key, value in receipt.items() if key != "integrity"}
    assert receipt["integrity"]["content_digest"] == module.canonical_digest(unsigned)


def test_ci_environment_failure_is_not_an_application_failure():
    module = load_script("evaluate_ci_execution.py")
    source = ci_observation()
    source["phases"][0] = {
        "name": "environment_preflight",
        "status": "failed",
        "exit_code": 1,
        "failure_class": "environment_preflight",
        "failure_reason": "Required accelerator was unavailable.",
    }
    source["phases"][1]["status"] = "not_run"
    source["phases"][2]["status"] = "not_run"
    source["phases"][3]["status"] = "not_run"
    source["test_results"] = None
    receipt = module.evaluate(source)
    assert receipt["outcome"] == "failed"
    assert receipt["failure"]["class"] == "environment_preflight"
    assert receipt["failure"]["phase"] == "environment_preflight"


def test_ci_postprocess_failure_preserves_passing_test_result():
    module = load_script("evaluate_ci_execution.py")
    source = ci_observation()
    source["phases"][3] = {
        "name": "postprocess",
        "status": "failed",
        "exit_code": 2,
        "failure_class": "postprocess",
        "failure_reason": "The wrapper split a multiline shell conditional.",
    }
    receipt = module.evaluate(source)
    assert receipt["outcome"] == "failed"
    assert receipt["failure"]["class"] == "postprocess"
    assert receipt["test_results"]["status"] == "passed"
    assert receipt["test_results"]["executed"] == 128
    assert receipt["test_results"]["failed"] == 0


def test_ci_zero_or_inconsistent_tests_fail_closed_as_harness_failure():
    module = load_script("evaluate_ci_execution.py")
    source = ci_observation()
    source["test_results"].update(
        {"status": "passed", "discovered": 0, "executed": 0, "passed": 0}
    )
    receipt = module.evaluate(source)
    assert receipt["outcome"] == "failed"
    assert receipt["failure"]["class"] == "test_harness"
    assert receipt["failure"]["phase"] == "test"


def test_ci_rejects_internally_inconsistent_counts_and_non_scalar_runner_facts():
    module = load_script("evaluate_ci_execution.py")
    source = ci_observation()
    source["test_results"]["executed"] = 127
    with pytest.raises(ValueError, match="executed must equal"):
        module.evaluate(source)

    source = ci_observation()
    source["runner"]["environment_facts"]["nested"] = {"unexpected": True}
    with pytest.raises(ValueError, match="values must be scalar"):
        module.evaluate(source)

    source = ci_observation()
    source["test_results"]["executed"] = True
    with pytest.raises(ValueError, match="non-negative integers"):
        module.evaluate(source)


def test_ci_execution_contract_and_evaluator_match_repository_template():
    assert (ROOT / "scripts" / "evaluate_ci_execution.py").read_text(encoding="utf-8").rstrip() == (
        ROOT / "repository-template" / "scripts" / "evaluate_ci_execution.py"
    ).read_text(encoding="utf-8").rstrip()
    assert json.loads((ROOT / "schemas" / "ci-execution-receipt-v1.schema.json").read_text(encoding="utf-8")) == json.loads(
        (ROOT / "repository-template" / ".ai-safe2" / "schemas" / "ci-execution-receipt-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )


def test_setup_assistant_matches_template_and_is_goal_based():
    release = (ROOT / "scripts" / "setup_assistant.py").read_text(encoding="utf-8")
    template = (ROOT / "repository-template" / "scripts" / "setup_assistant.py").read_text(
        encoding="utf-8"
    )
    assert release.rstrip() == template.rstrip()
    module = load_script("setup_assistant.py")
    plan = module.render_plan({"planning", "semantic-review", "strategic-review"})
    assert "Required core — always install" in plan
    assert "Superpowers" in plan
    assert "OPENROUTER_API_KEY" in plan
    assert "Greptile" in plan
    assert "does not install a" in plan
    assert "named human" in plan
    mobile_plan = module.render_plan({"deterministic-security"}, "mobile")
    assert "not bundled" in mobile_plan
    assert "planned" in mobile_plan
    assert "Do not substitute the game profile" in mobile_plan


def release_qualification_record():
    required = [
        "local-gate", "hosted-ci", "clean-game-canary", "security-review",
        "placeholder-resolution", "package-integrity"
    ]
    evidence = [{
        "capability": capability,
        "status": "produced",
        "subject_revision": "abc123",
        "producer": f"producer-{capability}",
        "evidence_ref": f"evidence/{capability}.json",
        "limitations": ["Evidence supports only the named candidate revision."]
    } for capability in required]
    return {
        "schema_version": "ai-safe2.release-qualification.v1",
        "candidate": {"version": "0.2.0-rc.1", "revision": "abc123"},
        "required_capabilities": required,
        "evidence": evidence,
        "outcome": "hold",
        "missing_capabilities": required,
        "human_authority": {"release_decision_recorded": False, "release_owner": None, "release_at": None, "rationale": None},
        "limitations": ["Qualification evidence does not publish or authorize the candidate."]
    }


def test_release_qualification_is_revision_bound_and_cannot_authorize():
    module = load_script("evaluate_release_qualification.py")
    record = release_qualification_record()
    result, errors = module.evaluate(record)
    assert errors == []
    assert result["outcome"] == "ready_for_human_release_decision"
    assert result["missing_capabilities"] == []
    assert result["human_authority"]["release_decision_recorded"] is False

    record["evidence"][1]["subject_revision"] = "old-revision"
    stale_result, stale_errors = module.evaluate(record)
    assert stale_errors == []
    assert stale_result["outcome"] == "hold"
    assert stale_result["missing_capabilities"] == ["hosted-ci"]


def test_release_qualification_rejects_missing_refs_and_duplicate_producers():
    module = load_script("evaluate_release_qualification.py")
    record = release_qualification_record()
    record["evidence"][0]["evidence_ref"] = None
    record["evidence"].append(dict(record["evidence"][0]))
    _, errors = module.evaluate(record)
    assert any("lacks evidence_ref" in error for error in errors)
    assert any("duplicate release evidence" in error for error in errors)
    weakened = release_qualification_record()
    weakened["required_capabilities"] = ["local-gate"]
    weakened["evidence"] = weakened["evidence"][:1]
    result, errors = module.evaluate(weakened)
    assert any("omits mandatory" in error for error in errors)
    assert result["outcome"] == "hold"


def test_clean_export_installation_canary(tmp_path):
    import shutil

    installed = tmp_path / "game-canary"
    shutil.copytree(ROOT / "repository-template", installed)
    for path in installed.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("REPLACE-", "canary-"), encoding="utf-8")
    commands = [
        ["scripts/validate_workflow.py", "--root", "."],
        ["scripts/validate_documentation_ownership.py", "--root", ".", "--manifest", ".ai-safe2/documentation-ownership.json", "--schema", ".ai-safe2/schemas/documentation-ownership-v1.schema.json"],
        ["scripts/setup_assistant.py", "--project-type", "game", "--goals", "planning,semantic-review", "--output", "setup-plan.md"],
    ]
    for command in commands:
        subprocess.run([sys.executable, *command], cwd=installed, check=True, capture_output=True, text=True)
    classifier = load_script("classify_change.py")
    profile = json.loads((installed / ".ai-safe2/profiles/game.json").read_text(encoding="utf-8"))
    for path, route in [("docs/guide.md", "standard"), ("src/player.cs", "enhanced"), ("src/payments/store.cs", "critical")]:
        assert classifier.classify([path], profile)["route"] == route
    assert "Superpowers" in (installed / "setup-plan.md").read_text(encoding="utf-8")


def test_release_qualification_contracts_are_exported_without_drift():
    for schema_name in ("product-profile-v1.schema.json", "release-qualification-v1.schema.json"):
        assert json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8")) == json.loads(
            (ROOT / "repository-template" / ".ai-safe2" / "schemas" / schema_name).read_text(encoding="utf-8")
        )
    assert (ROOT / "scripts" / "evaluate_release_qualification.py").read_text(encoding="utf-8").rstrip() == (
        ROOT / "repository-template" / "scripts" / "evaluate_release_qualification.py"
    ).read_text(encoding="utf-8").rstrip()
    release_template = json.loads((ROOT / "release-qualification.template.json").read_text(encoding="utf-8"))
    export_template = json.loads(
        (ROOT / "repository-template" / ".ai-safe2" / "release-qualification.template.json").read_text(encoding="utf-8")
    )
    assert release_template == export_template
    schema = json.loads((ROOT / "schemas" / "release-qualification-v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(release_template)
    module = load_script("evaluate_release_qualification.py")
    result, errors = module.evaluate(release_template)
    assert errors == []
    assert result["outcome"] == "hold"


def test_tool_setup_guide_is_linked_and_preserves_integration_boundaries():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    guide = (ROOT / "docs" / "TOOL-SETUP-GUIDE.md").read_text(encoding="utf-8")
    assert "docs/TOOL-SETUP-GUIDE.md" in readme
    for required in (
        "OPENROUTER_API_KEY",
        "PR-Agent with OpenRouter",
        "Greptile",
        "Superpowers",
        "CodeQL",
        "Semgrep",
        "Gitleaks",
        "manifest is not execution",
        "exact pull-request revision",
    ):
        assert required in guide

