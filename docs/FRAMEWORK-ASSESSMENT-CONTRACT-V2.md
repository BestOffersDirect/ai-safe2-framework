# Revision-bound framework evidence contract

[Framework home](../README.md) | [Schema](../safe2/data/requirement-assessment-v2.schema.json) | [Unexecuted example](examples/requirement-assessment-v2.json) | [Source dispositions](FRAMEWORK-SOURCE-UTILIZATION.md)

## Purpose and boundary

The framework defines `safe2.requirement-assessment.v2` to record the exact framework version, requirements revision, deployment/system revision, scope, applicability and clause evidence behind an assessment. It is a structural evidence-record contract. It grants no authority and supplies no new runtime or CLI evaluator.

The existing `safe2 framework readiness` command continues using its v1 declared-control evidence contract. It does not implement this v2 contract or clause-level verification. [Issue #439](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/439) owns future CLI/MCP/evaluator integration and migration; [#440](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/440) owns workflow binding. Framework records, schemas, implementations and executed results retain distinct identities.

## Required identity and evidence

Record system ID and revision, assessed scope/time and accountable assessment owner. Include the producing requirements revision and required clause IDs. Each clause records applicability and its basis; pass, fail, unknown, untested or not-applicable result; evidence references; collector scope; observation time; and evidence origin. An unsupported independence claim is distinct from verified external observation.

A pass entry requires evidence references. Not-applicable needs a reason and matching status. Unknown applicability cannot become a pass. The example is explicitly untested with no collector; schema validation does not run an agent or validate the described evidence.

## Semantic evaluation required of future consumers

Consumers must resolve the declared catalog/revision, reject unknown or conflicting clause identities, detect duplicate or missing required clauses and review applicability against the actual deployment. Verify freshness, provenance, source authenticity, collector coverage, claimed independence and result evidence. Merely declaring verified-external-observation does not establish it. The schema checks record shape; it cannot authenticate an owner, observe a destination or determine whether all applicable requirements were selected.

Missing, failed, conflicting, unknown and untested observations must remain distinct. A governance decision may deliberately narrow scope, but a consumer cannot infer a complete pass from a subset of favorable clauses. Link partial, inherited and excluded evidence with its reason. Closure and release claims require actual scoped results and owner decisions.

## Compatibility and migration

Keep v1 input/result identities and historical observations intact. v2 is a new framework contract, not a silent v1 semantics change. No v1 record is upgraded by changing its version label; reassess materially changed or newly applicable clauses. Do not mix requirement revisions without an explicit migration/applicability record. AISM scoring, existing CLI grades and framework control IDs are unchanged.
