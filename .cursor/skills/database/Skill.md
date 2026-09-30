# Database and Data Persistence

## 1. Purpose

Define and manage the SQLite database for the Expense Tracker, including the base expense features and the Version 2 monthly budget and category analytics capabilities.

This work must stay aligned with:

- [docs/AGENTS.md](../../docs/AGENTS.md)
- [docs/design.md](../../docs/design.md)
- [docs/requirements.md](../../docs/requirements.md)
- [docs/spec.md](../../docs/spec.md)
- [docs/tech-stack.md](../../docs/tech-stack.md)

## 2. Core Rules

- Use SQLite as the approved database technology.
- Keep the schema simple and aligned with the project scope.
- Store users, expenses, categories, subcategories, and monthly budgets in clear, separate data sets.
- Enforce user-specific access boundaries.
- Support category-based reporting and monthly totals without adding unnecessary complexity.

## 3. Data Model Expectations

### Users
- Store user identity information required for registration and login.
- Keep password values hashed rather than stored in plain text.
- Ensure unique user identity for login and duplicate prevention.

### Expenses
- Store the per-user expense entries.
- Include amount, category reference and display value, optional subcategory reference, Liability/Savings type, date, and description.
- Associate each expense with the correct user record.
- Keep the primary data model simple and consistent with the project design.

### Categories and subcategories
- Store categories per user with a normalized comparison key and a stable display name.
- Store subcategories under a parent category with a normalized comparison key.
- Enforce uniqueness by user/category and normalized name.
- Seed the approved built-in categories and subcategories idempotently per user without replacing custom entries.
- Normalize names by trimming/collapsing whitespace and case-folding comparisons.
- Migrate existing free-text expense categories to per-user category rows without losing expense records; default legacy expense type to Liability and leave subcategory unset.

### Budgets
- Store monthly budget records by user and month.
- Include the user ID, budget amount, month, year, and timestamps.
- Ensure a user has one active budget per month rather than overlapping duplicate entries.

## 4. Data Integrity Rules

- Every expense must belong to an authenticated user.
- Users may only operate on their own records.
- Reject invalid or incomplete records before saving.
- Require positive expense amounts with at most two decimal places.
- Validate that category belongs to the signed-in user and subcategory belongs to the selected category.
- Use consistent validation rules for category, date, amount, and budget values.
- Maintain normal SQLite behavior for reliable record updates and deletions.
- For duplicate monthly budgets, update the existing row instead of creating overlapping records.

## 5. Query Guidance

- Query expenses by the authenticated user ID.
- Filter by category and date where required.
- Calculate totals from the logged-in user’s records only.
- Aggregate monthly totals for the selected month and user.
- Aggregate category totals for category-wise analytics.
- Persist a new subcategory for an existing category immediately so it is available on later forms.
- Keep SQL simple, explicit, and readable.

## 6. Version 2 Database Guidance

### Monthly budget tracking
- Create a budget table that stores monthly budget data by user.
- Use a unique combination of user ID and month-year to prevent duplicates.
- Calculate remaining budget and usage percentage from total expenses in the selected month.

### Category analytics
- Summarize expense amounts by category for the selected month.
- Return empty-state results when there are no matching category totals.
- Keep analytics queries separate from normal CRUD logic and easy to understand.

## 7. Implementation Guidance

- Create a small, predictable schema.
- Use straightforward connection and query patterns.
- Keep application logic separate from database logic where appropriate.
- Avoid over-engineering or creating abstractions beyond the project’s scope.
- Prefer direct, readable SQL statements over unnecessary abstraction layers.

## 8. Quality Standards

- Data must be correct, secure, and user-specific.
- The schema should remain easy to maintain and understand.
- Do not add unsupported features or unrelated tables.
- Verify that database behavior aligns with the documented requirements and acceptance criteria.
