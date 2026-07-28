"""
Shared domain exception hierarchy for ShopApps.

Per .ai_files/coding-conventions.md §3:
- One base class; one subclass per domain.
- Always carries a Farsi message for the UI.
- Service layer is the only place that translates ORM/IntegrityError
  into these types. UI catches ShopAppsError (or a subclass) and shows
  .message_fa — never a raw traceback.

Aliases (*ServiceError) keep existing imports working during the migration.
"""

from __future__ import annotations


class ShopAppsError(Exception):
    """Base for all domain errors. Always carries a Farsi message."""

    def __init__(self, message_fa: str, *, cause: Exception | None = None):
        super().__init__(message_fa)
        self.message_fa = message_fa
        self.cause = cause


class InventoryError(ShopAppsError):
    """Inventory domain errors."""


class InsufficientStockError(InventoryError):
    """Sale/decrease would push on-hand below zero."""


class ContactError(ShopAppsError):
    """Contacts domain errors."""


class ContactInUseError(ContactError):
    """Delete blocked because receipts, purchases, or items still reference this contact."""


class AccountingError(ShopAppsError):
    """Accounting / receipts / purchases domain errors."""


# Backward-compatible aliases (existing UI and tests import these names).
InventoryServiceError = InventoryError
ContactServiceError = ContactError
AccountingServiceError = AccountingError
