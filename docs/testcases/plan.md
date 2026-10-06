# Test Plan

## Purpose and source documents

This plan covers the current application behavior described in
[requirements.md](../requirements.md) and [spec.md](../spec.md). It adds no
product behavior beyond those documents.

## Test scope

- Registration, login, logout, and authentication protection
- Expense create, view, edit, delete, validation, and user isolation
- User-owned categories, default seeding, custom category normalization, and
  legacy migration
- Add Expense date/category filters and filtered totals; unfiltered Expenses
  ledger
- Budget create/update, validation, calculations, and status
- Analytics filters, current-period limits, category calculations, empty states,
  and month comparison
- Browser interaction and responsive/accessible presentation

## Test strategy

- Use Python `unittest` and Flask's test client for backend and integration
  behavior.
- Use temporary SQLite databases for isolated schema and migration tests where
  appropriate.
- Use browser checks for frontend constraints, navigation, layout, and delete
  confirmation.
- Test user isolation with at least two independently authenticated users.

## Core cases

### Authentication and access

- Register and log in with valid username/password details.
- Reject duplicate usernames and invalid credentials.
- Redirect unauthenticated protected requests to login.
- Confirm invalidated sessions cannot access protected routes.
- Confirm another user cannot read or mutate an expense, category, or budget.
- Confirm passwords are stored as hashes and POST requests require CSRF tokens.

### Expense management

- Create an expense with a valid amount, owned category, date, and optional
  description.
- Reject missing, malformed, zero, negative, non-finite, and over-precision
  amounts.
- Reject invalid dates and dates after today on both create and edit.
- Confirm category selection is required and custom categories are normalized
  and user-scoped.
- Confirm create/edit validation preserves entered values where possible.
- Confirm edit updates only the owned expense.
- Confirm delete confirmation is shown and deletion is user-scoped.
- Confirm list contents, newest-first order, and empty state.
- Confirm there is no subcategory or expense-type field, validation, display, or
  persisted model field.

### Filtering and totals

- Confirm Add Expense matches its visual hierarchy: full-width Amount,
  Category beside Date controls, then Description and Save.
- Confirm the date filter is absent from the Expenses ledger and Today is
  selected by default with only today's existing records shown.
- Confirm there is one date-control state and one custom date picker, with no
  duplicate transaction-date input or category filter.
- Confirm Today saves today, Yesterday saves yesterday, Last 7 Days saves
  today, and Custom saves the selected date.
- Confirm Yesterday includes only the previous calendar day's records.
- Confirm Last 7 Days includes today plus the previous six days and excludes an
  expense seven days ago.
- Confirm a custom date includes only that date and clears the active quick
  filter.
- Confirm selecting a quick filter clears any prior custom date.
- Confirm exactly one quick filter is active and its accessible pressed state
  matches its visual state.
- Confirm category filtering combines with every date selection.
- Reject malformed and future custom dates with feedback and a safe Today
  fallback.
- Confirm list, spend/count/average/highest-category cards, and category
  analytics all recalculate for every date filter.
- Confirm the Analytics link carries the selected date filter and the Analytics
  selected-period summary and distribution honor it.
- Confirm list count and displayed totals use only matching records belonging
  to the signed-in user.
- Confirm changing date/category controls preserves unsaved values and does not
  save an expense.
- Confirm saving a new expense uses the selected date/category and refreshes
  the matching records and analytics.
- Verify the Add Expense date-filter controls wrap on tablet and mobile
  and remain usable with keyboard and screen reader controls.

### Budgets and Dashboard

- Create a valid monthly budget and update the same user/month/year without
  adding a duplicate row.
- Reject invalid month/year and non-positive, malformed, non-finite, or
  over-precision budget amounts.
- Check not-set, on-track, warning (at least 80%), and exceeded (spending
  greater than budget) states.
- Confirm expenses from other periods or users do not affect the dashboard.
- Confirm valid future-period budgets are permitted; the future-period limit is
  specific to Analytics.

### Analytics

- Default to the current month and include years with the user's expense data.
- Permit past periods and the current month.
- Reject a future year and a month later than the current month in the current
  year, then verify safe fallback and user feedback.
- Reject invalid month/year and invalid or future selected days.
- Confirm category ownership checks and selected-period totals, counts,
  averages, category amounts, percentages, and highest category.
- Confirm day selection narrows the selected-period summary while comparisons
  remain full-month; confirm category selection is consistently applied to both
  comparison months.
- Confirm month/year boundary comparison and empty-data states.

## Execution

Run from the repository root:

```powershell
python -m unittest discover -s tests -q
```

Manual browser checks should use a local instance started with
`python -m backend.app`.
