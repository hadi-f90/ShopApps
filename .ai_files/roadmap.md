# ShopApps Development Roadmap

## Minimum Working State (MVS) - Phase 1
Goal: Functional core for Karrayan Office Equipment Store with basic interconnections.

### 1. Shared Core (Foundation)
- Unified SQLite DB with Peewee models (User, Settings).
- Basic PySide6 main window + navigation (sidebar for sub-apps).
- RTL/Farsi support + theming.
- Config loading (dotenv).

### 2. Contacts Manager (MVS)
- CRUD contacts (name, phone, email, address, tags).
- VCF import/export (basic).
- Search/filter.
- Shared DB access.

### 3. Inventory Manager (MVS)
- Warehouse CRUD.
- Item CRUD (name, qty, purchase_price, sale_price, brand, vendor, tags).
- Stock add/remove (manual).
- Basic list view + search.

### 4. Accounting & Receipts (MVS)
- Create receipt: select customer (from Contacts), add items (from Inventory), calculate total.
- Simple purchase recording.
- Basic Toman pricing display.
- PDF receipt export.

### 5. Social/Messaging (MVS)
- Message template CRUD + shop signature.
- Manual send simulation (console or basic UI).

### Interconnections (MVS)
- Receipts auto-update Inventory stock.
- Receipts link to Contacts.

**Success Criteria**: Run desktop app, manage one sale end-to-end (contact → item sale → receipt → stock update).

## Future Phases & Features
### Phase 2: Polish + Expansion
- Advanced search, reports (Excel/PDF dashboards).
- Pricing strategies (discounts, wholesale).
- Multi-currency, taxes, logistics.
- User roles/auth.
- Social: Real SMS/IM integration (Twilio/API).
- Cython performance for large inventories.

### Phase 3: Advanced Business Features
- Full CRM: Purchase history, loyalty.
- Predictive inventory (low stock alerts, Grok AI suggestions).
- Multi-warehouse transfers.
- Accounting: Profit/loss, full ledger.
- Web sync / mobile companion.
- AI: Grok-powered chat for queries ("What sold best this month?").

### Phase 4: Scale & Integrations
- E-commerce sync.
- Barcode/QR support.
- Cloud backup (optional).
- More languages, full internationalization.

## Tech Reminders
- PySide6 UI everywhere (no Flet).
- Keep sub-apps runnable independently.
- Document APIs between modules.

Update this roadmap as features are completed.