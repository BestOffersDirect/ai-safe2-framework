# IETF mailing-list review drafts

Five reviews, one per target. Each is plain text and written to stand alone. Verify the target draft and list details before posting from your own address.

These were checked against the revisions named here on 9 November 2026. They are source material, not current-state proof. The agentproto use-cases draft became `draft-ietf-agentproto-usecases-requirements-00` on 20 November 2026, so that review now requires a fresh section and requirement-number check.

Do not post all five on one day. Lists notice. Two this week, three across the meeting week.

---

## 1. agentproto

**To:** agentproto@ietf.org
**Subject:** Review of draft-agentic-ai-usecases-requirements-07 ahead of adoption

I support adoption of this draft as the group's use cases and requirements document. Four comments, each with proposed text. They come from implementing delegation and authorization checkpoints in an open source enforcement layer, so they are about what broke under test.

1. Aggregate limits across a delegation tree (Section 4.4, B3 series). B3 requires scope narrowing at each hop and preserved originator identity. That bounds each delegate. It does not bound the tree. Ten delegates each inside a narrowed limit can together exceed what the originator authorized. Enforcing an aggregate needs one thing from the dialog protocol: each hop has to be able to name the originating authorization, not only the previous hop.

   Proposed B3-11: "Dialog context propagated across delegation hops MUST allow a recipient to identify the originating authorization, so that use of a quantity-limited authorization by any delegate can be attributed to it."

   This asks nothing of the authorization mechanism itself, which stays with OAuth and WIMSE.

2. Authorization checkpoints (Section 4.3, B2 series). The responses are approve, deny, or approve with modifications. In the third case the approval has to be bound to the modified operation, or the agent can execute something other than what was approved.

   Proposed addition to B2: "An approval, with or without modifications, MUST identify the specific operation it applies to in a form the executing agent cannot alter."

3. Unresolved operations (Section 4.2). The text says an operation whose outcome cannot be determined stays unresolved and should not be resent on resumption alone. This is correct and important for non-idempotent actions. It is currently prose. I suggest giving it a requirement ID, and adding a distinct error type under CMN-5 for "a required input could not be established", separate from an authorization denial. draft-konda-agentproto-evaluation-state makes the case for that distinction well.

4. Accountability and auditing (Section 7). Audit structures are out of charter and I am not asking to change that. But audit records defined elsewhere will depend on dialog context being stable. It would help to state which dialog-context elements are intended to be usable as audit correlation keys, so that work in SCITT and elsewhere can rely on them.

One observation rather than a request: CMN-8 covers credential validity at time of use. Where a credential was issued on condition of workload posture, the posture is not re-examined at use. I think that belongs in WIMSE and will raise it there.

I will submit a short requirements draft on these points when the submission tool reopens.

Vincent Sullivan
Cyber Strategy Institute

---

## 2. WIMSE

**To:** wimse@ietf.org (confirm on the WIMSE group page)
**Subject:** draft-ietf-wimse-aims-01: posture at time of use, and three smaller points

Thank you for this document. Composing existing mechanisms is the right call. Four comments.

1. Posture between issuance and use. Credential provisioning is tied to posture assessment, and credentials are short-lived. An agent still acts many times inside one credential lifetime, and a host altered after issuance keeps a valid identity, valid tokens, and valid delegations. Short lifetimes narrow the window. They do not let a resource server ask for more assurance on a high-impact request.

   Suggestion for the authorization section: "For actions a deployment designates as high-impact, an authorization decision SHOULD be able to take as input workload posture evidence with a stated freshness bound, in addition to credential validity." This does not require a new mechanism. It asks that the document name the input, so that Transaction Tokens or a RATS-based profile can carry it.

2. Confirmation during execution. The document notes that CIBA covers client-initiated flows and that more design may be needed. Whatever that design is, two properties seem necessary and could be stated now: the confirmation is bound to the specific action, and it arrives over a channel the agent does not control. The existing rule that local UI confirmation alone is insufficient already implies the second.

3. Audit record minimum fields. The list is good. Two additions would make records usable after the fact: the identifier and revision of the policy applied, and for each input to the decision whether it was verified by the decision point or asserted by another party. I would also say explicitly that denials produce records.

4. Remediation across delegation. Recipients of CAEP or RISC signals attenuate access. When the subject is an agent that has delegated onward, the revoking party may not be able to enumerate what was derived. A per-grant epoch that every derived token carries makes revocation of a subtree a single state change. Worth a sentence as a deployment consideration.

I have an open source implementation of points 1 and 4 and am glad to share what the failure cases looked like. A short requirements draft will follow when submissions reopen.

Vincent Sullivan
Cyber Strategy Institute

---

## 3. DAWN

**To:** dawn@ietf.org (confirm on the DAWN group page)
**Subject:** draft-king-dawn-requirements-02: change, withdrawal, and provenance of discovery records

Three proposed requirements and one clarification. They come from implementing an inventory of discovered agent tools, where the case that needed the most design was not a forged record but a legitimate record that changed.

1. Capability change. REQ-SEC-1 covers origin and integrity of discovery data. A record can be authentic and intact and still describe different capabilities than it did yesterday under the same name. A discoverer that has made a trust decision needs to detect that.

   Proposed: "The Minimum Discoverable Information MUST include a digest over the entity's declared capabilities, so that a discoverer can detect a change to those capabilities since a prior discovery."

2. Withdrawal. Freshness and validity data (REQ-PROP-5) tell a discoverer when to look again. They do not tell it that a record was withdrawn before its validity ended. Section 7 mentions update and withdrawal procedures as an operational note.

   Proposed: "A discovery mechanism MUST provide a way for a discoverer to learn that previously discovered information has been withdrawn, and MUST distinguish withdrawal from absence."

3. Provenance through referral. With directories and federation in scope, a record can reach a discoverer through parties other than its publisher.

   Proposed: "Discovery information obtained through referral or federation MUST allow the discoverer to distinguish the party that originated it from the parties that relayed it."

4. Clarification. Identity, authentication and authorization are out of scope, and Section 5 already warns that integrity does not authenticate the live peer. I suggest one more sentence: "Discovery information describes what an entity offers. It is not a grant of authority to the discoverer or to the entity." Implementations do conflate these.

On draft-iannone-dawn-privacy-considerations: the privacy and auditability section is still to be written. I can contribute text on carrying digests in place of identifiers in audit records if the authors want it.

Vincent Sullivan
Cyber Strategy Institute

---

## 4. NET4AI agent portability

**To:** the author, cc the NET4AI research group list
**Subject:** draft-raskar-net4ai-agent-portability-00: authority and state when a workload moves

The separation of representation, execution and placement is useful, and the statement that capability requirements are not authorization grants is exactly right. Four points for the research questions.

1. Authority does not travel. The security considerations say permissions granted in one domain should not transfer silently. I would make that a stated property of the architecture: placement at a new runtime requires a new grant from that runtime's authority, issued after that runtime has evaluated the workload. The portable contract can carry the class of grant needed. It should not carry the grant.

2. Move and copy are different. The draft treats placement as rebinding. If the source instance keeps running, the workload has been copied. For any authority that is consumed by use, such as a spending or rate limit, a copy doubles it unless both instances draw on the same account. The architecture should say whether placement is exclusive, and how a runtime learns that.

3. A sixth identity. Section 8 separates the delegating party, the logical agent, the artifact, the runtime, and the bound providers. In practice there is also the party that answers for the agent's actions and can stop it. That is often not the delegating user. It should survive a move unchanged, and the destination runtime needs to be able to reach it.

4. State as untrusted input. For the checkpoint question: persistent memory that arrives with a migrated workload should be handled by the destination as untrusted input carrying provenance, not as trusted internal state. Memory is where instructions planted earlier come back.

I maintain an open specification of a system identity manifest covering harness, tools, memory, environment, policies and authority. If it is useful as an input to the workload contract discussion, I will send it.

Vincent Sullivan
Cyber Strategy Institute

---

## 5. AIPREF (optional, weakest fit)

**To:** ai-control@ietf.org (confirm the list address on the AIPREF group page before posting)
**Subject:** draft-reilly-aipref-compliance-00: agents that retrieve on a user's behalf

Post this only if you intend to stay in the thread. CSI has no implementation in this area yet, so these are questions, not proposals.

1. Who is the processing entity when an AI agent retrieves content during a task for a user? The agent operator, the model provider, and the user's organization are three candidates, and they may assign different usage categories to the same retrieval.

2. The record captures the usage category assigned at retrieval. For an agent, the same content can be used in the session, written to persistent memory, and reused in a later session for a different purpose. Is a second record expected when the category changes, or is that out of scope?

3. Where was the preference evaluated? A record is stronger if it says whether the preference was read and applied by a component outside the model, such as a gateway, or whether compliance depended on the model following an instruction.

Vincent Sullivan
Cyber Strategy Institute




