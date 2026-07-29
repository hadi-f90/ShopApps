from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.apps.contacts.forms import ContactForm
from src.core.services.contact_service import (
    ContactService,
    ContactServiceError,
    LocalContactService,
)

# Page size keeps QTableWidget responsive for large imports (VCF).
# Full Model/View + DB offset is Phase 2 if lists grow into tens of thousands.
PAGE_SIZE = 100

# Column indices
COL_ID, COL_NAME, COL_PHONE, COL_MOBILE, COL_EMAIL, COL_ORG = range(6)
COL_CUSTOMER, COL_VENDOR, COL_TAGS, COL_TASKS = 6, 7, 8, 9


def _err(exc: Exception) -> str:
    return getattr(exc, "message_fa", None) or str(exc)


class ContactsManager(QWidget):
    def __init__(self, service: ContactService = None, parent=None):
        super().__init__(parent)
        self.service = service or LocalContactService()
        self._page = 0
        self._all_filtered = []  # ContactDTO cache for current search
        layout = QVBoxLayout(self)

        title = QLabel("👥 مخاطبین")
        title.setObjectName("page-title")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("جستجو در نام، موبایل، سازمان...")
        self.search_edit.textChanged.connect(self.filter_contacts)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        toolbar = QHBoxLayout()
        self.add_btn = QPushButton("➕ افزودن مخاطب")
        self.edit_btn = QPushButton("✏️ ویرایش")
        self.delete_btn = QPushButton("🗑️ حذف")
        self.import_btn = QPushButton("📥 ورود VCF")
        self.export_btn = QPushButton("📤 خروجی VCF")
        self.refresh_btn = QPushButton("🔄 بروزرسانی")

        self.add_btn.clicked.connect(self.add_contact)
        self.edit_btn.clicked.connect(self.edit_contact)
        self.delete_btn.clicked.connect(self.delete_contacts)
        self.import_btn.clicked.connect(self.import_vcf)
        self.export_btn.clicked.connect(self.export_vcf)
        self.refresh_btn.clicked.connect(lambda: self.load_data(reset_page=True))

        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addWidget(self.import_btn)
        toolbar.addWidget(self.export_btn)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "نام",
                "تلفن ثابت",
                "موبایل",
                "ایمیل",
                "سازمان",
                "مشتری",
                "فروشنده",
                "تگ‌ها",
                "تسک‌ها",
            ]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self._apply_column_widths()
        layout.addWidget(self.table)

        pager = QHBoxLayout()
        self.prev_btn = QPushButton("▶ قبلی")
        self.next_btn = QPushButton("بعدی ◀")
        self.page_label = QLabel("")
        self.prev_btn.clicked.connect(self._prev_page)
        self.next_btn.clicked.connect(self._next_page)
        pager.addWidget(self.prev_btn)
        pager.addWidget(self.page_label)
        pager.addWidget(self.next_btn)
        pager.addStretch()
        layout.addLayout(pager)

        self.load_data(reset_page=True)

    def _apply_column_widths(self):
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        # Fixed narrow columns
        header.setSectionResizeMode(COL_ID, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(COL_ID, 48)
        header.setSectionResizeMode(COL_CUSTOMER, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(COL_CUSTOMER, 52)
        header.setSectionResizeMode(COL_VENDOR, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(COL_VENDOR, 58)
        # Stretch name, tags, tasks
        header.setSectionResizeMode(COL_NAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_TAGS, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_TASKS, QHeaderView.ResizeMode.Stretch)
        # Moderate defaults for the rest
        for col, width in (
            (COL_PHONE, 100),
            (COL_MOBILE, 110),
            (COL_EMAIL, 140),
            (COL_ORG, 120),
        ):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
            self.table.setColumnWidth(col, width)

    def load_data(self, filter_text: str = "", *, reset_page: bool = False):
        if reset_page:
            self._page = 0
        text = filter_text if filter_text else self.search_edit.text()
        self._all_filtered = list(self.service.list_contacts(search=text))
        self._render_page()

    def _render_page(self):
        total = len(self._all_filtered)
        pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE) if total else 1
        if self._page >= pages:
            self._page = max(0, pages - 1)
        start = self._page * PAGE_SIZE
        chunk = self._all_filtered[start : start + PAGE_SIZE]

        self.table.setRowCount(0)
        self.table.setUpdatesEnabled(False)
        try:
            for row, c in enumerate(chunk):
                self.table.insertRow(row)
                id_item = QTableWidgetItem(str(c.id))
                id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, COL_ID, id_item)
                self.table.setItem(row, COL_NAME, QTableWidgetItem(c.name))
                self.table.setItem(row, COL_PHONE, QTableWidgetItem(c.phone))
                self.table.setItem(row, COL_MOBILE, QTableWidgetItem(c.mobile))
                self.table.setItem(row, COL_EMAIL, QTableWidgetItem(c.email))
                self.table.setItem(row, COL_ORG, QTableWidgetItem(c.organization))
                cust = QTableWidgetItem("✓" if c.is_customer else "")
                cust.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, COL_CUSTOMER, cust)
                vend = QTableWidgetItem("✓" if c.is_vendor else "")
                vend.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, COL_VENDOR, vend)
                self.table.setItem(row, COL_TAGS, QTableWidgetItem(c.tags or ""))
                self.table.setItem(row, COL_TASKS, QTableWidgetItem(c.tasks or ""))
        finally:
            self.table.setUpdatesEnabled(True)

        shown_from = start + 1 if total else 0
        shown_to = min(start + PAGE_SIZE, total)
        self.page_label.setText(
            f"{shown_from}–{shown_to} از {total}  |  صفحه {self._page + 1} / {pages}"
        )
        self.prev_btn.setEnabled(self._page > 0)
        self.next_btn.setEnabled(self._page < pages - 1)

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._render_page()

    def _next_page(self):
        self._page += 1
        self._render_page()

    def filter_contacts(self, text: str):
        self.load_data(text, reset_page=True)

    def _selected_ids(self) -> list[int]:
        rows = {idx.row() for idx in self.table.selectedIndexes()}
        ids: list[int] = []
        for row in sorted(rows):
            item = self.table.item(row, COL_ID)
            if item:
                ids.append(int(item.text()))
        return ids

    def add_contact(self):
        dialog = ContactForm(self, service=self.service)
        if dialog.exec():
            self.load_data(reset_page=True)

    def edit_contact(self):
        ids = self._selected_ids()
        if not ids:
            QMessageBox.warning(self, "خطا", "یک مخاطب انتخاب کنید")
            return
        if len(ids) > 1:
            QMessageBox.information(
                self,
                "ویرایش",
                "برای ویرایش فقط یک ردیف را انتخاب کنید (حذف می‌تواند چندتایی باشد).",
            )
            return
        try:
            contact = self.service.get_contact(ids[0])
        except ContactServiceError as exc:
            QMessageBox.warning(self, "خطا", _err(exc))
            return
        dialog = ContactForm(self, contact=contact, service=self.service)
        if dialog.exec():
            self.load_data()

    def delete_contacts(self):
        ids = self._selected_ids()
        if not ids:
            QMessageBox.warning(self, "خطا", "حداقل یک مخاطب انتخاب کنید")
            return
        n = len(ids)
        prompt = (
            f"آیا از حذف {n} مخاطب انتخاب‌شده مطمئن هستید؟"
            if n > 1
            else "آیا از حذف این مخاطب مطمئن هستید؟"
        )
        if QMessageBox.question(self, "تایید حذف", prompt) != QMessageBox.Yes:
            return

        failed: list[str] = []
        deleted = 0
        for cid in ids:
            try:
                self.service.delete_contact(cid)
                deleted += 1
            except ContactServiceError as exc:
                failed.append(f"#{cid}: {_err(exc)}")

        if failed:
            QMessageBox.warning(
                self,
                "حذف ناقص",
                f"حذف شد: {deleted}\nناموفق:\n" + "\n".join(failed[:12])
                + (f"\n… و {len(failed) - 12} مورد دیگر" if len(failed) > 12 else ""),
            )
        self.load_data()

    def import_vcf(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "ورود از فایل VCF",
            "",
            "vCard (*.vcf *.vcard);;All files (*)",
        )
        if not path:
            return
        try:
            report = self.service.import_vcf(path)
        except ContactServiceError as exc:
            QMessageBox.warning(self, "خطا", _err(exc))
            return
        msg = f"وارد شد: {report.created}"
        if report.skipped:
            msg += f"\nرد شد (بدون نام یا نامعتبر): {report.skipped}"
        if report.errors:
            msg += "\n" + "\n".join(report.errors)
        QMessageBox.information(self, "ورود VCF", msg)
        self.load_data(reset_page=True)

    def export_vcf(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "خروجی VCF",
            "contacts.vcf",
            "vCard (*.vcf);;All files (*)",
        )
        if not path:
            return
        if not path.lower().endswith(".vcf"):
            path += ".vcf"
        try:
            # Export selection if any, otherwise all
            ids = self._selected_ids() or None
            text = self.service.export_vcf(ids)
            Path(path).write_text(text, encoding="utf-8")
        except ContactServiceError as exc:
            QMessageBox.warning(self, "خطا", _err(exc))
            return
        except OSError as exc:
            QMessageBox.warning(self, "خطا", f"ذخیره فایل ممکن نشد: {exc}")
            return
        QMessageBox.information(self, "خروجی VCF", f"ذخیره شد:\n{path}")

    def refresh(self):
        """Called from MainWindow.switch_to_module after navigation."""
        self.load_data()
