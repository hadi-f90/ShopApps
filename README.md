# ShopApps

**Integrated Business Management Suite for Karrayan Office Equipment Store**

Modular PySide6 desktop apps sharing one SQLite database. Primary UI language: **Farsi (RTL)**.

## Current status (Phase 1 / MVS)

End-to-end shop flow works:

**Contact → Item → Receipt/Purchase → Stock movement**

| Sub-app | Status |
|---------|--------|
| **Contacts** | CRUD, customer/vendor flags, search, phone normalize, **VCF import/export**, delete guard |
| **Inventory** | Warehouses, items, append-only stock ledger, low-stock |
| **Accounting** | Receipts (sale movements), purchases (stock in), date filter, dashboard totals |
| **Reports** | Placeholder — Phase 2 |
| **Social / Messaging** | Deferred to **Phase 2** (nav shows “در حال توسعه”) |
| **Settings** | Placeholder |

## Stack

- Python 3.11+
- PySide6 (Qt Widgets only)
- Peewee + SQLite (WAL, foreign keys)
- jdatetime (Jalali display), qtawesome, python-dotenv

Money: **Rial integers in DB**, Toman display-only.  
Dates: **Gregorian storage**, Jalali display. Business “today” uses Iran Standard Time.

## Getting started

```bash
pip install -e ".[development]"
python -m src.shared_ui.desktop.windows.main_window
# or your preferred entry point
pytest tests/ -q
```

See `.ai_files/roadmap.md` for phases and `.ai_files/specs/` for acceptance criteria.
`.claude/skills/` documents the multi-agent development pipeline.

## License

MIT — see `LICENSE`.
