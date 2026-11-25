# Developer Workflow Upgrade Baseline and Acceptance

Status: proposed baseline contract for the next Developer Workflow release.

## Purpose

The upgrade must be measured against repository facts rather than reviewer
impressions. The baseline records what is visible at an exact revision and
keeps configuration, execution, review, and human authority separate.

Generate a baseline with:

```bash
python developer-workflow/scripts/measure_repository_baseline.py \
  --repository . \
  --output developer-workflow/evidence/repository-baseline.json
```

Validate the result against
`schemas/repository-baseline-v1.schema.json`. The generated report is evidence
about repository contents. It does not prove that CI ran, branch protection is
enabled, a reviewer is independent, or a control is effective.

The subject records the base revision and whether the measured working tree
contained uncommitted changes. A dirty report must not be presented as evidence
for the base commit alone.

## Verified starting observations

The current repository contains `CODEOWNERS`, declares mypy dependencies, and
includes NEXUS mypy configuration. A root pre-commit configuration was not
observed during this review. The repository contains an authored NEXUS
Challenge Lab, but automated mutation, property-based, and parser-fuzzing
results were not established for the Developer Workflow.

These observations must be regenerated at the implementation revision before
they are cited in a pull request or release decision.

## Upgrade acceptance contract

| Area | Required result | Evidence |
| --- | --- | --- |
| Repository discovery | Produces a schema-valid project map without modifying the target repository | Exact-revision output and negative tests |
| Local validation | Offers a bounded local gate that matches documented CI capabilities | Command output plus hosted CI comparison |
| Type checking | Names the paths and strictness policy; does not claim repository-wide coverage from dependency presence | Configuration, command, and exact result |
| Agent execution | Records task owner, scope, allowed tools, stop conditions, handoff, and revision | Execution plan and task receipts |
| Review independence | Records producer, provider, model family where available, human identity where applicable, and known dependence | Evidence envelope and review policy |
| Adversarial assurance | Reports property, mutation, or fuzz results without hiding survivors, failures, or unavailable tools | Tool-native result and evidence envelope |
| Documentation ownership | Identifies canonical sources and marks generated surfaces | Source mapping, freshness check, and generated-file notice |
| Human authority | Stops at `hold` or `ready_for_human_decision` until a named human records a decision | Decision record bound to the exact revision |

## Measures to compare before and after

- local failures caught before the first hosted CI run;
- hosted CI reruns required for a representative change;
- required capabilities with produced, failed, unavailable, or stale evidence;
- mutation survivors and property or fuzz failures on selected critical logic;
- manually repeated version, status, and capability claims;
- critical changes with an attributable human reviewer or an explicit review gap;
- decision records that can be replayed against the recorded revision.

No target may be presented as an improvement until the same method has been
used on both sides of the comparison. Provider scores and line coverage alone
do not establish defect detection or independence.

## Exclusions from this baseline

- A universal pull-request line limit. Review budgets will depend on risk,
  generated content, tests, and whether the decision record remains coherent.
- A target to delete a percentage of documentation. Duplication should be
  removed only after a canonical owner and navigation impact are established.
- A claim that multiple AI reviewers provide independent assurance. Their
  providers, models, prompts, context, and evidence sources may overlap.
- A claim that `CODEOWNERS` proves required human review. Hosted repository
  settings and an observed review are separate evidence.

## PR sequence

1. Baseline and acceptance contract.
2. Execution contracts and repository discovery.
3. Local validation and type boundaries.
4. Bounded agent execution and skill admission.
5. Evidence bridge and review-independence records.
6. Adversarial software assurance.
7. Documentation ownership and generation.
8. Setup experience, specialized profiles, and release qualification.
