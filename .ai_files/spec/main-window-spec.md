# Spec: Main Application Window - Minimum Working State (MVS)

## Problem Statement
Store staff at Karrayan Office Equipment Store need a single, easy-to-use desktop entry point to access all sub-apps (Inventory, Contacts, Accounting, Social) without switching between separate programs.

## User Stories
1. As a Store User, I want a central main window with navigation, so that I can quickly switch between different business modules.
   - Acceptance criteria:
     - [ ] Sidebar or top navigation menu with clear icons/labels for each sub-app
     - [ ] Clicking a module loads its interface in the main area
     - [ ] Consistent RTL/Farsi layout and Persian font support

2. As a Store User, I want a dashboard overview on startup, so that I can see important business status at a glance.
   - Acceptance criteria:
     - [ ] Basic summary cards (e.g., low stock count, today's sales, total items)
     - [ ] Quick links to main modules

3. As a Store User, I want the app to remember last used module and settings, so that workflow is continuous.
   - Acceptance criteria:
     - [ ] Simple session persistence (last opened tab)

## In Scope (MVS)
- Main PySide6 QMainWindow with sidebar navigation
- Placeholder areas for each sub-app
- Basic dashboard with summary widgets
- Application-wide theming and RTL support
- Menu bar (File, Settings, Help)

## Out of Scope (MVS)
- Full authentication / multi-user login
- Advanced dashboard charts
- Plugin system
- Mobile/responsive resizing beyond basic
- Cloud sync

## Assumptions
- Uses shared_ui/desktop/ structure
- Sub-apps will be loaded as widgets or stacked layouts
- Follows overall project styling from UI/UX guidelines

## Open Questions
- Preferred navigation style: Sidebar (default) or Tabbed interface?
- Should dashboard show real data from other modules in MVS or static placeholders?

## Revision Notes
- Initial version for core launcher