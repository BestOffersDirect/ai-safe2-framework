"""Framework evidence records are structural contracts, never authority."""
import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

ROOT=Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT/name).read_text(encoding="utf-8"))


def validator():
    return Draft202012Validator(load("safe2/data/requirement-assessment-v2.schema.json"),format_checker=FormatChecker())


def example():
    return load("docs/examples/requirement-assessment-v2.json")


def test_example_is_structural_evidence_without_execution_authority():
    record=example()
    validator().validate(record)
    assert record["authorization_granted"] is False
    assert record["clauses"][0]["result"]=="untested"


@pytest.mark.parametrize("field",["requirements_revision","system_revision","required_clause_ids","clauses"])
def test_missing_assessment_identity_is_rejected(field):
    record=example();record.pop(field)
    assert list(validator().iter_errors(record))


def test_pass_without_evidence_and_not_applicable_without_reason_are_rejected():
    record=example();record["clauses"][0]["result"]="pass"
    assert list(validator().iter_errors(record))
    record=example();record["clauses"][0].update(applicability="not_applicable",result="not_applicable",applicability_basis="")
    assert list(validator().iter_errors(record))
    record=example();record["authorization_granted"]=True
    assert list(validator().iter_errors(record))


def test_ledger_preserves_explicit_unresolved_original_corpus_coverage():
    source=load("safe2/data/framework-requirements-v3.5.json")
    ledger=load("docs/data/framework-source-dispositions-v35.json")
    assert ledger["original_corpus_coverage"]=="PARTIAL"
    assert {r["decision_id"] for r in ledger["records"]}=={r["review_id"] for r in source["decisions"]}
    for row in ledger["records"]:
        assert row["result_status"]=="NOT_LINKED_IN_THIS_LEDGER"
        assert row["source_claim_location_status"] in {"SOURCE_DOCUMENT_LINKED_CLAIM_LOCATION_PENDING","SOURCE_ATOMIZATION_PENDING"}


def test_current_titles_and_allocation_are_checked_without_erasing_research():
    import importlib.util
    path=ROOT/"scripts/check_release_identity_v35.py"
    spec=importlib.util.spec_from_file_location("release_identity",path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    current=load("safe2/data/framework-requirements-v3.5.json")["decisions"]
    assert module.decision_label_errors(current)==[]
    changed=deepcopy(current)
    changed[0]["title"]+=" candidate"
    assert module.decision_label_errors(changed)
    changed=deepcopy(current)
    changed[0]["validation"]="Allocate F3.6 only after catalog overlap review."
    assert module.decision_label_errors(changed)
    changed=deepcopy(current)
    changed[0].update(status="research",title="Candidate cognitive measurements")
    assert module.decision_label_errors(changed)==[]
