# AGENTS.md

Rules for implementing the Expense Tracker in this repository.

## Source of truth

Follow these documents. Do not invent requirements beyond them:

- `requirements.md`
- `intent.md`
- `spec.md`
- `tech-stack.md`
- `plan.md`

If documents conflict, prefer `spec.md` for behavior and `tech-stack.md` / `plan.md` for how to build it.

## Approved technology stack

Use only:

- HTML
- CSS
- JavaScript
- Flask
- SQLite

Do not add other languages, frameworks, libraries, tools, or dependencies.

## Scope and plan

- Build only what the documents describe: register/login, add/view/edit/delete expenses, category, filter by category and date, total spending.
- Follow the folder structure, file responsibilities, and implementation order in `plan.md`.
- Keep the implementation simple and beginner-friendly.
- Do not add unapproved features (for example: budget, search, payment method, extra pages, or extra fields) unless the source documents require them.

## Simplicity

- Prefer a small, readable Flask app with HTML pages, one CSS file, and one JavaScript file.
- Do not add complexity that the plan does not call for.

## Validation and security

From `spec.md`:

- Amount must be greater than 0.
- An expense must have a category.
- Expense date must be a valid date.
- Validate details before saving.
- An expense must belong to a registered user.
- User must create an account and log in before managing expenses.
- Passwords must not be stored as plain text.
- Users can access only their own expenses. Never show, edit, or delete another user’s records.

## Frontend, backend, and database

Keep responsibilities separate, as in `plan.md` and `tech-stack.md`:

- HTML: page and form structure
- CSS: simple, easy-to-use styling
- JavaScript: interactions (form actions, delete confirmation, filtering)
- Flask (`app.py`): authentication, validation, expense operations, totals
- SQLite: store user accounts and expense records

The browser talks to Flask. Flask talks to SQLite. Do not mix these roles.

## Verification

After implementing (or changing) behavior, verify against the acceptance criteria in `spec.md` and the checklist in `plan.md`:

- Registration (valid details; error for missing or existing email)
- Login (valid credentials; error for invalid credentials)
- Add, view, edit, delete expenses
- Filter by category and date
- Total spending displayed
- User sees only their own expenses

## Project documentation

Do not modify `requirements.md`, `intent.md`, `spec.md`, `tech-stack.md`, `plan.md`, or this file unless the user explicitly asks to change them.
