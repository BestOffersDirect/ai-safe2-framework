# Source disposition and framework coverage

[Framework home](../README.md) | [Machine ledger](data/framework-source-dispositions-v35.json) | [Requirements](CONTROLS-V3.5.md) | [Evidence record contract](FRAMEWORK-ASSESSMENT-CONTRACT-V2.md)

## What the ledger establishes

The ledger enumerates all 63 reviewed decisions and their clauses, rationale and research links. It preserves source statements and available observation/URL references, capability issue ownership where established, and explicit unresolved source locations and result links. It is a decision-to-requirement ledger, not an assertion that every statement in the original raw corpus has been atomized or reviewed.

**Original corpus coverage: PARTIAL.** Exact claim-location atomization and independent result linkage remain pending. A broad evidence-wave citation is not an exact source span. A source document link is not claim verification. NOT_LINKED_IN_THIS_LEDGER does not mean no tests exist anywhere; it means this ledger does not yet establish clause-level result coverage. Structural checks must not turn those fields into a conformance score.

The next source review must retain stable source hash/edition/date/location, individual claim, contradictions/supersession, why/why-not and accepted/absorbed/deferred/rejected disposition. Then link the owning clause/research, real implementation, test and result, issue and supported release claim. Fail unresolved references, but do not force every source statement into a new control. Preserve source-specific nuances and explicit reasons for exclusions.

## Original F3.6 source dispositions

| Original source requirement | Current disposition | Reason or nuance |
| --- | --- | --- |
| F3.6.1 unit-of-work ceiling | Retained in F3.6.R01/R02 and deepened in R08 | Task/delegation scope and units must be real; a calendar spend alert is not equivalent. |
| F3.6.2 independent enforcement | CP.12, CP.10 and F3.6.R08 | The agent cannot raise its own ceiling. Reject the literal claim that the agent cannot reason about its limit; secrecy is not a general security property. |
| F3.6.3 breach fails closed | Explicit F3.6.R09 | Halt/revoke affected consumption and observe cessation, rather than only warn. |
| F3.6.4 verified attribution and unattributed accounting | Explicit F3.6.R07 | Unattributed consumption counts; unknown exposure is conservatively reserved or held, not treated as zero. |
| F3.6.5 reconstructable evidence | CP.13 and F3.6.R09 | Independent custody, provenance and actual effect observation remain separate from agent reporting. |
| F3.6.6 governed ceiling increase | Explicit F3.6.R08 | Outside authority, recorded exact scope, and Class-H handling for ACT-3/4 mid-task increases. |
| F3.6.7 recoverable interrupted work | F3.6.R03/R09, A2.7 and A2.8 | Preserve state, idempotency, unknown external effects and verified recovery. |

These are framework dispositions; [#434](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/434) and [#436](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/436) own actual enforcement and accounting qualification.

## Remaining standards and partner-source context

The original standards package's thirteen-entry gap register still needs individual disposition and owner-only author/IPR/submission decisions. It is an explicit unresolved ledger item, not declared complete by this PR. [#245](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/245) carries the context for separate standards/capability work. This PR neither submits standards material nor makes an IPR determination.

Supplied partner specifications and the locally available frozen evidence carrier remain source artifacts. The carrier's raw hashes matched while two declared byte sizes differed; its static snapshots do not demonstrate a live gate or validate a human-state threshold. [#251](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/251), [#273](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/273) and [#449](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/449) retain that context for separate artifact, interoperability and validation work.

## Framework-first sequencing

PR #450 supplies requirements, research, schemas, source dispositions and structural safeguards. Capability insights were posted as comments on the eighteen open issues. No issue is closed by adding this ledger, no deployment is qualified and no capability is implemented by the framework contract. Work each capability separately against its recorded acceptance and constraints.
