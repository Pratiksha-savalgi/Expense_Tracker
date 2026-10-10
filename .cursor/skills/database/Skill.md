# Database and Data Persistence

## Purpose

Maintain the SQLite schema and persistence behavior described in
[docs/spec.md](../../docs/spec.md) and
[docs/design.md](../../docs/design.md).

## Current entities

- `users`: unique case-insensitive username and password hash.
- `categories`: owner user ID, display name, normalized name; unique per user
  and normalized name.
- `expenses`: owner user ID, amount, category ID and display value, ISO date,
  optional description.
- `budgets`: owner user ID, month, year, amount, timestamps; unique per user,
  month, and year.


## Rules

- Keep all data operations scoped to the owning user.
- Use foreign keys, parameterized queries, and existing connection helpers.
- Seed the built-in categories idempotently per user.
- Normalize custom category names consistently with the application layer.
- Store monetary values in the existing representation and use `Decimal` in
  application calculations.
- Preserve expense records during legacy migration.
- When migrating legacy data, link free-text expense categories to normalized
  user-owned categories and remove obsolete subcategory/expense-type schema
  elements.
- Ensure repeated budget saves for one user and period update the same row.

## Query patterns

- Filter expenses by user, and optionally category and date.
- Calculate totals from the exact user-owned rows shown by the Expenses page.
- Retrieve period/category analytics and budget data only for the active user.
- Keep monthly comparison queries consistent for the selected category and
  compare full months.

## Quality

Keep schema and migration code direct and readable. Update migration tests when
schema behavior changes. Run the relevant database tests and
`python -m unittest discover -s tests -q`.
