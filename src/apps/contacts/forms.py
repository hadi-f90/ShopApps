from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
)

from src.core.db.models import Contact


class ContactForm(QDialog):
    def __init__(self, parent=None, contact=None):
        super().__init__(parent)
        self.contact = contact
        self.setWindowTitle("Add/Edit Contact")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.address_edit = QTextEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["customer", "vendor"])
        self.tags_edit = QLineEdit()

        layout.addRow("Name *:", self.name_edit)
        layout.addRow("Phone:", self.phone_edit)
        layout.addRow("Email:", self.email_edit)
        layout.addRow("Address:", self.address_edit)
        layout.addRow("Type:", self.type_combo)
        layout.addRow("Tags:", self.tags_edit)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self.save_contact)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

        if self.contact:
            self.load_contact_data()

    def load_contact_data(self):
        self.name_edit.setText(self.contact.name)
        self.phone_edit.setText(self.contact.phone or "")
        self.email_edit.setText(self.contact.email or "")
        self.address_edit.setText(self.contact.address or "")
        self.type_combo.setCurrentText(self.contact.contact_type)
        self.tags_edit.setText(self.contact.tags or "")

    def save_contact(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Name is required")
            return

        if self.contact:
            # Update existing
            self.contact.name = self.name_edit.text()
            self.contact.phone = self.phone_edit.text()
            self.contact.email = self.email_edit.text()
            self.contact.address = self.address_edit.toPlainText()
            self.contact.contact_type = self.type_combo.currentText()
            self.contact.tags = self.tags_edit.text()
            self.contact.save()
        else:
            # Create new
            Contact.create(
                name=self.name_edit.text(),
                phone=self.phone_edit.text(),
                email=self.email_edit.text(),
                address=self.address_edit.toPlainText(),
                contact_type=self.type_combo.currentText(),
                tags=self.tags_edit.text(),
            )

        self.accept()