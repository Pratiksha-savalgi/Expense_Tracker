# Expense Tracker Requirements

## Purpose

The Expense Tracker is a web application for individuals to record, organize,
and review personal expenses. It also provides monthly budget tracking and
category-based spending analytics.

## Users and access

- A user can register with a username, password, and password confirmation.
- Usernames are unique without regard to letter case.
- A user signs in with their username and password, and can sign out.
- A user must be signed in to access the Dashboard, Expenses, Analytics, and
  expense or budget actions.
- Each user can access only their own expenses, categories, and budgets.

## Expense management

An expense consists of:

- A positive amount, entered with no more than two decimal places
- One category owned by the signed-in user
- A date that is not later than today
- An optional description

Users can add, view, edit, and delete their own expenses. The date defaults to
today when creating an expense. Deletion requires browser confirmation.

The application does not have subcategories or an expense-type classification.
Neither is collected, displayed, filtered, validated, or stored as part of the
current expense workflow.

### Categories

- Each user has their own category list.
- The application seeds these categories for each user: Food, Utilities,
  Transport, Household, Health, Shopping, Education, Entertainment, Bills, and
  Other.
- Users can add custom categories while entering or editing an expense.
- Category names are normalized for capitalization and whitespace so equivalent
  names do not create duplicate categories.
- An expense must reference a category owned by its user.

### Expenses and Add Expense filters

- The Expenses page shows amount, category, date, and description.
- Records are shown newest first.
- The Expenses page provides the unfiltered expense ledger and category filter.
- The Add Expense page uses the AddExpense visual hierarchy: Amount spans the
  form; Category and Date controls share a row; Description and Save follow.
- The Date controls provide Today, Yesterday, Last 7 Days (including today),
  and a custom date picker. Today is selected by default. This single selected
  period controls the existing-record preview and the date saved for the new
  expense.
- Today saves today's date; Yesterday saves yesterday's date; Last 7 Days saves
  today's date; Custom saves the selected calendar date.
- Exactly one date option is active. Selecting a custom date clears the active
  quick-filter state, and selecting a quick filter clears the custom-date state.
- The Category choice is the category for the new expense and filters the
  existing-record preview and analytics; no duplicate category filter is shown.
- The filtered total, record count, summary values, category analytics, and
  existing-expense list on the Add Expense page reflect the selected period
  and category.
- Changing a filter preserves the unsaved form values and does not save an
  expense. Saving refreshes the preview with the same selected filters.
- A custom date must be a valid date no later than today.
- Changing a date or category filter automatically refreshes the existing
  expense list, summary values, and category analytics.
- The selected date window can be opened in Analytics; Analytics applies it to
  the selected-period summary and category distribution.
- The integrated form remains usable on the Add Expense page on mobile, tablet,
  and desktop layouts.

## Dashboard and monthly budgets

- The Dashboard shows the signed-in user's current-month budget, expenses,
  remaining budget, utilization, status, and recent expenses.
- A user can create or update a budget for a selected month and year.
- A budget amount must be positive and use no more than two decimal places.
- There is one budget per user, month, and year; saving the same period updates
  its existing budget.
- Budget status is “not set” when no budget exists, “warning” when utilization
  is at least 80% and spending does not exceed the budget, “exceeded” when
  spending is greater than the budget, and “on track” otherwise.
- Budgets are stored separately from expenses.

## Analytics

- Analytics can be filtered by year, month, day, and category.
- Analytics show selected-period spending, expense count, average expense,
  category totals and percentages, and the highest-spending category.
- Analytics compare full-month spending and budget utilization with the
  previous calendar month. A category filter applies to both months; a selected
  day narrows the selected-period summary, not the full-month comparison.
- Analytics for a future year or a future month in the current year are not
  allowed. The latest selectable period is the current month of the current
  year.
- A selected day must be a valid calendar day and cannot be later than today.
- Invalid future or malformed period selections are rejected and reset to a
  safe period with user feedback.
- Empty periods show a useful empty state.

## Security and reliability

- Passwords are stored as hashes, never plain text.
- State-changing form submissions require a CSRF token.
- All expense, category, budget, and analytics reads and writes are scoped to
  the authenticated user.
- Saved data is persisted in SQLite.
- Monetary calculations use decimal arithmetic.

## Technology and operation

- Frontend: HTML, CSS, and lightweight JavaScript rendered with Flask templates.
- Backend: Python and Flask.
- Persistence: SQLite.
- Start locally from the repository root with `python -m backend.app`; the
  development server listens at `http://127.0.0.1:5000`.
- Install declared dependencies with `python -m pip install -r requirements.txt`.

## Acceptance criteria

- A user can register, sign in, and sign out; unauthenticated protected-page
  requests redirect to sign-in.
- Expense CRUD works for the signed-in user's category-only records.
- Invalid amounts, categories, dates, and future expense dates are rejected
  without saving an expense.
- Date quick filters and custom date, alone or combined with category, produce
  the correct user-scoped list, summary values, and category analytics.
- Dashboard budget values and status match the selected current-month data.
- Analytics filters, category distribution, empty state, and previous-month
  comparison use the signed-in user's data and enforce the current-period limit.
- No application surface or persisted expense field represents subcategory or
  expense type.
