from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QDateEdit,
)

from src.apps.inventory import inventory_logic as logic
from src.core.services.inventory_service import (
    InventoryService,
    InventoryServiceError,
    ItemDTO,
    WarehouseDTO,
)


class ItemForm(QDialog):
    def __init__(self, service: InventoryService, parent=None, item: ItemDTO = None):
        super().__init__(parent)
        self.service = service
        self.item = item
        self.setWindowTitle("افزودن/ویرایش کالا")
        self.setMinimumWidth(480)

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.brand_edit = QLineEdit()
        self.vendor_edit = QLineEdit()
        self.tags_edit = QLineEdit()
        self.expiration = QDateEdit(),

        self.purchase_price_edit = QSpinBox()
        self.purchase_price_edit.setRange(0, 10_000_000_000)
        self.purchase_price_edit.setSuffix(" ریال")

        self.sale_price_edit = QSpinBox()
        self.sale_price_edit.setRange(0, 10_000_000_000)
        self.sale_price_edit.setSuffix(" ریال")

        self.threshold_edit = QSpinBox()
        self.threshold_edit.setRange(0, 1_000_000)
        self.threshold_edit.setValue(logic.DEFAULT_LOW_STOCK_THRESHOLD)

        layout.addRow("نام کالا *:", self.name_edit)
        layout.addRow("قیمت خرید:", self.purchase_price_edit)
        layout.addRow("قیمت فروش:", self.sale_price_edit)
        layout.addRow("برند:", self.brand_edit)
        layout.addRow("فروشنده/تامین‌کننده:", self.vendor_edit)
        layout.addRow("تاریخ انقضاء:", self.expiration)
        layout.addRow("تگ‌ها:", self.tags_edit)
        layout.addRow("آستانه هشدار موجودی کم:", self.threshold_edit)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("ذخیره")
        cancel_btn = QPushButton("انصراف")
        save_btn.clicked.connect(self.save_item)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

        if self.item:
            self.load_item()

    def load_item(self):
        self.name_edit.setText(self.item.name)
        self.purchase_price_edit.setValue(self.item.purchase_price)
        self.sale_price_edit.setValue(self.item.sale_price)
        self.brand_edit.setText(self.item.brand)
        self.vendor_edit.setText(self.item.vendor)
        self.tags_edit.setText(self.item.tags)
        self.expiration.setText(self.item.expiration)
        self.threshold_edit.setValue(self.item.low_stock_threshold)

    def save_item(self):
        try:
            if self.item:
                self.service.update_item(
                    self.item.id,
                    name=self.name_edit.text(),
                    purchase_price=self.purchase_price_edit.value(),
                    sale_price=self.sale_price_edit.value(),
                    brand=self.brand_edit.text(),
                    vendor=self.vendor_edit.text(),
                    tags=self.tags_edit.text(),
                    expiration=self.expiration.Text(),
                    low_stock_threshold=self.threshold_edit.value(),
                )
            else:
                self.service.create_item(
                    name=self.name_edit.text(),
                    purchase_price=self.purchase_price_edit.value(),
                    sale_price=self.sale_price_edit.value(),
                    brand=self.brand_edit.text(),
                    vendor=self.vendor_edit.text(),
                    tags=self.tags_edit.text(),
                    expiration=self.expiration.Text(),#Todo expiration date
                    low_stock_threshold=self.threshold_edit.value(),
                )
        except InventoryServiceError as exc:
            QMessageBox.warning(self, "خطا", str(exc))
            return
        self.accept()


class WarehouseForm(QDialog):
    def __init__(self, service: InventoryService, parent=None, warehouse: WarehouseDTO = None):
        super().__init__(parent)
        self.service = service
        self.warehouse = warehouse
        self.setWindowTitle("افزودن/ویرایش انبار")
        self.setMinimumWidth(400)

        layout = QFormLayout(self)
        self.name_edit = QLineEdit()
        self.location_edit = QLineEdit()
        layout.addRow("نام انبار *:", self.name_edit)
        layout.addRow("موقعیت:", self.location_edit)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("ذخیره")
        cancel_btn = QPushButton("انصراف")
        save_btn.clicked.connect(self.save_warehouse)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

        if self.warehouse:
            self.name_edit.setText(self.warehouse.name)
            self.location_edit.setText(self.warehouse.location)

    def save_warehouse(self):
        try:
            self.service.create_warehouse(
                name=self.name_edit.text(),
                location=self.location_edit.text(),
            )
        except InventoryServiceError as exc:
            QMessageBox.warning(self, "خطا", str(exc))
            return
        self.accept()


class StockMovementForm(QDialog):
    """Covers internal_consumption, spoilage, manual_adjustment (+/-), and
    manual entry of purchase/sale for cases outside a formal Accounting flow
    (Accounting itself calls InventoryService.record_movement directly for
    receipts and purchases — see inventory-mvs-spec.md, 'Stock Movements')."""

    MOVEMENT_LABELS = {
        "purchase": "خرید (ورود دستی)",
        "sale": "فروش (ورود دستی)",
        "internal_consumption": "مصرف داخلی",
        "spoilage": "ضایعات",
        "manual_adjustment": "اصلاح دستی (شمارش انبار)",
    }

    def __init__(self, service: InventoryService, parent=None):
        super().__init__(parent)
        self.service = service
        self.setWindowTitle("ثبت تراکنش موجودی")
        self.setMinimumWidth(480)

        layout = QFormLayout(self)

        self.item_combo = QComboBox()
        self.warehouse_combo = QComboBox()
        self.movement_type_combo = QComboBox()
        for mt in logic.MOVEMENT_TYPES:
            self.movement_type_combo.addItem(self.MOVEMENT_LABELS[mt], mt)

        self.quantity_edit = QSpinBox()
        self.quantity_edit.setRange(-1_000_000, 1_000_000)
        self.quantity_edit.setValue(1)

        self.note_edit = QTextEdit()

        self._populate_combos()

        layout.addRow("کالا *:", self.item_combo)
        layout.addRow("انبار *:", self.warehouse_combo)
        layout.addRow("نوع تراکنش *:", self.movement_type_combo)
        layout.addRow("مقدار (+/-):", self.quantity_edit)
        layout.addRow("یادداشت:", self.note_edit)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("ثبت")
        cancel_btn = QPushButton("انصراف")
        save_btn.clicked.connect(self.save_movement)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def _populate_combos(self):
        for item in self.service.list_items():
            self.item_combo.addItem(item.name, item.id)
        for w in self.service.list_warehouses():
            self.warehouse_combo.addItem(w.name, w.id)

    def save_movement(self):
        item_id = self.item_combo.currentData()
        warehouse_id = self.warehouse_combo.currentData()
        movement_type = self.movement_type_combo.currentData()
        quantity = self.quantity_edit.value()

        if item_id is None or warehouse_id is None:
            QMessageBox.warning(self, "خطا", "ابتدا یک کالا و انبار تعریف کنید")
            return

        try:
            self.service.record_movement(
                item_id=item_id,
                warehouse_id=warehouse_id,
                quantity_delta=quantity,
                movement_type=movement_type,
                note=self.note_edit.toPlainText(),
            )
        except InventoryServiceError as exc:
            QMessageBox.warning(self, "خطا", str(exc))
            return
        self.accept()
