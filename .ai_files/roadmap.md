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
- **UI polish (MVS):** page title on each sub-app screen; highlight active
  sidebar button (see `design/sidebar-navigation-design.md`).
- See `.ai_files/technical-conventions.md` for the full set of locked
  technical decisions (currency, dates, stack) this roadmap assumes.

### 2. Contacts Manager (MVS)
- CRUD contacts (name, phone, email, address, `is_customer`/`is_vendor`
  flags, tags).
- **Phone normalization on save:** strip spaces/separators from pasted
  phone/mobile values before storing.
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
- **Contacts — structured name fields (optional):** split `name` into
  `first_name` / `last_name` (or keep a single “full name” display with
  optional parts). **Not required for Iranian shop workflow** where a single
  full name + organization is usually enough; only add if CRM/export needs
  it. Requires migration + VCF mapping update.
- **Contacts — social media usernames:** optional fields (e.g. Telegram,
  Instagram, WhatsApp, LinkedIn) or a small related table
  `ContactSocial(platform, username)`. Needs Product spec + migration;
  useful for Phase 2 messaging/outreach, not for MVS sales loop.
- **Contacts — stricter phone validation:** Iranian mobile format checks
  (09xxxxxxxxx) after normalization.
- UI: Model/View tables for Contacts/Accounting lists; Persian digit option;
  collapsible sidebar.

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
- E-commerce sync — publish Inventory items to an external storefront/
  website. **Status: idea only, not scoped.** Explicitly NOT part of any
  MVS phase; do not start implementation (schema, UI, or service-layer)
  until a `spec.md` exists via the Product/Requirements Agent. That spec
  must resolve at minimum:
  - Sync direction: Inventory → website only (push), or bidirectional
    (website sales also need to decrement stock — which would mean a
    second producer of `sale` movements alongside Accounting's receipt
    flow, and needs an explicit conflict/ownership rule if so).
  - Target platform: existing third-party storefront (e.g. WooCommerce/
    Shopify-style API) vs. something ShopApps hosts itself. These are
    very different sizes of work and imply different auth/security
    models.
  - Item photo support: this needs its own Database Agent decision
    (new field(s) on `Item` or a separate `ItemImage` table, on-disk
    storage path convention, file size/type limits) and Security Agent
    review (upload validation, no execution of uploaded file content) —
    it is not a detail to fold into a Social sub-app feature.
  - This is also the first feature that breaks the "offline-first,
    single-machine" assumption baked into the rest of the architecture
    (see `technical-conventions.md`) — that trade-off should be named
    explicitly in the spec, not discovered during implementation.
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
