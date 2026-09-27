# Backend API and Business Logic

## 1. Purpose

Build the Flask backend that handles routes, validation, session checks, and business logic for the Expense Tracker. This skill covers the application behavior that supports registration, login, expense management, filtering, and total calculation.

This work must stay aligned with:

- [docs/AGENTS.md](../../docs/AGENTS.md)
- [docs/requirements.md](../../docs/requirements.md)
- [docs/spec.md](../../docs/spec.md)
- [docs/design.md](../../docs/design.md)

## 2. Core Rules

- Follow the approved Flask + SQLite architecture.
- Keep business logic server-side.
- Validate all incoming request data before database operations.
- Enforce user-specific access rules.
- Keep the implementation simple, readable, and within the approved project scope.

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

### Totals
- Calculate total spending based on the currently authenticated user’s records.
- Keep totals consistent with the system’s filtering and record rules.

## 4. Validation Rules

- Amount must be greater than zero.
- Expense data must include valid required fields.
- A record must belong to a registered user.
- Users must authenticate before accessing expense actions.
- Prevent cross-user access to sensitive record operations.

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

Keep route names and logic consistent with the project documentation and design intent.

## 6. Data Handling Guidance

- Read and write through the database layer rather than directly from the UI.
- Use normalized, simple data handling patterns.
- Keep validation rules explicit and easy to review.
- Return user-friendly error or confirmation messages to the frontend.

## 7. Quality Standards

- Prefer simple, maintainable code.
- Do not add extra features outside the approved scope.
- Keep business logic understandable for a beginner-friendly project.
- Validate the implementation against the documented requirements before considering the task complete.
