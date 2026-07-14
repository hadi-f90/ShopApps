import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)




# Icon handling
try:
    import qtawesome as qta
    HAS_ICONS = True
except ImportError:
    HAS_ICONS = False
    print("⚠️ qtawesome not installed → pip install qtawesome")

from src.apps.contacts.main import ContactsManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("شاپ‌اپس - تجهیزات اداری کارایان")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(1280, 800)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)

        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)

        self.setup_modules()
        self.switch_to_module(0)

    def create_sidebar(self):
        frame = QFrame()
        frame.setFixedWidth(280)
        frame.setStyleSheet("background-color: #2c3e50; color: white;")
        layout = QVBoxLayout(frame)

        title = QLabel("شاپ‌اپس")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)

        nav_data = [
            ("خانه", "fa6.solid.house", 0),
            ("انبار", "fa6.solid.boxes-stacked", 1),
            ("مخاطبین", "fa6.solid.users", 2),
            ("حسابداری", "fa6.solid.receipt", 3),
            ("شبکه‌های اجتماعی", "fa6.solid.comments", 4),
        ]

        for label, icon_name, index in nav_data:
            if HAS_ICONS:
                try:
                    icon = qta.icon(icon_name, color="white")
                    btn = QPushButton(icon, f"  {label}")
                except Exception:
                    btn = QPushButton(f"  {label}")
            else:
                btn = QPushButton(f"  {label}")

            btn.setStyleSheet(
                """
                text-align: right;
                padding: 14px 20px;
                border: none;
                font-size: 15px;
            """
            )
            btn.clicked.connect(lambda _, idx=index: self.switch_to_module(idx))
            layout.addWidget(btn)

        layout.addStretch()
        return frame

    def setup_modules(self):
        # Dashboard
        dash = QWidget()
        QVBoxLayout(dash).addWidget(QLabel("🏠 داشبورد\n\nدر حال توسعه..."))
        self.content_stack.addWidget(dash)

        # Inventory
        inv = QWidget()
        QVBoxLayout(inv).addWidget(QLabel("📦 انبار\n\nدر حال توسعه..."))
        self.content_stack.addWidget(inv)

        # Contacts
        self.contacts_page = ContactsManager()
        self.content_stack.addWidget(self.contacts_page)

        # Accounting & Social
        for name in ["حسابداری", "شبکه‌های اجتماعی"]:
            p = QWidget()
            QVBoxLayout(p).addWidget(QLabel(f"{name}\n\nدر حال توسعه..."))
            self.content_stack.addWidget(p)

    def switch_to_module(self, index):
        self.content_stack.setCurrentIndex(index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())