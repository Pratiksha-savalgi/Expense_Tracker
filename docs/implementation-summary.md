# Expense Tracker Implementation Summary

Updated: 2026-09-30

## Project Structure

- `backend/app.py` contains the Flask application, routes, authentication, expense validation, filtering, and total calculation.
- `database/database.py` contains SQLite connection, schema initialization, legacy category migration, and per-user built-in category seeding.
- `database/expenses.sqlite3` is the runtime database for users, expenses, categories, subcategories, and budgets. Existing expense rows are preserved while legacy free-text categories are linked to user-owned category records.
- `frontend/templates/` contains the shared layout and login, registration, dashboard, add-expense, and edit-expense templates.
- `frontend/static/` contains the shared CSS and lightweight JavaScript.
- `requirements.txt` declares Flask. `.gitignore` excludes the virtual environment, Python bytecode, and runtime SQLite files.

## Implemented Features

- Registration with a unique, case-insensitive username, password, and required matching password confirmation.
- Login and logout using the username.
- Password hashing, Flask session authentication, CSRF checks for POST forms, and protected expense routes.
- User-scoped expense creation, viewing, editing, and deletion. Delete asks for browser confirmation.
- Expense validation for positive amounts with at most two decimal places, required categories and types, valid ISO dates, and category-owned subcategories. Description is optional.
- Per-user built-in category and subcategory options, including Food, Utilities, Transport, Household, Health, Shopping, Education, Entertainment, Bills, and Other.
- Custom categories and subcategories with case/whitespace normalization. A subcategory under an existing category can be saved immediately; one under a new category is saved with the expense.
- Expense type selection (Liability or Savings), shown with category and optional subcategory in the expense list.
- Category and date filters, including combined filtering. The displayed total is calculated from the filtered records for the signed-in user.
- Responsive HTML/CSS pages and show/hide eye controls on the login password, registration password, and confirmation fields.

## Data and Security

Users, expenses, categories, subcategories, and budgets are stored in SQLite. Expense/category writes and reads are scoped to the authenticated user; subcategories are scoped to their parent category. Existing expense types default to Liability during migration. Passwords are stored as hashes, not plain text. The SQLite file is ignored by Git so local account and expense data are not included in source changes.

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
- Flask's in-process test client checked account creation, password-confirmation rejection, duplicate usernames, password hashing, login, protected pages, expense CRUD, category/subcategory behavior, validation, user isolation, and legacy category migration.
- Package startup and delivery of the moved templates and static assets were checked without browser automation.
- The relocated SQLite database was confirmed readable, with existing account and expense records retained.
- The complete 10-test suite passed before the independent immediate-save subcategory endpoint was added. That endpoint has not yet been covered by a test run.

## Known Documentation Difference

The implementation uses usernames because that was explicitly requested. The existing requirements, specification, and testcase-plan documents still describe email-based authentication; they were left unchanged under the documentation-protection instruction. Update those references separately if the username behavior is now the intended project requirement.

Payment-method tracking, keyword search, and other unapproved features remain out of scope. Monthly budget tracking and category analytics are Version 2 capabilities already present in the application.

## Version 2 Scope Extension

Version 2 adds two major capabilities to the Expense Tracker:

1. Monthly Budget Tracking
2. Category-wise Analytics

These features are intended to make the application more useful for personal financial planning without changing the current core user experience.

### New Capabilities

- Monthly budget creation and update for the logged-in user
- Monthly remaining balance calculation
- Budget utilization percentage display
- Budget warning and over-budget alerts
- Total spending by category for a selected month
- Category contribution percentages
- Summary information for highest- and lowest-spending categories
- Dashboard-level presentation of budget and analytics status

### Expected Deliverables

- Budget table and budget management logic in the data layer
- Backend calculations for budget remaining, utilization, and warning states
- Category aggregation queries for dashboard analytics
- UI enhancements to show budget and category summary panels
- Testing documentation covering budget and analytics flows

### Database Changes

A new `budgets` table is recommended with:

- id
- user_id
- month
- year
- budget_amount
- created_at
- updated_at

This keeps budget values separate from the expense log while allowing the app to compare actual spend against monthly capacity.

### API and Backend Changes

The backend should expose logic for:

- creating or updating a monthly budget
- retrieving remaining budget for the active month
- calculating budget utilization percentage
- aggregating monthly spend by category
- calculating weighted category percentages
- exposing summary data to the dashboard template

### UI Changes

- Budget card on the dashboard
- Monthly budget form or settings area
- Warning and exceeded-state banners
- Category summary list or chart area
- Month filter for analytics review

### Testing Impact

The Version 2 scope will require new validation coverage for:

- valid and invalid budget values
- warning and exceeded states
- total and percentage accuracy
- category aggregation correctness
- empty month data handling
- dashboard rendering accuracy

This keeps the project aligned with the intended evolution from a simple expense recorder to a personal budgeting and spending analytics tool.