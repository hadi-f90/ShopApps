"""یافتن و ادغام مخاطبین تکراری موجود در پایگاه داده."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont
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
    """نمایش گروه‌های تکراری؛ خارج‌کردن از گروه و ادغام انتخابی."""

    def __init__(self, service: ContactService, parent=None):
        super().__init__(parent)
        self.service = service
        self.setWindowTitle("یافتن مخاطبین تکراری")
        self.setMinimumSize(760, 480)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._groups: list[list[ContactDTO]] = []
        # Contact ids the user opted out of merge for this session
        self._excluded: set[int] = set()

        layout = QVBoxLayout(self)
        self.summary = QLabel("در حال بررسی...")
        layout.addWidget(self.summary)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(
            ["نام", "موبایل", "تلفن", "ایمیل", "سازمان", "شناسه", "وضعیت"]
        )
        self.tree.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.tree.setAlternatingRowColors(True)
        layout.addWidget(self.tree)

        actions = QHBoxLayout()
        self.exclude_btn = QPushButton("خارج کردن از گروه")
        self.include_btn = QPushButton("بازگرداندن به گروه")
        self.merge_btn = QPushButton("ادغام گروه (بدون خارج‌شده‌ها)")
        self.refresh_btn = QPushButton("بررسی دوباره")
        self.exclude_btn.clicked.connect(self._exclude_selected)
        self.include_btn.clicked.connect(self._include_selected)
        self.merge_btn.clicked.connect(self._merge_selected_group)
        self.refresh_btn.clicked.connect(self._full_reload)
        for b in (
            self.exclude_btn,
            self.include_btn,
            self.merge_btn,
            self.refresh_btn,
        ):
            actions.addWidget(b)
        actions.addStretch()
        layout.addLayout(actions)

        hint = QLabel(
            "• مخاطبی که نباید ادغام شود را انتخاب کنید و «خارج کردن از گروه» بزنید "
            "(می‌توانید چند ردیف را با Ctrl انتخاب کنید).\n"
            "• برای ادغام، مخاطبِ هدف (که نگه داشته می‌شود) را انتخاب کنید؛ "
            "فقط اعضای خارج‌نشدهٔ همان گروه ادغام/حذف می‌شوند.\n"
            "• شماره‌هایی مثل ‎+98912…‎ و ‎0912…‎ یکسان در نظر گرفته می‌شوند.\n"
            "• اگر مخاطبی در فاکتور یا خرید استفاده شده باشد حذف نمی‌شود."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("بستن")
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        self.reload()

    def _full_reload(self):
        self._excluded.clear()
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

        active_groups = 0
        for gi, group in enumerate(self._groups):
            active = [c for c in group if c.id not in self._excluded]
            if len(active) >= 2:
                active_groups += 1
            root = QTreeWidgetItem(
                [
                    f"گروه {gi + 1} — {len(group)} مخاطب"
                    + (f" (فعال برای ادغام: {len(active)})" if self._excluded else ""),
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            )
            root.setData(0, Qt.ItemDataRole.UserRole, ("group", gi))
            font = root.font(0)
            font.setBold(True)
            root.setFont(0, font)
            for c in group:
                excluded = c.id in self._excluded
                child = QTreeWidgetItem(
                    [
                        c.name,
                        c.mobile,
                        c.phone,
                        c.email,
                        c.organization,
                        str(c.id),
                        "خارج‌شده از ادغام" if excluded else "در گروه",
                    ]
                )
                child.setData(0, Qt.ItemDataRole.UserRole, ("contact", c.id, gi))
                if excluded:
                    brush = QBrush(QColor("#999999"))
                    for col in range(7):
                        child.setForeground(col, brush)
                    f = child.font(0)
                    f.setStrikeOut(True)
                    child.setFont(0, f)
                root.addChild(child)
            self.tree.addTopLevelItem(root)
            root.setExpanded(True)

        excl_n = len(self._excluded)
        self.summary.setText(
            f"{len(self._groups)} گروه تکراری"
            + (f" | {active_groups} گروه قابل ادغام" if excl_n else "")
            + (f" | {excl_n} مخاطب خارج‌شده" if excl_n else "")
        )

    def _selected_contact_items(self) -> list[QTreeWidgetItem]:
        items = []
        for item in self.tree.selectedItems():
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and data[0] == "contact":
                items.append(item)
        return items

    def _exclude_selected(self):
        items = self._selected_contact_items()
        if not items:
            QMessageBox.warning(
                self,
                "انتخاب لازم است",
                "یک یا چند مخاطب داخل گروه را برای خارج کردن انتخاب کنید.",
            )
            return
        for item in items:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            self._excluded.add(int(data[1]))
        self.reload()

    def _include_selected(self):
        items = self._selected_contact_items()
        if not items:
            QMessageBox.warning(
                self,
                "انتخاب لازم است",
                "مخاطب(های) خارج‌شده را برای بازگرداندن انتخاب کنید.",
            )
            return
        for item in items:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            self._excluded.discard(int(data[1]))
        self.reload()

    def _merge_selected_group(self):
        item = self.tree.currentItem()
        if item is None:
            QMessageBox.warning(
                self,
                "انتخاب لازم است",
                "مخاطبی که باید نگه داشته شود را داخل گروه انتخاب کنید.",
            )
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        keep_id = None
        group_index = None
        if data and data[0] == "contact":
            keep_id = int(data[1])
            group_index = int(data[2])
        elif data and data[0] == "group":
            group_index = int(data[1])
            group = self._groups[group_index]
            active = [c for c in group if c.id not in self._excluded]
            if not active:
                QMessageBox.warning(self, "گروه خالی", "همهٔ اعضای این گروه خارج شده‌اند.")
                return
            keep_id = active[0].id

        if group_index is None or keep_id is None:
            QMessageBox.warning(
                self,
                "انتخاب لازم است",
                "یک مخاطب داخل گروه را برای نگه‌داشتن انتخاب کنید.",
            )
            return

        if keep_id in self._excluded:
            QMessageBox.warning(
                self,
                "مخاطب خارج‌شده",
                "مخاطب هدف خارج از گروه است. ابتدا بازگردانید یا مخاطب دیگری انتخاب کنید.",
            )
            return

        group = self._groups[group_index]
        others = [
            c
            for c in group
            if c.id != keep_id and c.id not in self._excluded
        ]
        if not others:
            QMessageBox.information(
                self,
                "چیزی برای ادغام نیست",
                "پس از خارج‌کردن‌ها، عضو دیگری برای ادغام در این گروه نمانده است.",
            )
            return

        if (
            QMessageBox.question(
                self,
                "تایید ادغام",
                f"ادغام {len(others)} مخاطب در شماره {keep_id} و حذف آن‌ها؟\n"
                f"(مخاطبین خارج‌شده دست‌نخورده می‌مانند.)",
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
        # Drop successfully deleted from exclusion set
        self.reload()
