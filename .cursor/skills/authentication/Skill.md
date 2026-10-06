# Authentication and Authorization

## Purpose

Implement account access and ownership checks for the current Expense Tracker.
Align behavior with [docs/requirements.md](../../docs/requirements.md) and
[docs/spec.md](../../docs/spec.md).

## Required behavior

- Register using username, password, and password confirmation.
- Enforce case-insensitive unique usernames.
- Hash passwords before persistence and verify hashes on login.
- Create a session only after valid credentials; clear it on logout.
- Require authentication for Dashboard, Expenses, Analytics, expense actions,
  and budget actions.
- Clear invalid user sessions and redirect to login.
- Scope every expense, category, budget, filter, and analytics operation to the
  active user.
- Protect POST form submissions with the existing CSRF token validation.

## Scope

The account identifier is username, not email. Expense data consists of amount,
category, date, and optional description; there is no subcategory or expense
type. Do not implement authorization or persistence paths for those removed
fields.

## Quality

Keep backend session and authorization checks authoritative. Do not expose
password hashes or internal errors in user-facing messages. Test unauthenticated
access and cross-user record operations.
