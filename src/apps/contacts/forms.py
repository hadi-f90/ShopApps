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
        self.setWindowTitle("افزودن/ویرایش مخاطب")
        self.setMinimumWidth(520)

        layout = QFormLayout(self)

        # All fields from model
        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.mobile_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.organization_edit = QLineEdit()
        self.title_edit = QLineEdit()
        self.address_edit = QTextEdit()
        self.tags_edit = QLineEdit()  # ← Added Tags
        self.note_edit = QTextEdit()
        self.tasks_edit = QTextEdit()

        self.type_combo = QComboBox()
        self.type_combo.addItems(["customer", "vendor"])

        layout.addRow("نام کامل *:", self.name_edit)
        layout.addRow("تلفن ثابت:", self.phone_edit)
        layout.addRow("تلفن همراه:", self.mobile_edit)
        layout.addRow("ایمیل:", self.email_edit)
        layout.addRow("سازمان/شرکت:", self.organization_edit)
        layout.addRow("سمت/نقش:", self.title_edit)
        layout.addRow("آدرس:", self.address_edit)
        layout.addRow("تگ‌ها:", self.tags_edit)
        layout.addRow("نوع مخاطب:", self.type_combo)
        layout.addRow("یادداشت:", self.note_edit)
        layout.addRow("تسک‌ها/پروژه‌ها:", self.tasks_edit)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("ذخیره")
        cancel_btn = QPushButton("انصراف")
        save_btn.clicked.connect(self.save_contact)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

        if self.contact:
            self.load_contact()

    def load_contact(self):
        self.name_edit.setText(self.contact.name)
        self.phone_edit.setText(self.contact.phone or "")
        self.mobile_edit.setText(self.contact.mobile or "")
        self.email_edit.setText(self.contact.email or "")
        self.organization_edit.setText(self.contact.organization or "")
        self.title_edit.setText(self.contact.title or "")
        self.address_edit.setText(self.contact.address or "")
        self.tags_edit.setText(self.contact.tags or "")
        self.note_edit.setText(self.contact.note or "")
        self.tasks_edit.setText(self.contact.tasks or "")
        self.type_combo.setCurrentText(self.contact.contact_type)

    def save_contact(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "خطا", "نام الزامی است")
            return

        if self.contact:
            # Update existing
            self.contact.name = self.name_edit.text()
            self.contact.phone = self.phone_edit.text()
            self.contact.mobile = self.mobile_edit.text()
            self.contact.email = self.email_edit.text()
            self.contact.organization = self.organization_edit.text()
            self.contact.title = self.title_edit.text()
            self.contact.address = self.address_edit.toPlainText()
            self.contact.tags = self.tags_edit.text()
            self.contact.contact_type = self.type_combo.currentText()
            self.contact.note = self.note_edit.toPlainText()
            self.contact.tasks = self.tasks_edit.toPlainText()
            self.contact.save()
        else:
            # Create new
            Contact.create(
                name=self.name_edit.text(),
                phone=self.phone_edit.text(),
                mobile=self.mobile_edit.text(),
                email=self.email_edit.text(),
                organization=self.organization_edit.text(),
                title=self.title_edit.text(),
                address=self.address_edit.toPlainText(),
                tags=self.tags_edit.text(),
                contact_type=self.type_combo.currentText(),
                note=self.note_edit.toPlainText(),
                tasks=self.tasks_edit.toPlainText(),
            )
        self.accept()