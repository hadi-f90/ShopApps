# ShopApps

**Integrated Business Management Suite for Karrayan Office Equipment Store**

## Overview
ShopApps is a modular Python desktop application suite designed to manage all aspects of a small office equipment retail business (inventory, sales, customers, accounting, marketing). Each sub-app can run **independently** yet shares the same database(s) for seamless interconnection.

## Key Features
- Full **RTL/Farsi** support (primary) + English.
- Agile development: Start with Minimum Viable Features (MVF), then enhance backend logic + UI/UX.
- Performance: Cython/Numba for bottlenecks.
- Inter-app data flow (e.g., Contacts → Receipts → Inventory updates).

## Sub-Apps
- **Contacts Manager**: CRUD contacts, VCF import/export, tags, history.
- **Social Media & Messaging Manager**: SMS/IM/social messaging, templates with shop signature.
- **Inventory Manager**: Warehouses, items (specs, prices, brands, vendors, tags), stock adjustments.
- **Accounting & Receipt Manager**: Receipts/invoices (linked to contacts/inventory), purchases, pricing strategies (discounts/taxes), Toman/Rials, reports.

## Shared Capabilities
- Unified SQLite database.
- Reusable PySide6 UI widgets/dashboards.
- Exports (PDF/Excel), reporting, future Grok AI integration.
- Security & audit logs.

## Technologies
- **Python** 3.11+
- **PySide6** (Qt) for modern RTL desktop UI
- **Peewee** ORM + SQLite
- Cython/Numba, python-dotenv, openpyxl, etc.

## Getting Started
1. Clone & `pip install -e .[development]`
2. Run sub-app mains or build main launcher.
3. Use `scripts/scaffold_project.sh`

## Karrayan Focus
Tailored for office equipment: printers, furniture, stationery — fast sales, supplier tracking, local pricing.

## Development Roadmap
See [`.ai_files/roadmap.md`](.ai_files/roadmap.md) for Minimum Working State (MVS) per app and future features.