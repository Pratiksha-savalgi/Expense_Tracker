# Expense Tracker Team Requirements

This document summarizes the current product requirements for implementation
and testing. [docs/requirements.md](docs/requirements.md) and
[docs/spec.md](docs/spec.md) contain the full product and behavioral
specifications.

## Shared requirements

- Use the existing Flask, SQLite, HTML, CSS, and JavaScript stack.
- Authenticate with username and password; hash passwords and protect state
  changes with CSRF tokens.
- Scope expenses, categories, budgets, and analytics to the signed-in user.
- Keep forms labeled, feedback actionable, and layouts usable on small screens.
- Validate on the server even when browser-side validation is provided.
- The current expense fields are amount, category, date, and optional
  description. Do not add subcategory or expense type.

## Module A: Expenses and categories

### Behavior

- Support add, view, edit, and delete for a user's expenses.
- Require a positive amount with at most two decimal places, an owned category,
  and a valid date no later than today.
- Default a new expense date to today; description is optional.
- Provide the seeded default categories and allow user-owned custom categories.
- Normalize category names for capitalization and whitespace.
- Keep the Expenses page as the user-owned ledger with category filtering.
- Provide Today (default), Yesterday, Last 7 Days including today, and a custom
  date picker beside Category in the Add Expense form, matching
  [docs/design/visuals/AddExpense.jpg](docs/design/visuals/AddExpense.jpg).
- Use the selected date period as the new expense date and to filter the
  existing-record list, summary cards, and category analytics. Today and Last 7
  Days save today, Yesterday saves yesterday, and Custom saves the selected
  date. Carry the selected date window into Analytics.
- Changing a date or category selection refreshes matching existing data
  without saving the draft; saving uses the selected date and category.
- Ask for confirmation before deletion and preserve user values on validation
  failure where possible.
- Migrate legacy free-text categories without losing expenses.

### Acceptance

- Valid expenses are saved and can be viewed, edited, and deleted by their owner.
- Invalid amount, category, or date is rejected by the server.
- Future expense dates are blocked by both browser and server validation.
- Category/date filters and totals are correct and user-scoped.
- No subcategory or expense-type UI, validation, API behavior, or model field
  remains.

## Module B: Budgets and analytics

### Budget behavior

- Store one budget per user, month, and year; saving an existing period updates
  it.
- Require a valid month/year and positive amount with at most two decimal
  places.
- Show current-month budget, spending, remaining amount, utilization, status,
  and recent records on Dashboard.
- Statuses are not set, on track, warning at 80% utilization or above without
  exceeding the budget, and exceeded when spending is greater than budget.
- A budget may be saved for any valid period; analytics date limits do not
  restrict budget entry.

### Analytics behavior

- Provide year, month, day, and category filters.
- Allow only the current month and past months; disallow future years and future
  months of the current year.
- Reject selected days that are invalid or later than today.
- Show selected-period totals, count, average, highest category, category
  amounts, and contribution percentages.
- Compare full-month spending and budget utilization with the previous calendar
  month. Apply category filter to both months; day narrows the selected-period
  summary only.
- Show an empty state when no matching records exist.

## Integration and verification

Shared data fields and validation are defined in the specification; both
modules must use that contract. Run:

```powershell
python -m unittest discover -s tests -q
```

Then manually verify the main flows in a browser at desktop and mobile widths.
