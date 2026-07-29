from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
)

from src.core.services.contact_service import (
    ContactDTO,
    ContactService,
    ContactServiceError,
    LocalContactService,
)


class ContactForm(QDialog):
    def __init__(
        self,
        parent=None,
        contact: ContactDTO = None,
        service: ContactService = None,
    ):
        super().__init__(parent)
        self.contact = contact
        self.service = service or LocalContactService()
        self.setWindowTitle("افزودن/ویرایش مخاطب")
        self.setMinimumWidth(520)

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.mobile_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.organization_edit = QLineEdit()
        self.title_edit = QLineEdit()
        self.address_edit = QTextEdit()
        self.tags_edit = QLineEdit()
        self.note_edit = QTextEdit()
        self.tasks_edit = QTextEdit()

        self.is_customer_cb = QCheckBox("مشتری")
        self.is_customer_cb.setChecked(True)
        self.is_vendor_cb = QCheckBox("فروشنده / تامین‌کننده")

        layout.addRow("نام کامل *:", self.name_edit)
        layout.addRow("تلفن ثابت:", self.phone_edit)
        layout.addRow("تلفن همراه:", self.mobile_edit)
        layout.addRow("ایمیل:", self.email_edit)
        layout.addRow("سازمان/شرکت:", self.organization_edit)
        layout.addRow("سمت/نقش:", self.title_edit)
        layout.addRow("آدرس:", self.address_edit)
        layout.addRow("تگ‌ها:", self.tags_edit)
        layout.addRow("نقش‌ها:", self.is_customer_cb)
        layout.addRow("", self.is_vendor_cb)
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
        c = self.contact
        self.name_edit.setText(c.name)
        self.phone_edit.setText(c.phone)
        self.mobile_edit.setText(c.mobile)
        self.email_edit.setText(c.email)
        self.organization_edit.setText(c.organization)
        self.title_edit.setText(c.title)
        self.address_edit.setText(c.address)
        self.tags_edit.setText(c.tags)
        self.note_edit.setText(c.note)
        self.tasks_edit.setText(c.tasks)
        self.is_customer_cb.setChecked(c.is_customer)
        self.is_vendor_cb.setChecked(c.is_vendor)

    def save_contact(self):
        try:
            kwargs = dict(
                name=self.name_edit.text(),
                phone=self.phone_edit.text(),
                mobile=self.mobile_edit.text(),
                email=self.email_edit.text(),
                organization=self.organization_edit.text(),
                title=self.title_edit.text(),
                address=self.address_edit.toPlainText(),
                is_customer=self.is_customer_cb.isChecked(),
                is_vendor=self.is_vendor_cb.isChecked(),
                tags=self.tags_edit.text(),
                note=self.note_edit.toPlainText(),
                tasks=self.tasks_edit.toPlainText(),
            )
            if self.contact and self.contact.id:
                self.service.update_contact(self.contact.id, **kwargs)
            else:
                self.service.create_contact(**kwargs)
        except ContactServiceError as exc:
            QMessageBox.warning(
                self, "خطا", getattr(exc, "message_fa", None) or str(exc)
            )
            return
        self.accept()
