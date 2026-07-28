from PySide6.QtWidgets import (
    QHBoxLayout,
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


class ContactsManager(QWidget):
    def __init__(self, service: ContactService = None, parent=None):
        super().__init__(parent)
        self.service = service or LocalContactService()
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
        self.refresh_btn = QPushButton("🔄 بروزرسانی")

        self.add_btn.clicked.connect(self.add_contact)
        self.edit_btn.clicked.connect(self.edit_contact)
        self.delete_btn.clicked.connect(self.delete_contact)
        self.refresh_btn.clicked.connect(self.load_data)

        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
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
            ]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.load_data()

    def load_data(self, filter_text: str = ""):
        self.table.setRowCount(0)
        text = filter_text if filter_text else self.search_edit.text()
        contacts = self.service.list_contacts(search=text)
        for row, c in enumerate(contacts):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(c.id)))
            self.table.setItem(row, 1, QTableWidgetItem(c.name))
            self.table.setItem(row, 2, QTableWidgetItem(c.phone))
            self.table.setItem(row, 3, QTableWidgetItem(c.mobile))
            self.table.setItem(row, 4, QTableWidgetItem(c.email))
            self.table.setItem(row, 5, QTableWidgetItem(c.organization))
            self.table.setItem(row, 6, QTableWidgetItem("✓" if c.is_customer else ""))
            self.table.setItem(row, 7, QTableWidgetItem("✓" if c.is_vendor else ""))
            self.table.setItem(row, 8, QTableWidgetItem(c.tags))

    def filter_contacts(self, text: str):
        self.load_data(text)

    def add_contact(self):
        dialog = ContactForm(self, service=self.service)
        if dialog.exec():
            self.load_data()

    def edit_contact(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "خطا", "یک مخاطب انتخاب کنید")
            return
        contact_id = int(self.table.item(row, 0).text())
        try:
            contact = self.service.get_contact(contact_id)
        except ContactServiceError as exc:
            QMessageBox.warning(self, "خطا", str(exc))
            return
        dialog = ContactForm(self, contact=contact, service=self.service)
        if dialog.exec():
            self.load_data()

    def delete_contact(self):
        row = self.table.currentRow()
        if row < 0:
            return
        if (
            QMessageBox.question(self, "تایید حذف", "آیا از حذف این مخاطب مطمئن هستید؟")
            == QMessageBox.Yes
        ):
            contact_id = int(self.table.item(row, 0).text())
            try:
                self.service.delete_contact(contact_id)
            except ContactServiceError as exc:
                QMessageBox.warning(self, "خطا", str(exc))
                return
            self.load_data()
