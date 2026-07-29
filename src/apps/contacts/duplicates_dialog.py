"""یافتن و ادغام مخاطبین تکراری موجود در پایگاه داده."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from src.core.services.contact_service import ContactDTO, ContactService, ContactServiceError


def _err(exc: Exception) -> str:
    return getattr(exc, "message_fa", None) or str(exc)


class DuplicatesDialog(QDialog):
    """نمایش گروه‌های تکراری؛ امکان ادغام گروه در یک مخاطب نگهداشته‌شده."""

    def __init__(self, service: ContactService, parent=None):
        super().__init__(parent)
        self.service = service
        self.setWindowTitle("یافتن مخاطبین تکراری")
        self.setMinimumSize(720, 440)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._groups: list[list[ContactDTO]] = []

        layout = QVBoxLayout(self)
        self.summary = QLabel("در حال بررسی...")
        layout.addWidget(self.summary)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(
            ["نام", "موبایل", "تلفن", "ایمیل", "سازمان", "شناسه"]
        )
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setAlternatingRowColors(True)
        layout.addWidget(self.tree)

        actions = QHBoxLayout()
        self.merge_btn = QPushButton("ادغام گروه انتخاب‌شده")
        self.refresh_btn = QPushButton("بررسی دوباره")
        self.merge_btn.clicked.connect(self._merge_selected_group)
        self.refresh_btn.clicked.connect(self.reload)
        actions.addWidget(self.merge_btn)
        actions.addWidget(self.refresh_btn)
        actions.addStretch()
        layout.addLayout(actions)

        hint = QLabel(
            "روی یک ردیف داخل گروه کلیک کنید (مخاطبی که نگه داشته می‌شود). "
            "سایر اعضای گروه در آن ادغام و سپس حذف می‌شوند — "
            "اگر مخاطبی در فاکتور/خرید استفاده شده باشد حذف نمی‌شود."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("بستن")
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        self.reload()

    def reload(self):
        self.tree.clear()
        try:
            self._groups = self.service.find_duplicate_groups()
        except Exception as exc:
            QMessageBox.warning(self, "خطا", _err(exc))
            self._groups = []
        if not self._groups:
            self.summary.setText("تکراری مشخصی یافت نشد.")
            return
        self.summary.setText(f"{len(self._groups)} گروه تکراری یافت شد.")
        for gi, group in enumerate(self._groups, start=1):
            root = QTreeWidgetItem(
                [f"گروه {gi} — {len(group)} مخاطب", "", "", "", "", ""]
            )
            root.setData(0, Qt.ItemDataRole.UserRole, ("group", gi - 1))
            for c in group:
                child = QTreeWidgetItem(
                    [
                        c.name,
                        c.mobile,
                        c.phone,
                        c.email,
                        c.organization,
                        str(c.id),
                    ]
                )
                child.setData(0, Qt.ItemDataRole.UserRole, ("contact", c.id))
                root.addChild(child)
            self.tree.addTopLevelItem(root)
            root.setExpanded(True)

    def _merge_selected_group(self):
        item = self.tree.currentItem()
        if item is None:
            QMessageBox.warning(
                self, "انتخاب لازم است", "یک مخاطب داخل گروه را انتخاب کنید (هدف ادغام)."
            )
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        # If group header selected, use first child as keep
        keep_id = None
        group_index = None
        if data and data[0] == "contact":
            keep_id = data[1]
            parent = item.parent()
            if parent:
                gdata = parent.data(0, Qt.ItemDataRole.UserRole)
                if gdata and gdata[0] == "group":
                    group_index = gdata[1]
        elif data and data[0] == "group":
            group_index = data[1]
            group = self._groups[group_index]
            keep_id = group[0].id

        if group_index is None or keep_id is None:
            QMessageBox.warning(
                self, "انتخاب لازم است", "یک مخاطب داخل گروه را برای نگه‌داشتن انتخاب کنید."
            )
            return

        group = self._groups[group_index]
        others = [c for c in group if c.id != keep_id]
        if not others:
            return

        if (
            QMessageBox.question(
                self,
                "تایید ادغام",
                f"ادغام {len(others)} مخاطب در شماره {keep_id} و حذف بقیه؟",
            )
            != QMessageBox.Yes
        ):
            return

        try:
            keep = self.service.get_contact(keep_id)
        except ContactServiceError as exc:
            QMessageBox.warning(self, "خطا", _err(exc))
            return

        merged_ok = 0
        delete_fail: list[str] = []
        for other in others:
            # Merge fields into keep
            fields: dict = {}
            if not keep.phone and other.phone:
                fields["phone"] = other.phone
            if not keep.mobile and other.mobile:
                fields["mobile"] = other.mobile
            if not keep.email and other.email:
                fields["email"] = other.email
            if not keep.organization and other.organization:
                fields["organization"] = other.organization
            if not keep.title and other.title:
                fields["title"] = other.title
            if not keep.address and other.address:
                fields["address"] = other.address
            if other.tags:
                if not keep.tags:
                    fields["tags"] = other.tags
                elif other.tags not in keep.tags:
                    fields["tags"] = f"{keep.tags}, {other.tags}"
            if not keep.note and other.note:
                fields["note"] = other.note
            if not keep.tasks and other.tasks:
                fields["tasks"] = other.tasks
            # Prefer both roles
            if other.is_customer and not keep.is_customer:
                fields["is_customer"] = True
            if other.is_vendor and not keep.is_vendor:
                fields["is_vendor"] = True
            try:
                if fields:
                    keep = self.service.update_contact(keep_id, **fields)
                self.service.delete_contact(other.id)
                merged_ok += 1
            except ContactServiceError as exc:
                delete_fail.append(f"#{other.id}: {_err(exc)}")

        msg = f"ادغام و حذف موفق: {merged_ok}"
        if delete_fail:
            msg += "\nحذف‌نشده (در حال استفاده):\n" + "\n".join(delete_fail[:8])
        QMessageBox.information(self, "نتیجه ادغام", msg)
        self.reload()
