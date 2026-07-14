# Spec: Accounting & Receipt Manager - Minimum Working State (MVS)

## Problem Statement
Store owners need a simple way to create customer receipts for office equipment sales and record basic financial transactions.

## User Stories
1. As a Store Cashier, I want to create a new receipt, so that I can complete a sale quickly.
   - Acceptance criteria:
     - [ ] Select customer from Contacts (searchable dropdown)
     - [ ] Add items from Inventory (search + quantity)
     - [ ] Auto-calculate subtotal, total in Toman
     - [ ] Save receipt to DB and print/PDF

2. As a Store Owner, I want to view recent receipts, so that I can track daily sales.
   - Acceptance criteria:
     - [ ] List view of receipts with date, customer, total
     - [ ] Basic search/filter by date or customer

3. As a Store Owner, I want to record purchase expenses, so that costs are tracked.
   - Acceptance criteria:
     - [ ] Simple form to log vendor purchase (linked to Inventory)

## In Scope (MVS)
- Receipt creation using existing Contacts + Inventory data
- Basic total calculation (no complex discounts yet)
- PDF receipt export
- List of past receipts
- Shared DB integration

## Out of Scope (MVS)
- Advanced pricing strategies / taxes / logistics
- Full ledger / profit-loss reports
- Payment methods (cash only for MVS)
- Invoice numbering automation

## Assumptions
- Uses data from Inventory and Contacts modules
- PySide6 forms and table views

## Open Questions
- Should receipt support multiple payment types in MVS?
- Preferred receipt template layout?

## Revision Notes
- Initial MVS version