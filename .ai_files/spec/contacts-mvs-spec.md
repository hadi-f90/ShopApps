# Spec: Contacts Manager - Minimum Working State (MVS)

## Problem Statement
Store staff need an easy way to manage customer and vendor contact information for sales and purchases at Karrayan Office Equipment Store.

## User Stories
1. As a Store User, I want to add, edit and view contacts, so that I can maintain a customer/vendor database.
   - Acceptance criteria:
     - [ ] Form to add/edit contact (name, phone, email, address, type: customer/vendor, tags)
     - [ ] Searchable table list of all contacts
     - [ ] Basic VCF import/export functionality

2. As a Store User, I want to quickly find a contact when creating a receipt, so that sales are fast.
   - Acceptance criteria:
     - [ ] Searchable dropdown/list when selecting customer in other modules

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

## Assumptions
- Uses shared Peewee models
- PySide6 table and form widgets
- RTL/Farsi text support

## Open Questions
- Should we differentiate customer vs vendor with separate tabs or a type field?
- Default fields required in MVS?

## Revision Notes
- Initial MVS version