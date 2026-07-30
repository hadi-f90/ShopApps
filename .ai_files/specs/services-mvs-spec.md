# Spec: Services Catalog - Minimum Working State (MVS)

## Problem Statement
Karrayan Office Equipment sells **goods** (Inventory) and also performs
**services** (printing, repair, installation, etc.). Staff need a simple
catalog of sellable services with prices, without mixing them into the
physical stock ledger or changing how receipts currently work for items.

## Design principle (consistency with existing apps)

| Domain | Owns | Does *not* own |
|--------|------|----------------|
| **Inventory** | Warehouses, `Item`, append-only `StockMovement` | Service definitions |
| **Contacts** | Customers / vendors | Service catalog |
| **Accounting** | Receipts / purchases for **items** (MVS) | Service lines until Phase 2 |
| **Services** (this spec) | Catalog of named services + sale price | Stock quantities, warehouses |

**Do not** implement services as `Item` rows with a flag or zero quantity.
That would break low-stock logic, warehouse on-hand rules, and purchase/sale
movement semantics documented in `inventory-mvs-spec.md` and
`technical-conventions.md`.

**Do not** require Accounting changes in this MVS. Selling a service on a
receipt is explicitly Phase 2 so the existing end-to-end path
(contact → item → receipt → `sale` movement) stays valid and tested.

## User Stories

1. As a Store User, I want to define services we offer (e.g. چاپ، تعمیر
   پرینتر، نصب), so that prices and names are not only in someone’s head.
   - Acceptance criteria:
     - [ ] Form to create/edit a service: **name** (required), **sale price**
       (Rial integer, required, ≥ 0), optional description/note, optional
       tags, **is_active** flag (default true)
     - [ ] Searchable list of services (active and optionally inactive)
     - [ ] Soft deactivate preferred over hard delete when a future receipt
       might reference the service; if hard delete is offered, only allow when
       no dependent rows exist (none in MVS yet — delete is allowed)
     - [ ] UI shows money as Toman at the boundary; DB stores Rial only
       (`technical-conventions.md`, shared `src/core/currency.py`)

2. As a Store User, I want services in the main app navigation, so I can
   manage them without opening Inventory.
   - Acceptance criteria:
     - [ ] Sidebar entry **خدمات** (or equivalent Farsi label) opens the
       Services page with page title, consistent with Contacts/Inventory
     - [ ] UI talks only to `ServiceService` — no direct Peewee model imports
       from the UI layer (`coding-conventions.md` / service seam)

## Data model (MVS)

New table/model `Service` (name may be `services` in SQLite):

| Field | Type | Notes |
|-------|------|--------|
| `id` | PK | |
| `name` | string, required | Unique among active services recommended; enforce unique `name` for MVS simplicity |
| `sale_price` | integer | **Rial**; never Toman |
| `description` | text, optional | |
| `tags` | string, optional | Same loose convention as Contacts/Inventory tags |
| `is_active` | bool | Default `true` |
| `created_at` / `updated_at` | datetime | Naive UTC storage per conventions |

No foreign keys to `Item`, `Warehouse`, or `StockMovement` in MVS.

Migration: next sequential `m000N_*.py` after existing migrations; must not
alter Contact flags, Item, or Receipt schemas.

## Service layer

- Protocol: `ServiceService` in `src/core/services/`
- Implementation: `LocalServiceService`
- DTO: `ServiceDTO` (same pattern as `ContactDTO` / inventory DTOs)
- Errors: raise domain errors under `ShopAppsError` hierarchy with
  `.message_fa` (same as Accounting/Contacts) — do not invent a disconnected
  exception type

Suggested methods (MVS):

- `create_service(...)`, `update_service(...)`, `get_service(id)`
- `list_services(search="", active_only=True)`
- `delete_service(id)` or `set_active(id, bool)`

## In Scope (MVS)

- CRUD + search for services
- Rial storage / Toman display
- Sidebar page + service seam
- Spec + migration + unit tests for the service layer

## Out of Scope (MVS) — explicitly deferred

- Receipt / invoice **lines** that sell a service (Accounting Phase 2)
- **Material consumption** (service completion → `internal_consumption` or
  dedicated movements on linked items) — requires Accounting + Inventory
  design; do not invent a parallel stock API
- Bill of materials / packages (service “uses” N sheets of paper)
- Duration, scheduling, technician assignment, workshop job tickets
- Purchase cost of a service (internal cost accounting)
- Photos, barcodes for services
- Treating services as inventory items or warehouses for services

## Interconnections (non-breaking)

| From | To | MVS |
|------|-----|-----|
| Services UI | `ServiceService` | Yes |
| Accounting | Services | **No** — receipts stay item-only |
| Inventory | Services | **No** — no shared stock path |
| Contacts | Services | **No** |

Future (Phase 2+, separate specs required before code):

- Accounting receipt line: `item_id` **xor** `service_id`
- Optional post-completion material list → Inventory movements via
  existing `InventoryService.record_movement` only

## Assumptions

- Same stack: PySide6 Widgets, Peewee, SQLite WAL, RTL/Farsi
- Same currency and timestamp rules as all other apps
- Sub-app path: e.g. `src/apps/services/` with `main.py` / forms, runnable
  via MainWindow stack like other modules
- Roadmap: add “Services catalog (define-only)” under Phase 1 or early
  Phase 2 without changing the **success criterion** of item sale → stock;
  do not block MVS sale loop on Services

## Open Questions

- None for define-only MVS.
- (Phase 2) Whether inactive services remain selectable on old receipts for
  display only — resolve in the Accounting+Services sales spec, not here.

## Revision Notes

- Initial: catalog-only Services MVS; separate from Inventory items; no
  Accounting or stock coupling so existing Contacts / Inventory / Accounting
  behavior and tests remain unchanged.
- Aligns with product decision: services are not zero-qty items; consumption
  and receipt lines come later with their own specs.
