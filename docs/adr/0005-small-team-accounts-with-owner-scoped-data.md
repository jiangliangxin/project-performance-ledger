# Support small-team accounts with owner-scoped data

**Status**: accepted

## Context

The system is deployed on a public server. The original user may invite several colleagues to use it, but the product is still a personal performance ledger rather than a shared project-management system. Each person's performance and payout records should remain private.

## Decision

The first public release supports a small number of accounts with two roles:

- `admin`: creates, disables and resets member accounts; manages shared project types and rules; can view and manage only records owned by that account;
- `member`: manages and views only records owned by that account.

Both roles, including `admin`, can access only business data owned by the authenticated account. Administrative powers do not grant cross-owner access to companies, cooperation records, payouts, imports, dashboard summaries or exports.

There is no public self-registration, team task collaboration, shared editing or fine-grained organization permission model. Every user-owned business query is filtered by the authenticated owner on the server side.

The database keeps `owner_id` on user-owned records. Project types and their versioned rules are shared and maintained by administrators. This keeps the current model small while leaving a later workspace/organization model possible without changing the meaning of a cooperation record.

## Consequences

- The public deployment requires authentication from the first release.
- No role can use a client-supplied owner identifier to access another account's business data.
- SQLite remains acceptable for the expected four-to-five users and low write frequency, with one application process and daily changed-only backups.
- If users need shared records, cross-user workflows, multiple application instances or high write concurrency, the system should introduce workspaces/permissions and evaluate PostgreSQL.
