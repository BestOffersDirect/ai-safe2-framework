"""Shared Budget Authority: pre-partitioned limits for independent decision points."""

from __future__ import annotations

import hashlib
import hmac
import json
import threading
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol

from nexus_sdk.payments.execution_plane import ComponentAssurance, ExecutionRecord
from nexus_sdk.payments.objects import canonical_hash, parse_ts, utcnow

__all__ = [
    "AtomicPartitionStore",
    "BudgetPartition",
    "BudgetPartitionAuthenticator",
    "BudgetPartitionConflictError",
    "BudgetPartitionIssuer",
    "BudgetPartitionUnavailableError",
    "InMemoryAtomicPartitionStore",
    "InProcessHMACTestBudgetAuthenticator",
    "PartitionBudgetLedger",
    "PartitionedCoordinatorStateStore",
    "PartitionAllocation",
    "PartitionReservation",
]


class BudgetPartitionConflictError(RuntimeError):
    """A partition or reservation would exceed or contradict bound authority."""


class BudgetPartitionUnavailableError(RuntimeError):
    """The authoritative partition boundary is unavailable; callers fail closed."""


@dataclass(frozen=True)
class BudgetPartition:
    """Signed exclusive budget assigned to one decision point."""

    partition_id: str
    parent_scope_id: str
    decision_point_id: str
    currency: str
    parent_ceiling_minor: int
    ceiling_minor: int
    allocated_total_minor: int
    issued_at: str
    expires_at: str
    issuer_id: str
    allocation_sequence: int
    proof: str = ""

    @property
    def partition_digest(self) -> str:
        return canonical_hash(self.proof_values())

    def proof_values(self) -> dict:
        return {
            "partition_id": self.partition_id,
            "parent_scope_id": self.parent_scope_id,
            "decision_point_id": self.decision_point_id,
            "currency": self.currency,
            "parent_ceiling_minor": self.parent_ceiling_minor,
            "ceiling_minor": self.ceiling_minor,
            "allocated_total_minor": self.allocated_total_minor,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "issuer_id": self.issuer_id,
            "allocation_sequence": self.allocation_sequence,
        }

    def to_dict(self) -> dict:
        return {
            **self.proof_values(),
            "partition_digest": self.partition_digest,
            "proof": self.proof,
        }


class BudgetPartitionAuthenticator(Protocol):
    """Protected issuer and verifier for partition proofs."""

    authenticator_id: str
    assurance: ComponentAssurance

    def seal(self, partition: BudgetPartition) -> str: ...
    def verify(self, partition: BudgetPartition) -> bool: ...


class AtomicPartitionStore(Protocol):
    """Atomic parent-budget allocator used before partitions are distributed."""

    assurance: ComponentAssurance

    def allocate(
        self,
        *,
        parent_scope_id: str,
        decision_point_id: str,
        currency: str,
        parent_ceiling_minor: int,
        partition_ceiling_minor: int,
    ) -> PartitionAllocation: ...


@dataclass(frozen=True)
class PartitionAllocation:
    """Atomic allocation result preserved in the signed partition evidence."""

    sequence: int
    allocated_total_minor: int


class InMemoryAtomicPartitionStore:
    """Thread-safe reference allocator. Production issuers use durable storage."""

    assurance = ComponentAssurance.REFERENCE

    def __init__(self) -> None:
        self._allocations: dict[tuple[str, str], dict[str, int]] = {}
        self._ceilings: dict[tuple[str, str], int] = {}
        self._sequences: dict[tuple[str, str], int] = {}
        self._lock = threading.RLock()
        self.available = True

    def allocate(
        self,
        *,
        parent_scope_id: str,
        decision_point_id: str,
        currency: str,
        parent_ceiling_minor: int,
        partition_ceiling_minor: int,
    ) -> PartitionAllocation:
        if not self.available:
            raise BudgetPartitionUnavailableError(
                "shared budget allocation authority is unavailable"
            )
        if (
            not parent_scope_id
            or not decision_point_id
            or not currency
            or parent_ceiling_minor < 0
            or partition_ceiling_minor <= 0
        ):
            raise ValueError("complete positive budget allocation fields are required")
        key = (parent_scope_id, currency)
        with self._lock:
            established_ceiling = self._ceilings.get(key)
            if established_ceiling is not None and established_ceiling != parent_ceiling_minor:
                raise BudgetPartitionConflictError(
                    "parent budget ceiling changed after partition allocation began"
                )
            self._ceilings[key] = parent_ceiling_minor
            allocations = self._allocations.setdefault(key, {})
            if decision_point_id in allocations:
                raise BudgetPartitionConflictError(
                    "decision point already has a partition for this parent and currency"
                )
            if sum(allocations.values()) + partition_ceiling_minor > parent_ceiling_minor:
                raise BudgetPartitionConflictError(
                    "partition allocation would exceed the parent budget"
                )
            allocations[decision_point_id] = partition_ceiling_minor
            sequence = self._sequences.get(key, 0) + 1
            self._sequences[key] = sequence
            return PartitionAllocation(
                sequence=sequence,
                allocated_total_minor=sum(allocations.values()),
            )


class InProcessHMACTestBudgetAuthenticator:
    """Reference proof backend for tests; production uses protected signing keys."""

    assurance = ComponentAssurance.REFERENCE

    def __init__(self, key: bytes, *, authenticator_id: str = "budget-test-hmac") -> None:
        if not key or not authenticator_id:
            raise ValueError("key and authenticator identity are required")
        self._key = key
        self.authenticator_id = authenticator_id

    def seal(self, partition: BudgetPartition) -> str:
        payload = json.dumps(
            partition.proof_values(), sort_keys=True, separators=(",", ":")
        ).encode()
        return hmac.new(self._key, payload, hashlib.sha256).hexdigest()

    def verify(self, partition: BudgetPartition) -> bool:
        return (
            partition.issuer_id == self.authenticator_id
            and bool(partition.proof)
            and hmac.compare_digest(self.seal(partition), partition.proof)
        )


class BudgetPartitionIssuer:
    """Human name: Shared Budget Authority. Technical name: BudgetPartitionIssuer."""

    human_name = "Shared Budget Authority"
    technical_name = "BudgetPartitionIssuer"

    def __init__(self, *, store: AtomicPartitionStore,
                 authenticator: BudgetPartitionAuthenticator) -> None:
        self.store = store
        self.authenticator = authenticator

    @property
    def assurance(self) -> ComponentAssurance:
        if (
            self.store.assurance is ComponentAssurance.DEPLOYMENT
            and self.authenticator.assurance is ComponentAssurance.DEPLOYMENT
        ):
            return ComponentAssurance.DEPLOYMENT
        return ComponentAssurance.REFERENCE

    def issue(
        self,
        *,
        parent_scope_id: str,
        decision_point_id: str,
        currency: str,
        parent_ceiling_minor: int,
        partition_ceiling_minor: int,
        expires_at: str,
        now: datetime | None = None,
    ) -> BudgetPartition:
        issued_at = now or utcnow()
        expiry = parse_ts(expires_at)
        if (
            expiry is None
            or issued_at.tzinfo is None
            or expiry.tzinfo is None
            or expiry <= issued_at
        ):
            raise ValueError("partition expiry must be timezone-aware and in the future")
        allocation = self.store.allocate(
            parent_scope_id=parent_scope_id,
            decision_point_id=decision_point_id,
            currency=currency,
            parent_ceiling_minor=parent_ceiling_minor,
            partition_ceiling_minor=partition_ceiling_minor,
        )
        partition = BudgetPartition(
            partition_id="bpt_" + uuid.uuid4().hex[:24],
            parent_scope_id=parent_scope_id,
            decision_point_id=decision_point_id,
            currency=currency,
            parent_ceiling_minor=parent_ceiling_minor,
            ceiling_minor=partition_ceiling_minor,
            allocated_total_minor=allocation.allocated_total_minor,
            issued_at=issued_at.isoformat(),
            expires_at=expiry.isoformat(),
            issuer_id=self.authenticator.authenticator_id,
            allocation_sequence=allocation.sequence,
        )
        proof = self.authenticator.seal(partition)
        if not proof:
            raise RuntimeError("budget partition authenticator returned no proof")
        return replace(partition, proof=proof)


@dataclass(frozen=True)
class PartitionReservation:
    reservation_id: str
    partition_id: str
    transaction_intent_id: str
    amount_minor: int
    currency: str
    created_at: str
    status: str = "reserved"
    settlement_id: str = ""
    release_reason: str = ""

    def to_dict(self) -> dict:
        return dict(self.__dict__)


class PartitionBudgetLedger:
    """Atomic local ledger for one exclusive, signed budget partition."""

    human_name = "Partition Budget Ledger"
    technical_name = "PartitionBudgetLedger"
    assurance = ComponentAssurance.REFERENCE

    def __init__(self, *, partition: BudgetPartition,
                 decision_point_id: str,
                 authenticator: BudgetPartitionAuthenticator,
                 now: datetime | None = None) -> None:
        self._now = (lambda: now) if now is not None else utcnow
        evaluated_at = self._now()
        issued_at = parse_ts(partition.issued_at)
        expires_at = parse_ts(partition.expires_at)
        if not authenticator.verify(partition):
            raise BudgetPartitionConflictError("budget partition proof is invalid")
        if partition.decision_point_id != decision_point_id:
            raise BudgetPartitionConflictError(
                "budget partition is bound to another decision point"
            )
        if (
            issued_at is None
            or expires_at is None
            or evaluated_at.tzinfo is None
            or issued_at.tzinfo is None
            or expires_at.tzinfo is None
            or issued_at > evaluated_at
            or expires_at <= evaluated_at
        ):
            raise BudgetPartitionConflictError("budget partition is not currently valid")
        self.partition = partition
        self.decision_point_id = decision_point_id
        self.authenticator = authenticator
        self._reservations: dict[str, PartitionReservation] = {}
        self._by_intent: dict[str, str] = {}
        self._lock = threading.RLock()
        self.available = True

    def reserve(self, *, transaction_intent_id: str, amount_minor: int,
                currency: str, now: datetime | None = None) -> PartitionReservation:
        if not self.available:
            raise BudgetPartitionUnavailableError("partition budget ledger is unavailable")
        if not transaction_intent_id or amount_minor < 0 or currency != self.partition.currency:
            raise ValueError("valid intent, amount, and partition currency are required")
        evaluated_at = now or self._now()
        expiry = parse_ts(self.partition.expires_at)
        if (
            expiry is None
            or expiry.tzinfo is None
            or evaluated_at.tzinfo is None
            or expiry <= evaluated_at
        ):
            raise BudgetPartitionConflictError("budget partition has expired")
        with self._lock:
            existing_id = self._by_intent.get(transaction_intent_id)
            if existing_id:
                existing = self._reservations[existing_id]
                if existing.amount_minor != amount_minor or existing.currency != currency:
                    raise BudgetPartitionConflictError(
                        "transaction intent was replayed with different budget terms"
                    )
                if existing.status == "released":
                    raise BudgetPartitionConflictError(
                        "released transaction intent cannot reserve budget again"
                    )
                return existing
            exposure = sum(
                value.amount_minor
                for value in self._reservations.values()
                if value.status in {"reserved", "committed"}
            )
            if exposure + amount_minor > self.partition.ceiling_minor:
                raise BudgetPartitionConflictError("partition budget would be exceeded")
            reservation = PartitionReservation(
                reservation_id="bpr_" + uuid.uuid4().hex[:24],
                partition_id=self.partition.partition_id,
                transaction_intent_id=transaction_intent_id,
                amount_minor=amount_minor,
                currency=currency,
                created_at=evaluated_at.isoformat(),
            )
            self._reservations[reservation.reservation_id] = reservation
            self._by_intent[transaction_intent_id] = reservation.reservation_id
            return reservation

    def commit(self, reservation_id: str, *, settlement_id: str) -> PartitionReservation:
        if not self.available:
            raise BudgetPartitionUnavailableError("partition budget ledger is unavailable")
        if not settlement_id:
            raise ValueError("settlement_id is required")
        with self._lock:
            current = self._reservations.get(reservation_id)
            if current is None or current.status != "reserved":
                raise BudgetPartitionConflictError(
                    "budget reservation is missing or no longer reservable"
                )
            updated = replace(current, status="committed", settlement_id=settlement_id)
            self._reservations[reservation_id] = updated
            return updated

    def reservation_for_intent(
        self, transaction_intent_id: str
    ) -> PartitionReservation | None:
        with self._lock:
            reservation_id = self._by_intent.get(transaction_intent_id)
            if reservation_id is None:
                return None
            return self._reservations[reservation_id]

    def release(self, reservation_id: str, *, reason: str) -> PartitionReservation:
        if not self.available:
            raise BudgetPartitionUnavailableError("partition budget ledger is unavailable")
        if not reason:
            raise ValueError("release reason is required")
        with self._lock:
            current = self._reservations.get(reservation_id)
            if current is None or current.status != "reserved":
                raise BudgetPartitionConflictError(
                    "budget reservation is missing or no longer releasable"
                )
            updated = replace(current, status="released", release_reason=reason)
            self._reservations[reservation_id] = updated
            return updated

    @property
    def remaining_minor(self) -> int:
        with self._lock:
            exposure = sum(
                value.amount_minor
                for value in self._reservations.values()
                if value.status in {"reserved", "committed"}
            )
            return self.partition.ceiling_minor - exposure


class CoordinatorBackingState(Protocol):
    """State operations required by the partition-enforcing coordinator wrapper."""

    assurance: ComponentAssurance

    def create(self, record: ExecutionRecord) -> None: ...
    def get(self, execution_id: str) -> ExecutionRecord | None: ...
    def compare_and_swap(
        self, *, expected: ExecutionRecord, updated: ExecutionRecord
    ) -> bool: ...
    def current_revocation_epoch(self, principal_id: str) -> int: ...
    def reserve_execution(
        self,
        record: ExecutionRecord,
        *,
        amount_minor: int,
        currency: str,
        ceilings_minor: Mapping[str, int],
    ) -> ExecutionRecord: ...
    def settle_execution(
        self, *, expected: ExecutionRecord, updated: ExecutionRecord
    ) -> bool: ...
    def release_execution(
        self, *, expected: ExecutionRecord, updated: ExecutionRecord, reason: str
    ) -> bool: ...


class PartitionedCoordinatorStateStore:
    """Coordinator state wrapper that enforces one signed partition ceiling."""

    human_name = "Partition-Enforced Gateway State"
    technical_name = "PartitionedCoordinatorStateStore"

    def __init__(self, *, state: CoordinatorBackingState,
                 budget: PartitionBudgetLedger) -> None:
        self.state = state
        self.budget = budget

    @property
    def assurance(self) -> ComponentAssurance:
        if (
            self.state.assurance is ComponentAssurance.DEPLOYMENT
            and self.budget.assurance is ComponentAssurance.DEPLOYMENT
        ):
            return ComponentAssurance.DEPLOYMENT
        return ComponentAssurance.REFERENCE

    def create(self, record: ExecutionRecord) -> None:
        self.state.create(record)

    def get(self, execution_id: str) -> ExecutionRecord | None:
        return self.state.get(execution_id)

    def compare_and_swap(
        self, *, expected: ExecutionRecord, updated: ExecutionRecord
    ) -> bool:
        return self.state.compare_and_swap(expected=expected, updated=updated)

    def current_revocation_epoch(self, principal_id: str) -> int:
        return self.state.current_revocation_epoch(principal_id)

    def reserve_execution(
        self,
        record: ExecutionRecord,
        *,
        amount_minor: int,
        currency: str,
        ceilings_minor: Mapping[str, int],
    ) -> ExecutionRecord:
        expected = {self.budget.partition.partition_id: self.budget.partition.ceiling_minor}
        if dict(ceilings_minor) != expected:
            raise BudgetPartitionConflictError(
                "coordinator ceilings do not match the signed budget partition"
            )
        budget_reservation = self.budget.reserve(
            transaction_intent_id=record.transaction_intent_id,
            amount_minor=amount_minor,
            currency=currency,
        )
        try:
            return self.state.reserve_execution(
                record,
                amount_minor=amount_minor,
                currency=currency,
                ceilings_minor=expected,
            )
        except Exception:
            try:
                self.budget.release(
                    budget_reservation.reservation_id,
                    reason="gateway state reservation failed",
                )
            except (BudgetPartitionConflictError, BudgetPartitionUnavailableError):
                pass
            raise

    def settle_execution(
        self, *, expected: ExecutionRecord, updated: ExecutionRecord
    ) -> bool:
        budget_reservation = self._require_budget_reservation(expected)
        if not updated.settlement_id:
            raise BudgetPartitionConflictError("settlement identifier is required")
        self.budget.commit(
            budget_reservation.reservation_id,
            settlement_id=updated.settlement_id,
        )
        return self.state.settle_execution(expected=expected, updated=updated)

    def release_execution(
        self, *, expected: ExecutionRecord, updated: ExecutionRecord, reason: str
    ) -> bool:
        budget_reservation = self._require_budget_reservation(expected)
        released = self.state.release_execution(
            expected=expected, updated=updated, reason=reason
        )
        if released:
            self.budget.release(budget_reservation.reservation_id, reason=reason)
        return released

    def _require_budget_reservation(
        self, execution: ExecutionRecord
    ) -> PartitionReservation:
        reservation = self.budget.reservation_for_intent(
            execution.transaction_intent_id
        )
        if reservation is None:
            raise BudgetPartitionConflictError(
                "execution has no reservation in the signed budget partition"
            )
        return reservation
