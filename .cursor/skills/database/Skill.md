# Database and Data Persistence

## 1. Purpose

Define and manage the SQLite database for the Expense Tracker. This skill covers the table structure, data integrity rules, user-specific record access, and the simple persistence layer required for the application.

This work must stay aligned with:

- [docs/AGENTS.md](../../docs/AGENTS.md)
- [docs/design.md](../../docs/design.md)
- [docs/requirements.md](../../docs/requirements.md)
- [docs/spec.md](../../docs/spec.md)

## 2. Core Rules

- Use SQLite as the approved database technology.
- Keep the schema simple and aligned with the project scope.
- Store users and expenses in separate logical data sets.
- Enforce user-specific access boundaries.
- Do not introduce unnecessary complexity or unsupported database features.

## 3. Data Model Expectations

### Users
- Store user identity information required for registration and login.
- Keep password values hashed rather than stored in plain text.
- Ensure unique user identity for login and duplicate prevention.

### Expenses
- Store the per-user expense entries.
- Include fields required by the project for amount, category, date, and description.
- Associate each expense with the correct user record.

## 4. Data Integrity Rules

- Every expense must belong to an authenticated user.
- Users may only operate on their own records.
- Reject invalid or incomplete records before saving.
- Use consistent validation rules for category, date, and amount.
- Maintain normal SQLite behavior for reliable record updates and deletions.

## 5. Query Guidance

- Query expenses by the authenticated user ID.
- Filter by category and date where required.
- Calculate totals from the logged-in user’s records only.
- Keep SQL simple, explicit, and readable.

## 6. Implementation Guidance

- Create a small, predictable schema.
- Use straightforward connection and query patterns.
- Keep application logic separate from database logic where appropriate.
- Avoid over-engineering or creating abstractions beyond the project’s scope.

## 7. Quality Standards

- Data must be correct, secure, and user-specific.
- The schema should remain easy to maintain and understand.
- Do not add unsupported features or unrelated tables.
- Verify that database behavior aligns with the project requirements and acceptance criteria.
