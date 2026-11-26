"""Runtime Verifier: independent attestation evaluation and bound receipts."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol

from nexus_sdk.payments.attestation import AttestationResult, AttestationVerifier
from nexus_sdk.payments.execution_plane import ComponentAssurance
from nexus_sdk.payments.key_guardian import RuntimeAuthorizationReceipt
from nexus_sdk.payments.objects import (
    CanonicalTransaction,
    EvaluationState,
    RuntimeMeasurement,
    SettlementFinality,
    canonical_hash,
    utcnow,
)

__all__ = [
    "FinalityFreshnessPolicy",
    "IndependentRuntimeVerifier",
    "RuntimeReceiptIssuer",
    "RuntimeVerificationDecision",
    "RuntimeVerifierProfile",
]


@dataclass(frozen=True)
class FinalityFreshnessPolicy:
    """Reversibility-Aware Freshness Policy for runtime evidence.

    Human name: Reversibility-Aware Freshness Policy.
    Technical name: ``FinalityFreshnessPolicy``.
    """

    reversible_seconds: int = 120
    mediated_seconds: int = 60
    irreversible_seconds: int = 30

    def __post_init__(self) -> None:
        values = (
            self.reversible_seconds,
            self.mediated_seconds,
            self.irreversible_seconds,
        )
        if any(value <= 0 for value in values):
            raise ValueError("freshness ceilings must be positive")
        if not self.reversible_seconds >= self.mediated_seconds >= self.irreversible_seconds:
            raise ValueError(
                "freshness must tighten as settlement becomes less reversible"
            )

    def ceiling_for(self, finality: SettlementFinality) -> int:
        return {
            SettlementFinality.REVERSIBLE: self.reversible_seconds,
            SettlementFinality.MEDIATED: self.mediated_seconds,
            SettlementFinality.IRREVERSIBLE: self.irreversible_seconds,
        }[finality]

    def to_dict(self) -> dict[str, int]:
        return {
            "reversible": self.reversible_seconds,
            "mediated": self.mediated_seconds,
            "irreversible": self.irreversible_seconds,
        }


@dataclass(frozen=True)
class RuntimeVerifierProfile:
    """Immutable identity for verifier code, trust roots, and accepted methods."""

    verifier_id: str
    verifier_version: str
    trust_roots_digest: str
    accepted_methods: frozenset[str]
    allowed_workload_ids: frozenset[str]
    max_measurement_age_seconds: int = 120
    finality_freshness: FinalityFreshnessPolicy = FinalityFreshnessPolicy()

    @property
    def profile_digest(self) -> str:
        return canonical_hash({
            "verifier_id": self.verifier_id,
            "verifier_version": self.verifier_version,
            "trust_roots_digest": self.trust_roots_digest,
            "accepted_methods": sorted(self.accepted_methods),
            "allowed_workload_ids": sorted(self.allowed_workload_ids),
            "max_measurement_age_seconds": self.max_measurement_age_seconds,
            "finality_freshness": self.finality_freshness.to_dict(),
        })


class RuntimeReceiptIssuer(Protocol):
    """Protected proof issuer trusted by Key Guardian."""

    authenticator_id: str
    assurance: ComponentAssurance

    def seal_runtime(self, receipt: RuntimeAuthorizationReceipt) -> str: ...


@dataclass(frozen=True)
class RuntimeVerificationDecision:
    """Inspectable outcome; only accepted results contain a receipt."""

    result: AttestationResult
    profile_digest: str
    receipt: RuntimeAuthorizationReceipt | None = None
    evaluation_state: EvaluationState = EvaluationState.NOT_ESTABLISHED

    @property
    def authorized(self) -> bool:
        return (
            self.evaluation_state is EvaluationState.ESTABLISHED
            and self.result.accepted
            and self.receipt is not None
        )


class IndependentRuntimeVerifier:
    """Attestation-verification and receipt-issuance boundary."""

    human_name = "Runtime Verifier"
    technical_name = "IndependentRuntimeVerifier"
    assurance = ComponentAssurance.REFERENCE

    def __init__(self, *, verifier: AttestationVerifier,
                 profile: RuntimeVerifierProfile,
                 receipt_issuer: RuntimeReceiptIssuer) -> None:
        if (
            not profile.verifier_id
            or not profile.trust_roots_digest
            or not profile.accepted_methods
            or not profile.allowed_workload_ids
            or profile.max_measurement_age_seconds <= 0
            or not receipt_issuer.authenticator_id
        ):
            raise ValueError("complete verifier profile and receipt issuer identity are required")
        if profile.accepted_methods & {"none", "declared"}:
            raise ValueError("unverified attestation methods cannot be accepted")
        self.verifier = verifier
        self.profile = profile
        self.receipt_issuer = receipt_issuer

    def verify(self, canonical: CanonicalTransaction, measurement: RuntimeMeasurement, *,
               expected_baseline: str, now: datetime | None = None) -> RuntimeVerificationDecision:
        verified_at = now or utcnow()
        refusal = self._preflight(canonical, measurement, expected_baseline, verified_at)
        if refusal is not None:
            return RuntimeVerificationDecision(refusal, self.profile.profile_digest)
        result = self.verifier.verify(
            measurement,
            expected_baseline=expected_baseline,
            now=verified_at,
        )
        if not result.accepted:
            return RuntimeVerificationDecision(
                result,
                self.profile.profile_digest,
                evaluation_state=EvaluationState.DENIED,
            )
        receipt = RuntimeAuthorizationReceipt(
            runtime_measurement_id=measurement.runtime_measurement_id,
            canonical_digest=canonical.canonical_digest,
            signing_digest=canonical.signing_digest(),
            verifier_id=self.profile.verifier_id,
            accepted=True,
            verified_at=verified_at.isoformat(),
            authenticator_id=self.receipt_issuer.authenticator_id,
            proof="",
            verifier_profile_digest=self.profile.profile_digest,
            settlement_finality=canonical.finality.value,
            freshness_ceiling_seconds=self._freshness_ceiling(canonical, measurement),
        )
        receipt = replace(receipt, proof=self.receipt_issuer.seal_runtime(receipt))
        if not receipt.proof:
            raise RuntimeError("runtime receipt issuer returned no proof")
        return RuntimeVerificationDecision(
            result,
            self.profile.profile_digest,
            receipt,
            EvaluationState.ESTABLISHED,
        )

    def _preflight(self, canonical: CanonicalTransaction,
                   measurement: RuntimeMeasurement,
                   expected_baseline: str,
                   now: datetime) -> AttestationResult | None:
        reason = ""
        if measurement.runtime_measurement_id != canonical.runtime_measurement_id:
            reason = "runtime measurement identity does not match canonical transaction"
        elif not expected_baseline or measurement.baseline_digest() != expected_baseline:
            reason = "runtime baseline is missing or does not match"
        elif measurement.attestation_method not in self.profile.accepted_methods:
            reason = "attestation method is not permitted by the verifier profile"
        elif not measurement.attested or not measurement.workload_id:
            reason = "attested workload identity is missing"
        elif measurement.workload_id not in self.profile.allowed_workload_ids:
            reason = "workload identity is not permitted by the verifier profile"
        elif not measurement.verifier_challenge:
            reason = "fresh verifier challenge is required"
        elif not 0 <= measurement.age_seconds(now) <= self._freshness_ceiling(
            canonical, measurement
        ):
            reason = "runtime measurement is stale"
        elif measurement.policy_id and measurement.policy_id != canonical.policy_id:
            reason = "runtime measurement policy does not match canonical transaction"
        if reason:
            return AttestationResult(False, reason, self.profile.verifier_id)
        return None

    def _freshness_ceiling(
        self,
        canonical: CanonicalTransaction,
        measurement: RuntimeMeasurement,
    ) -> int:
        return min(
            measurement.max_age_seconds,
            self.profile.max_measurement_age_seconds,
            self.profile.finality_freshness.ceiling_for(canonical.finality),
        )
