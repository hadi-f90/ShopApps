# Spec: Inventory Manager - Minimum Working State (MVS)

## Problem Statement
Store owners at Karrayan Office Equipment need a simple way to track office
supplies and equipment stock to avoid running out of popular items and to
know current value of inventory.

## User Stories
1. As a Store Owner, I want to add and view inventory items, so that I can
   keep track of stock levels.
   - Acceptance criteria:
     - [ ] Can create item with name, purchase price, sale price (both stored
       as Rial integers — see `technical-conventions.md`), brand, vendor,
       tags
     - [ ] Items are displayed in a searchable table
     - [ ] Stock in/out adjustment is recorded as a movement, not a direct
       quantity edit (see "Stock Movements" below)
     - [ ] Current on-hand quantity per item/warehouse is shown, derived from
       its movement history

2. As a Store Owner, I want to manage warehouses, so that I can track stock in
   different locations if needed.
   - Acceptance criteria:
     - [ ] Can create/edit warehouses
     - [ ] Stock movements are recorded per warehouse

3. As a Store Owner, I want to see low stock alerts, so that I can reorder in
   time.
   - Acceptance criteria:
     - [ ] Simple threshold-based warning in UI; default threshold is 5 units,
       overridable per item

## Stock Movements
Stock quantity is never edited directly — every change is an append-only
movement record (item, warehouse, quantity delta, type, timestamp, optional
reference, optional note). MVS movement types:

- `purchase` (+) — stock received from a vendor (created from Accounting's
  purchase-recording flow, or manually here)
- `sale` (−) — created automatically when a receipt is completed in
  Accounting
- `internal_consumption` (−) — shop's own use of stock (not a sale)
- `spoilage` (−) — expired or damaged goods (e.g. batteries past shelf life)
- `manual_adjustment` (+/−) — correction, e.g. after a physical stock count

- [ ] The manual "stock in/out adjustment" screen lets the user pick one of
  the above types (not just a raw + / − quantity) so the reason is always
  recorded
- [ ] `purchase` and `sale` movements can also be created programmatically by
  the Accounting app via the shared `InventoryService` interface; the UI
  screen here covers the other three types plus manual entry of the first two
  when needed outside a formal accounting flow

## In Scope (MVS)
- Basic CRUD for items and warehouses
- Stock movement recording with the five MVS types above
- Search and list view (PySide6 table)
- Shared database access for Accounting integration (receipts → `sale`
  movements, purchases → `purchase` movements)

## Out of Scope (MVS)
- Advanced pricing strategies
- Barcode scanning
- Purchase order automation
- Reports / charts
- Image upload for items
- Warehouse-to-warehouse transfers (Phase 3)
- Fractional/weight-based units of measure — MVS assumes whole-unit items only

## Assumptions
- Uses shared Peewee SQLite database
- PySide6 UI following the main app style
- Monetary values: Rial integers internally, Toman shown in UI (see
  `technical-conventions.md`)
- Quantities are whole integers for MVS

## Open Questions
- None outstanding for MVS. (Previously open: "units of measure" — resolved
  above under Out of Scope; "default low-stock threshold" — resolved above as
  5, overridable.)

## Revision Notes
- Revised: replaced "manual stock add/remove" with a typed, append-only
  movement ledger (purchase, sale, internal consumption, spoilage, manual
  adjustment); added Rial currency convention; closed prior open questions.
