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
from src.core.currency import rial_to_toman
from src.core.services.accounting_service import LocalAccountingService
from src.core.services.contact_service import LocalContactService
from src.core.services.inventory_service import LocalInventoryService


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
        QFrame#sidebar QPushButton {
            background-color: #2c3e50; color: white; border: none;
            padding: 14px 20px; qproperty-layoutDirection: RightToLeft;
            qproperty-iconSize: 16px 16px; text-align: center;
            font-size: 15px; font-weight: 500;
            border-right: 4px solid transparent;
        }
        QFrame#sidebar QPushButton:hover { background-color: #34495e; }
        QFrame#sidebar QPushButton:pressed { background-color: #1a252f; }
        QFrame#sidebar QPushButton#nav-active {
            background-color: #1a252f;
            border-right: 4px solid #3498db;
            font-weight: 700;
        }
        QFrame#dash-card {
            background-color: white; border-radius: 8px;
            border: 1px solid #e0e0e0; padding: 16px;
        }
        QLabel#dash-value { font-size: 22px; font-weight: bold; color: #2c3e50; }
        QLabel#dash-title { font-size: 13px; color: #666; }
        QLabel#page-title {
            font-size: 20px; font-weight: bold; color: #2c3e50;
            padding: 4px 0 12px 0;
        }
    """


def make_page_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("page-title")
    return label


class DashboardPage(QWidget):
    def __init__(self, inventory, accounting, parent=None):
        super().__init__(parent)
        self.inventory = inventory
        self.accounting = accounting
        layout = QVBoxLayout(self)
        layout.addWidget(make_page_title("🏠 داشبورد"))

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
            logger.warning("Dashboard: failed to load low-stock count", exc_info=True)
            self._set_card_value(self.low_stock_card, "—")

        try:
            items = self.inventory.list_items()
            active = sum(1 for i in items if i.is_active)
            self._set_card_value(self.items_card, str(active))
        except Exception:
            logger.warning("Dashboard: failed to load item count", exc_info=True)
            self._set_card_value(self.items_card, "—")

        try:
            total_rial = self.accounting.today_sales_total_rial()
            toman = rial_to_toman(total_rial)
            self._set_card_value(self.sales_card, f"{toman:,} تومان")
        except Exception:
            logger.warning("Dashboard: failed to load today sales", exc_info=True)
            self._set_card_value(self.sales_card, "—")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        from src.core.db import init_db

        init_db()
        self.setWindowTitle("شاپ‌اپس - تجهیزات اداری کارایان")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(1280, 800)

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

        self._nav_buttons: list[QPushButton] = []
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
            self._nav_buttons.append(btn)

        layout.addStretch()
        return frame

    def _highlight_nav(self, active_index: int):
        for i, btn in enumerate(self._nav_buttons):
            btn.setObjectName("nav-active" if i == active_index else "")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()

    def setup_modules(self):
        self.dashboard = DashboardPage(
            self.inventory_service, self.accounting_service
        )
        self.content_stack.addWidget(self.dashboard)

        self.inventory_page = InventoryManager(service=self.inventory_service)
        self.content_stack.addWidget(self.inventory_page)

        self.contacts_page = ContactsManager(service=self.contact_service)
        self.content_stack.addWidget(self.contacts_page)

        self.accounting_page = AccountingManager(
            accounting=self.accounting_service,
            inventory=self.inventory_service,
            contacts=self.contact_service,
        )
        self.content_stack.addWidget(self.accounting_page)

        for title_text, body in (
            ("📊 گزارش‌ها", "فاز ۲ — در حال توسعه..."),
            ("💬 شبکه‌های اجتماعی", "در حال توسعه..."),
            ("⚙️ پیکربندی", "در حال توسعه..."),
        ):
            page = QWidget()
            lay = QVBoxLayout(page)
            lay.addWidget(make_page_title(title_text))
            lay.addWidget(QLabel(body))
            lay.addStretch()
            self.content_stack.addWidget(page)

    def switch_to_module(self, index):
        """Refresh the target page on every navigation so cross-app writes
        (e.g. Accounting purchase → Inventory on-hand) are visible without
        restarting the app.

        Later (Reports Manager): prefer an in-process signal on
        InventoryService.record_movement that open widgets can subscribe to —
        same staleness class of bug. See this method when implementing Reports.
        """
        self.content_stack.setCurrentIndex(index)
        self._highlight_nav(index)
        page = self.content_stack.widget(index)
        if page is None:
            return
        if hasattr(page, "refresh") and callable(page.refresh):
            page.refresh()
        elif hasattr(page, "reload") and callable(page.reload):
            page.reload()


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
