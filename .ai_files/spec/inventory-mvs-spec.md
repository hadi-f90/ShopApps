# Spec: Inventory Manager - Minimum Working State (MVS)

## Problem Statement
Store owners at Karrayan Office Equipment need a simple way to track office supplies and equipment stock to avoid running out of popular items and to know current value of inventory.

## User Stories
1. As a Store Owner, I want to add and view inventory items, so that I can keep track of stock levels.
   - Acceptance criteria:
     - [ ] Can create item with name, quantity, purchase price, sale price, brand, vendor, tags
     - [ ] Items are displayed in a searchable table
     - [ ] Basic stock in/out adjustment works

2. As a Store Owner, I want to manage warehouses, so that I can track stock in different locations if needed.
   - Acceptance criteria:
     - [ ] Can create/edit warehouses
     - [ ] Assign items to warehouses

3. As a Store Owner, I want to see low stock alerts, so that I can reorder in time.
   - Acceptance criteria:
     - [ ] Simple threshold-based warning in UI

## In Scope (MVS)
- Basic CRUD for items and warehouses
- Simple stock quantity adjustment
- Search and list view (PySide6 table)
- Shared database access for future receipt integration

## Out of Scope (MVS)
- Advanced pricing strategies
- Barcode scanning
- Purchase order automation
- Reports / charts
- Image upload for items

## Assumptions
- Uses shared Peewee SQLite database
- PySide6 UI following the main app style

## Open Questions
- Should we support multiple units of measure (pieces, boxes) in MVS?
- Preferred default low-stock threshold?

## Revision Notes
- Initial version - MVS focus