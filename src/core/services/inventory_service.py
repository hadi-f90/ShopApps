"""
Backend service layer for Inventory.

Wires App Logic (inventory_logic) to Peewee models and exposes a narrow
Protocol so UI and other sub-apps never import ORM models directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Protocol

from peewee import DoesNotExist, IntegrityError

from src.apps.inventory import inventory_logic as logic
from src.core.db.models import Item, StockMovement, Warehouse, db
from src.core.errors import InventoryServiceError, InsufficientStockError
from src.core.services.contact_service import ContactService, LocalContactService


@dataclass(frozen=True)
class WarehouseDTO:
    id: Optional[int]
    name: str
    location: str = ""
    is_active: bool = True


@dataclass(frozen=True)
class ItemDTO:
    id: Optional[int]
    name: str
    purchase_price: int  # Rial
    sale_price: int  # Rial
    brand: str = ""
    vendor_contact_id: Optional[int] = None
    vendor_name: str = ""
    tags: str = ""
    low_stock_threshold: int = logic.DEFAULT_LOW_STOCK_THRESHOLD
    is_active: bool = True
    on_hand_quantity: int = 0


@dataclass(frozen=True)
class StockMovementDTO:
    id: Optional[int]
    item_id: int
    warehouse_id: int
    quantity_delta: int
    movement_type: str
    timestamp: Optional[datetime] = None
    reference: str = ""
    note: str = ""


class InventoryService(Protocol):
    def create_warehouse(self, name: str, location: str = "") -> WarehouseDTO: ...

    def list_warehouses(self) -> List[WarehouseDTO]: ...

    def create_item(
        self,
        name: str,
        purchase_price: int,
        sale_price: int,
        brand: str = "",
        vendor_contact_id: Optional[int] = None,
        tags: str = "",
        low_stock_threshold: int = logic.DEFAULT_LOW_STOCK_THRESHOLD,
    ) -> ItemDTO: ...

    def update_item(self, item_id: int, **fields) -> ItemDTO: ...

    def list_items(self, search: str = "") -> List[ItemDTO]: ...

    def get_item(self, item_id: int) -> ItemDTO: ...

    def record_movement(
        self,
        item_id: int,
        warehouse_id: int,
        quantity_delta: int,
        movement_type: str,
        reference: str = "",
        note: str = "",
    ) -> StockMovementDTO: ...

    def get_on_hand_quantity(
        self, item_id: int, warehouse_id: Optional[int] = None
    ) -> int: ...

    def get_low_stock_items(self) -> List[ItemDTO]: ...


class LocalInventoryService:
    """Direct in-process Peewee-backed implementation of InventoryService."""

    def __init__(self, contact_service: ContactService = None):
        self.contact_service = contact_service or LocalContactService()

    def _to_warehouse_dto(self, w: Warehouse) -> WarehouseDTO:
        return WarehouseDTO(
            id=w.id, name=w.name, location=w.location or "", is_active=w.is_active
        )

    def _to_item_dto(self, item: Item) -> ItemDTO:
        vendor_name = ""
        if item.vendor_contact_id:
            try:
                vendor_name = self.contact_service.get_contact(item.vendor_contact_id).name
            except Exception:
                vendor_name = ""
        return ItemDTO(
            id=item.id,
            name=item.name,
            purchase_price=item.purchase_price,
            sale_price=item.sale_price,
            brand=item.brand or "",
            vendor_contact_id=item.vendor_contact_id,
            vendor_name=vendor_name,
            tags=item.tags or "",
            low_stock_threshold=item.low_stock_threshold,
            is_active=item.is_active,
            on_hand_quantity=self.get_on_hand_quantity(item.id),
        )

    def _to_movement_dto(self, m: StockMovement) -> StockMovementDTO:
        return StockMovementDTO(
            id=m.id,
            item_id=m.item_id,
            warehouse_id=m.warehouse_id,
            quantity_delta=m.quantity_delta,
            movement_type=m.movement_type,
            timestamp=m.timestamp,
            reference=m.reference or "",
            note=m.note or "",
        )

    def create_warehouse(self, name: str, location: str = "") -> WarehouseDTO:
        errors = logic.validate_warehouse_fields(name)
        if errors:
            raise InventoryServiceError("؛ ".join(errors))
        try:
            w = Warehouse.create(name=name.strip(), location=location or None)
        except IntegrityError:
            raise InventoryServiceError("انباری با این نام از قبل وجود دارد")
        return self._to_warehouse_dto(w)

    def list_warehouses(self) -> List[WarehouseDTO]:
        return [
            self._to_warehouse_dto(w) for w in Warehouse.select().order_by(Warehouse.name)
        ]

    def create_item(
        self,
        name: str,
        purchase_price: int,
        sale_price: int,
        brand: str = "",
        vendor_contact_id: Optional[int] = None,
        tags: str = "",
        low_stock_threshold: int = logic.DEFAULT_LOW_STOCK_THRESHOLD,
    ) -> ItemDTO:
        errors = logic.validate_item_fields(
            name, purchase_price, sale_price, low_stock_threshold
        )
        if errors:
            raise InventoryServiceError("؛ ".join(errors))
        try:
            item = Item.create(
                name=name.strip(),
                purchase_price=purchase_price,
                sale_price=sale_price,
                brand=brand or None,
                vendor_contact=vendor_contact_id,
                tags=tags or None,
                low_stock_threshold=low_stock_threshold,
            )
        except IntegrityError as exc:
            # Only the vendor FK is a realistic IntegrityError on Item today;
            # still avoid a blanket "invalid vendor" for future constraints.
            msg = str(exc).lower()
            if "vendor" in msg or "foreign" in msg or "contact" in msg:
                raise InventoryServiceError("فروشنده انتخاب‌شده معتبر نیست", cause=exc)
            raise InventoryServiceError(f"ثبت کالا ناموفق بود: {exc}", cause=exc)
        return self._to_item_dto(item)

    def update_item(self, item_id: int, **fields) -> ItemDTO:
        try:
            item = Item.get_by_id(item_id)
        except Item.DoesNotExist:
            raise InventoryServiceError("کالای مورد نظر یافت نشد")

        name = fields.get("name", item.name)
        purchase_price = fields.get("purchase_price", item.purchase_price)
        sale_price = fields.get("sale_price", item.sale_price)
        low_stock_threshold = fields.get("low_stock_threshold", item.low_stock_threshold)

        errors = logic.validate_item_fields(
            name, purchase_price, sale_price, low_stock_threshold
        )
        if errors:
            raise InventoryServiceError("؛ ".join(errors))

        for field_name in (
            "name",
            "purchase_price",
            "sale_price",
            "brand",
            "vendor_contact_id",
            "tags",
            "low_stock_threshold",
            "is_active",
        ):
            if field_name in fields:
                setattr(item, field_name, fields[field_name])
        try:
            item.save()
        except IntegrityError as exc:
            msg = str(exc).lower()
            if "vendor" in msg or "foreign" in msg or "contact" in msg:
                raise InventoryServiceError("فروشنده انتخاب‌شده معتبر نیست", cause=exc)
            raise InventoryServiceError(f"به‌روزرسانی کالا ناموفق بود: {exc}", cause=exc)
        return self._to_item_dto(item)

    def list_items(self, search: str = "") -> List[ItemDTO]:
        query = Item.select()
        if search:
            query = query.where(
                Item.name.contains(search)
                | Item.tags.contains(search)
                | Item.brand.contains(search)
            )
        return [self._to_item_dto(i) for i in query.order_by(Item.name)]

    def get_item(self, item_id: int) -> ItemDTO:
        try:
            item = Item.get_by_id(item_id)
        except Item.DoesNotExist:
            raise InventoryServiceError("کالای مورد نظر یافت نشد")
        return self._to_item_dto(item)

    def record_movement(
        self,
        item_id: int,
        warehouse_id: int,
        quantity_delta: int,
        movement_type: str,
        reference: str = "",
        note: str = "",
    ) -> StockMovementDTO:
        try:
            logic.validate_movement_sign(movement_type, quantity_delta)
        except logic.InventoryLogicError as exc:
            raise InventoryServiceError(str(exc), cause=exc)

        if quantity_delta < 0:
            on_hand = self.get_on_hand_quantity(item_id, warehouse_id)
            try:
                logic.validate_sale_does_not_exceed_stock(on_hand, quantity_delta)
            except logic.InventoryLogicError as exc:
                raise InsufficientStockError(str(exc), cause=exc)

        with db.atomic():
            try:
                movement = StockMovement.create(
                    item=item_id,
                    warehouse=warehouse_id,
                    quantity_delta=quantity_delta,
                    movement_type=movement_type,
                    reference=reference or None,
                    note=note or None,
                )
            except IntegrityError as exc:
                raise InventoryServiceError(
                    "ثبت تراکنش ناموفق بود: کالا یا انبار مورد نظر معتبر نیست",
                    cause=exc,
                )
        return self._to_movement_dto(movement)

    def get_on_hand_quantity(
        self, item_id: int, warehouse_id: Optional[int] = None
    ) -> int:
        query = StockMovement.select().where(StockMovement.item == item_id)
        if warehouse_id is not None:
            query = query.where(StockMovement.warehouse == warehouse_id)
        return logic.compute_on_hand_quantity(m.quantity_delta for m in query)

    def get_low_stock_items(self) -> List[ItemDTO]:
        candidates = (
            self._to_item_dto(i)
            for i in Item.select().where(Item.is_active == True)  # noqa: E712
        )
        return [
            dto
            for dto in candidates
            if logic.is_low_stock(dto.on_hand_quantity, dto.low_stock_threshold)
        ]
