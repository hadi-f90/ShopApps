"""
Backend service layer for Accounting & Receipts (MVS).

Creates receipts that drive sale stock movements, and purchases that
drive purchase stock movements, exclusively through InventoryService.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import List, Optional, Protocol

from peewee import DoesNotExist

from src.core.db.models import (
    Contact,
    Item,
    Purchase,
    Receipt,
    ReceiptLine,
    Warehouse,
    db,
)
from src.core.services.contact_service import ContactService, LocalContactService
from src.core.services.inventory_service import (
    InventoryService,
    InventoryServiceError,
    LocalInventoryService,
)


class AccountingServiceError(Exception):
    """Domain error surfaced to the UI. Message text is Farsi-facing."""


@dataclass(frozen=True)
class ReceiptLineInput:
    item_id: int
    quantity: int
    unit_price_rial: int


@dataclass(frozen=True)
class ReceiptLineDTO:
    id: Optional[int]
    item_id: int
    item_name: str
    quantity: int
    unit_price_rial: int
    line_total_rial: int


@dataclass(frozen=True)
class ReceiptDTO:
    id: Optional[int]
    contact_id: Optional[int]
    contact_name: str
    timestamp: Optional[datetime]
    total_rial: int
    note: str = ""
    lines: List[ReceiptLineDTO] = field(default_factory=list)


@dataclass(frozen=True)
class PurchaseDTO:
    id: Optional[int]
    vendor_contact_id: Optional[int]
    vendor_name: str
    item_id: int
    item_name: str
    warehouse_id: int
    warehouse_name: str
    quantity: int
    unit_cost_rial: int
    total_rial: int
    timestamp: Optional[datetime]
    note: str = ""


class AccountingService(Protocol):
    def create_receipt(
        self,
        customer_id: Optional[int],
        lines: List[ReceiptLineInput],
        warehouse_id: int,
        note: str = "",
    ) -> ReceiptDTO: ...

    def list_receipts(
        self,
        search: str = "",
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[ReceiptDTO]: ...

    def get_receipt(self, receipt_id: int) -> ReceiptDTO: ...

    def record_purchase(
        self,
        item_id: int,
        warehouse_id: int,
        quantity: int,
        unit_cost_rial: int,
        vendor_contact_id: Optional[int] = None,
        note: str = "",
    ) -> PurchaseDTO: ...

    def list_purchases(self, search: str = "") -> List[PurchaseDTO]: ...

    def today_sales_total_rial(self) -> int: ...


class LocalAccountingService:
    def __init__(
        self,
        inventory_service: InventoryService = None,
        contact_service: ContactService = None,
    ):
        self.inventory = inventory_service or LocalInventoryService()
        self.contacts = contact_service or LocalContactService()

    def _to_receipt_dto(self, r: Receipt, include_lines: bool = True) -> ReceiptDTO:
        contact_name = ""
        if r.contact_id:
            try:
                contact_name = self.contacts.get_contact(r.contact_id).name
            except Exception:
                contact_name = ""
        lines: List[ReceiptLineDTO] = []
        if include_lines:
            for ln in r.lines:
                item_name = ""
                try:
                    item_name = Item.get_by_id(ln.item_id).name
                except DoesNotExist:
                    item_name = f"#{ln.item_id}"
                lines.append(
                    ReceiptLineDTO(
                        id=ln.id,
                        item_id=ln.item_id,
                        item_name=item_name,
                        quantity=ln.quantity,
                        unit_price_rial=ln.unit_price_rial,
                        line_total_rial=ln.line_total_rial,
                    )
                )
        return ReceiptDTO(
            id=r.id,
            contact_id=r.contact_id,
            contact_name=contact_name,
            timestamp=r.timestamp,
            total_rial=r.total_rial,
            note=r.note or "",
            lines=lines,
        )

    def _to_purchase_dto(self, p: Purchase) -> PurchaseDTO:
        vendor_name = ""
        if p.vendor_contact_id:
            try:
                vendor_name = self.contacts.get_contact(p.vendor_contact_id).name
            except Exception:
                pass
        item_name = ""
        warehouse_name = ""
        try:
            item_name = Item.get_by_id(p.item_id).name
        except DoesNotExist:
            item_name = f"#{p.item_id}"
        try:
            warehouse_name = Warehouse.get_by_id(p.warehouse_id).name
        except DoesNotExist:
            warehouse_name = f"#{p.warehouse_id}"
        return PurchaseDTO(
            id=p.id,
            vendor_contact_id=p.vendor_contact_id,
            vendor_name=vendor_name,
            item_id=p.item_id,
            item_name=item_name,
            warehouse_id=p.warehouse_id,
            warehouse_name=warehouse_name,
            quantity=p.quantity,
            unit_cost_rial=p.unit_cost_rial,
            total_rial=p.total_rial,
            timestamp=p.timestamp,
            note=p.note or "",
        )

    def create_receipt(
        self,
        customer_id: Optional[int],
        lines: List[ReceiptLineInput],
        warehouse_id: int,
        note: str = "",
    ) -> ReceiptDTO:
        if not lines:
            raise AccountingServiceError("حداقل یک قلم کالا برای فاکتور لازم است")
        if warehouse_id is None:
            raise AccountingServiceError("انبار الزامی است")

        # Validate customer is marked is_customer when provided
        if customer_id is not None:
            try:
                cust = self.contacts.get_contact(customer_id)
            except Exception:
                raise AccountingServiceError("مشتری انتخاب‌شده معتبر نیست")
            if not cust.is_customer:
                raise AccountingServiceError("مخاطب انتخاب‌شده مشتری نیست")

        for ln in lines:
            if ln.quantity <= 0:
                raise AccountingServiceError("تعداد باید بزرگ‌تر از صفر باشد")
            if ln.unit_price_rial < 0:
                raise AccountingServiceError("قیمت واحد نمی‌تواند منفی باشد")

        total = sum(ln.quantity * ln.unit_price_rial for ln in lines)

        try:
            with db.atomic():
                receipt = Receipt.create(
                    contact=customer_id,
                    total_rial=total,
                    note=note or None,
                )
                for ln in lines:
                    ReceiptLine.create(
                        receipt=receipt.id,
                        item=ln.item_id,
                        quantity=ln.quantity,
                        unit_price_rial=ln.unit_price_rial,
                        line_total_rial=ln.quantity * ln.unit_price_rial,
                    )
                    # sale movement (negative delta)
                    self.inventory.record_movement(
                        item_id=ln.item_id,
                        warehouse_id=warehouse_id,
                        quantity_delta=-ln.quantity,
                        movement_type="sale",
                        reference=f"receipt:{receipt.id}",
                        note=note or "",
                    )
        except InventoryServiceError as exc:
            raise AccountingServiceError(str(exc))
        except Exception as exc:
            raise AccountingServiceError(f"ثبت فاکتور ناموفق بود: {exc}")

        return self._to_receipt_dto(receipt)

    def list_receipts(
        self,
        search: str = "",
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[ReceiptDTO]:
        query = Receipt.select().order_by(Receipt.timestamp.desc())
        if date_from is not None:
            query = query.where(
                Receipt.timestamp >= datetime.combine(date_from, time.min)
            )
        if date_to is not None:
            query = query.where(
                Receipt.timestamp <= datetime.combine(date_to, time.max)
            )
        results = [self._to_receipt_dto(r, include_lines=False) for r in query]
        if search:
            s = search.strip().lower()
            results = [
                r
                for r in results
                if s in (r.contact_name or "").lower()
                or s in str(r.id)
                or s in (r.note or "").lower()
            ]
        return results

    def get_receipt(self, receipt_id: int) -> ReceiptDTO:
        try:
            r = Receipt.get_by_id(receipt_id)
        except DoesNotExist:
            raise AccountingServiceError("فاکتور مورد نظر یافت نشد")
        return self._to_receipt_dto(r, include_lines=True)

    def record_purchase(
        self,
        item_id: int,
        warehouse_id: int,
        quantity: int,
        unit_cost_rial: int,
        vendor_contact_id: Optional[int] = None,
        note: str = "",
    ) -> PurchaseDTO:
        if quantity <= 0:
            raise AccountingServiceError("تعداد باید بزرگ‌تر از صفر باشد")
        if unit_cost_rial < 0:
            raise AccountingServiceError("بهای واحد نمی‌تواند منفی باشد")

        if vendor_contact_id is not None:
            try:
                v = self.contacts.get_contact(vendor_contact_id)
            except Exception:
                raise AccountingServiceError("فروشنده انتخاب‌شده معتبر نیست")
            if not v.is_vendor:
                raise AccountingServiceError("مخاطب انتخاب‌شده فروشنده نیست")

        total = quantity * unit_cost_rial
        try:
            with db.atomic():
                purchase = Purchase.create(
                    vendor_contact=vendor_contact_id,
                    item=item_id,
                    warehouse=warehouse_id,
                    quantity=quantity,
                    unit_cost_rial=unit_cost_rial,
                    total_rial=total,
                    note=note or None,
                )
                self.inventory.record_movement(
                    item_id=item_id,
                    warehouse_id=warehouse_id,
                    quantity_delta=quantity,
                    movement_type="purchase",
                    reference=f"purchase:{purchase.id}",
                    note=note or "",
                )
        except InventoryServiceError as exc:
            raise AccountingServiceError(str(exc))
        except Exception as exc:
            raise AccountingServiceError(f"ثبت خرید ناموفق بود: {exc}")

        return self._to_purchase_dto(purchase)

    def list_purchases(self, search: str = "") -> List[PurchaseDTO]:
        query = Purchase.select().order_by(Purchase.timestamp.desc())
        results = [self._to_purchase_dto(p) for p in query]
        if search:
            s = search.strip().lower()
            results = [
                p
                for p in results
                if s in (p.vendor_name or "").lower()
                or s in (p.item_name or "").lower()
                or s in str(p.id)
            ]
        return results

    def today_sales_total_rial(self) -> int:
        today = date.today()
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)
        total = (
            Receipt.select()
            .where((Receipt.timestamp >= start) & (Receipt.timestamp <= end))
        )
        return sum(r.total_rial for r in total)
