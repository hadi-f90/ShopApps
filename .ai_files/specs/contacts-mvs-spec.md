# Spec: Contacts Manager - Minimum Working State (MVS)

## Problem Statement
Store staff need an easy way to manage customer and vendor contact information
for sales and purchases at Karrayan Office Equipment Store.

## User Stories
1. As a Store User, I want to add, edit and view contacts, so that I can
   maintain a customer/vendor database.
   - Acceptance criteria:
     - [x] Form to add/edit contact (name, phone, email, address, `is_customer`
       flag, `is_vendor` flag, tags)
     - [x] A contact may be both a customer and a vendor at once
     - [x] Searchable table list of all contacts
     - [x] Basic VCF import/export functionality
     - [x] Phone/mobile values are normalized on save

2. As a Store User, I want to quickly find a contact when creating a receipt,
   so that sales are fast.
   - Acceptance criteria:
     - [x] Searchable dropdown/list when selecting customer in other modules,
       filtered to contacts with `is_customer = true`

## VCF (MVS detail)
- Format: vCard 3.0 text (`.vcf`)
- Import/export via `ContactService.import_vcf` / `export_vcf` (UI only picks files)
- Security: max 2 MiB; max 500 cards; allowlisted properties only; PHOTO/binary skipped
- Mapped fields: FN/N→name, TEL (CELL→mobile, else phone), EMAIL, ORG, TITLE, ADR, NOTE, CATEGORIES→tags
- Roles: import defaults `is_customer=True`, `is_vendor=False` (user can edit after)
- No duplicate detection (Out of Scope)

## In Scope (MVS)
- CRUD, search, phone normalize, VCF basic I/O, shared DB via services

## Out of Scope (MVS)
- CRM history, Excel bulk, SMS, photos, social usernames, first/last name split,
  strict Iranian mobile validation, VCF dedupe

## Assumptions
- Peewee models + ContactService; independent `is_customer` / `is_vendor` flags
