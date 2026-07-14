from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,)

from src.core.db.models import Contact
from src.apps.contacts.forms import ContactForm



class ContactsManager(QWidget):
    def __init__(self):
        super().__init__()
        from src.core.db import init_db
        init_db()   # Ensure table exists
        self.layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        self.add_btn = QPushButton("Add Contact➕")
        self.edit_btn = QPushButton("Edit✏️")
        self.delete_btn = QPushButton("Delete🗑️")
        self.refresh_btn = QPushButton("Refresh🔄")

        self.add_btn.clicked.connect(self.add_contact)
        self.edit_btn.clicked.connect(self.edit_contact)
        self.delete_btn.clicked.connect(self.delete_contact)
        self.refresh_btn.clicked.connect(self.load_data)

        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addStretch()
        self.layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Phone", "Email", "Type", "Tags"])
        self.layout.addWidget(self.table)

        self.load_data()

    def load_data(self):
        self.table.setRowCount(0)
        contacts = Contact.select().order_by(Contact.name)
        for row, contact in enumerate(contacts):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(contact.id)))
            self.table.setItem(row, 1, QTableWidgetItem(contact.name))
            self.table.setItem(row, 2, QTableWidgetItem(contact.phone or ""))
            self.table.setItem(row, 3, QTableWidgetItem(contact.email or ""))
            self.table.setItem(row, 4, QTableWidgetItem(contact.contact_type))
            self.table.setItem(row, 5, QTableWidgetItem(contact.tags or ""))

    def add_contact(self):
        dialog = ContactForm(self)
        if dialog.exec() == QDialog.Accepted:
            self.load_data()

    def edit_contact(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a contact")
            return
        contact_id = int(self.table.item(row, 0).text())
        contact = Contact.get_by_id(contact_id)
        dialog = ContactForm(self, contact)
        if dialog.exec() == QDialog.Accepted:
            self.load_data()

    def delete_contact(self):
        row = self.table.currentRow()
        if row < 0:
            return
        if QMessageBox.question(self, "Confirm", "Delete this contact?") == QMessageBox.Yes:
            contact_id = int(self.table.item(row, 0).text())
            Contact.get_by_id(contact_id).delete_instance()
            self.load_data()