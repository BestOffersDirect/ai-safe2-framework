"""Deterministic execution-authority state classification."""

from nexus_sdk.payments.firewall import PaymentVerdict
from nexus_sdk.payments.objects import (
    EvaluationState,
    PaymentDecision,
    PaymentReasonCode,
)


def verdict(decision: PaymentDecision, *codes: PaymentReasonCode) -> PaymentVerdict:
    return PaymentVerdict(
        decision=decision,
        transaction_intent_id="intent-state-test",
        reason_codes=list(codes),
    )


def test_only_allow_establishes_execution_authority():
    result = verdict(PaymentDecision.ALLOW)
    assert result.evaluation_state is EvaluationState.ESTABLISHED
    assert result.to_dict()["evaluation_state"] == "established"


def test_missing_required_evidence_is_not_established():
    result = verdict(PaymentDecision.DENY, PaymentReasonCode.NO_RUNTIME_MEASUREMENT)
    assert result.evaluation_state is EvaluationState.NOT_ESTABLISHED


def test_human_approval_pending_is_not_established():
    result = verdict(PaymentDecision.ESCALATE, PaymentReasonCode.HEAR_REQUIRED)
    assert result.evaluation_state is EvaluationState.NOT_ESTABLISHED


def test_rule_violation_is_denied_after_evaluation():
    result = verdict(PaymentDecision.DENY, PaymentReasonCode.AMOUNT_EXCEEDS_GRANT)
    assert result.evaluation_state is EvaluationState.DENIED


def test_invalid_attestation_is_denied_not_missing():
    result = verdict(
        PaymentDecision.DENY,
        PaymentReasonCode.ATTESTATION_VERIFICATION_FAILED,
    )
    assert result.evaluation_state is EvaluationState.DENIED


def test_unavailable_authority_is_indeterminate():
    result = verdict(
        PaymentDecision.DENY,
        PaymentReasonCode.POLICY_AUTHORITY_UNAVAILABLE,
    )
    assert result.evaluation_state is EvaluationState.INDETERMINATE


def test_reconciliation_is_indeterminate():
    result = verdict(
        PaymentDecision.RECONCILE,
        PaymentReasonCode.SETTLEMENT_AMBIGUOUS,
    )
    assert result.evaluation_state is EvaluationState.INDETERMINATE
