# Spec: Accounting & Receipt Manager - Minimum Working State (MVS)

## Problem Statement
Store owners need a simple way to create customer receipts for office
equipment sales and record basic financial transactions.

## User Stories
1. As a Store Cashier, I want to create a new receipt, so that I can complete
   a sale quickly.
   - Acceptance criteria:
     - [ ] Select customer from Contacts (searchable dropdown, filtered to
       `is_customer = true`)
     - [ ] Add items from Inventory (search + quantity)
     - [ ] Auto-calculate subtotal and total, stored internally as Rial,
       displayed as Toman (see `technical-conventions.md`)
     - [ ] Save receipt to DB
     - [ ] Completing a receipt creates one `sale` stock movement per line
       item in Inventory (see `inventory-mvs-spec.md`)

2. As a Store Owner, I want to view recent receipts, so that I can track
   daily sales.
   - Acceptance criteria:
     - [ ] List view of receipts with date (Jalali display, Gregorian
       storage), customer, total
     - [ ] Basic search/filter by date or customer
     - [ ] Receipts are identified by their database id for MVS; no formal
       sequential invoice-numbering scheme yet (see Out of Scope)

3. As a Store Owner, I want to record purchase expenses, so that costs are
   tracked and stock is replenished.
   - Acceptance criteria:
     - [ ] Simple form to log a vendor purchase (linked to Inventory: item,
       quantity, unit cost, vendor)
     - [ ] Saving a purchase creates a `purchase` stock movement in Inventory,
       increasing on-hand quantity — purchases are not just a financial
       record, they are the primary way stock gets replenished for MVS
     - [ ] Purchase is optionally linked to a Contact flagged `is_vendor`

## In Scope (MVS)
- Receipt creation using existing Contacts + Inventory data
- Basic total calculation (no complex discounts yet)
- List of past receipts
- Purchase recording that also updates Inventory stock
- Shared DB integration

## Out of Scope (MVS)
- Advanced pricing strategies / taxes / logistics
- Full ledger / profit-loss reports
- Payment methods (cash only for MVS)
- Sequential/formal invoice numbering — DB id is sufficient for MVS
- PDF receipt export — moved to Phase 2. MVS's own success criterion is the
  end-to-end sale flow (contact → item sale → receipt → stock update); PDF
  generation adds an RTL-PDF-text-shaping problem that isn't required to
  prove that loop and can be added once the core flow is solid

## Assumptions
- Uses data from Inventory and Contacts modules via `core/services`
  interfaces, not direct cross-app model access
- PySide6 forms and table views
- Monetary values: Rial integers internally, Toman shown in UI
- Non-sale stock decreases (internal consumption, spoilage) are recorded from
  the Inventory app directly, not from Accounting — Accounting only produces
  `sale` and `purchase` movements

## Open Questions
- Should receipt support multiple payment types in MVS? — Deferred; cash only
  for MVS per Out of Scope, revisit Phase 2.
- Preferred receipt template layout? — Deferred along with PDF export to
  Phase 2.

## Revision Notes
- Revised: added Rial/Toman convention; deferred PDF export to Phase 2;
  made explicit that purchases update Inventory stock via a `purchase`
  movement, closing the gap between this spec and the roadmap's
  interconnection list; clarified receipt identification without formal
  invoice numbering.
