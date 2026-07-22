# Coding & Process Conventions — ShopApps

Companion to `technical-conventions.md`. That file is the source of truth for
**decisions** (currency, dates, stack, architecture, and — as of this
revision — secret storage, DB file permissions, and dependency-pinning
policy). This file is the source of truth for **how code and history are
written day to day** (naming, git/branching, logging, error handling,
testing, and the code-level behavioral rules that implement the security
decisions). If the two ever conflict, `technical-conventions.md` wins on
decisions; this file wins on style/process. Neither file should restate the
other — if you find yourself copying a rule between them, delete the copy
and cross-reference instead.

**Status legend** used below: ✅ already enforced by existing code · 🔜
planned — the pattern to follow the next time that layer is touched, not yet
present in the repo. Anything marked 🔜 is a rule for new/changed code, not a
claim about current code.

---

## 1. Naming Conventions

### Files & modules
- `snake_case.py` everywhere, no exceptions.
- Per sub-app, per layer, fixed suffixes:
  - App Logic: `<domain>_logic.py` (e.g. `inventory_logic.py`)
  - Backend Service: `<domain>_service.py` (e.g. `inventory_service.py`)
  - Forms/dialogs: `forms.py` (one file per sub-app unless it exceeds ~300
    lines, then split as `<entity>_form.py`)
  - Top-level sub-app widget: `main.py`, class `<Domain>Manager`
    (`InventoryManager`, `ContactsManager`) — already the de facto pattern,
    now locked in.

### Classes
- Service interface: `<Domain>Service` (Protocol).
- Local concrete implementation: `Local<Domain>Service`. `Local` is the fixed
  prefix — when the LAN/remote phase arrives, that implementation is
  `Remote<Domain>Service`, never a bare second `<Domain>Service`.
- DTOs: `<Entity>DTO` (`ItemDTO`, `StockMovementDTO`). DTOs are
  `@dataclass(frozen=True)` unless a field must be mutated after construction
  — mutability is the exception, justify it in a comment when used.
- Domain exceptions: see §3.

### Database fields
- Boolean flags: `is_<noun>` (`is_customer`, `is_vendor`) — already
  established in the Contacts spec; apply it everywhere, no `<noun>_flag` or
  bare adjectives.
- Foreign keys: `<referenced_singular>_id` implicit via Peewee
  `ForeignKeyField`, named after the singular entity (`item`, not `item_ref`).
- Timestamps: `created_at`, `updated_at` on every table that supports
  editing; `StockMovement` additionally has `occurred_at` (business time) —
  don't conflate the two.

### UI-facing strings
- Farsi UI text stays inline as string literals for MVS (matches current
  practice in `forms.py`/`main.py`) — do **not** partially migrate to the
  `.ts` Qt Linguist pipeline mid-project; that's an all-or-nothing switch
  scheduled for i18n work, not incidental to feature work.
- Every user-facing string must be Farsi. No mixed English/Farsi labels in
  the same widget (currently consistent — keep it that way).

### Tests
- `tests/unit/test_<module>.py` — pure logic, no DB/UI fixtures.
- `tests/integration/test_<module>.py` — service + DB, no UI.
- `tests/ui/test_<module>.py` — `pytest-qt`, marked `@pytest.mark.ui` (see §5).
- Directory structure mirrors `src/` per sub-app: `tests/unit/inventory/`,
  `tests/integration/inventory/`, not one flat folder.

---

## 2. Git & Branching

Solo-maintainer-plus-agents workflow, trunk-based, no long-lived feature
branches.

### Branches
- `main` — always in a runnable state. Nothing broken gets merged here.
- `feature/<subapp>-<short-desc>` — e.g. `feature/inventory-low-stock-alert`
- `fix/<short-desc>` — bug fixes
- `chore/<short-desc>` — tooling, deps, scaffolding
- `spec/<subapp>-<short-desc>` — spec-only changes (no code), so spec churn
  doesn't pollute feature branch history
- `docs/<short-desc>` — README/roadmap/conventions-only changes

### Commits — Conventional Commits, strictly
```
<type>(<scope>): <short imperative summary>

[optional body — why, not what]
```
- `type`: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `security`
- `scope`: the sub-app or layer — `inventory`, `contacts`, `accounting`,
  `core`, `db`
- Examples: `feat(inventory): add manual stock adjustment dialog`,
  `fix(contacts): require phone or email on save`,
  `security(inventory): parameterize search query`

### Commit sequence per feature
Mirrors the agent pipeline — commit at each layer boundary, not one giant
commit at the end:
1. `db(<scope>): add/modify models`
2. `feat(<scope>): app logic for <rule>` + `test(<scope>): unit tests for <rule>`
3. `feat(<scope>): service layer wiring`
4. `test(<scope>): integration tests`
5. `feat(<scope>): UI` + `test(<scope>): ui tests`
6. `security(<scope>): review pass` (only if it changed something — see §6)
7. `docs(<scope>): update spec checkboxes / roadmap`

This makes `git bisect` and rollback meaningful — right now everything lands
as undifferentiated commits, which defeats the point of having a layered
architecture.

### Before merging to `main` (solo self-review checklist)
- [ ] Every acceptance-criteria checkbox this touches is checked in `spec.md`
- [ ] `pytest` passes (unit + integration; UI tests if touched)
- [ ] No `print()` left in — see §4
- [ ] No direct cross-app ORM import introduced (Contacts' current debt is
  the example to *not* repeat — see `technical-conventions.md`)
- [ ] Security checklist in §6 reviewed if the change touches input
  handling, file I/O, or SQL

---

## 3. Error Handling

**Status: 🔜 planned.** `src/core/errors.py` does not exist yet. This section
describes the pattern to introduce the next time a service-layer change needs
to raise a domain error — not a claim that this hierarchy is already in use.
Until it lands, keep translating `IntegrityError` etc. into plain exceptions
carrying a Farsi message string, and migrate to the hierarchy below in the
same change that first needs a second exception subclass.

### Exception hierarchy
Add `src/core/errors.py`:
```python
class ShopAppsError(Exception):
    """Base for all domain errors. Always carries a Farsi message."""
    def __init__(self, message_fa: str, *, cause: Exception | None = None):
        super().__init__(message_fa)
        self.message_fa = message_fa
        self.cause = cause

class InventoryError(ShopAppsError): ...
class InsufficientStockError(InventoryError): ...
class ContactError(ShopAppsError): ...
class AccountingError(ShopAppsError): ...
```
- One base class, one subclass per domain, further subclasses only for
  errors the UI needs to branch on differently (e.g. insufficient stock vs.
  a generic save failure).
- **Translation happens once, at the service layer boundary** (already
  memory-documented for `IntegrityError` → domain error — this formalizes it
  as the *only* place it's allowed to happen). App Logic never raises
  `ShopAppsError` subclasses directly from pure functions; it returns
  `Result`-style values or raises plain `ValueError`/`TypeError` for
  programmer errors, and the service layer wraps those.
- UI layer **never** shows a raw exception or traceback to the user. Every
  `except` in a form/tab catches `ShopAppsError` (or a specific subclass) and
  shows `.message_fa` in a `QMessageBox`. If UI code catches bare
  `Exception`, that's a bug to fix, not a pattern to repeat.

---

## 4. Logging

Two separate concerns — don't merge them:

- **Technical/debug logging** — `logging` module, never `print()`. Every
  module that logs gets `logger = logging.getLogger(__name__)` at module
  scope. `main_window.py`'s current `print("try ran")` / `print("else ran")`
  debug statements are exactly what this replaces — remove them as part of
  the next touch to that file.
  - `DEBUG`: dev-only detail (icon load attempts, widget construction)
  - `INFO`: normal lifecycle events (DB initialized, module switched)
  - `WARNING`: recoverable problems (icon failed to load, falling back)
  - `ERROR`/`CRITICAL`: unrecoverable — always paired with a domain
    exception being raised
- **Business audit trail** — stays exactly as already decided in
  `security-agent`'s SKILL.md: reuses `StockMovement` and receipt history as
  the audit mechanism. Do not build a parallel "audit log" via the `logging`
  module — that would create two competing audit trails. If a future
  business event needs auditing and has no natural ledger row, that's a
  spec question, not a logging-config question.

---

## 5. Testing

**Status: 🔜 planned** for the shared fixture and the `ui` marker — neither
exists in the repo yet; `test_contacts.py` still defines its own
`setup_database` fixture inline. Introduce the shared version the next time a
second test file needs a DB fixture, rather than writing a third inline copy.

- Replace the per-file `setup_database` fixture duplicated in
  `test_contacts.py` with a shared `tests/conftest.py`:
  ```python
  @pytest.fixture
  def test_db():
      db.init(':memory:')
      db.connect()
      db.create_tables([...])
      yield db
      db.drop_tables([...])
      db.close()
  ```
  Use `:memory:` SQLite for unit/integration tests — never point tests at
  `shopapps.db`. (Note: `:memory:` doesn't exercise WAL-mode/pragma behavior;
  add one dedicated integration test that opens a real temp-file DB
  specifically to assert WAL + foreign-key pragmas are applied, since that's
  the exact class of bug the security review already caught once.)
- Mark every `pytest-qt` test `@pytest.mark.ui` and register the marker in
  `pyproject.toml`. CI/local runs default to `pytest -m "not ui"` for fast
  feedback; full suite (including UI) runs before merge to `main`.
- One behavior per test; name as `test_<behavior>_<condition>`
  (`test_save_contact_rejects_empty_name`, not `test_security_input_validation`
  — the current name in `test_contacts.py` describes a *category*, not a
  behavior, and its body is a no-op `pass`, which is worse than no test:
  it looks covered but proves nothing. Fix or delete it.).
- Every `spec.md` acceptance-criteria checkbox maps to at least one test
  (already stated in `testing-qa-agent` — repeated here only as the
  enforcement point: a PR that checks a box without an accompanying test
  fails self-review).

---

## 6. Security — code-level rules

These are behavioral rules for code you write. The underlying policy
decisions they implement (where secrets live, what permissions the DB file
gets, when dependencies get pinned) are **decisions**, not style, and now
live in `technical-conventions.md` under **Security** — see that section for
the "what." This section covers only the "how":

- **No raw SQL string interpolation, ever.** Peewee's query builder only. If
  a query genuinely needs raw SQL, it must use parameterized `db.execute_sql()`
  with `?` placeholders — never an f-string or `.format()` building SQL text.
- **VCF import**: parse with a strict field allowlist and a hard size limit
  (e.g. reject files >5MB or >10k entries before parsing). Never `eval`,
  `exec`, or dynamically import based on file content.
- **No `eval`/`exec`/`pickle.loads` on any data that originates outside the
  process**, full stop.

For the secret-storage mechanism, SQLite file-permission requirement, and
dependency-pinning timeline this code must comply with, see
`technical-conventions.md` → Security.

---

## 7. Type Hints & Docstrings

- `mypy` is already a dev dependency — enforce what it implies: every public
  function/method in `core/`, `*_logic.py`, and `*_service.py` has full type
  hints on parameters and return value. UI event handlers are exempt from
  return-type strictness (Qt slots often return `None` implicitly) but
  parameter types are still required.
- Docstrings: Google style, required on every public class and every
  function in the App Logic and Service layers (the layers meant to be
  understood without reading the implementation). UI widget methods only
  need a docstring if their behavior isn't obvious from the method name.

---

## Ownership
This file is maintained by the **Documentation Agent**, same as
`technical-conventions.md` and `roadmap.md`. Any new pattern introduced by
another agent that isn't covered here should be added here immediately (with
a 🔜 status tag if the artifact it depends on doesn't exist yet), not left
implicit in code.