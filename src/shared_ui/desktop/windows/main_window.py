import logging
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFontDatabase, QPalette
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

logger = logging.getLogger(__name__)

try:
    import qtawesome as qta

    HAS_ICONS = True
except ImportError:
    HAS_ICONS = False
    logger.warning(
        "qtawesome not installed — sidebar icons disabled (pip install qtawesome)"
    )

from src.apps.accounting.main import AccountingManager
from src.apps.contacts.main import ContactsManager
from src.apps.inventory.main import InventoryManager
from src.core.services.accounting_service import LocalAccountingService
from src.core.services.contact_service import LocalContactService
from src.core.services.inventory_service import LocalInventoryService
from src.apps.inventory import inventory_logic as logic


def load_fonts():
    fonts_dir = Path(__file__).parent.parent.parent / "assets" / "fonts" / "vazirmatin"
    if fonts_dir.exists():
        for font_file in fonts_dir.glob("*.ttf"):
            font_id = QFontDatabase.addApplicationFont(str(font_file))
            if font_id == -1:
                logger.warning("Failed to load font: %s", font_file)
    else:
        logger.warning("Fonts directory not found: %s", fonts_dir)


def apply_light_palette(app: QApplication):
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#f5f5f5"))
    palette.setColor(QPalette.WindowText, QColor("#222222"))
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#f0f0f0"))
    palette.setColor(QPalette.Text, QColor("#222222"))
    palette.setColor(QPalette.Button, QColor("#e8e8e8"))
    palette.setColor(QPalette.ButtonText, QColor("#222222"))
    palette.setColor(QPalette.ToolTipBase, QColor("#ffffe1"))
    palette.setColor(QPalette.ToolTipText, QColor("#222222"))
    palette.setColor(QPalette.Highlight, QColor("#2c3e50"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.PlaceholderText, QColor("#8a8a8a"))
    app.setPalette(palette)


def create_app_stylesheet():
    return """
        * {
            font-family: Vazirmatn;
            font-size: 13px;
        }
        QMainWindow { background-color: #f5f5f5; }
        QFrame#sidebar { background-color: #2c3e50; color: white; }
        QLabel#sidebar-title {
            font-size: 24px; font-weight: bold; padding: 20px; color: white;
        }
        QPushButton {
            background-color: #2c3e50; color: white; border: none;
            padding: 14px 20px; qproperty-layoutDirection: RightToLeft;
            qproperty-iconSize: 16px 16px; text-align: center;
            font-size: 15px; font-weight: 500;
        }
        QPushButton:hover { background-color: #34495e; }
        QPushButton:pressed { background-color: #1a252f; }
        QFrame#dash-card {
            background-color: white; border-radius: 8px;
            border: 1px solid #e0e0e0; padding: 16px;
        }
        QLabel#dash-value { font-size: 22px; font-weight: bold; color: #2c3e50; }
        QLabel#dash-title { font-size: 13px; color: #666; }
    """


class DashboardPage(QWidget):
    """Live summary cards via core/services (main-window-spec)."""

    def __init__(
        self,
        inventory: LocalInventoryService,
        accounting: LocalAccountingService,
        parent=None,
    ):
        super().__init__(parent)
        self.inventory = inventory
        self.accounting = accounting
        layout = QVBoxLayout(self)
        title = QLabel("🏠 داشبورد")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        cards_row = QHBoxLayout()
        self.low_stock_card = self._make_card("موجودی کم", "—")
        self.items_card = self._make_card("تعداد کالاها", "—")
        self.sales_card = self._make_card("فروش امروز", "—")
        cards_row.addWidget(self.low_stock_card)
        cards_row.addWidget(self.items_card)
        cards_row.addWidget(self.sales_card)
        layout.addLayout(cards_row)
        layout.addStretch()
        self.refresh()

    def _make_card(self, title: str, value: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("dash-card")
        v = QVBoxLayout(frame)
        t = QLabel(title)
        t.setObjectName("dash-title")
        val = QLabel(value)
        val.setObjectName("dash-value")
        val.setProperty("role", "value")
        v.addWidget(t)
        v.addWidget(val)
        return frame

    def _set_card_value(self, card: QFrame, text: str):
        for child in card.findChildren(QLabel):
            if child.objectName() == "dash-value":
                child.setText(text)
                break

    def refresh(self):
        try:
            low = len(self.inventory.get_low_stock_items())
            self._set_card_value(self.low_stock_card, str(low))
        except Exception:
            self._set_card_value(self.low_stock_card, "—")

        try:
            items = self.inventory.list_items()
            active = sum(1 for i in items if i.is_active)
            self._set_card_value(self.items_card, str(active))
        except Exception:
            self._set_card_value(self.items_card, "—")

        try:
            total_rial = self.accounting.today_sales_total_rial()
            toman = logic.rial_to_toman(total_rial)
            self._set_card_value(
                self.sales_card, f"{toman:,} تومان"
            )
        except Exception:
            self._set_card_value(self.sales_card, "—")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        from src.core.db import init_db

        init_db()
        self.setWindowTitle("شاپ‌اپس - تجهیزات اداری کارایان")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(1280, 800)

        # Shared service instances (single process)
        self.contact_service = LocalContactService()
        self.inventory_service = LocalInventoryService(
            contact_service=self.contact_service
        )
        self.accounting_service = LocalAccountingService(
            inventory_service=self.inventory_service,
            contact_service=self.contact_service,
        )

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
                except Exception:
                    btn = QPushButton(f"{label}")
            else:
                btn = QPushButton(f"{label}")
            btn.clicked.connect(lambda _, idx=index: self.switch_to_module(idx))
            layout.addWidget(btn)

        layout.addStretch()
        return frame

    def setup_modules(self):
        # 0 Dashboard
        self.dashboard = DashboardPage(
            self.inventory_service, self.accounting_service
        )
        self.content_stack.addWidget(self.dashboard)

        # 1 Inventory
        self.inventory_page = InventoryManager(service=self.inventory_service)
        self.content_stack.addWidget(self.inventory_page)

        # 2 Contacts
        self.contacts_page = ContactsManager(service=self.contact_service)
        self.content_stack.addWidget(self.contacts_page)

        # 3 Accounting
        self.accounting_page = AccountingManager(
            accounting=self.accounting_service,
            inventory=self.inventory_service,
            contacts=self.contact_service,
        )
        self.content_stack.addWidget(self.accounting_page)

        # 4 Reports (Phase 2 placeholder)
        reports = QWidget()
        QVBoxLayout(reports).addWidget(
            QLabel("گزارش‌ها\n\nفاز ۲ — در حال توسعه...")
        )
        self.content_stack.addWidget(reports)

        # 5 Social (placeholder)
        social = QWidget()
        QVBoxLayout(social).addWidget(
            QLabel("شبکه‌های اجتماعی\n\nدر حال توسعه...")
        )
        self.content_stack.addWidget(social)

        # 6 Settings
        settings = QWidget()
        QVBoxLayout(settings).addWidget(
            QLabel("📦 پیکربندی\n\nدر حال توسعه...")
        )
        self.content_stack.addWidget(settings)

    def switch_to_module(self, index):
        self.content_stack.setCurrentIndex(index)
        if index == 0:
            self.dashboard.refresh()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    app = QApplication(sys.argv)
    load_fonts()
    apply_light_palette(app)
    app.setStyleSheet(create_app_stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
