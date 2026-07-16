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
from PySide6.QtGui import QFont, QFontDatabase

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

        from src.core.db import init_db

        init_db()
        self.setWindowTitle("شاپ‌اپس - تجهیزات اداری کارایان")
        self.setLayoutDirection(Qt.RightToLeft)
        QFontDatabase.addApplicationFont("path/to/Vazirmatn-Regular.ttf")

        self.setFont(QFont("Vazirmatn"))
        app_stylesheet = """* {
        font-family: Vazirmatn;
            }
        """
        self.setStyleSheet(app_stylesheet)
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

        title = QLabel("مدیر فروشگاه")
        title.setStyleSheet("font-family: Vazirmatn; font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)

        nav_data = [
            ("خانه", "fa5s.home", 0),
            ("انبار", "fa6s.boxes-stacked", 1),
            ("مخاطبین", "fa6s.address-book", 2),
            ("حسابداری", "fa6s.receipt", 3),
            ("گزارش‌ها", "fa6s.chart-line", 4),
            ("شبکه‌های اجتماعی", "fa6s.comments", 5),
            ("پیکربندی", "fa6s.screwdriver-wrench", 6),
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
                font-family: Vazirmatn;
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

        # Settings
        inv = QWidget()
        QVBoxLayout(inv).addWidget(QLabel("📦 پیکربندی\n\nدر حال توسعه..."))
        self.content_stack.addWidget(inv)

    def switch_to_module(self, index):
        self.content_stack.setCurrentIndex(index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())