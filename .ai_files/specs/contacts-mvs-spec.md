# Spec: Contacts Manager - Minimum Working State (MVS)

## Problem Statement
Store staff need an easy way to manage customer and vendor contact information
for sales and purchases at Karrayan Office Equipment Store.

## User Stories
1. As a Store User, I want to add, edit and view contacts, so that I can
   maintain a customer/vendor database.
   - Acceptance criteria:
     - [ ] Form to add/edit contact (name, phone, email, address, `is_customer`
       flag, `is_vendor` flag, tags)
     - [ ] A contact may be both a customer and a vendor at once (e.g. a
       supplier who also buys retail) — the two flags are independent, not a
       single exclusive type
     - [ ] Searchable table list of all contacts, filterable by
       customer/vendor
     - [ ] Basic VCF import/export functionality

2. As a Store User, I want to quickly find a contact when creating a receipt,
   so that sales are fast.
   - Acceptance criteria:
     - [ ] Searchable dropdown/list when selecting customer in other modules,
       filtered to contacts with `is_customer = true`

## In Scope (MVS)
- CRUD operations for contacts
- Simple search and filtering
- VCF basic import/export
- Shared database access for use by Accounting & other modules

## Out of Scope (MVS)
- Advanced CRM features (purchase history, loyalty points)
- Bulk import from Excel
- Email/SMS integration
- Photo attachment for contacts
- Duplicate-contact detection on VCF import (e.g. matching by phone number) —
  deferred; MVS import may create duplicates that must be merged manually

## Assumptions
- Uses shared Peewee models (see Database Agent skill / `core/models/`)
- PySide6 table and form widgets
- RTL/Farsi text support
- Customer vs. vendor is represented as two independent boolean flags, not a
  single type field or separate tabs — resolves the prior open question in
  favor of the model that reflects real shop contacts (a party can be both)

## Open Questions
- None outstanding for MVS. (Previously open: "type field vs. tabs" — resolved
  above under Assumptions. "Default required fields" — name and at least one
  of phone/email required; all else optional for MVS.)

## Revision Notes
- Revised: replaced single customer/vendor type with independent flags;
  closed the open question that contradicted the acceptance criteria.
