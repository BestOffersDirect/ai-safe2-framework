# v3.5 evidence boundary requirements revision

[Framework home](../README.md) | [Control contracts](CONTROLS-V3.5.md) | [Research](../research/README.md) | [Case specifications](../challenges/003-evidence-boundary/README.md) | [Technology Card](assessments/2026-11-23-evidence-boundary/TECHNOLOGY-CARD.md)

## Scope and decision

Requirements revision **2026-11-23** extends merged v3.5 baseline `78bd1e6c02eb66aa68e73fc16f6c55f2782cc896`. The October security brief was already retained in the local evidence register. This change closes a source-utilization gap: specific contract, evidence-interface, monitoring-selection and learning-promotion duties now have explicit child clauses and acceptance routes.

The framework retains **173 core controls**, 19 MCP profile IDs, twelve MCP child requirements, eleven threat families and AISM v1 scoring. The current revision has **175 core child clauses and 63 research decisions/notes**, up from 157 and 53. Eighteen added clauses belong to five existing controls. Four additional records deepen research/acceptance under existing requirements without creating new clauses. Two previously research-disposition clauses remain research-only.

This is an additive requirements revision within framework v3.5, not a package release or a new runtime implementation. Record framework version and requirements revision together. Earlier results keep their original revision and do not establish coverage of newly applicable clauses. This PR does not rewrite the historical v3.5 release or create a new tag. An incompatible future scoring, public data-contract or control-identity change needs its own version decision.

## Explicit additions and placement

| Decision | Existing owner | Added clauses | Specific question |
| --- | --- | --- | --- |
| C54 | CP.12 Final-Effect Authorization | CP.12.R07-R09 | Does the generated contract faithfully represent trusted task scope? |
| C55 | CP.13 Control Evidence Independence | CP.13.R08-R10 | Do retained, displayed and exported records agree? |
| C56 | M4.4 Adversarial Behavior Detection Pipeline | M4.4.R01-R03 | What does the audit selector omit by consequence class? |
| C57 | E5.4 Red-Team Artifact Repository | E5.4.R01-R03 | Can hostile strategy memory promote itself into production rules? |
| C58 | S1.3 | None | How does delayed influence reach operative action arguments? |
| C59 | CP.13 | None | What do external collectors miss across subprocesses and repeated runs? |
| C60 | CP.12 | None | How is target authority preserved through human-led multi-product operations? |
| C61 | CP.4 | None | Can hostile security telemetry become defensive-agent authority? |
| C62 | F3.6 | F3.6.R07-R09 | How are attribution, ceiling changes and breach recovery protected? |
| C63 | CP.13 | CP.13.R11-R13 | Which requirements revision and clause evidence supports the assessment? |

Each decision has a source-specific note with placement alternatives, advantages, costs, source limits and cases. Existing ownership avoids a new control per paper. A separate control becomes appropriate when ownership, applicability, lifecycle or conformance cannot be represented by its current parent. Requirement counts follow those decisions rather than a preset expansion limit.

Contract fidelity is distinct from enforcement fidelity: a gate may correctly enforce the wrong scope. Evidence custody is distinct from trustworthy presentation: unchanged storage can coexist with a misleading viewer. Monitor coverage is distinct from audit cost: the selector and auditor can miss different actions. Reusable red-team findings are distinct from approved production rules: evidence cannot authorize its own promotion.

## Source and evidence boundaries

The supplied brief is stored in an October 30 folder but internally covers **October 3-9, 2026**. Preserve coverage, file date, publisher date and review date separately. This revision adds eight attributed October source observations to the machine register; they are study/advisory/investigation records, not eight newly counted operational incidents.

Primary sources: [APEX](https://arxiv.org/html/2610.06966v1), [staged boundary auditing](https://arxiv.org/html/2610.05163v1), [AgentSpy](https://arxiv.org/html/2610.06001v1), [ASPIRE](https://arxiv.org/html/2610.08951v1), [selective auditing](https://arxiv.org/html/2610.07256v1), [CrowdStrike ARTEX investigation](https://www.crowdstrike.com/en-us/blog/unknown-threat-actor-uses-artex-to-target-south-korean-finance/), [specific ngCERT advisory](https://cert.gov.ng/index.php/advisories/ghostjacking-an-indirect-prompt-injection-against-ai-agents), and [METR article](https://metr.org/blog/2026-10-06-ai-systems-could-cover-up-misbehavior/).

Reviewed November 23, 2026: five papers, CrowdStrike and ngCERT material were opened. METR's article timed out; [METR's organizational post](https://www.linkedin.com/company/metr-evals/) corroborated its viewer demonstration and limits. No study implementation, raw dataset or independent replication was executed. E2/E3 ratings remain attributed to the brief. Pillar contribution ratings are not organizational maturity scores. CrowdStrike's source left the affected-organization count unconfirmed; ngCERT recognition is not a new independent reproduction. Paper vulnerability-path units are not automatically CVEs. No source establishes universal prevention or regulatory compliance.

## Reconciled inherited descriptions

- A2.5 now requires observable actions, parameters, memory events, available summaries and explicit collector omissions. It does not promise unavailable private reasoning. The same meaning is carried through both catalogs, dashboard and current AISM references.
- M4.4 separates collecting red-team findings from validated, approved and reversible production promotion.
- The AISM T1 table includes final-effect authorization under P3; the legacy categorical input-detectability claim is removed. Staged injection and persistent conditioning retain distinct scopes without pretending input screening is complete.

AISM-P01 now includes viewer/export substitution, omitted subprocess observations and compromised audit selection. AISM-P02 includes contract mistranslation and discovered-target drift. AISM-P03 includes manipulated evidence displays/consent. IDs, parent-family counts and scoring arithmetic remain unchanged.

## Dedicated work packages and existing issue ownership

| Work package | Tracking and acceptance |
| --- | --- |
| Shared evidence rendering/export/verification | [#448](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/448): all consumers, constrained active content, transformation/completeness records, independent verification and V05/V06 |
| Challenge Lab and evaluator coverage | [#449](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/449): ten case families, selector/auditor separation, paired legitimate tasks, held-out cases and governed strategy memory |
| Core Gateway | [#434](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/434): contract fidelity and mandatory gate coverage; links #448/#449 |
| NEXUS | [#436](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/436): contract revision and distributed delegation, target drift and selector outage |
| MCP enforcement | [#437](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/437): hostile tool/telemetry data cannot widen grants; current contract binding |
| Sovereign runtimes | [#438](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/438): one independently observed source-to-effect path, then per-runtime qualification |
| CLI/MCP distribution | [#439](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/439): packaged revision identity and evidence consumer coverage |
| Developer Workflow | [#440](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/440): task-to-contract scope and change/receipt binding; source, display and export disagreements |
| Scanner | [#435](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/435): bounded static indicators with positive/negative/legitimate fixtures; no static runtime-conformance pass |
| Source mappings | [#441](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/441): direct-source relationship validation, not new compliance claims from these studies |
| Human oversight | [#442](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/442): evidence presentation/comprehension and practical intervention without speculative psychological thresholds |
| Existing specific requests | [#234](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/234) keeps observable trace examples; [#308](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/308) keeps its separate original denominator correction |

These issues remain open for implementation and qualification. The framework PR supplies requirements and specifications; it does not close them by documentation alone. Existing #235, #250, #251 and #273 keep their specific authenticated adapter and interoperability scope.

## Validation specification and sequence

[The case manifest](../challenges/003-evidence-boundary/cases.json) defines V01-V10: contract over/under-grant, delayed influence, correct deliverable with prohibited process, hostile viewer, altered export, hostile telemetry/strategy memory, selector evasion/overload, repeated-run variance and target drift. Every case specifies a legitimate paired task, independent observations and UNKNOWN for missing evidence. They are **NOT_EXECUTED** specifications, not a runnable benchmark or efficacy result.

First implement contract fidelity and evidence-chain agreement in one maintained runtime with synthetic sinks. Then exercise cost/coverage selection and governed strategy reuse. Record raw opportunities, effects, false blocks, useful completion, unknowns, cost, latency and recovery. Qualify additional runtimes separately. Freeze any confirmatory protocol before execution; neither Challenge 001 nor prospective Challenge 002 is silently amended.

## Excluded claims and recovery

No mandatory research-product dependency, universal metric threshold, inferred private reasoning, new legal coverage or benchmark-to-maturity conversion is introduced. Trust a stable contract against untrusted input; legitimate material task changes require a newly authorized revision rather than a permanently frozen scope.

On a failed or unknown applicable requirement, narrow authority to its demonstrated boundary, preserve observations and have the named owner correct and retest. Restore a prior framework dataset only together with matching projections and its declared requirements revision; do not erase adverse evidence or relabel old assessments.

## Framework-first completion

[Revision-bound evidence contract](FRAMEWORK-ASSESSMENT-CONTRACT-V2.md) and [source dispositions](FRAMEWORK-SOURCE-UTILIZATION.md) specify the remaining framework obligations. They do not implement a CLI evaluator, Gateway, Scanner or runtime adapter. The machine ledger declares partial original-corpus atomization and missing clause-result links explicitly. Capability insights are preserved in issue comments for separate work.
