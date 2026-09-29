# Backend API and Business Logic

## 1. Purpose

Build the Flask backend that handles routes, validation, session checks, and business logic for the Expense Tracker. This skill covers the application behavior that supports registration, login, expense management, filtering, monthly budget tracking, and category-wise analytics.

This work must stay aligned with:

- [docs/AGENTS.md](../../docs/AGENTS.md)
- [docs/requirements.md](../../docs/requirements.md)
- [docs/spec.md](../../docs/spec.md)
- [docs/design.md](../../docs/design.md)
- [docs/tech-stack.md](../../docs/tech-stack.md)

## 2. Core Rules

- Follow the approved Flask + SQLite architecture.
- Keep business logic server-side.
- Validate all incoming request data before database operations.
- Enforce user-specific access rules.
- Keep the implementation simple, readable, and within the approved project scope.
- Support the Version 2 budget and analytics requirements without changing the project architecture.

## 3. Functional Responsibilities

### User Management
- Register new users.
- Log users in and out.
- Maintain session state for authenticated users.
- Reject invalid or duplicate registration attempts.

### Expense Management
- Add expense records with required fields.
- View expense records belonging to the current user.
- Edit existing expense records.
- Delete expense records.
- Ensure records are tied to the authenticated user.

### Expense Queries
- Filter expenses by category and date as required by the project.
- Support listing the user’s own expenses in a simple, usable manner.
- Return only expense data belonging to the active user.

### Totals and Monthly Budget
- Calculate total spending based on the currently authenticated user’s records.
- Calculate the monthly total for the selected month and user.
- Save, update, and read monthly budget values per user and month.
- Compare actual spending against the budget and surface warnings or alerts.

### Category Analytics
- Summarize expenses by category for the selected month.
- Return category totals that match the currently authenticated user’s records.
- Handle empty category datasets gracefully with empty-state responses.

## 4. Validation Rules

- Amount must be greater than zero.
- Budget amount must be greater than zero.
- Expense data must include valid required fields.
- A record must belong to a registered user.
- Users must authenticate before accessing expense, budget, or analytics actions.
- Prevent cross-user access to sensitive record operations.
- Duplicate budget entries for the same month and user should update in place rather than creating overlapping records.

## 5. Route Design Guidance

Use straightforward Flask routes for the major flows:

- login
- logout
- register
- dashboard
- add expense
- edit expense
- delete expense
- filter expenses
- view totals
- set monthly budget
- view monthly budget status
- view category analytics

Keep route names and logic consistent with the project documentation and design intent.

## 6. Data Handling Guidance

- Read and write through the database layer rather than directly from the UI.
- Use normalized, simple data handling patterns.
- Keep validation rules explicit and easy to review.
- Return user-friendly error or confirmation messages to the frontend.
- For analytics, compute totals from the authenticated user’s data only.

## 7. Version 2 Business Logic Guidance

### Monthly budget workflow
- Accept a selected month and budget amount from the logged-in user.
- Validate the values before saving the budget.
- Store the budget for that user and month.
- Compare current-month spending against the budget threshold.
- Show warning or exceeded states when appropriate.

### Category analytics workflow
- Accept the selected month for analysis.
- Aggregate expenses by category for the current user.
- Return the category totals and ensure empty months still render a valid empty state.

## 8. Quality Standards

- Prefer simple, maintainable code.
- Do not add extra features outside the approved scope.
- Keep business logic understandable for a beginner-friendly project.
- Validate the implementation against the documented requirements before considering the task complete.
