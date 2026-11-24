"""Guard evidence-boundary requirements without claiming runtime qualification."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))


def test_followthrough_keeps_control_identity_and_required_obligations():
    source=load("safe2/data/framework-requirements-v3.5.json")
    assert source["requirements_revision"]=="2026-11-23"
    additions=[d for d in source["decisions"] if 54<=int(d["review_id"][1:])<=61]
    assert len(additions)==8
    assert sum(len(d["clauses"]) for d in additions)==12
    assert {d["control_id"] for d in additions if d["clauses"]}=={"CP.12","CP.13","M4.4","E5.4"}
    for d in additions:
        assert d["research_question"] and d["alternatives"] and d["advantages"] and d["costs"]
        assert (ROOT/d["research_path"]).is_file()


def test_case_specs_preserve_unexecuted_status_and_independent_observations():
    cases=load("challenges/003-evidence-boundary/cases.json")
    assert cases["kind"]=="validation-specification"
    assert cases["confirmatory_results"]=="NOT_EXECUTED"
    assert len(cases["cases"])==10
    ids=set()
    for case in cases["cases"]:
        assert case["id"] not in ids
        ids.add(case["id"])
        assert case["legitimate_pair"] and case["independent_observations"]
        assert case["forbidden_effect"] and case["missing_evidence_result"]=="UNKNOWN"
        assert case["execution_status"]=="NOT_EXECUTED"


def test_inherited_descriptions_agree_with_observable_and_promotion_boundaries():
    catalog=load("safe2/data/ai-safe2-controls-v3.5.json")
    controls={c["id"]:c for c in catalog["pillar_controls"]+catalog["cross_pillar_controls"]}
    assert "private reasoning" in controls["A2.5"]["description"]
    assert "approved" in controls["M4.4"]["description"]
    matrix=(ROOT/"AISM/agent-threat-control-matrix.md").read_text(encoding="utf-8")
    assert "T1: Prompt Injection | Primary | Supporting | Primary" in matrix


def test_lookup_returns_revision_and_supporting_notes_do_not_invent_clauses():
    from safe2.framework import query
    result=query(control_id="CP.12")
    assert result["requirements_revision"]=="2026-11-23"
    source=load("safe2/data/framework-requirements-v3.5.json")
    for record in source["decisions"]:
        if record["status"]=="supporting-analysis":
            assert record["clauses"]==[]
            note=(ROOT/record["research_path"]).read_text(encoding="utf-8")
            assert "adds no mandatory child clauses" in note
