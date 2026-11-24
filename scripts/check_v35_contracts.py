"""Validate v3.5 catalog identity, requirement ownership and generated parity."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from safe2.framework import audit_registry
from jsonschema import Draft202012Validator, FormatChecker


def main() -> int:
    def load(name):
        return json.loads((ROOT/name).read_text(encoding='utf-8'))
    errors=[]
    manifest=load('ai-safe2.manifest.json')
    current=load(manifest['machine_readable']['core_controls'])
    packaged=load('safe2/data/ai-safe2-controls-v3.5.json')
    if current!=packaged:errors.append('core_catalog_distribution_mismatch')
    controls=current['pillar_controls']+current['cross_pillar_controls']
    ids={c['id'] for c in controls}
    if len(controls)!=173 or len(ids)!=173:errors.append('core_control_identity_mismatch')
    if current['metadata']['total_controls']!=len(ids):errors.append('core_count_metadata_mismatch')
    requirements=load('safe2/data/framework-requirements-v3.5.json')
    decisions=requirements['decisions']
    revision=requirements['requirements_revision']
    if current['metadata'].get('requirements_revision')!=revision or manifest['framework'].get('requirements_revision')!=revision:
        errors.append('requirements_revision_distribution_mismatch')
    clauses=[cl for d in decisions for cl in d['clauses']]
    if len(decisions)!=63 or len(clauses)!=175 or len({c['id'] for c in clauses})!=175:
        errors.append('decision_or_clause_identity_mismatch')
    for d in decisions:
        if d['control_id'] not in ids or not (ROOT/d['research_path']).is_file():
            errors.append('unresolved_requirement_owner_or_research')
    ledger=load('docs/data/framework-source-dispositions-v35.json')
    records=ledger['records']
    if len(records)!=len(decisions) or {r['decision_id'] for r in records}!={d['review_id'] for d in decisions}:
        errors.append('source_disposition_decision_coverage_mismatch')
    decision_by_id={d['review_id']:d for d in decisions}
    for record in records:
        owner=decision_by_id.get(record['decision_id'],{})
        if record['clause_ids']!=[c['id'] for c in owner.get('clauses',[])] or record['research_path']!=owner.get('research_path'):
            errors.append('source_disposition_owner_mismatch')
    if ledger['original_corpus_coverage']!='PARTIAL' or any(r['result_status']!='NOT_LINKED_IN_THIS_LEDGER' for r in records):
        errors.append('unverified_corpus_or_result_coverage_promoted')
    shape=load('safe2/data/requirement-assessment-v2.schema.json')
    example=load('docs/examples/requirement-assessment-v2.json')
    if list(Draft202012Validator(shape,format_checker=FormatChecker()).iter_errors(example)):
        errors.append('framework_assessment_example_invalid')
    clause_ids={c['id'] for c in clauses}
    if example['requirements_revision']!=revision or not set(example['required_clause_ids'])<=clause_ids:
        errors.append('framework_assessment_example_revision_or_clause_mismatch')
    flattened=[cl for c in controls for cl in c['requirements']]
    if sorted(flattened,key=lambda c:c['id'])!=sorted(clauses,key=lambda c:c['id']):
        errors.append('core_child_requirement_parity_mismatch')
    profile=load('skills/mcp/data/mcp-profile-v3.5.json')
    for name in ['safe2/data/mcp-profile-v3.5.json','dashboard/public/data/mcp-profile-v3.5.json']:
        if load(name)!=profile:errors.append('mcp_distribution_mismatch')
    if len(profile['controls'])!=19 or len({cl['id'] for c in profile['controls'] for cl in c['requirements']})!=12:
        errors.append('mcp_identity_mismatch')
    dashboard=load('dashboard/public/data/controls.json')
    if {c['id'] for c in dashboard}!=ids:errors.append('dashboard_core_identity_mismatch')
    embedded=re.search(r'const CONTROLS_DATA = ', (ROOT/'dashboard/index.html').read_text(encoding='utf-8'))
    embedded_controls=json.JSONDecoder().raw_decode((ROOT/'dashboard/index.html').read_text(encoding='utf-8')[embedded.end():])[0] if embedded else []
    expected={c['id']:c for c in controls}
    if {c['id'] for c in embedded_controls}!=ids:errors.append('dashboard_embedded_identity_mismatch')
    for c in embedded_controls:
        if c.get('act')!=expected[c['id']]['act_minimum']:errors.append('dashboard_tier_metadata_mismatch')
    for projected in [dashboard,embedded_controls]:
        for c in projected:
            owner=expected.get(c['id'],{})
            if any(c.get(k)!=owner.get(k) for k in ('name','description','requirements','implementation_status')):
                errors.append('dashboard_embedded_requirement_mismatch')
    audit=audit_registry(load('safe2/data/rosetta-v3.5.json'))
    if audit['errors'] or any(c['status']=='fail' for c in audit['checks'].values()):
        errors.append('rosetta_structural_integrity_failed')
    # Reviewed external coverage remains unavailable until source validation is performed.
    if audit['approved_relationships']!=0 or audit['verified_external_coverage'] is not None:
        errors.append('unverified_recovery_mapping_promoted')
    for error in errors:print(error)
    if not errors:print('v3.5 controls, requirements, profiles, research and mapping integrity passed')
    return bool(errors)


if __name__=='__main__':
    raise SystemExit(main())
