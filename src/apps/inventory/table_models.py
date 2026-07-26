from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from src.apps.inventory import inventory_logic as logic
from src.core.services.inventory_service import ItemDTO, WarehouseDTO

ITEM_COLUMNS = [
    ("id", "شناسه"),
    ("name", "نام"),
    ("brand", "برند"),
    ("vendor_name", "فروشنده"),
    ("purchase_price_toman", "قیمت خرید (تومان)"),
    ("sale_price_toman", "قیمت فروش (تومان)"),
    ("on_hand_quantity", "موجودی"),
    ("low_stock_threshold", "آستانه هشدار"),
    ("tags", "تگ‌ها"),
]


class ItemsTableModel(QAbstractTableModel):
    def __init__(self, items=None, parent=None):
        super().__init__(parent)
        self._items: list[ItemDTO] = items or []

    def set_items(self, items: list[ItemDTO]):
        self.beginResetModel()
        self._items = items
        self.endResetModel()

    def item_at(self, row: int) -> ItemDTO:
        return self._items[row]

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def columnCount(self, parent=QModelIndex()):
        return len(ITEM_COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return ITEM_COLUMNS[section][1]
        return None

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        item = self._items[index.row()]
        field, _ = ITEM_COLUMNS[index.column()]

        if role == Qt.DisplayRole:
            if field == "purchase_price_toman":
                return str(logic.rial_to_toman(item.purchase_price))
            if field == "sale_price_toman":
                return str(logic.rial_to_toman(item.sale_price))
            return str(getattr(item, field, ""))

        if role == Qt.BackgroundRole:
            if logic.is_low_stock(item.on_hand_quantity, item.low_stock_threshold):
                return QColor("#fdecea")  # soft red — low-stock warning row

        return None


WAREHOUSE_COLUMNS = [
    ("id", "شناسه"),
    ("name", "نام"),
    ("location", "موقعیت"),
]


class WarehousesTableModel(QAbstractTableModel):
    def __init__(self, warehouses=None, parent=None):
        super().__init__(parent)
        self._warehouses: list[WarehouseDTO] = warehouses or []

    def set_warehouses(self, warehouses: list[WarehouseDTO]):
        self.beginResetModel()
        self._warehouses = warehouses
        self.endResetModel()

    def warehouse_at(self, row: int) -> WarehouseDTO:
        return self._warehouses[row]

    def rowCount(self, parent=QModelIndex()):
        return len(self._warehouses)

    def columnCount(self, parent=QModelIndex()):
        return len(WAREHOUSE_COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return WAREHOUSE_COLUMNS[section][1]
        return None

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        w = self._warehouses[index.row()]
        field, _ = WAREHOUSE_COLUMNS[index.column()]
        if role == Qt.DisplayRole:
            return str(getattr(w, field, "") or "")
        return None
