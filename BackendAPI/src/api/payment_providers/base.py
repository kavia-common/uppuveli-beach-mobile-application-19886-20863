"""Payment provider interface and selector for stubbed implementations.

This module defines a simple interface for payment providers and exposes a
factory for selecting the provider based on a method string.

Currently implemented providers:
- StripeStubProvider
- PayPalStubProvider

These are stubs intended for local development and testing. They DO NOT call
real payment gateways.

Environment variables (via src.api.config.get_settings()):
- STRIPE_KEY: Stripe secret key (optional for stub)
- PAYPAL_KEY: PayPal client secret (optional for stub)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from src.api.config import get_settings


@dataclass
class ChargeResult:
    """Represents the result of a charge attempt from a payment provider stub."""
    ok: bool
    reference: str
    message: str = "ok"


class PaymentProvider(Protocol):
    """Protocol for payment providers."""
    # PUBLIC_INTERFACE
    def charge(self, amount: float) -> ChargeResult:
        """Attempt to charge the given amount and return a ChargeResult."""
        ...


class _BaseProvider(ABC):
    """Base class with helpers shared by stub providers."""

    def _ts_ref(self, prefix: str) -> str:
        """Create a timestamped reference for traceability."""
        return f"{prefix}_{int(datetime.now(timezone.utc).timestamp())}"

    @abstractmethod
    def charge(self, amount: float) -> ChargeResult:
        """Charge an amount and return a ChargeResult."""
        raise NotImplementedError


class StripeStubProvider(_BaseProvider):
    """Stubbed Stripe provider implementation."""

    def charge(self, amount: float) -> ChargeResult:
        if amount <= 0:
            return ChargeResult(ok=False, reference="", message="amount_must_be_positive")
        settings = get_settings()
        # In a real impl, ensure settings.stripe_key is valid and call Stripe API.
        # For stub, we accept the payment and include a stub reference.
        ref = self._ts_ref("stripe_stub" if not settings.stripe_key else "stripe_tx")
        return ChargeResult(ok=True, reference=ref, message="paid")


class PayPalStubProvider(_BaseProvider):
    """Stubbed PayPal provider implementation."""

    def charge(self, amount: float) -> ChargeResult:
        if amount <= 0:
            return ChargeResult(ok=False, reference="", message="amount_must_be_positive")
        settings = get_settings()
        # In a real impl, ensure settings.paypal_key is valid and call PayPal API.
        ref = self._ts_ref("paypal_stub" if not settings.paypal_key else "paypal_tx")
        return ChargeResult(ok=True, reference=ref, message="paid")


# PUBLIC_INTERFACE
def get_payment_provider(method: str) -> PaymentProvider:
    """Return a payment provider instance for the given method.

    Supported methods (case-insensitive):
    - "stripe": StripeStubProvider
    - "paypal": PayPalStubProvider
    - "wallet": special in-app wallet flow handled by routers (no provider)

    Raises:
        ValueError: if the method is unsupported for external providers.
    """
    m = (method or "").strip().lower()
    if m == "stripe":
        return StripeStubProvider()
    if m == "paypal":
        return PayPalStubProvider()
    raise ValueError("unsupported_payment_method")
