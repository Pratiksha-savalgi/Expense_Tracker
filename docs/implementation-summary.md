# Current Application Summary

Updated: 2026-10-05

## Implemented features

- Username/password registration and login, password hashing, logout, session
  protection, and CSRF validation.
- Per-user default and custom categories, normalized to avoid duplicate names.
- Expense create, list, edit, and delete using amount, category, date, and
  optional description.
- Client-side and server-side restrictions against future expense dates.
- The Expenses page provides an unfiltered user-owned ledger with a category
  filter.
- The Add Expense page follows its visual reference with integrated date
  presets/custom picker beside Category. Its single date/category selection
  drives the saved expense and matching existing-record summary/list/analytics.
  Filter-only submissions preserve drafts and never save an expense.
- Dashboard with current-month budget metrics, status, recent expenses, and
  budget create/update controls.
- Analytics with year, month, day, and category filters; selected-period
  spending and category distribution; and full-month comparison with the
  previous calendar month.
- Analytics period validation prevents selecting a future month or year;
  selected analytics days cannot be future dates.
- Analytics can receive the active Expenses date window and applies it to the
  selected-period summary and category distribution; full-month comparison
  remains unchanged.
- Responsive HTML/CSS interface and lightweight JavaScript interactions.

## Current expense fields

The expense model consists of amount, category, date, and optional description.
Subcategory and Liability/Savings expense type are not part of the current
application or current schema.

## Storage and migration

SQLite stores users, categories, expenses, and budgets. The database initializer
seeds per-user defaults, migrates legacy free-text expense categories without
losing expense records, and removes obsolete subcategory/expense-type schema
elements when migrating a legacy database.

The default runtime database path is `database/expenses.sqlite3`; it can be
overridden with `EXPENSE_TRACKER_DB`. Set `EXPENSE_TRACKER_SECRET` to a stable
secret if sessions should remain valid across restarts.

## Run locally

From the repository root:

```powershell
python -m pip install -r requirements.txt
python -m backend.app
```

The development server listens at `http://127.0.0.1:5000`.

## Verification

Run the project tests with:

```powershell
python -m unittest discover -s tests -q
```

## Scope limits

The application does not currently provide subcategories, expense types,
keyword search, payment-method tracking, or multi-user administration. Analytics
cannot go beyond the current month; budget records may be entered for any valid
month and year.
