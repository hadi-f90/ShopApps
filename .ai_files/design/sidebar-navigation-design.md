# Design: Sidebar Navigation

> This is UI/UX Agent design output, produced from `main-window-spec.md`
> Story 1. It's not a `spec.md` in the Product/Requirements Agent template
> (no user stories/acceptance criteria) — kept separate from
> `.ai_files/specs/` for that reason. Moved from `specs/` to `design/` on
> revision so the pipeline stage that produced each file is clear at a
> glance.

## Key Design (for Main Application Window)

**Left sidebar**, fixed width ~220px, collapsible (collapse = Phase 2).

**Sections:**
- Dashboard (home icon) — Overview
- Inventory — Items & Warehouses
- Contacts — Customers & Vendors
- Accounting — Receipts & Reports
- Social — Messaging & Templates

**Bottom section:** Settings, Help, Exit

- Icons via `qtawesome` + text labels (Farsi primary)
- **Highlight active module** (MVS): darker background + accent border on the
  selected nav button (`QPushButton#nav-active` in the app stylesheet)
- RTL support: icons move to the right side of the label when the app is in
  RTL mode

## Page titles (MVS)

Each content page shows a clear top heading (same visual weight as the
Dashboard title), e.g. «انبار», «مخاطبین», «حسابداری», so the user always
knows which module is open even when the sidebar highlight is subtle.
