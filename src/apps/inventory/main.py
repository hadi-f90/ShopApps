from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.apps.inventory.forms import ItemForm, StockMovementForm, WarehouseForm
from src.apps.inventory.table_models import ItemsTableModel, WarehousesTableModel
from src.core.services.inventory_service import InventoryService, LocalInventoryService


class ItemsTab(QWidget):
    def __init__(self, service: InventoryService, parent=None):
        super().__init__(parent)
        self.service = service
        layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("جستجو در نام، برند، تگ‌ها...")
        self.search_edit.textChanged.connect(self.reload)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        toolbar = QHBoxLayout()
        self.add_btn = QPushButton("➕ افزودن کالا")
        self.edit_btn = QPushButton("✏️ ویرایش")
        self.movement_btn = QPushButton("🔄 ثبت تراکنش موجودی")
        self.refresh_btn = QPushButton("↻ بروزرسانی")

        self.add_btn.clicked.connect(self.add_item)
        self.edit_btn.clicked.connect(self.edit_item)
        self.movement_btn.clicked.connect(self.open_movement_form)
        self.refresh_btn.clicked.connect(self.reload)

        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.movement_btn)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.model = ItemsTableModel()
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.reload()

    def reload(self, search_text: str = None):
        text = self.search_edit.text() if search_text is None else search_text
        self.model.set_items(self.service.list_items(search=text))

    def _selected_item(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        return self.model.item_at(rows[0].row())

    def add_item(self):
        dialog = ItemForm(self.service, self)
        if dialog.exec():
            self.reload()

    def edit_item(self):
        item = self._selected_item()
        if not item:
            QMessageBox.warning(self, "خطا", "یک کالا انتخاب کنید")
            return
        dialog = ItemForm(self.service, self, item)
        if dialog.exec():
            self.reload()

    def open_movement_form(self):
        dialog = StockMovementForm(self.service, self)
        if dialog.exec():
            self.reload()


class WarehousesTab(QWidget):
    def __init__(self, service: InventoryService, parent=None):
        super().__init__(parent)
        self.service = service
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.add_btn = QPushButton("➕ افزودن انبار")
        self.refresh_btn = QPushButton("↻ بروزرسانی")
        self.add_btn.clicked.connect(self.add_warehouse)
        self.refresh_btn.clicked.connect(self.reload)
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.model = WarehousesTableModel()
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.reload()

    def reload(self):
        self.model.set_warehouses(self.service.list_warehouses())

    def add_warehouse(self):
        dialog = WarehouseForm(self.service, self)
        if dialog.exec():
            self.reload()


class InventoryManager(QWidget):
    """Top-level Inventory sub-app widget."""

    def __init__(self, service: InventoryService = None, parent=None):
        super().__init__(parent)
        self.service = service or LocalInventoryService()

        layout = QVBoxLayout(self)
        title = QLabel("📦 انبار")
        title.setObjectName("page-title")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        self.tabs = QTabWidget()
        self.items_tab = ItemsTab(self.service)
        self.warehouses_tab = WarehousesTab(self.service)
        self.tabs.addTab(self.items_tab, "کالاها")
        self.tabs.addTab(self.warehouses_tab, "انبارها")
        layout.addWidget(self.tabs)
