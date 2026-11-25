# NEXUS Standards Submission Plan

[Standards home](README.md) | [Crosswalk](EXECUTION-AUTHORITY-CROSSWALK.md) | [IETF review drafts](IETF-LIST-REVIEWS.md) | [Body-specific briefs](STANDARDS-BODY-BRIEFS.md)

**Owner:** Vincent Sullivan

**Current state:** Draft package prepared; no external submission recorded in this repository.

## Decision

Submit the execution-time authority requirements as an individual Internet-Draft and use NEXUS only as implementation evidence. Ask each venue for the requirement that fits its charter. Do not ask a body to adopt NEXUS as a product or claim that the current reference implementation meets all 20 requirements.

## Gate 1: repository evidence

- Keep ETA-1 through ETA-20 stable between the XML source, TXT rendering, and crosswalk.
- Keep all Partial and Gap findings visible.
- Run XML rendering, IETF checks, local-link checks, manifest checks, and the NEXUS test suite.
- Pin the repository commit used for the implementation-status section.

## Gate 2: IETF submission

1. Update the adopted agentproto citation. The individual `draft-agentic-ai-usecases-requirements-07` became the working-group document `draft-ietf-agentproto-usecases-requirements-00` on 20 November 2026.
2. Recheck every referenced Internet-Draft revision on the day of submission.
3. Render the XML with current `xml2rfc` and clear errors and actionable warnings.
4. Run the IETF submission checks and review the rendered TXT and HTML manually.
5. Submit `draft-sullivan-wimse-execution-authority-00` through the IETF Datatracker.
6. Complete the Datatracker email confirmation. A successful upload alone does not publish the draft.
7. Record the accepted Datatracker URL, revision, date, and repository commit here.

## Gate 3: working-group engagement

| Order | Venue | Ask | Evidence to offer |
| ---: | --- | --- | --- |
| 1 | agentproto | Originating-authorization correlation, action-bound approval, unresolved outcome semantics | ETA-1, ETA-8, ETA-16 and refusal-path tests |
| 2 | WIMSE | Time-of-use posture, action-bound confirmation, audit provenance, subtree revocation | ETA-4, ETA-10, ETA-15, ETA-17 |
| 3 | DAWN | Capability-change digest, withdrawal, referral provenance, discovery is not authority | AgBOM capability-change hold and provenance records |
| 4 | NET4AI | Re-authorization after placement, shared budgets for copies, accountable authority, untrusted migrated memory | ETA-8, ETA-9, ETA-13 and Memory Vaccine boundaries |

The AIPREF review remains optional. The source brief labels it the weakest fit and states that CSI has no implementation in that area.

## Gate 4: other standards bodies

- FIDO: contribute runtime-state, cumulative delegation, revocation, and execution-receipt requirements to mandate harmonization.
- NIST: translate the requirements into control-enhancement and assessment-objective language.
- OWASP: contribute test cases, false-assurance failures, and a control-level crosswalk.
- CoSAI: submit the time-of-use authority pattern with one threat per property.
- AAIF: keep the MCP proposal narrow, centered on capability-manifest change detection.

Every route requires a current charter, contribution agreement, contact address, and revision check. Items marked VERIFY in the briefs remain blocked until checked against the body’s own pages.

## Stop conditions

Do not submit if the draft overstates NEXUS implementation status, the XML and TXT disagree, citations point to obsolete revisions without explanation, local evidence paths fail, or the contribution asks a body to approve NEXUS rather than a requirement.

