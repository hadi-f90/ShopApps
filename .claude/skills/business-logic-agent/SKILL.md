---
name: business-logic-agent
description: Implements pure business rules and domain logic for ShopApps — pricing calculations, currency conversion, stock-movement rules, receipt totals — with no UI or I/O. Use after a spec.md exists and before Backend API Agent wires it up.
---

# Business Logic Agent

> Note: this folder covers the same scope as `app-logic-agent`. They appear
> to be a naming duplicate (this file was found empty). Content mirrored from
> `app-logic-agent` so nothing is missing — pick one of the two folder names
> and delete the other once decided, so only one skill with this
> `description` exists.

## Role & Scope
Domain-logic specialist. Turns an approved spec into pure, testable business
rules — the "what should happen" layer, independent of how data is stored or
displayed.

**In scope:**
- Pricing strategy calculations (discount, wholesale/retail, tax, logistics)
  as pluggable, composable functions/classes.
- Currency conversion (Rial ↔ Toman display — see
  `.ai_files/technical-conventions.md`).
- Stock-movement rules: which movement type applies to which event, and
  validation (e.g. can't sell more than on-hand, unless backorders are
  explicitly allowed).
- Receipt total calculation logic.

**Out of scope (leave for downstream):**
- Database models/queries → Database Agent
- Wiring, service interfaces, inter-app calls → Backend API Agent
- UI → UI/UX Agent

## Required Input
- Approved `spec.md` for the feature
- `.ai_files/technical-conventions.md`

## Guidelines
- No imports of PySide6, Peewee, or any I/O — this layer should be testable
  with plain `pytest`, no DB or UI fixtures required.
- Business rules take plain Python values/dataclasses in and out; the Backend
  API Agent is responsible for translating to/from ORM models.
- Currency inputs/outputs are always Rial integers; conversion to Toman
  happens only in code explicitly marked as display formatting, never inside
  a calculation.
- Support agile iteration: implement the MVS rule set first (the spec's "In
  Scope" section), but leave clear extension points (e.g. a `PricingStrategy`
  base class) for Phase 2 strategies rather than hardcoding just the MVS case.
