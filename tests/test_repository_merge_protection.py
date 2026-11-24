"""Exercise live-rule comparison and incomplete skill checks as negative cases."""
import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]


def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/"scripts"/(name+".py"))
    loaded=importlib.util.module_from_spec(spec);spec.loader.exec_module(loaded);return loaded


def policy():return json.loads((ROOT/".github/required-checks.json").read_text(encoding="utf-8"))


def live_rules():
    p=policy()
    return {"target":"branch","enforcement":"active","bypass_actors":[],"conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"],"exclude":[]}},"rules":[{"type":"deletion"},{"type":"non_fast_forward"},{"type":"pull_request","parameters":{"required_review_thread_resolution":True,"dismiss_stale_reviews_on_push":True}},{"type":"required_status_checks","parameters":{"required_status_checks":deepcopy(p["required_status_checks"]),"strict_required_status_checks_policy":True,"do_not_enforce_on_create":False}}]}


def test_current_policy_and_live_shape():
    guard=module("check_merge_protection")
    assert guard.policy_errors(policy())==[]
    assert guard.compare_ruleset(policy(),live_rules())==[]
    names={c["context"] for c in policy()["required_status_checks"]}
    assert {"Repository UX Consistency","Agent Discovery and Manifest Integrity","v3.5 contracts and generated freshness","CodeQL","Merge Protection Integrity"}<=names


@pytest.mark.parametrize("mutation",["missing-check","wrong-emitter","bypass","stale","threads","inactive"])
def test_weakened_live_protection_is_rejected(mutation):
    actual=live_rules()
    if mutation=="missing-check":actual["rules"][-1]["parameters"]["required_status_checks"].pop()
    elif mutation=="wrong-emitter":actual["rules"][-1]["parameters"]["required_status_checks"][0]["integration_id"]=1
    elif mutation=="bypass":actual["bypass_actors"]=[{"actor_id":1}]
    elif mutation=="stale":actual["rules"][-1]["parameters"]["strict_required_status_checks_policy"]=False
    elif mutation=="threads":actual["rules"][-2]["parameters"]["required_review_thread_resolution"]=False
    elif mutation=="inactive":actual["enforcement"]="disabled"
    assert module("check_merge_protection").compare_ruleset(policy(),actual)


@pytest.mark.parametrize("discovery,applicability,scan",[("failure","false","skipped"),("cancelled","true","success"),("success","true","cancelled"),("success","true","skipped"),("success","true","failure"),("success","","skipped")])
def test_incomplete_skill_execution_cannot_report_pass(discovery,applicability,scan):
    with pytest.raises(ValueError):module("check_skill_gate_results").decision(discovery,applicability,scan)


def test_no_skill_change_is_explicitly_not_applicable():
    assert module("check_skill_gate_results").decision("success","false","skipped").startswith("not-applicable")
    assert module("check_skill_gate_results").decision("success","true","success").startswith("pass")


def test_helper_changes_trigger_bundle_scan_and_empty_diff_is_safe(tmp_path):
    bundle=tmp_path/"skills"/"sample";bundle.mkdir(parents=True)
    (bundle/"SKILL.md").write_text("source data",encoding="utf-8")
    (tmp_path/"skill.md").write_text("compatibility redirect",encoding="utf-8")
    discover=module("discover_changed_skills")
    assert discover.roots_for_changes(tmp_path,["skills/sample/scripts/helper.py"])==["skills/sample"]
    assert discover.roots_for_changes(tmp_path,[])==[]
    assert discover.roots_for_changes(tmp_path,["docs/README.md"])==[]
    with pytest.raises(ValueError):discover.roots_for_changes(tmp_path,["../outside/SKILL.md"])


def test_required_workflows_cannot_disappear_on_documentation_only_prs():
    for name in ["cli-release-qualification.yml","skill-trust-gate.yml","v31-consistency.yml"]:
        source=(ROOT/".github/workflows"/name).read_text(encoding="utf-8")
        event=source.split("  pull_request:",1)[1].split("  push:",1)[0]
        assert "paths:" not in event and "paths-ignore:" not in event
    source=(ROOT/".github/workflows/skill-trust-gate.yml").read_text(encoding="utf-8")
    summary=source.split("  trust-gate-summary:",1)[1]
    assert "if: always()" in summary
    assert "check_skill_gate_results.py" in summary
