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




# Safe icon handling
try:
    import qtawesome as qta
    HAS_ICONS = True
except ImportError:
    HAS_ICONS = False
    print("⚠️ Install qtawesome: pip install qtawesome")

from src.apps.contacts.main import ContactsManager


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        from src.core.db import init_db

        init_db()
        self.setWindowTitle("شاپ‌اپس - تجهیزات اداری کارایان")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(1366, 768)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)

        # Content
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, stretch=1)

        self.setup_modules()
        self.switch_module(0)

    def create_sidebar(self):
        frame = QFrame()
        frame.setFixedWidth(270)
        frame.setStyleSheet("background-color: #2c3e50; color: #ecf0f1;")
        layout = QVBoxLayout(frame)
        layout.setSpacing(6)

        # Title
        title = QLabel("شاپ‌اپس")
        title.setStyleSheet(
            "font-size: 26px; font-weight: bold; padding: 25px 15px;")
        layout.addWidget(title)

        # Navigation
        nav_items = [
            ("خانه", 0),
            ("انبار", 1),
            ("مخاطبین", 2),
            ("حسابداری", 3),
            ("گزارش‌ها", 4),
            ("شبکه‌های اجتماعی", 5),
            ("پیکربندی",6)
        ]

        for label, index in nav_items:
            btn = QPushButton(f"  {label}")
            if HAS_ICONS:
                try:
                    # Safe icon names
                    icon_map = {
                        0: "fa5s.home",
                        1: "fa6s.boxes-stacked",
                        2: "fa6s.address-book",
                        3: "fa6s.receipt",
                        4: "fa6s.chart-line",
                        5: "fa6.comments",
                        6: "fa6s.screwdriver-wrench",
                    }
                    btn.setIcon(qta.icon(icon_map[index], color="#ecf0f1"))
                except:
                    pass  # fallback to text only

            btn.setStyleSheet("""
                text-align: right;
                padding: 16px 20px;
                border: none;
                font-size: 15px;
            """)
            btn.clicked.connect(lambda _, i=index: self.switch_module(i))
            layout.addWidget(btn)

        layout.addStretch()
        return frame

    def setup_modules(self):
        # Dashboard
        dash = QWidget()
        QVBoxLayout(dash).addWidget(QLabel("🏠 داشبورد\n\nخلاصه وضعیت"))
        self.content_stack.addWidget(dash)

        # Placeholders
        for name in ["انبار", "حسابداری", "گزارش‌ها", "شبکه‌های اجتماعی", "پیکربندی"]:
            p = QWidget()
            QVBoxLayout(p).addWidget(QLabel(f"{name}\n\nدر حال توسعه..."))
            self.content_stack.addWidget(p)

        self.contacts_widget = ContactsManager()
        self.content_stack.addWidget(self.contacts_widget)  # index 2

    def switch_module(self, index):
        self.content_stack.setCurrentIndex(index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
