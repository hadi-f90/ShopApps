"""Accounting & Receipts sub-app (MVS)."""

from datetime import date
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.apps.accounting import accounting_logic as alogic
from src.core.currency import rial_to_toman
from src.core.services.accounting_service import (
    AccountingService,
    AccountingServiceError,
    LocalAccountingService,
    ReceiptLineInput,
)
from src.core.services.contact_service import ContactService, LocalContactService
from src.core.services.inventory_service import InventoryService, LocalInventoryService
from src.core.utils.jalali import gregorian_to_jalali_display, jalali_str_to_gregorian
from src.shared_ui.desktop.widgets.rial_spinbox import make_rial_spinbox


def _toman_label(rial: int) -> str:
    return f"{rial_to_toman(rial):,} تومان"


def _err_text(exc: Exception) -> str:
    return getattr(exc, "message_fa", None) or str(exc)


class ReceiptForm(QDialog):
    def __init__(
        self,
        accounting: AccountingService,
        inventory: InventoryService,
        contacts: ContactService,
        parent=None,
    ):
        super().__init__(parent)
        self.accounting = accounting
        self.inventory = inventory
        self.contacts = contacts
        self._lines: List[dict] = []

        self.setWindowTitle("فاکتور فروش جدید")
        self.setMinimumWidth(720)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.customer_combo = QComboBox()
        self.customer_combo.addItem("— بدون مشتری —", None)
        for c in self.contacts.list_customers():
            label = c.name
            if c.mobile:
                label += f" ({c.mobile})"
            self.customer_combo.addItem(label, c.id)

        self.warehouse_combo = QComboBox()
        for w in self.inventory.list_warehouses():
            self.warehouse_combo.addItem(w.name, w.id)

        form.addRow("مشتری:", self.customer_combo)
        form.addRow("انبار *:", self.warehouse_combo)
        layout.addLayout(form)

        line_row = QHBoxLayout()
        self.item_combo = QComboBox()
        for it in self.inventory.list_items():
            # Show BOTH units, clearly labeled — spin box is Rial-only.
            # Avoid Toman-only in the combo next to a Rial spin (10x risk).
            label = (
                f"{it.name} — "
                f"{it.sale_price:,} ریال "
                f"({_toman_label(it.sale_price)})"
            )
            self.item_combo.addItem(label, it.id)
            self.item_combo.setItemData(
                self.item_combo.count() - 1, it.sale_price, Qt.UserRole + 1
            )

        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 1_000_000)
        self.qty_spin.setValue(1)

        self.price_spin = make_rial_spinbox()
        self.item_combo.currentIndexChanged.connect(self._sync_price)

        add_line_btn = QPushButton("افزودن قلم")
        add_line_btn.clicked.connect(self._add_line)

        line_row.addWidget(QLabel("کالا:"))
        line_row.addWidget(self.item_combo, 2)
        line_row.addWidget(QLabel("تعداد:"))
        line_row.addWidget(self.qty_spin)
        line_row.addWidget(QLabel("قیمت واحد (ریال):"))
        line_row.addWidget(self.price_spin)
        line_row.addWidget(add_line_btn)
        layout.addLayout(line_row)

        hint = QLabel(
            "قیمت قابل ویرایش است (تخفیف موردی). واحد ورودی و ذخیره همیشه ریال است."
        )
        hint.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(hint)

        self.lines_table = QTableWidget(0, 5)
        self.lines_table.setHorizontalHeaderLabels(
            ["کالا", "تعداد", "قیمت واحد (ریال)", "جمع (ریال)", ""]
        )
        self.lines_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.lines_table)

        self.total_label = QLabel("جمع کل: ۰ ریال (۰ تومان)")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 15px;")
        layout.addWidget(self.total_label)

        self.note_edit = QTextEdit()
        self.note_edit.setMaximumHeight(60)
        self.note_edit.setPlaceholderText("یادداشت (اختیاری)")
        layout.addWidget(self.note_edit)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("ثبت فاکتور")
        cancel_btn = QPushButton("انصراف")
        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        if self.item_combo.count():
            self._sync_price()

    def _sync_price(self):
        price = self.item_combo.currentData(Qt.UserRole + 1)
        if price is not None:
            self.price_spin.setValue(int(price))

    def _add_line(self):
        item_id = self.item_combo.currentData()
        if item_id is None:
            QMessageBox.warning(self, "خطا", "کالایی انتخاب نشده")
            return
        name = self.item_combo.currentText().split(" — ")[0]
        qty = self.qty_spin.value()
        unit = int(self.price_spin.value())
        self._lines.append(
            {"item_id": item_id, "name": name, "qty": qty, "unit_price": unit}
        )
        self._refresh_lines_table()

    def _refresh_lines_table(self):
        self.lines_table.setRowCount(0)
        pure = [
            alogic.LineInput(
                item_id=ln["item_id"],
                quantity=ln["qty"],
                unit_price_rial=ln["unit_price"],
            )
            for ln in self._lines
        ]
        total = alogic.receipt_total_rial(pure) if pure else 0
        for i, ln in enumerate(self._lines):
            line_total = alogic.line_total_rial(ln["qty"], ln["unit_price"])
            self.lines_table.insertRow(i)
            self.lines_table.setItem(i, 0, QTableWidgetItem(ln["name"]))
            self.lines_table.setItem(i, 1, QTableWidgetItem(str(ln["qty"])))
            self.lines_table.setItem(i, 2, QTableWidgetItem(f"{ln['unit_price']:,}"))
            self.lines_table.setItem(i, 3, QTableWidgetItem(f"{line_total:,}"))
            rm = QPushButton("حذف")
            rm.clicked.connect(lambda _, idx=i: self._remove_line(idx))
            self.lines_table.setCellWidget(i, 4, rm)
        self.total_label.setText(
            f"جمع کل: {total:,} ریال ({_toman_label(total)})"
        )

    def _remove_line(self, idx: int):
        if 0 <= idx < len(self._lines):
            self._lines.pop(idx)
            self._refresh_lines_table()

    def _save(self):
        if not self._lines:
            QMessageBox.warning(self, "خطا", "حداقل یک قلم اضافه کنید")
            return
        warehouse_id = self.warehouse_combo.currentData()
        if warehouse_id is None:
            QMessageBox.warning(self, "خطا", "انبار را انتخاب کنید")
            return
        customer_id = self.customer_combo.currentData()
        lines = [
            ReceiptLineInput(
                item_id=ln["item_id"],
                quantity=ln["qty"],
                unit_price_rial=ln["unit_price"],
            )
            for ln in self._lines
        ]
        try:
            self.accounting.create_receipt(
                customer_id=customer_id,
                lines=lines,
                warehouse_id=warehouse_id,
                note=self.note_edit.toPlainText(),
            )
        except AccountingServiceError as exc:
            QMessageBox.warning(self, "خطا", _err_text(exc))
            return
        QMessageBox.information(self, "موفق", "فاکتور ثبت شد و موجودی به‌روز شد")
        self.accept()


class PurchaseForm(QDialog):
    def __init__(
        self,
        accounting: AccountingService,
        inventory: InventoryService,
        contacts: ContactService,
        parent=None,
    ):
        super().__init__(parent)
        self.accounting = accounting
        self.inventory = inventory
        self.contacts = contacts
        self.setWindowTitle("ثبت خرید / ورود کالا")
        self.setMinimumWidth(480)

        layout = QFormLayout(self)

        self.vendor_combo = QComboBox()
        self.vendor_combo.addItem("— بدون فروشنده —", None)
        for v in self.contacts.list_vendors():
            label = v.name
            if v.organization:
                label += f" — {v.organization}"
            self.vendor_combo.addItem(label, v.id)

        self.item_combo = QComboBox()
        for it in self.inventory.list_items():
            self.item_combo.addItem(
                f"{it.name} — {it.purchase_price:,} ریال", it.id
            )
            self.item_combo.setItemData(
                self.item_combo.count() - 1, it.purchase_price, Qt.UserRole + 1
            )

        self.warehouse_combo = QComboBox()
        for w in self.inventory.list_warehouses():
            self.warehouse_combo.addItem(w.name, w.id)

        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 1_000_000)
        self.qty_spin.setValue(1)

        self.cost_spin = make_rial_spinbox()
        self.item_combo.currentIndexChanged.connect(self._sync_cost)

        self.note_edit = QTextEdit()
        self.note_edit.setMaximumHeight(60)

        layout.addRow("فروشنده:", self.vendor_combo)
        layout.addRow("کالا *:", self.item_combo)
        layout.addRow("انبار *:", self.warehouse_combo)
        layout.addRow("تعداد *:", self.qty_spin)
        layout.addRow("بهای واحد (ریال) *:", self.cost_spin)
        layout.addRow("یادداشت:", self.note_edit)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("ثبت خرید")
        cancel_btn = QPushButton("انصراف")
        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addRow(btn_row)

        if self.item_combo.count():
            self._sync_cost()

    def _sync_cost(self):
        cost = self.item_combo.currentData(Qt.UserRole + 1)
        if cost is not None:
            self.cost_spin.setValue(int(cost))

    def _save(self):
        item_id = self.item_combo.currentData()
        warehouse_id = self.warehouse_combo.currentData()
        if item_id is None or warehouse_id is None:
            QMessageBox.warning(self, "خطا", "کالا و انبار الزامی است")
            return
        try:
            self.accounting.record_purchase(
                item_id=item_id,
                warehouse_id=warehouse_id,
                quantity=self.qty_spin.value(),
                unit_cost_rial=int(self.cost_spin.value()),
                vendor_contact_id=self.vendor_combo.currentData(),
                note=self.note_edit.toPlainText(),
            )
        except AccountingServiceError as exc:
            QMessageBox.warning(self, "خطا", _err_text(exc))
            return
        QMessageBox.information(self, "موفق", "خرید ثبت شد و موجودی افزایش یافت")
        self.accept()


class AccountingManager(QWidget):
    def __init__(
        self,
        accounting: AccountingService = None,
        inventory: InventoryService = None,
        contacts: ContactService = None,
        parent=None,
    ):
        super().__init__(parent)
        self.accounting = accounting or LocalAccountingService()
        self.inventory = inventory or LocalInventoryService()
        self.contacts = contacts or LocalContactService()

        layout = QVBoxLayout(self)
        title = QLabel("🧾 حسابداری")
        title.setObjectName("page-title")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        self.tabs = QTabWidget()

        receipts_page = QWidget()
        r_layout = QVBoxLayout(receipts_page)
        r_toolbar = QHBoxLayout()
        self.new_receipt_btn = QPushButton("➕ فاکتور جدید")
        self.refresh_receipts_btn = QPushButton("↻ بروزرسانی")
        self.receipt_search = QLineEdit()
        self.receipt_search.setPlaceholderText("جستجو در مشتری / شماره / یادداشت...")
        self.date_from_edit = QLineEdit()
        self.date_from_edit.setPlaceholderText("از تاریخ جلالی YYYY/MM/DD")
        self.date_from_edit.setMaximumWidth(160)
        self.date_to_edit = QLineEdit()
        self.date_to_edit.setPlaceholderText("تا تاریخ جلالی YYYY/MM/DD")
        self.date_to_edit.setMaximumWidth(160)

        self.new_receipt_btn.clicked.connect(self.open_receipt_form)
        self.refresh_receipts_btn.clicked.connect(self.reload_receipts)
        self.receipt_search.textChanged.connect(self.reload_receipts)
        self.date_from_edit.editingFinished.connect(self.reload_receipts)
        self.date_to_edit.editingFinished.connect(self.reload_receipts)

        r_toolbar.addWidget(self.new_receipt_btn)
        r_toolbar.addWidget(self.refresh_receipts_btn)
        r_toolbar.addWidget(self.receipt_search)
        r_toolbar.addWidget(QLabel("از:"))
        r_toolbar.addWidget(self.date_from_edit)
        r_toolbar.addWidget(QLabel("تا:"))
        r_toolbar.addWidget(self.date_to_edit)
        r_layout.addLayout(r_toolbar)

        self.receipts_table = QTableWidget(0, 5)
        self.receipts_table.setHorizontalHeaderLabels(
            ["شماره", "تاریخ (جلالی)", "مشتری", "جمع (ریال)", "تومان"]
        )
        self.receipts_table.horizontalHeader().setStretchLastSection(True)
        r_layout.addWidget(self.receipts_table)
        self.tabs.addTab(receipts_page, "فاکتورها")

        purchases_page = QWidget()
        p_layout = QVBoxLayout(purchases_page)
        p_toolbar = QHBoxLayout()
        self.new_purchase_btn = QPushButton("➕ ثبت خرید")
        self.refresh_purchases_btn = QPushButton("↻ بروزرسانی")
        self.new_purchase_btn.clicked.connect(self.open_purchase_form)
        self.refresh_purchases_btn.clicked.connect(self.reload_purchases)
        p_toolbar.addWidget(self.new_purchase_btn)
        p_toolbar.addWidget(self.refresh_purchases_btn)
        p_toolbar.addStretch()
        p_layout.addLayout(p_toolbar)

        self.purchases_table = QTableWidget(0, 6)
        self.purchases_table.setHorizontalHeaderLabels(
            ["شماره", "تاریخ", "فروشنده", "کالا", "تعداد", "جمع (ریال)"]
        )
        self.purchases_table.horizontalHeader().setStretchLastSection(True)
        p_layout.addWidget(self.purchases_table)
        self.tabs.addTab(purchases_page, "خریدها")

        layout.addWidget(self.tabs)
        self.reload_receipts()
        self.reload_purchases()

    def refresh(self):
        """Called from MainWindow.switch_to_module."""
        self.reload_receipts()
        self.reload_purchases()

    def open_receipt_form(self):
        dialog = ReceiptForm(self.accounting, self.inventory, self.contacts, self)
        if dialog.exec():
            self.reload_receipts()

    def open_purchase_form(self):
        dialog = PurchaseForm(self.accounting, self.inventory, self.contacts, self)
        if dialog.exec():
            self.reload_purchases()

    def _parse_jalali_optional(self, widget: QLineEdit) -> Optional[date]:
        text = widget.text().strip()
        if not text:
            return None
        try:
            return jalali_str_to_gregorian(text)
        except Exception:
            QMessageBox.warning(
                self, "خطا", f"تاریخ نامعتبر: {text}\nفرمت: YYYY/MM/DD جلالی"
            )
            return None

    def reload_receipts(self):
        search = self.receipt_search.text() if hasattr(self, "receipt_search") else ""
        date_from = self._parse_jalali_optional(self.date_from_edit) if hasattr(self, "date_from_edit") else None
        date_to = self._parse_jalali_optional(self.date_to_edit) if hasattr(self, "date_to_edit") else None
        # If parse failed and text non-empty, still show unfiltered to avoid empty UI
        rows = self.accounting.list_receipts(
            search=search, date_from=date_from, date_to=date_to
        )
        self.receipts_table.setRowCount(0)
        for i, r in enumerate(rows):
            self.receipts_table.insertRow(i)
            ts = r.timestamp.date() if r.timestamp else None
            self.receipts_table.setItem(i, 0, QTableWidgetItem(str(r.id)))
            self.receipts_table.setItem(
                i, 1, QTableWidgetItem(gregorian_to_jalali_display(ts))
            )
            self.receipts_table.setItem(i, 2, QTableWidgetItem(r.contact_name or "—"))
            self.receipts_table.setItem(i, 3, QTableWidgetItem(f"{r.total_rial:,}"))
            self.receipts_table.setItem(
                i, 4, QTableWidgetItem(f"{rial_to_toman(r.total_rial):,}")
            )

    def reload_purchases(self):
        rows = self.accounting.list_purchases()
        self.purchases_table.setRowCount(0)
        for i, p in enumerate(rows):
            self.purchases_table.insertRow(i)
            ts = p.timestamp.date() if p.timestamp else None
            self.purchases_table.setItem(i, 0, QTableWidgetItem(str(p.id)))
            self.purchases_table.setItem(
                i, 1, QTableWidgetItem(gregorian_to_jalali_display(ts))
            )
            self.purchases_table.setItem(i, 2, QTableWidgetItem(p.vendor_name or "—"))
            self.purchases_table.setItem(i, 3, QTableWidgetItem(p.item_name))
            self.purchases_table.setItem(i, 4, QTableWidgetItem(str(p.quantity)))
            self.purchases_table.setItem(i, 5, QTableWidgetItem(f"{p.total_rial:,}"))
