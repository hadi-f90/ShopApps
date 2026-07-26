from typing import Optional

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.apps.inventory import inventory_logic as logic
from src.core.services.contact_service import ContactDTO, ContactService, LocalContactService
from src.core.services.inventory_service import (
    InventoryService,
    InventoryServiceError,
    ItemDTO,
    WarehouseDTO,
)

# QSpinBox wraps a 32-bit C int (max ~2.1 billion) — too small for Rial
# amounts, which routinely run into the billions for higher-value office
# equipment (a printer at 45,000,000 Rial is unremarkable). QDoubleSpinBox
# uses a C double internally, so it comfortably holds integer Rial values
# up to ~10^12 with 0 decimal places shown and stored.
MAX_RIAL_AMOUNT = 999_999_999_999


def _rial_spinbox() -> QDoubleSpinBox:
    box = QDoubleSpinBox()
    box.setDecimals(0)
    box.setRange(0, MAX_RIAL_AMOUNT)
    box.setSuffix(" ریال")
    box.setGroupSeparatorShown(True)
    return box


class VendorPickerDialog(QDialog):
    """Search/select a supplier from Contacts filtered to vendors.

    Reads through ContactService only — never imports the Contact model —
    so Inventory doesn't repeat the direct-ORM-import pattern that's
    already flagged as debt in the Contacts sub-app.
    """

    def __init__(self, contact_service: ContactService, parent=None):
        super().__init__(parent)
        self.contact_service = contact_service
        self.selected_vendor: Optional[ContactDTO] = None
        self._vendors: list[ContactDTO] = []

        self.setWindowTitle("انتخاب فروشنده/تامین‌کننده")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("جستجو در نام، موبایل، سازمان...")
        self.search_edit.textChanged.connect(self.reload)
        layout.addWidget(self.search_edit)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        select_btn = QPushButton("انتخاب")
        cancel_btn = QPushButton("انصراف")
        select_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(select_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.reload()

    def reload(self, search_text: str = None):
        query = self.search_edit.text() if search_text is None else search_text
        self._vendors = self.contact_service.list_vendors(search=query)
        self.list_widget.clear()
        for v in self._vendors:
            label = v.name
            if v.organization:
                label += f" — {v.organization}"
            if v.mobile:
                label += f" ({v.mobile})"
            self.list_widget.addItem(label)

    def accept(self):
        row = self.list_widget.currentRow()
        if row < 0:
            QMessageBox.warning(self, "خطا", "یک فروشنده انتخاب کنید")
            return
        self.selected_vendor = self._vendors[row]
        super().accept()


class ItemForm(QDialog):
    def __init__(
        self,
        service: InventoryService,
        parent=None,
        item: ItemDTO = None,
        contact_service: ContactService = None,
    ):
        super().__init__(parent)
        self.service = service
        self.item = item
        self.contact_service = contact_service or LocalContactService()
        self._vendor_contact_id: Optional[int] = None
        self.setWindowTitle("افزودن/ویرایش کالا")
        self.setMinimumWidth(480)

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.brand_edit = QLineEdit()
        self.tags_edit = QLineEdit()

        self.purchase_price_edit = _rial_spinbox()
        self.sale_price_edit = _rial_spinbox()

        self.threshold_edit = QSpinBox()
        self.threshold_edit.setRange(0, 1_000_000)
        self.threshold_edit.setValue(logic.DEFAULT_LOW_STOCK_THRESHOLD)

        # Single "default/preferred supplier" — informational, sourced from
        # Contacts. This is NOT per-purchase vendor history (an item can be
        # bought from several suppliers over time) — that belongs to
        # Accounting's future Purchase records.
        self.vendor_display = QLineEdit()
        self.vendor_display.setReadOnly(True)
        self.vendor_display.setPlaceholderText("فروشنده‌ای انتخاب نشده")
        self.vendor_pick_btn = QPushButton("انتخاب از مخاطبین")
        self.vendor_clear_btn = QPushButton("حذف")
        self.vendor_pick_btn.clicked.connect(self.pick_vendor)
        self.vendor_clear_btn.clicked.connect(self.clear_vendor)

        vendor_row = QWidget()
        vendor_row_layout = QHBoxLayout(vendor_row)
        vendor_row_layout.setContentsMargins(0, 0, 0, 0)
        vendor_row_layout.addWidget(self.vendor_display)
        vendor_row_layout.addWidget(self.vendor_pick_btn)
        vendor_row_layout.addWidget(self.vendor_clear_btn)

        layout.addRow("نام کالا *:", self.name_edit)
        layout.addRow("قیمت خرید:", self.purchase_price_edit)
        layout.addRow("قیمت فروش:", self.sale_price_edit)
        layout.addRow("برند:", self.brand_edit)
        layout.addRow("فروشنده پیش‌فرض:", vendor_row)
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

    def pick_vendor(self):
        dialog = VendorPickerDialog(self.contact_service, self)
        if dialog.exec() and dialog.selected_vendor:
            self._vendor_contact_id = dialog.selected_vendor.id
            self.vendor_display.setText(dialog.selected_vendor.name)

    def clear_vendor(self):
        self._vendor_contact_id = None
        self.vendor_display.clear()

    def load_item(self):
        self.name_edit.setText(self.item.name)
        self.purchase_price_edit.setValue(self.item.purchase_price)
        self.sale_price_edit.setValue(self.item.sale_price)
        self.brand_edit.setText(self.item.brand)
        self.tags_edit.setText(self.item.tags)
        self.threshold_edit.setValue(self.item.low_stock_threshold)
        if self.item.vendor_contact_id:
            self._vendor_contact_id = self.item.vendor_contact_id
            self.vendor_display.setText(self.item.vendor_name)

    def save_item(self):
        try:
            if self.item:
                self.service.update_item(
                    self.item.id,
                    name=self.name_edit.text(),
                    purchase_price=int(self.purchase_price_edit.value()),
                    sale_price=int(self.sale_price_edit.value()),
                    brand=self.brand_edit.text(),
                    vendor_contact_id=self._vendor_contact_id,
                    tags=self.tags_edit.text(),
                    low_stock_threshold=self.threshold_edit.value(),
                )
            else:
                self.service.create_item(
                    name=self.name_edit.text(),
                    purchase_price=int(self.purchase_price_edit.value()),
                    sale_price=int(self.sale_price_edit.value()),
                    brand=self.brand_edit.text(),
                    vendor_contact_id=self._vendor_contact_id,
                    tags=self.tags_edit.text(),
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
