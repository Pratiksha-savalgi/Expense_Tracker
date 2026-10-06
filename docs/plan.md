# Application Plan and Current Structure

This plan records the implemented application structure and its responsibilities.
It is not a proposal for features that are absent from the running application.

## Project structure

```text
backend/app.py
database/database.py
frontend/static/script.js
frontend/static/style.css
frontend/templates/
tests/
docs/
.cursor/skills/
requirements.txt
```

## Responsibilities

- `backend/app.py`: Flask routes, session and CSRF handling, expense and budget
  validation, user-scoped reads/writes, dashboard calculations, and analytics.
- `database/database.py`: SQLite connection management, schema creation,
  default category seeding, and migration of legacy category data.
- `frontend/templates/`: login, registration, Dashboard, Expenses, Analytics,
  add-expense, and edit-expense pages.
- `frontend/static/script.js`: password visibility, form interactions,
  client-side date/amount checks, analytics day choices, and delete confirmation.
- `frontend/static/style.css`: shared responsive visual design.
- `tests/`: unit and Flask integration coverage.

## Implemented workflows

1. Register and sign in with a username and password.
2. Add or edit an expense with amount, one category, date, and optional
   description; reject dates after today.
3. View, filter, total, and delete the signed-in user's expenses.
4. Create or update a monthly budget for a valid month/year.
5. Review current-month budget status on the Dashboard.
6. Review category analytics through the current month, optionally filtered by
   day and category, and compare a selected month with the month before it.

The current product has no subcategory or expense-type feature.

## Verification

Run the test suite from the repository root:

```powershell
python -m unittest discover -s tests -q
```

Start the local development server with:

```powershell
python -m backend.app
```

The server listens on `http://127.0.0.1:5000`.
