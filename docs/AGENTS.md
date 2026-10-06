# Project Guidance

## Goal

Maintain the current Expense Tracker: account access, user-scoped expense
management, monthly budgets, and category analytics.

## Source of truth

- [requirements.md](requirements.md) defines product scope.
- [spec.md](spec.md) defines behavior, validation, and data rules.
- [design.md](design.md) describes the architecture and current data model.
- [plan.md](plan.md) records the current structure and verification commands.
- [tech-stack.md](tech-stack.md) records the approved technology stack.
- [../expense-tracker-team-requirements.md](../expense-tracker-team-requirements.md)
  summarizes the current feature requirements.
- Skill files in [../.cursor/skills](../.cursor/skills) provide layer-specific
  implementation guidance.

Keep all of these documents consistent with the application. If a document
conflicts with current behavior or another source-of-truth document, update the
conflicting documentation rather than preserving contradictory requirements.

## Architecture and scope

- HTML, CSS, and lightweight JavaScript provide the browser interface.
- Flask handles routes, authentication, validation, authorization, and business
  logic.
- SQLite persists user, category, expense, and budget records.
- Expense fields are amount, category, date, and optional description.
- There are no subcategories or Liability/Savings expense types.
- Expenses and categories belong to a user; all reads and writes must enforce
  user ownership.
- Analytics must not allow a future month or year, and expense dates must not
  exceed today.
- Budget entry accepts any valid month/year; the analytics period restriction
  does not limit budgets.

## Engineering workflow

1. Read the relevant requirements and specification before changing behavior.
2. Follow the existing backend, database, frontend, and testing patterns.
3. Keep changes focused and avoid adding features outside the documented scope.
4. Validate request data on the server even where browser validation exists.
5. Add or update targeted tests for behavior changes.
6. Run `python -m unittest discover -s tests -q` when application behavior
   changes.
7. Update affected documentation in place; replace obsolete instructions rather
   than appending contradictory corrections.

## Security and quality

- Hash passwords and require a valid session for protected routes.
- Require CSRF protection for state-changing requests.
- Scope SQL reads and writes to the active user.
- Keep database operations parameterized and monetary arithmetic decimal-safe.
- Preserve saved user data during legacy schema migrations.
