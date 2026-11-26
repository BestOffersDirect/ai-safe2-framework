"""Adversarial tests for ETA-9 pre-partitioned shared budgets."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from nexus_sdk.payments.execution_plane import ExecutionRecord, ExecutionState
from nexus_sdk.payments.shared_budget import (
    BudgetPartitionConflictError,
    BudgetPartitionIssuer,
    BudgetPartitionUnavailableError,
    InMemoryAtomicPartitionStore,
    InProcessHMACTestBudgetAuthenticator,
    PartitionBudgetLedger,
    PartitionedCoordinatorStateStore,
)
from nexus_sdk.payments.sqlite_state import SQLiteGatewayStateStore

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=timezone.utc)
KEY = b"shared-budget-authority-test-key"


def configured():
    store = InMemoryAtomicPartitionStore()
    authenticator = InProcessHMACTestBudgetAuthenticator(KEY)
    issuer = BudgetPartitionIssuer(store=store, authenticator=authenticator)
    return store, authenticator, issuer


def issue(issuer, *, holder="decision-point-a", ceiling=6_000):
    return issuer.issue(
        parent_scope_id="grant-root-1",
        decision_point_id=holder,
        currency="USD",
        parent_ceiling_minor=10_000,
        partition_ceiling_minor=ceiling,
        expires_at=(NOW + timedelta(hours=1)).isoformat(),
        now=NOW,
    )


def test_atomic_issuer_never_overallocates_parent_budget():
    _, _, issuer = configured()

    def allocate(holder):
        try:
            return issue(issuer, holder=holder, ceiling=6_000)
        except BudgetPartitionConflictError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(allocate, ("decision-point-a", "decision-point-b")))
    assert sum(result is not None for result in results) == 1


def test_two_hosts_cannot_multiply_the_parent_limit():
    _, authenticator, issuer = configured()
    first = issue(issuer, holder="decision-point-a", ceiling=6_000)
    second = issue(issuer, holder="decision-point-b", ceiling=4_000)
    assert first.parent_ceiling_minor == 10_000
    assert first.allocated_total_minor == 6_000
    assert second.allocated_total_minor == 10_000
    assert first.to_dict()["partition_digest"] == first.partition_digest
    assert first.to_dict()["proof"]
    ledger_a = PartitionBudgetLedger(
        partition=first,
        decision_point_id="decision-point-a",
        authenticator=authenticator,
        now=NOW,
    )
    ledger_b = PartitionBudgetLedger(
        partition=second,
        decision_point_id="decision-point-b",
        authenticator=authenticator,
        now=NOW,
    )
    ledger_a.reserve(
        transaction_intent_id="intent-a", amount_minor=6_000, currency="USD", now=NOW
    )
    ledger_b.reserve(
        transaction_intent_id="intent-b", amount_minor=4_000, currency="USD", now=NOW
    )
    assert ledger_a.remaining_minor == 0
    assert ledger_b.remaining_minor == 0
    with pytest.raises(BudgetPartitionConflictError, match="would be exceeded"):
        ledger_b.reserve(
            transaction_intent_id="intent-b2", amount_minor=1, currency="USD", now=NOW
        )


def test_parent_ceiling_cannot_change_after_allocation_starts():
    store, _, _ = configured()
    store.allocate(
        parent_scope_id="grant-root-1",
        decision_point_id="decision-point-a",
        currency="USD",
        parent_ceiling_minor=10_000,
        partition_ceiling_minor=6_000,
    )
    with pytest.raises(BudgetPartitionConflictError, match="ceiling changed"):
        store.allocate(
            parent_scope_id="grant-root-1",
            decision_point_id="decision-point-b",
            currency="USD",
            parent_ceiling_minor=100_000,
            partition_ceiling_minor=4_000,
        )


def test_partition_is_bound_to_one_decision_point():
    _, authenticator, issuer = configured()
    partition = issue(issuer)
    with pytest.raises(BudgetPartitionConflictError, match="another decision point"):
        PartitionBudgetLedger(
            partition=partition,
            decision_point_id="decision-point-attacker",
            authenticator=authenticator,
            now=NOW,
        )


def test_partition_tampering_invalidates_proof():
    _, authenticator, issuer = configured()
    partition = issue(issuer)
    forged = replace(partition, ceiling_minor=partition.ceiling_minor + 1)
    with pytest.raises(BudgetPartitionConflictError, match="proof is invalid"):
        PartitionBudgetLedger(
            partition=forged,
            decision_point_id="decision-point-a",
            authenticator=authenticator,
            now=NOW,
        )


def test_expired_partition_fails_closed():
    _, authenticator, issuer = configured()
    partition = issue(issuer)
    with pytest.raises(BudgetPartitionConflictError, match="not currently valid"):
        PartitionBudgetLedger(
            partition=partition,
            decision_point_id="decision-point-a",
            authenticator=authenticator,
            now=NOW + timedelta(hours=2),
        )


def test_naive_partition_expiry_is_refused():
    _, _, issuer = configured()
    with pytest.raises(ValueError, match="timezone-aware"):
        issuer.issue(
            parent_scope_id="grant-root-1",
            decision_point_id="decision-point-a",
            currency="USD",
            parent_ceiling_minor=10_000,
            partition_ceiling_minor=6_000,
            expires_at="2026-11-25T13:00:00",
            now=NOW,
        )


def test_replay_is_idempotent_but_term_substitution_is_refused():
    _, authenticator, issuer = configured()
    ledger = PartitionBudgetLedger(
        partition=issue(issuer),
        decision_point_id="decision-point-a",
        authenticator=authenticator,
        now=NOW,
    )
    first = ledger.reserve(
        transaction_intent_id="intent-1", amount_minor=2_000, currency="USD", now=NOW
    )
    repeated = ledger.reserve(
        transaction_intent_id="intent-1", amount_minor=2_000, currency="USD", now=NOW
    )
    assert repeated == first
    with pytest.raises(BudgetPartitionConflictError, match="different budget terms"):
        ledger.reserve(
            transaction_intent_id="intent-1", amount_minor=2_001, currency="USD", now=NOW
        )


def test_release_restores_capacity_but_commit_does_not():
    _, authenticator, issuer = configured()
    ledger = PartitionBudgetLedger(
        partition=issue(issuer),
        decision_point_id="decision-point-a",
        authenticator=authenticator,
        now=NOW,
    )
    released = ledger.reserve(
        transaction_intent_id="intent-release",
        amount_minor=2_000,
        currency="USD",
        now=NOW,
    )
    ledger.release(released.reservation_id, reason="authoritative rail rejection")
    assert ledger.remaining_minor == 6_000
    committed = ledger.reserve(
        transaction_intent_id="intent-commit",
        amount_minor=2_000,
        currency="USD",
        now=NOW,
    )
    committed_result = ledger.commit(
        committed.reservation_id, settlement_id="settlement-1"
    )
    assert ledger.remaining_minor == 4_000
    assert committed_result.to_dict()["partition_id"] == ledger.partition.partition_id
    assert committed_result.to_dict()["status"] == "committed"


def test_unavailable_authority_and_ledger_fail_closed():
    store, authenticator, issuer = configured()
    store.available = False
    with pytest.raises(BudgetPartitionUnavailableError):
        issue(issuer)
    store.available = True
    ledger = PartitionBudgetLedger(
        partition=issue(issuer),
        decision_point_id="decision-point-a",
        authenticator=authenticator,
        now=NOW,
    )
    ledger.available = False
    with pytest.raises(BudgetPartitionUnavailableError):
        ledger.reserve(
            transaction_intent_id="intent-1", amount_minor=1, currency="USD", now=NOW
        )


def test_coordinator_state_enforces_partition_and_tracks_settlement(tmp_path):
    _, authenticator, issuer = configured()
    partition = issue(issuer)
    ledger = PartitionBudgetLedger(
        partition=partition,
        decision_point_id="decision-point-a",
        authenticator=authenticator,
        now=NOW,
    )
    backing = SQLiteGatewayStateStore(tmp_path / "gateway.db")
    state = PartitionedCoordinatorStateStore(state=backing, budget=ledger)
    initial = ExecutionRecord(
        execution_id="exec-1",
        transaction_intent_id="intent-1",
        canonical_digest="sha256:canonical-1",
        idempotency_key="idem-1",
        authority_grant_id="grant-root-1",
        revocation_epoch=0,
    )
    state.create(initial)
    accepted = initial.transition(ExecutionState.POLICY_ACCEPTED)
    assert state.compare_and_swap(expected=initial, updated=accepted)
    with pytest.raises(BudgetPartitionConflictError, match="do not match"):
        state.reserve_execution(
            accepted,
            amount_minor=2_000,
            currency="USD",
            ceilings_minor={"attacker-supplied": 999_999},
        )
    reserved = state.reserve_execution(
        accepted,
        amount_minor=2_000,
        currency="USD",
        ceilings_minor={partition.partition_id: partition.ceiling_minor},
    )
    assert ledger.remaining_minor == 4_000
    credentialed = reserved.transition(
        ExecutionState.CREDENTIAL_RELEASED, authorization_id="authorization-1"
    )
    assert state.compare_and_swap(expected=reserved, updated=credentialed)
    submitted = credentialed.transition(ExecutionState.SUBMITTED)
    assert state.compare_and_swap(expected=credentialed, updated=submitted)
    settled = submitted.transition(ExecutionState.SETTLED, settlement_id="settlement-1")
    assert state.settle_execution(expected=submitted, updated=settled)
    budget_record = ledger.reservation_for_intent("intent-1")
    assert budget_record is not None
    assert budget_record.status == "committed"
    assert budget_record.settlement_id == "settlement-1"
