# Expense Tracker Implementation Summary

Updated: 2026-09-28

## Project Structure

- `backend/app.py` contains the Flask application, routes, authentication, expense validation, filtering, and total calculation.
- `database/database.py` contains SQLite connection and schema initialization logic.
- `database/expenses.sqlite3` is the runtime database for users and expenses. The existing database was moved here with its data preserved.
- `frontend/templates/` contains the shared layout and login, registration, dashboard, add-expense, and edit-expense templates.
- `frontend/static/` contains the shared CSS and lightweight JavaScript.
- `requirements.txt` declares Flask. `.gitignore` excludes the virtual environment, Python bytecode, and runtime SQLite files.

## Implemented Features

- Registration with a unique, case-insensitive username, password, and required matching password confirmation.
- Login and logout using the username.
- Password hashing, Flask session authentication, CSRF checks for POST forms, and protected expense routes.
- User-scoped expense creation, viewing, editing, and deletion. Delete asks for browser confirmation.
- Expense validation for positive amounts, non-empty categories, and valid ISO dates. Description is optional.
- Category and date filters, including combined filtering. The displayed total is calculated from the filtered records for the signed-in user.
- Responsive HTML/CSS pages and show/hide eye controls on the login password, registration password, and confirmation fields.

## Data and Security

Users and expenses are stored in separate SQLite tables. Every expense query and write is scoped to the authenticated user's ID. Passwords are stored as hashes, not plain text. The SQLite file is ignored by Git so local account and expense data are not included in source changes.

Set `EXPENSE_TRACKER_SECRET` to a persistent secret when stable sessions across restarts are needed. If it is not set, the app generates a new secret when it starts, which invalidates existing sessions after a restart.

## Run Locally

From the repository root:

```powershell
python -m pip install -r requirements.txt
python -m backend.app
```

The development server listens at `http://127.0.0.1:5000`.

## Verification Performed

- Python compilation and editor diagnostics passed for the backend, database module, templates, CSS, and JavaScript.
- Flask's in-process test client checked account creation, password-confirmation rejection, duplicate usernames, password hashing, login, protected pages, and expense operations.
- Package startup and delivery of the moved templates and static assets were checked without browser automation.
- The relocated SQLite database was confirmed readable, with existing account and expense records retained.
- No Playwright testcase run or permanent automated test suite was added.

## Known Documentation Difference

The implementation uses usernames because that was explicitly requested. The existing requirements, specification, and testcase-plan documents still describe email-based authentication; they were left unchanged under the documentation-protection instruction. Update those references separately if the username behavior is now the intended project requirement.

Budgeting, payment-method tracking, keyword search, and other unapproved features remain out of scope.