# ShopApps Development Roadmap

## Minimum Working State (MVS) - Phase 1
Goal: Functional core for Karrayan Office Equipment Store with basic
interconnections.

### 1. Shared Core (Foundation)
- Unified SQLite DB (WAL mode + `busy_timeout`) with Peewee models (User,
  Settings).
- `core/services` interfaces (Protocol classes) with local in-process
  implementations — the seam that will later allow a LAN/remote
  implementation without changing sub-app code.
- Basic PySide6 (Qt Widgets) main window + sidebar navigation.
- RTL/Farsi support + theming.
- Config loading (dotenv).
- See `.ai_files/technical-conventions.md` for the full set of locked
  technical decisions (currency, dates, stack) this roadmap assumes.

### 2. Contacts Manager (MVS)
- CRUD contacts (name, phone, email, address, `is_customer`/`is_vendor`
  flags, tags).
- VCF import/export (basic).
- Search/filter.
- Shared DB access.

### 3. Inventory Manager (MVS)
- Warehouse CRUD.
- Item CRUD (name, purchase/sale price in Rial, brand, vendor, tags).
- Stock movements: `purchase`, `sale`, `internal_consumption`, `spoilage`,
  `manual_adjustment` (append-only ledger, not a mutable quantity field).
- Basic list view + search + low-stock alert (default threshold 5, per item
  override).

### 4. Accounting & Receipts (MVS)
- Create receipt: select customer (from Contacts), add items (from
  Inventory), calculate total (Rial internal, Toman display).
- Purchase recording that also creates `purchase` stock movements.
- List of past receipts.
- (PDF receipt export moved to Phase 2 — see Accounting spec revision notes.)

### 5. Social/Messaging (MVS)
- Message template CRUD + shop signature.
- Manual send simulation (console or basic UI).

### Interconnections (MVS)
- Receipts create `sale` stock movements in Inventory.
- Purchases create `purchase` stock movements in Inventory.
- Receipts link to Contacts.

**Success Criteria**: Run desktop app, manage one sale end-to-end (contact →
item sale → receipt → stock update).

## Future Phases & Features

### Phase 2: Polish + Expansion
- Advanced search, reports (Excel/PDF dashboards).
- PDF receipt export (deferred from MVS).
- Pricing strategies (discounts, wholesale).
- Multi-currency, taxes, logistics.
- User roles/auth.
- Social: Real SMS/IM integration (Twilio/API).
- Cython performance for large inventories (only after profiling shows a
  real bottleneck).

### Phase 3: Advanced Business Features
- Full CRM: Purchase history, loyalty.
- Predictive inventory (low stock alerts, AI suggestions).
- Multi-warehouse transfers.
- Accounting: Profit/loss, full ledger.
- Same-shop-LAN multi-user mode: remote implementation of `core/services`
  behind the existing interface seam, likely backed by a small local server
  or a client-server DB.
- AI-powered chat for queries ("What sold best this month?").

### Phase 4: Scale & Integrations
- E-commerce sync.
- Barcode/QR support.
- Cloud backup (optional).
- More languages, full internationalization.
- Mobile companion — revisit UI stack choice at this point; PySide6 mobile
  deployment is not solid enough today to plan around.

## Tech Reminders
- PySide6 Qt Widgets everywhere — no QML/QtQuick, no Flet (see
  `technical-conventions.md`).
- Peewee ORM, not PonyORM.
- Keep sub-apps runnable independently; talk to each other only through
  `core/services`.
- Document APIs between modules.
- Rial internal / Toman display for currency; Gregorian storage / Jalali
  display for dates — never the reverse.

Update this roadmap as features are completed.
