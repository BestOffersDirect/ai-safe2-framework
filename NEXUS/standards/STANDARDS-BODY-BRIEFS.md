# Standards-body briefs: AI SAFE2 contribution framing

Status snapshot from 9 November 2026. Each brief records the state observed then, what CSI could contribute, the entry path, and draft language. It is planning evidence, not current-state proof. Recheck every item against the body's own pages before acting. Items marked VERIFY remain blocked until that check is recorded.

One rule across all of them: lead with the gap the body has already named, offer one mechanism with a test behind it, and state the evidence level. By CSI's own Evidence Assurance v1.0 rubric the mechanisms offered here are E2 to E3. Say that. It reads as credibility, not weakness.

---

## Tier 1: act within 30 days

### FIDO Alliance - Payments Technical Working Group and Agentic Authentication Technical Working Group

**State.** Google contributed AP2 v0.2 and Mastercard contributed Verifiable Intent on 28 April 2026. The Payments working group is chaired by members from Mastercard and Visa. Targets presented at the W3C/GS1 workshop in September: specifications in a public repository for review in September 2026, harmonized AP2 and Verifiable Intent by end of 2026, first consolidated version in mid-2027. VERIFY: one tracker found no public FIDO agentic repository as of 21 October 2026.

**What CSI contributes.** The layer the mandate does not cover: evidence that the workload exercising a mandate was in an approved state at the moment of use, cumulative constraints across delegated agents, revocation semantics for an authority tree, trusted rendering of what the user approved, and an execution receipt that separates deny, escalate and unresolved. This is CP.5.APAY, 20 controls, with a refusal-path test for each.

**Framing that works here.** Liability and dispute evidence. A mandate proves what the user authorized. It does not prove the agent that used it was the agent the user authorized. When there is no chargeback, the party that cannot prove its side carries the loss.

**Entry path.** Working-group participation requires FIDO membership. VERIFY the current membership class and fee that grants working-group access. Without membership: comment on the public review drafts when they appear, and contribute through the W3C and IETF liaisons.

**Opening statement.**
> AP2 and Verifiable Intent establish what a user authorized and that an agent presented a valid mandate. Neither establishes that the software exercising the mandate at settlement time is the software that was authorized. We have implemented and tested a control profile for that interval: runtime-state evidence bound to the transaction, aggregate limits across delegated agents, and single-step revocation of an authority tree. We offer the control set, the threat model, and twelve falsifiable test scenarios as input to the harmonization work, and we are not proposing a competing mandate format.

### NIST - CAISI AI Agent Standards Initiative, COSAiS overlays, NCCoE agent identity project

**State.** CSI responded to the CAISI RFI in March 2026. CAISI published its analysis of responses in May. COSAiS is producing SP 800-53 overlays for five AI use cases. As of the most recent secondary sources (August 2026), the single-agent and multi-agent overlays had not been released for comment. VERIFY on the CSRC COSAiS page. The NCCoE concept paper on agent identity and authorization closed for comment on 2 April.

**What CSI contributes.** Control-enhancement language in SP 800-53 form for the two agent overlays: authority bound to workload state at time of use (AC-3, AC-4, SI-7 family), aggregate limits across delegated non-person entities (AC-6), named accountable authority with an independent stop path (AC-2, IR-4), and decision records that state how each input was established (AU-2, AU-3, AU-10). CSI's March appendices already mapped seven controls. Update them to v3.1 and the two new invariants.

**Framing that works here.** Overlay-ready text, outcome-based, with assessment procedures. NIST adopts what it can paste.

**Entry path.** Public comment when each overlay drafts. Join the COSAiS community channel now so the release is not missed. For NCCoE, respond to the Federal Register notice when the project seeks collaborators.

**Opening statement.**
> The agent overlays will need to address a condition existing controls do not: an agent whose identity, credentials and delegations are all valid while its host is compromised. We propose control enhancements, with assessment objectives, that bind authorization for designated actions to current workload evidence, bound cumulative use of delegated authority, and require a decision record that distinguishes verified inputs from asserted ones. Each is implemented in open source and tested on the refusal path.

### OWASP GenAI Security Project - Agentic Security Initiative, AIVSS, Agent Control Standard, Framework Crosswalk

**State.** Top 10 for Agentic Applications 2026 is published. State of Agentic AI Security and Governance 2.01 was published 1 June 2026. AIVSS is at v0.8 with v1 intended. The Agent Control Standard was donated to the project in 2026. A GenAI Security Industry Framework Crosswalk was announced as an open resource.

**What CSI contributes.** Three things, in order of effort. First, a crosswalk entry: AI SAFE2 v3.1 mapped to the Agentic Top 10 and to ACS, submitted to the Framework Crosswalk. Second, the NEXUS bridge to ACS as a worked example of running a Guardian with cryptographic identity underneath. VERIFY that the ACS version the NEXUS bridge targets is the one now hosted at OWASP. Third, scoring input to AIVSS on how agentic amplification factors change when authority is runtime-bound.

**Framing that works here.** Practitioner evidence. Test cases, evasion lists, things that failed. The October false-assurance hardening work (a poisoned MCP server that scored as acceptable, hostile skills that passed a gate) is exactly the material this community values, because it is a framework reporting its own defects.

**Entry path.** Open. Join the initiative's Slack channel and GitHub, attend the workstream call, submit by pull request.

**Opening statement.**
> We maintain AI SAFE2, an open control framework with a reference enforcement implementation. We would like to contribute a control-level mapping to the Agentic Top 10 and the Agent Control Standard, and a write-up of an adversarial battery we ran against our own tooling, including the cases where our scanner and trust gate gave false assurance and what closed them.

---

## Tier 2: act within 90 days

### CoSAI (OASIS Open) - Workstream 4, Secure Design Patterns for Agentic Systems

**State.** Published MCP Security (January 2026), Principles for Secure-by-Design Agentic Systems, and Agentic Identity and Access Management (spring 2026). An Agent Credentials RFC group exists under Workstream 4. OWASP, the AI Alliance and CSA joined the technical steering committee.

**What CSI contributes.** Their own co-lead said valid identity alone is insufficient because credentials can be correct while outcomes are harmful. Offer the time-of-use authority requirements as a design pattern, and the 19-control MCP profile as a review against their 40-threat MCP taxonomy.

**Framing.** Secure design patterns with a threat mapped to each. They organize by threat category.

**Entry path.** Contributions through the cosai-oasis GitHub organization. VERIFY whether workstream participation requires sponsor status or an OASIS contributor agreement only.

### Agentic AI Foundation (Linux Foundation) - MCP and A2A

**State.** AAIF hosts MCP, A2A (joined 17 August 2026, v1.0 shipped March 2026), agentgateway and others. MCP changes go through Spec Enhancement Proposals. Working groups include Security and Privacy, Identity and Trust, Observability and Traceability, Agentic Commerce, and Governance, Risk and Regulatory Alignment.

**What CSI contributes.** One SEP, small and concrete: a signal for capability-manifest change so a client that pinned a server's tool manifest can detect a change before use. This is the rug-pull hold already implemented in AgBOM. For A2A: comment on the open proposals for scoped delegation with cascade revocation, offering the epoch approach.

**Framing.** Minimal protocol change, backward compatible, with a reference implementation. The MCP specification has so far kept security primitives light and left enforcement to implementations. A change-detection signal fits that posture.

**Entry path.** Open. SEP by pull request. A2A by GitHub issue. Do not lead with the argument that MCP needs a successor. It closes the door.

### OpenID Foundation - AI Identity Management Community Group

**State.** Community group chaired by members from CrowdStrike and AWS. Published the Identity Management for Agentic AI whitepaper in October 2025 and responded to the NIST RFI in March 2026 through its threat modeling subgroup. Weekly calls open to anyone who signs the participation agreement.

**What CSI contributes.** Threat-model input on post-issuance host compromise, and a use case for the Shared Signals Framework: revoking a delegation subtree with one event.

**Framing.** Identity people. Speak OAuth, CAEP, and token semantics. One of the AIMS authors co-chairs this group, so a good WIMSE review opens this door too.

**Entry path.** Sign the participation agreement, join the list, bring the use case to a call.

---

## Tier 3: position and monitor

### W3C - AI Agent Protocol Community Group, Agent Identity Registry Protocol Community Group, and the e-commerce agents workshop follow-up

**State.** Community groups are open without W3C membership. The W3C/GS1 workshop on e-commerce for humans and AI agents ran 8 to 9 September 2026 and a report is in preparation. A Digital Policy working group charter is under development following the ODRL workshop. Several new agent community groups formed in June 2026.

**Contribution.** Present the irreversible-action example to the AI Agent Protocol group, which has already hosted AP2 and x402 sessions. Watch the workshop report for a proposed working group.

### Cloud Security Alliance - AARM, Agentic Trust Framework, MAESTRO, AI Controls Matrix

**State.** CSA published a landscape note on 27 October 2026 that lists the candidates for agent governance: OWASP ACS, CSA's AARM v1.0, ETSI TS 104 328 and others. AI SAFE2 is not on it.

**Contribution.** A crosswalk from AI SAFE2 to AARM and AICM, sent to the research team behind the landscape note with a request for inclusion in its next revision. AI SAFE2 already maps to MAESTRO.

### ISO/IEC JTC 1/SC 42 and CEN-CENELEC JTC 21

**State.** SC 42 has no dedicated agentic work item. ISO/IEC 22989 terminology is being revised and may address agents. JTC 21's first harmonised standard under the EU AI Act, EN 18286 on quality management, was cited in the Official Journal on 14 October 2026. Standards for logging, human oversight and cybersecurity are still in development.

**Contribution.** Long game, entered through a national body. In the US that is the INCITS mirror committee for SC 42. VERIFY membership terms. IT-AAC may be a better vehicle than CSI for the membership. The contribution, when a work item opens, is the capability-tier model: proportional obligations by autonomy level.

### ITU-T - SG17 and SG21

**State.** SG17 has a work item on a canonical agentic AI identity data model (X.aiidm, target June 2027) and a technical report on trust frameworks for agentic AI. SG21 has a work item on AI agent platforms. Supporting members on the platform item are predominantly Chinese operators and institutes.

**Contribution.** None directly. Participation runs through member states and sector members. Raise it with NIST as part of the international-engagement pillar of the Agent Standards Initiative.

### ETSI TC SAI

**State.** A work item for baseline agentic AI cybersecurity requirements, TS 104 328, was reported adopted on 1 October 2026. VERIFY: the source that reported it could not locate the public work-programme record.

**Contribution.** Monitor. If confirmed, ETSI drafts are open for comment by members, and a baseline-requirements document is a natural home for the capability-tier model.

### Decentralized Identity Foundation (KYA-OS) and the x402 Foundation

**State.** Named in the NEXUS payments README as engagement targets. Not re-verified in this pass.

**Contribution.** As already written in `NEXUS/payments/README.md`: attenuation dimensions and descendant-revocation evidence for KYA-OS; pre-settlement policy hooks, idempotency and revocation epochs for x402. Sequence these after FIDO, since both will track where AP2 lands.

---

## What not to do, in any venue

- Do not ask a body to adopt AI SAFE2 or NEXUS. Ask it to adopt a requirement. The framework is the evidence, not the ask.
- Do not send the same text to two bodies. Each gets the piece that fits its charter.
- Do not claim coverage percentages against another body's framework in a submission to that body. They will check, and a single disputed row discredits the rest.
- Do not use "sovereign" as a product adjective in standards text. Use it once, defined: the deploying party keeps the accountable authority and the stop path.




