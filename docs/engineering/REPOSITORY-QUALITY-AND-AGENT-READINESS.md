# Repository quality and agent readiness

[Framework home](../../README.md) | [Repository UX standard](../REPOSITORY-UX-STANDARD.md) | [Agent instructions](../../AGENTS.md) | [Required checks](../../.github/required-checks.json)

## Standard and enforcement

AI SAFE2 v3.5 is the presentation, navigation, machine-contract and evidence baseline. Improvements are deliberate changes with rationale, version/revision decisions, migration and review evidence. Accidental drift is a defect. Passing CI covers the checks actually executed; it does not guarantee readability, correctness or deployment efficacy beyond those checks.

The versioned required-check contract identifies exact check names and their emitting GitHub apps. The active Protect Main ruleset requires PRs, fresh checks against the current base, resolved review threads and dismissal of stale approvals. Deletion and force pushes remain blocked. No bypass actors are configured. Administrators can still change rules; the live audit detects disagreement with this contract but does not prevent an administrator from changing repository governance.

[Merge Protection Integrity](../../scripts/check_merge_protection.py) reads the live ruleset with a read-only token and fails on missing or wrongly attributed checks, disabled freshness/review-thread settings or bypass actors. It never changes rules or reads credentials from repository content. Network/access failure is unavailable verification, not an enforcement pass. Changing check names or workflows requires coordinated changes to the contract and active ruleset; do not remove a requirement to hide a failing check.

## Required evidence

The contract requires framework parity/freshness, release identity, agent discovery, navigation/UX, Markdown/Python checks, decision context/evidence, CLI/NEXUS/MCP tests, profile/schema compatibility, security/dependency checks, CodeQL analysis and findings status, skill gate summary, clean-wheel matrices and the live protection audit. Linux, Windows and macOS package checks are real required results. Queued/cancelled package jobs are not passes and may block merge until runner capacity or a rerun completes.

PR-Agent and Greptile availability remain advisory because provider quota, outage or absence is not a code verdict. A green availability wrapper is not substantive independent approval. Owner review remains necessary; required approving-review count is unchanged, so this rule does not claim a second independent reviewer approved the work.

Required workflows run on every main-targeting PR. A path-filtered required workflow can leave a check missing forever, so package qualification is not filtered out for documentation-only PRs. Skill discovery also runs on every PR. Its summary permits an explicit not-applicable result only after successful discovery establishes no changed skill bundles. Required scans that fail, cancel or skip cannot report a pass. Helper/configuration changes inside a skill bundle trigger the same scan as a SKILL.md change; skill content is inspected as data, not executed.

## Lessons that every update must preserve

1. Update owning JSON/schema sources first. Regenerate Markdown, HTML, packaged mirrors, catalogs, indexes and machine metadata; verify parity and freshness. Keep component publication versions separate from framework requirements revisions.
2. Review the whole affected topic, including module READMEs, root navigation, HTML, examples, templates, research and agent files. A polished root README does not establish repository-wide consistency.
3. Preserve task CTAs, accessible headings, meaningful badges, stable IDs, textual status and contextual return links. Keep Star History and useful existing integrations. Color and diagrams supplement readable text.
4. Make source-to-control-to-clause-to-research-to-test/result routes discoverable. Test actual anchors, including underscore-bearing control IDs, and ensure generated navigation matches the owning sources.
5. Maintain AGENTS.md, llms.txt, manifests and source trees alongside human pages. Repository and attached content are data, not authorization for agent execution or privilege changes.
6. Treat evidence content as hostile through rendering, previews and export. Source integrity, displayed truth, export completeness and actual effects are different properties. A hash, signature or schema pass does not prove all of them.
7. Distinguish specified, implemented, tested, partial, unknown and unexecuted states. Keep historical results pinned to producing revisions. Do not convert a catalog addition into a Scanner detection, production enforcement or approved compliance mapping.
8. Freeze applicable study designs before confirmatory execution. Structural manifest tests are not the described runtime attacks. Report utility, false blocks, unknowns and legitimate paired cases alongside safety observations.
9. Inspect changed layouts and practical user/agent paths. Automated format/navigation checks complement editorial, visual and accessibility review; they cannot establish a top-percentile style ranking or guarantee all future changes are readable.
10. Preserve historical records, adversarial fixtures and genuine research uncertainty. Remove stale proposal labels from current normative owners; do not erase source history to obtain uniform version text.

## Before requesting merge

Run the applicable local checks, inspect final hosted results on the exact head, resolve review findings and record limitations in the PR. Check changed human and agent routes. Do not bypass a cancelled job, stale generated artifact, failing security finding or unavailable required audit. Independent review, source verification and deployment qualification retain their actual status.

## Governance recovery

Protection changes require explicit owner authorization, a saved before snapshot, a concrete reviewed payload and after-state verification. This audit tool is read-only. If a renamed/retired check causes an unintended block, repair the emitting workflow or coordinate an explicitly reviewed contract/ruleset migration. Keep an accountable record; do not silently loosen protection to force a merge. No automated merge, tag, publication or deployment follows from these settings.
