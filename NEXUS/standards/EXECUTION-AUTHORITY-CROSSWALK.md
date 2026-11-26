# Execution-Time Authority Crosswalk

[Standards home](README.md) | [Machine-readable crosswalk](execution-authority-crosswalk.json) | [Internet-Draft XML](ietf/draft-sullivan-wimse-execution-authority-00.xml)

**Assessment target:** NEXUS source version 0.6.0

**Assessment date:** 25 November 2026

**Evidence level:** Repository self-assessment. No independent evaluation or production deployment evidence.

## Status summary

| Status | Count | Meaning |
| --- | ---: | --- |
| Implemented | 11 | The stated property exists in the reference implementation and has refusal-path tests |
| Partial | 8 | Some property or test exists, but the full requirement or deployment boundary is not met |
| Gap | 1 | The requirement is not implemented as stated |

## Requirement mapping

| ID | Requirement | NEXUS status | Evidence or remaining gap |
| --- | --- | --- | --- |
| ETA-1 | Bind action, grant, policy revision, posture reference, and epoch at decision time | Implemented | Canonical transaction, policy authority, runtime receipt, and coordinator state are bound before release |
| ETA-2 | Fix the binding no later than the decision | Implemented | Coordinator and Key Guardian reject substitutions after policy evaluation |
| ETA-3 | Keep decision and credential authority outside model reach | Partial | `NullCredentialBroker` refuses by default and Key Guardian exposes no raw-key return; production isolation is a deployment obligation |
| ETA-4 | Apply a declared posture-freshness bound at use | Implemented | Independent runtime verifier rejects missing, stale, future, or mismatched evidence |
| ETA-5 | Record unavailable or stale posture as not established | Implemented | `EvaluationState` preserves established, not-established, denied, and indeterminate states in runtime, policy, OPA, and receipt evidence; only established decisions carry execution authority |
| ETA-6 | Tighten freshness as reversibility decreases | Implemented | `FinalityFreshnessPolicy` enforces positive monotonic ceilings for reversible, mediated, and irreversible settlement; the Runtime Verifier applies and records the effective ceiling |
| ETA-7 | Prevent delegated authority from widening | Implemented | Authority graph checks attenuation across scope, duration, counterparties, depth, and consumable quantity |
| ETA-8 | Charge consumption to every ancestor | Implemented | Subtree exposure and transactional reservations enforce ancestor ceilings |
| ETA-9 | Share or pre-partition limits across decision points | Implemented | `BudgetPartitionIssuer` atomically pre-partitions a pinned parent ceiling into signed, holder-bound budgets; independent ledgers enforce each exclusive partition and fail closed on conflict, expiry, tampering, replay, or unavailability |
| ETA-10 | Revoke a delegation subtree without enumeration | Partial | Chain and grant revocation exist, while the durable gateway epoch remains principal-scoped rather than per-grant |
| ETA-11 | Recheck revocation at execution | Implemented | Credential release re-reads the current epoch and refuses stale authorization |
| ETA-12 | Declare and enforce revocation propagation time | Partial | Freshness and fail-closed behavior exist, but the implementation does not prove a deployment-wide propagation objective |
| ETA-13 | Bind irreversible action authority to an independent accountable authority | Partial | AIM ownership and kill paths exist; immutable registration and independent stop operation require deployment proof |
| ETA-14 | Use registered capability tier and default missing tier to most restrictive | Implemented | AIM registry governs the tier; missing tier is treated as ACT-4 |
| ETA-15 | Bind confirmation to the action over an agent-independent channel | Partial | Human-intent receipts bind the transaction; channel independence is an external verifier and deployment obligation |
| ETA-16 | Preserve permit, deny, escalate, and unresolved outcomes | Implemented | Payment decisions and reconciliation distinguish refusal, escalation, and ambiguous settlement without blind retry |
| ETA-17 | Sign every decision and state how each input was established | Partial | Hash-chained receipts and signed authority records exist, but denials and per-input evaluation provenance are not uniformly signed |
| ETA-18 | Permit verification without the agent or original session | Partial | Digest-bound evidence supports later verification, but external trust roots, retained keys, and complete independent reconstruction need deployment proof |
| ETA-19 | Support SCITT Signed Statements | Gap | NEXUS does not emit RFC 9943 Signed Statements |
| ETA-20 | Prevent assurance downgrade across boundaries | Partial | Payment bindings enforce assurance floors and refuse unsupported paths; general cross-protocol enforcement is incomplete |

## Submission claim boundary

The standards contribution is the requirement set. NEXUS supplies running code, refusal-path tests, and documented failures. It does not establish that every ETA requirement is solved, that a deployment is safe, or that another implementation must use NEXUS.

The remaining gap is SCITT-compatible Signed Statements under ETA-19.

