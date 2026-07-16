import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase,QTextLayout, QPageLayout
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
    QLayout,
)

# Icon handling
try:
    import qtawesome as qta
    HAS_ICONS = True
except ImportError:
    HAS_ICONS = False
    print("⚠️ qtawesome not installed → pip install qtawesome")

from src.apps.contacts.main import ContactsManager


def load_fonts():
    """Load custom fonts from assets/fonts directory."""
    fonts_dir = Path(__file__).parent.parent.parent / "assets" / "fonts" / "vazirmatin"

    if fonts_dir.exists():
        for font_file in fonts_dir.glob("*.ttf"):
            font_id = QFontDatabase.addApplicationFont(str(font_file))
            if font_id == -1:
                print(f"⚠️ Failed to load font: {font_file}")
            else:
                print(f"✓ Loaded font: {font_file.name}")
    else:
        print(f"⚠️ Fonts directory not found: {fonts_dir}")


def create_app_stylesheet():
    """Create application-wide stylesheet with RTL support."""
    return """
        * {
            font-family: Vazirmatn;
            font-size: 13px;
        }

        QMainWindow {
            background-color: #f5f5f5;
        }

        QFrame#sidebar {
            background-color: #2c3e50;
            color: white;
        }

        QLabel#sidebar-title {
            font-size: 24px;
            font-weight: bold;
            padding: 20px;
            color: white;
        }

        QPushButton {
            background-color: #2c3e50;
            color: white;
            border: none;
            padding: 14px 20px;
            qproperty-layoutDirection: RightToLeft;
            qproperty-iconSize: 16px 16px;
            text-align: center;
            font-size: 15px;
            font-weight: 500;
        }

        QPushButton:hover {
            background-color: #34495e;
        }

        QPushButton:pressed {
            background-color: #1a252f;
        }

        QLabel {
            color: #333333;
        }
    """


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        from src.core.db import init_db

        init_db()
        self.setWindowTitle("شاپ‌اپس - تجهیزات اداری کارایان")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(1280, 800)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)

        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, 1)

        self.setup_modules()
        self.switch_to_module(0)

    def create_sidebar(self):
        frame = QFrame()
        frame.setObjectName("sidebar")
        frame.setFixedWidth(200)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("مدیر فروشگاه")
        title.setObjectName("sidebar-title")
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
                    btn = QPushButton(icon, f"{label}")
                    btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                    print("try ran")
                except Exception:
                    btn = QPushButton(f"{label}")
                    print("except ran")
            else:
                btn = QPushButton(f"{label}")
                print("else ran")

            btn.clicked.connect(lambda _, idx=index: self.switch_to_module(idx))
            print(f"Button text: {btn.text()}")
            print(f"Button layout direction: {btn.layoutDirection()}")
            print(f"Button icon size: {btn.iconSize()}")
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
        settings = QWidget()
        QVBoxLayout(settings).addWidget(QLabel("📦 پیکربندی\n\nدر حال توسعه..."))
        self.content_stack.addWidget(settings)

    def switch_to_module(self, index):
        self.content_stack.setCurrentIndex(index)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load custom fonts
    load_fonts()

    # Apply app-level stylesheet
    app.setStyleSheet(create_app_stylesheet())

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
