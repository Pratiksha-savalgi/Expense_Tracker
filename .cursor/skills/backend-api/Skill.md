# Backend API and Business Logic

## Purpose

Implement Flask routes and server-side business logic for the current Expense
Tracker. Follow [docs/requirements.md](../../docs/requirements.md),
[docs/spec.md](../../docs/spec.md), and [docs/design.md](../../docs/design.md).

## Responsibilities

- Register, authenticate, and sign out users using username/password sessions.
- Protect POST requests with the existing CSRF pattern.
- Require a valid user session for protected pages and actions.
- Implement user-scoped expense create, list, edit, and delete routes.
- Validate amount, category ownership, ISO expense date, and optional
  description before database writes.
- Reject expense dates later than today.
- Provide user-scoped category/date filters and filtered totals.
- Support Expenses date periods: today, yesterday, last seven calendar days
  including today, and a selected custom date.
- Validate custom dates as canonical ISO dates no later than today; on invalid
  input, show feedback and use the safe Today period.
- Apply identical date bounds to the expense list, spend/count/average/category
  summaries, and selected-period analytics.
- Accept the Expenses date period on Analytics so its selected-period summary
  and category distribution use the same bounds. Keep month-over-month
  comparison behavior unchanged.
- Calculate Dashboard budget summaries and Analytics results using the active
  user's data.
- Validate budget amount and calendar month/year.
- Validate Analytics year/month/day and category; block future months/years and
  future days.

## Expense contract

The current expense fields are amount, category, date, and optional description.
There is no subcategory or Liability/Savings classification. Do not accept,
validate, return, or persist either as an expense field.

## Validation and calculation rules

- Expense amount must be finite, positive, and have no more than two decimal
  places.
- Category must belong to the active user; normalize custom category names to
  prevent duplicates.
- Expense date must be valid and no later than today.
- Budget amount must be finite, positive, and have at most two decimal places;
  month/year must form a valid calendar period. Budget dates are not subject to
  the Analytics future-period restriction.
- Analytics period must be at or before the current month. An invalid period
  must show user feedback and use the safe current-month fallback. Optional day
  must be valid and no later than today.
- Use `Decimal` for monetary calculations and scope every query to the active
  user.

## Current route surface

Use the established Flask endpoints for registration, login, logout, Dashboard,
Expenses, Analytics, expense add/edit/delete, and budget save. Do not add a
separate subcategory endpoint.

## Quality

Use parameterized SQL through the database layer, make failures visible through
the application's established error/flash behavior, and add tests for changed
behavior. Run `python -m unittest discover -s tests -q` after backend changes.
