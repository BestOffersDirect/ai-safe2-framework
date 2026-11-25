#!/usr/bin/env python3
"""Attach validated evidence envelopes to a human decision record."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def canonical_digest(envelope: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in envelope.items() if key != "integrity"}
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def validate_envelope(envelope: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = [f"schema: {error.message}" for error in validator.iter_errors(envelope)]
    if not errors and envelope["integrity"]["content_digest"] != canonical_digest(envelope):
        errors.append("integrity: content_digest does not match canonical envelope content")
    return sorted(errors)


def attach(record: dict[str, Any], envelopes: list[dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    if record["outcome"] not in {"hold", "ready_for_human_decision"}:
        return record, ["refusing to alter a recorded human decision"]
    errors: list[str] = []
    expected_identifier = record["subject"]["identifier"]
    expected_revision = record["subject"]["revision"]
    attached: dict[tuple[str, str], dict[str, str]] = {
        (item["evidence_id"], item["capability"]): item for item in record["evidence"]
    }
    producer_versions = dict(record["replay"]["producer_versions"])
    incoming_evidence: dict[str, str] = {}
    incoming_producers: dict[str, str] = {}
    for envelope in envelopes:
        subject = envelope["subject"]
        evidence_id = envelope["evidence_id"]
        evidence_digest = envelope["integrity"]["content_digest"]
        if evidence_id in incoming_evidence and incoming_evidence[evidence_id] != evidence_digest:
            errors.append(f"{evidence_id}: duplicate evidence_id has conflicting content")
        incoming_evidence[evidence_id] = evidence_digest
        if subject["identifier"] != expected_identifier:
            errors.append(f"{evidence_id}: subject identifier does not match decision record")
        if subject["revision"] != expected_revision:
            errors.append(f"{evidence_id}: subject revision does not match decision record")
        if envelope["execution"]["policy_digest"] != record["replay"]["policy_digest"]:
            errors.append(f"{evidence_id}: policy digest does not match decision record")
        producer = envelope["producer"]
        producer_name = producer["adapter_id"]
        if producer_name in incoming_producers and incoming_producers[producer_name] != producer["version"]:
            errors.append(f"{producer_name}: conflicting producer versions in attached evidence")
        incoming_producers[producer_name] = producer["version"]
        producer_versions[producer_name] = producer["version"]
        for capability in producer["capabilities"]:
            key = (evidence_id, capability)
            candidate = {
                "evidence_id": evidence_id,
                "capability": capability,
                "status": envelope["execution"]["status"],
                "subject_revision": subject["revision"],
                "producer": producer_name,
            }
            if key in attached and attached[key] != candidate:
                errors.append(f"{evidence_id}: conflicting evidence entry for capability {capability}")
            else:
                attached[key] = candidate
    result = dict(record)
    result["evidence"] = [attached[key] for key in sorted(attached)]
    result["replay"] = dict(record["replay"])
    result["replay"]["producer_versions"] = producer_versions
    return result, sorted(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--envelope", type=Path, action="append", required=True)
    parser.add_argument("--evidence-schema", type=Path, required=True)
    parser.add_argument("--decision-schema", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record = load(args.record)
    evidence_schema = load(args.evidence_schema)
    decision_schema = load(args.decision_schema)
    envelopes: list[dict[str, Any]] = []
    errors: list[str] = []
    for path in args.envelope:
        envelope = load(path)
        errors.extend(f"{path}: {error}" for error in validate_envelope(envelope, evidence_schema))
        envelopes.append(envelope)
    validator = Draft202012Validator(decision_schema, format_checker=FormatChecker())
    errors.extend(f"decision record schema: {error.message}" for error in validator.iter_errors(record))
    if not errors:
        record, errors = attach(record, envelopes)
    if errors:
        for error in sorted(errors):
            print(f"ERROR: {error}")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"attached_envelopes": len(envelopes), "outcome": record["outcome"], "human_decision_recorded": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
