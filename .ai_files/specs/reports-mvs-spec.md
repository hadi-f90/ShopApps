# Spec: Reports Manager - Minimum Working State (MVS)

## Problem Statement
Store owner needs quick visual and printable reports on sales, inventory, and financial status.

## User Stories
1. As a Store Owner, I want to see basic reports, so that I can make informed decisions.
   - Acceptance criteria:
     - [ ] Sales summary (today, this week, total)
     - [ ] Low stock items list
     - [ ] Top selling items
     - [ ] Export to PDF/Excel

2. As a Store Owner, I want to generate receipt history report.

## In Scope (MVS)
- Dashboard-style summary cards
- Simple table reports (sales, stock)
- PDF export button
- Data from existing modules (Contacts, Inventory, Accounting)

## Out of Scope (MVS)
- Advanced charts/graphs
- Custom report builder
- Scheduled email reports

## Assumptions
- Uses data from other modules via shared DB

## Open Questions
- Preferred report formats?

## Revision Notes
- Initial MVS