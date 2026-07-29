# Spec: Receipt / Purchase Void (draft — not MVS)

## Problem Statement
Staff need to correct mistaken receipts or purchases without destroying the
append-only stock audit trail.

## User Stories
1. As a Store Owner, I want to void a receipt, so that stock is restored and
   the original sale remains visible as cancelled.
   - Acceptance criteria:
     - [ ] Receipt gains a `status` field (`active` | `void`)
     - [ ] Void creates a reversing StockMovement (positive qty, type e.g.
       `manual_adjustment` or dedicated `sale_void`) referencing the receipt
     - [ ] Original sale movement is **not** deleted
     - [ ] Voided receipts remain in the list (visually distinct)
     - [ ] No hard-delete UI for receipts

2. As a Store Owner, I want to void a purchase similarly (stock decreases via
   reversing movement; purchase row stays marked void).

## Out of Scope
- Silent edit of line quantities/prices after save
- Physical DELETE of receipt/purchase rows

## Assumptions
- Requires Database Agent migration + Security review of audit semantics
- Do not implement until this spec is approved via Product/Requirements Agent
