# Deterministic imports and auditable ledger corrections

**Status**: accepted

## Context

The ledger receives project rows from spreadsheets and clipboard text, and users may discover errors months after a project or payout was recorded. Automatic inference or destructive edits would make the resulting personal earnings difficult to verify.

## Decision

- Parse supported clipboard and spreadsheet layouts deterministically; do not use AI or infer unprovided values.
- Show validation results before writing. Users select valid rows; invalid rows cannot be selected. The server reparses and validates the selected row numbers, then creates all selected records in one transaction.
- Duplicate company/type pairs across history or within the import are warnings only. Never merge records automatically; a user-confirmed repeat remains a separate cooperation record.
- Do not model project cancellation as a financial/workflow status in V1. Archive only hides a record from the default list and is reversible; amounts, milestones and payouts remain unchanged. Legacy cancellation values are read-only compatible data.
- If personal ratio or due amount is unknown, show `pending_ratio` even when a payout was recorded. Keep paid amount visible while due and outstanding remain unknown.
- Financial edits and milestone corrections require a reason and are retained in the record history. Correct an erroneous payout by voiding it with a reason and creating a replacement; never erase the original fact.

## Consequences

- Import behavior is predictable and reviewable, but V1 does not offer arbitrary column mapping or whole-batch undo after a successful commit.
- Users can fix mistakes without losing the original financial evidence.
- Historical records that used the former cancellation value are not mass-rewritten; the application prevents new writes of that value.
