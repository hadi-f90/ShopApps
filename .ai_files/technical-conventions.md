# Technical Conventions — ShopApps

Single source of truth for cross-cutting technical decisions. Every `spec.md` and
`SKILL.md` should defer to this document when in doubt. This supersedes any
conflicting statements elsewhere (notably older passages in `project_descrition.md`).
For day-to-day coding style, git workflow, and code-level rules, see
`.ai_files/coding-conventions.md` — that file implements the decisions below,
it doesn't redefine them.

## Stack
- Python 3.11+
- UI: **PySide6, Qt Widgets only.** QML/QtQuick and Flet are explicitly not used.
  Widgets was chosen deliberately — these are data-heavy CRUD/table/form apps,
  which is Widgets' strong suit. Revisit only if a touch-first mobile companion
  is built later.
- ORM: **Peewee** (not PonyORM) — actively maintained, has a working migration
  path via `playhouse.migrate`.
- Database: SQLite, one shared file, **WAL journal mode + `busy_timeout`**
  enabled once in `core/db`, used by every sub-app.
- Distribution: single installer bundling all four sub-apps behind one shared
  launcher. Target: Linux and Windows, offline-first, single machine / single
  user for now.
- Native/Cython: only after profiling proves a bottleneck. Default to a
  well-maintained compiled library first.

## Currency
- All monetary values are stored internally as **Rial**, integers only (no
  fractional Rial).
- **Toman is display-only**: Toman = Rial ÷ 10, computed at the UI boundary.
  Never store Toman.
- Every UI element showing a monetary value must make the unit unambiguous —
  this is the single highest-risk correctness area in the project.

## Dates
- All dates/timestamps are stored in the database as standard **Gregorian**
  (ISO 8601) — this is what the DB, migrations, and sorting/comparison logic
  assume.
- **Jalali (Solar Hijri)** display is a presentation-layer conversion only,
  applied when rendering to the user and when parsing Jalali input fields.
  Use `jdatetime` or `persiantools`. Never store Jalali dates directly.

## Inter-app architecture
- Modular monolith: one shared `core` library (models, business logic, service
  interfaces) imported by four independently-runnable apps (`apps/contacts`,
  `apps/inventory`, `apps/accounting`, `apps/social`). No network API between
  them at this stage — calls are in-process.
- `core/services` exposes abstract interfaces (Python `Protocol`) per domain
  (`ContactService`, `InventoryService`, `AccountingService`, ...), with one
  concrete **local** implementation (direct in-process DB access) for now.
- This seam exists specifically so a future **remote** implementation (calling
  a small LAN server) can be substituted later, when same-shop-LAN multi-user
  support is built, without changing any sub-app's code.

## Inventory stock movements
Stock quantity is **never mutated directly**. Every change is recorded as an
append-only **movement**: item, warehouse, quantity delta (+/-), movement
type, timestamp, optional reference (receipt id / purchase id), optional note.

MVS movement types:
| Type | Delta | Trigger |
|---|---|---|
| `purchase` | + | Purchase recorded in Accounting |
| `sale` | − | Receipt created in Accounting |
| `internal_consumption` | − | Shop's own use of stock |
| `spoilage` | − | Expired / damaged goods |
| `manual_adjustment` | +/− | Manual correction (e.g. stock count fix) |

`transfer` (warehouse-to-warehouse, +/− paired) is a Phase 3 addition, not MVS.

Current on-hand quantity is derived from the sum of movements for an
item/warehouse. If a denormalized cached quantity column is used for query
speed, it must be written to exclusively through the movement-recording path —
never mutated anywhere else.

## Translations
Qt Linguist workflow: `.ts` source files, compiled `.qm` via
`pyside6-lupdate` / `lrelease`, under `src/translations/`. `gettext`/Babel are
not used, to avoid running two i18n systems in parallel.

## Security
Policy decisions (secret storage, file permissions, dependency pinning). For
the code-level rules that implement these decisions (no raw SQL, no
`eval`/`exec`, VCF allowlist parsing, etc.), see `coding-conventions.md` →
Security.

- **Secrets**: stored in a local `.env` file, loaded via `python-dotenv`
  (already a `pyproject.toml` dependency). `.env` must be listed in
  `.gitignore`; a `.env.example` with placeholder keys (no real values) is
  committed instead, so the required variables are discoverable without
  exposing anything.
- **SQLite file permissions**: on POSIX, `shopapps.db` is created with mode
  `0600` (owner read/write only) at initialization in `core/db`. No group or
  world access. Windows relies on the OS user-profile ACLs by default; no
  extra handling needed there for MVS.
- **Dependency pinning**: dependencies stay loosely versioned in
  `pyproject.toml` during active MVS development, to keep iteration friction
  low. Before the first distributed installer build (Phase 2 packaging),
  every dependency must be pinned to an exact version, so builds are
  reproducible across machines.

## Multi-user (future — not MVS)
Planned model: same-shop LAN with a small local server, not cloud sync.
SQLite/WAL is not safe over a network file share — this phase will need either
a lightweight local sync/API service or a client-server DB, implemented behind
the `core/services` seam described above. Nothing about this needs to be built
now; the seam is what needs to exist now.