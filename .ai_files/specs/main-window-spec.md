# Spec: Main Application Window - Minimum Working State (MVS)

## Problem Statement
Store staff at Karrayan Office Equipment Store need a single, easy-to-use
desktop entry point to access all sub-apps (Inventory, Contacts, Accounting,
Social) without switching between separate programs.

## User Stories
1. As a Store User, I want a central main window with navigation, so that I
   can quickly switch between different business modules.
   - Acceptance criteria:
     - [ ] Sidebar navigation menu with clear icons/labels for each sub-app
       (see `sidebar-navigation-spec.md`)
     - [ ] Clicking a module loads its interface in the main area
     - [ ] Consistent RTL/Farsi layout and Persian font support

2. As a Store User, I want a dashboard overview on startup, so that I can see
   important business status at a glance.
   - Acceptance criteria:
     - [ ] Summary cards show live data read through `core/services`
       interfaces (low stock count from `InventoryService`, today's sales
       total from `AccountingService`, total item count from
       `InventoryService`) — not static placeholders. The main window reads
       this data the same way any other sub-app would, through the shared
       service layer, so no extra plumbing is required beyond what
       `core/services` already exposes
     - [ ] Quick links to main modules
     - [ ] Dates on the dashboard display in Jalali; underlying values stay
       Gregorian (see `technical-conventions.md`)

3. As a Store User, I want the app to remember last used module and settings,
   so that workflow is continuous.
   - Acceptance criteria:
     - [ ] Simple session persistence (last opened tab)

## In Scope (MVS)
- Main PySide6 QMainWindow with sidebar navigation
- Placeholder areas for each sub-app
- Dashboard with summary widgets showing live data (see above)
- Application-wide theming and RTL support
- Menu bar (File, Settings, Help)

## Out of Scope (MVS)
- Full authentication / multi-user login
- Advanced dashboard charts
- Plugin system
- Mobile/responsive resizing beyond basic
- Cloud sync

## Assumptions
- Uses `shared_ui/desktop/` structure
- Sub-apps are loaded as widgets or stacked layouts
- Follows overall project styling from UI/UX Agent guidelines
- Dashboard reads through `core/services`, never directly through another
  sub-app's models

## Open Questions
- None outstanding for MVS. (Previously open: "sidebar vs. tabbed
  navigation" — resolved as sidebar, see `sidebar-navigation-spec.md`;
  "real data vs. placeholders" — resolved above in favor of real data.)

## Revision Notes
- Revised: dashboard now explicitly requires live data via `core/services`,
  removing the contradiction between Story 2's acceptance criteria and the
  prior open question; added Jalali/Gregorian date-display note.
