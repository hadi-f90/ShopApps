# Design: Sidebar Navigation

> This is UI/UX Agent design output, produced from `main-window-spec.md`
> Story 1. It's not a `spec.md` in the Product/Requirements Agent template
> (no user stories/acceptance criteria) — kept separate from
> `.ai_files/specs/` for that reason. Moved from `specs/` to `design/` on
> revision so the pipeline stage that produced each file is clear at a
> glance.

## Key Design (for Main Application Window)

**Left sidebar**, fixed width ~220px, collapsible.

**Sections:**
- Dashboard (home icon) — Overview
- Inventory — Items & Warehouses
- Contacts — Customers & Vendors
- Accounting — Receipts & Reports
- Social — Messaging & Templates

**Bottom section:** Settings, Help, Exit

- Icons via `qtawesome` + text labels (Farsi + English)
- Highlight active module
- RTL support: icons move to the right side of the label when the app is in
  RTL mode
