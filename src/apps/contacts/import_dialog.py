"""پنجره انتخاب مخاطبین از فایل VCF برای ورود انتخابی."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from src.apps.contacts.vcf import VCardData
from src.core.services.contact_service import (
    DUP_CREATE,
    DUP_MERGE,
    DUP_SKIP,
    VcfPreviewRow,
)

COL_CHECK, COL_NAME, COL_MOBILE, COL_PHONE, COL_EMAIL, COL_ORG, COL_STATUS = range(7)

REASON_FA = {
    "mobile": "موبایل یکسان",
    "phone": "تلفن یکسان",
    "email": "ایمیل یکسان",
    "name_fuzzy": "نام مشابه",
}


class VcfImportDialog(QDialog):
    """نمایش کارت‌های استخراج‌شده از VCF برای انتخاب و تعیین رفتار تکراری‌ها."""

    def __init__(self, rows: list[VcfPreviewRow], parent=None):
        super().__init__(parent)
        self.setWindowTitle("انتخاب مخاطبین برای ورود از VCF")
        self.setMinimumSize(820, 480)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._rows = rows
        self.selected_cards: list[VCardData] = []
        self.duplicate_policy = DUP_SKIP

        layout = QVBoxLayout(self)
        dup_count = sum(1 for r in rows if r.match_id is not None)
        layout.addWidget(
            QLabel(
                f"یافت شد: {len(rows)} مخاطب"
                + (f"  |  احتمالاً تکراری: {dup_count}" if dup_count else "")
            )
        )

        policy_row = QHBoxLayout()
        policy_row.addWidget(QLabel("در صورت تکراری بودن:"))
        self.policy_combo = QComboBox()
        self.policy_combo.addItem("رد کردن (وارد نشود)", DUP_SKIP)
        self.policy_combo.addItem(
            "ادغام با مخاطب موجود (پر کردن فیلدهای خالی)", DUP_MERGE
        )
        self.policy_combo.addItem("ایجاد به‌عنوان مخاطب جدید", DUP_CREATE)
        policy_row.addWidget(self.policy_combo, 1)
        layout.addLayout(policy_row)

        sel_row = QHBoxLayout()
        btn_all = QPushButton("انتخاب همه")
        btn_none = QPushButton("هیچکدام")
        btn_inv = QPushButton("برعکس")
        btn_new = QPushButton("فقط جدیدها")
        btn_all.clicked.connect(lambda: self._set_all(True))
        btn_none.clicked.connect(lambda: self._set_all(False))
        btn_inv.clicked.connect(self._invert)
        btn_new.clicked.connect(self._select_new_only)
        for b in (btn_all, btn_none, btn_inv, btn_new):
            sel_row.addWidget(b)
        sel_row.addStretch()
        layout.addLayout(sel_row)

        self.table = QTableWidget(len(rows), 7)
        self.table.setHorizontalHeaderLabels(
            ["", "نام", "موبایل", "تلفن", "ایمیل", "سازمان", "وضعیت"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(COL_CHECK, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(COL_CHECK, 36)
        header.setSectionResizeMode(COL_NAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_STATUS, QHeaderView.ResizeMode.Stretch)

        self.table.setUpdatesEnabled(False)
        try:
            for i, row in enumerate(rows):
                check = QTableWidgetItem()
                check.setFlags(
                    Qt.ItemFlag.ItemIsUserCheckable
                    | Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                )
                check.setCheckState(
                    Qt.CheckState.Unchecked
                    if row.match_id
                    else Qt.CheckState.Checked
                )
                self.table.setItem(i, COL_CHECK, check)
                self.table.setItem(i, COL_NAME, QTableWidgetItem(row.card.name))
                self.table.setItem(i, COL_MOBILE, QTableWidgetItem(row.card.mobile))
                self.table.setItem(i, COL_PHONE, QTableWidgetItem(row.card.phone))
                self.table.setItem(i, COL_EMAIL, QTableWidgetItem(row.card.email))
                self.table.setItem(i, COL_ORG, QTableWidgetItem(row.card.organization))
                if row.match_id:
                    reason_fa = REASON_FA.get(row.match_reason, row.match_reason)
                    score_txt = (
                        f" ({row.match_score:.0%})"
                        if row.match_reason == "name_fuzzy" and row.match_score
                        else ""
                    )
                    status = (
                        f"تکراری — {reason_fa}{score_txt} → "
                        f"{row.match_name} (شماره {row.match_id})"
                    )
                else:
                    status = "جدید"
                self.table.setItem(i, COL_STATUS, QTableWidgetItem(status))
        finally:
            self.table.setUpdatesEnabled(True)
        layout.addWidget(self.table)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("ورود انتخاب‌شده‌ها")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("انصراف")
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _set_all(self, checked: bool):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for i in range(self.table.rowCount()):
            item = self.table.item(i, COL_CHECK)
            if item:
                item.setCheckState(state)

    def _invert(self):
        for i in range(self.table.rowCount()):
            item = self.table.item(i, COL_CHECK)
            if not item:
                continue
            item.setCheckState(
                Qt.CheckState.Unchecked
                if item.checkState() == Qt.CheckState.Checked
                else Qt.CheckState.Checked
            )

    def _select_new_only(self):
        for i, row in enumerate(self._rows):
            item = self.table.item(i, COL_CHECK)
            if item:
                item.setCheckState(
                    Qt.CheckState.Unchecked
                    if row.match_id
                    else Qt.CheckState.Checked
                )

    def _accept(self):
        self.duplicate_policy = self.policy_combo.currentData()
        selected: list[VCardData] = []
        for i, row in enumerate(self._rows):
            item = self.table.item(i, COL_CHECK)
            if item and item.checkState() == Qt.CheckState.Checked:
                selected.append(row.card)
        if not selected:
            QMessageBox.warning(
                self, "انتخاب لازم است", "حداقل یک مخاطب را برای ورود انتخاب کنید."
            )
            return
        self.selected_cards = selected
        self.accept()
