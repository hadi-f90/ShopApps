from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.apps.contacts.forms import ContactForm
from src.core.db.models import Contact


class ContactsManager(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Search
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("جستجو در نام، موبایل، سازمان...")
        self.search_edit.textChanged.connect(self.filter_contacts)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # Toolbar
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

        # Table with more fields
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            ["ID", "نام", "تلفن ثابت", "موبایل", "ایمیل", "سازمان", "سمت/نقش", "نوع", "تگ‌ها"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.load_data()

    def load_data(self, filter_text=""):
        self.table.setRowCount(0)
        query = Contact.select()
        if filter_text:
            query = query.where(
                Contact.name.contains(filter_text)
                | Contact.mobile.contains(filter_text)
                | Contact.organization.contains(filter_text)
            )
        for row, c in enumerate(query):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(c.id)))
            self.table.setItem(row, 1, QTableWidgetItem(c.name))
            self.table.setItem(row, 2, QTableWidgetItem(c.phone or ""))
            self.table.setItem(row, 3, QTableWidgetItem(c.mobile or ""))
            self.table.setItem(row, 4, QTableWidgetItem(c.email or ""))
            self.table.setItem(row, 5, QTableWidgetItem(c.organization or ""))
            self.table.setItem(row, 6, QTableWidgetItem(c.title or ""))
            self.table.setItem(row, 7, QTableWidgetItem(c.contact_type))
            self.table.setItem(row, 8, QTableWidgetItem(c.tags or ""))

    def filter_contacts(self, text):
        self.load_data(text)

    def add_contact(self):
        dialog = ContactForm(self)
        if dialog.exec():
            self.load_data()

    def edit_contact(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "خطا", "یک مخاطب انتخاب کنید")
            return
        contact_id = int(self.table.item(row, 0).text())
        contact = Contact.get_by_id(contact_id)
        dialog = ContactForm(self, contact)
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
            Contact.get_by_id(contact_id).delete_instance()
            self.load_data()