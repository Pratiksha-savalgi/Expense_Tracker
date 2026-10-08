# Expense Tracker Specification

This specification describes the current implementation. [requirements.md](requirements.md)
defines the product scope; this document defines its observable behavior and
data rules.

### Authentication and authorization

- Registration collects username, role-based access, password, and password confirmation.
- Usernames are unique with regard to letter case (must be case sensitive).
- Usernames must be 3–15 characters long, contain no spaces, and must include a combination of letters, numbers, and at least one allowed special character (`_` or `@`).
- Usernames may contain uppercase letters, lowercase letters, numbers, underscores, and the at-rate symbol (`@`).
- Passwords must be 8–36 characters long, contain no spaces, and must include a combination of uppercase letters, lowercase letters, numbers, and special symbols.
- Passwords should not be common or easily guessable.
- Password and password confirmation must match.
- Users must not be allowed to copy and paste into the password and password confirmation fields.
- The "Create Account" button must be enabled only when all registration conditions are met.
- Login uses username and password. The "Sign In" button must be enabled only when all login conditions are met.
- Invalid credentials produce an error.
- Logout clears the session.
- A user must be signed in to access the Dashboard, Expenses, Analytics, and add expense or budget actions.
- Every data operation is scoped to the signed-in user. A record belonging to another user cannot be viewed, edited, or deleted.
- Each user can access only their own expenses, categories, and budgets.
- POST forms include a session CSRF token; requests without the valid token are rejected.

## Expense data and behavior

The expense model contains:

| Field | Rule |
| --- | --- |
| Amount | Required, finite, greater than zero, at most two decimal places |
| Category | Required; must belong to the signed-in user |
| Date | Required ISO date; must be today or earlier |
| Description | Optional text |

There is no subcategory or expense-type field in the current model, forms, list,
API behavior, or database schema.

### Categories

- Categories are user-owned records with a display name and normalized unique name.
- Categories are automatically assigned based on the user's selected role during registration.

### Default Categories by Role

#### Student
- Education
- Hostel / Rent
- Food & Dining
- Transportation
- Mobile & Internet
- Books & Stationery
- Entertainment
- Shopping
- Personal Care
- Healthcare
- Gifts
- Other

#### Homemaker
- Groceries
- Household
- Utilities
- Food & Dining
- Healthcare
- Children & Education
- Transportation
- Shopping
- Personal Care
- Gifts & Festivals
- Domestic Help
- Other

#### Professional
- Rent / Housing
- Food & Dining
- Transportation
- Utilities
- Mobile & Internet
- Work & Professional
- Shopping
- Entertainment
- Healthcare
- Personal Care
- Travel
- Subscriptions
- Gifts
- Other

### Constraints

- Users can select only from categories available to their role.
- A user's categories remain private and visible only to that user.
- Category names are normalized by collapsing whitespace and standardizing capitalization.

### Create and edit

- New expense dates default to today.
- Expense dates must not be later than today.
- The amount must be greater than zero and contain no more than two decimal places.
- The selected category must belong to the signed-in user.
- The description is optional.
- The backend validates the expense details before saving.
- Validation failures reopen the Add Expense popup with user feedback and
  preserve entered values where possible.
- Successful creation returns to the page where the popup was opened and shows
  a confirmation. Successful edits follow the edit flow.

### List, filters, totals, analytics, and deletion

- The Expenses page lists a user's records newest first, with amount, category,
  date, description, and edit/delete actions.
- The Expenses page is the unfiltered ledger, optionally filtered by category.
- Add Expense opens as a popup after login and from Add Expense actions on
  authenticated pages; it does not navigate to a standalone entry page.
- The popup contains Amount, a role-specific Category dropdown, Date controls,
  optional Description, and Save. Subcategories and category creation are not
  offered in this form.
- The Date controls provide only Today, Yesterday, and a custom date picker.
  Today is selected by default. Today saves today's date; Yesterday saves the
  previous calendar date; Custom saves the selected calendar date.
- Exactly one date option is active. Selecting a custom date clears the active
  quick-filter state, and selecting a quick filter clears the custom-date state.
- A category must be one of the signed-in user's default categories for their
  registered role.
- Validation failures reopen the popup with entered values and clear feedback.
- A successful save displays a confirmation; acknowledging it leaves a blank
  form ready for another expense.
- A custom date must be valid and not later than today.
- The popup remains usable on mobile, tablet, and desktop layouts.
- Date controls expose the active preset through accessible pressed state and
  visually distinguish the selected option.
- Delete is a POST action with CSRF protection; JavaScript requests confirmation
  before submission. The backend scopes deletion to the signed-in user.

## Dashboard and budgets

- The Dashboard uses the current calendar month and year to show budget amount,
  expenses, remaining amount, utilization, status, and recent expenses.
- `POST /budget` accepts a month, year, and positive amount with at most two
  decimal places. Month/year must be a valid calendar period.
- A unique `(user_id, month, year)` key makes repeated saves update the existing
  budget.
- Budget records are independent of expense rows.
- Status is exceeded when spending is greater than budget, warning at utilization
  of 80% or higher when not exceeded, and on track otherwise. Missing budgets
  show a not-set state.
- The budget form currently accepts any valid month and year; the analytics
  future-period limit does not apply to budget entry.

## Analytics

- `GET /analytics` accepts `year`, `month`, optional `day`, and optional
  user-owned `category`.
- Defaults are the current year and month.
- `year` and `month` must be a valid calendar period no later than the current
  month. The current year cannot select a later month.
- `day`, when supplied, must be a valid day in that month and cannot be later
  than today.
- Invalid period selections show feedback and fall back to the current month;
  an invalid day is cleared. An unowned category is cleared with feedback.
- Year choices include the current year and years with the user's expenses,
  excluding future years.
- The selected-period summary and category distribution honor day and category
  filters. The month-over-month spending and utilization comparison uses full
  calendar months; the category filter is consistently applied to both months.
- Empty category data is rendered as an empty state, not as an error.

## Persistence

SQLite stores:

- `users`: unique username and password hash
- `categories`: user ID, display name, normalized name
- `expenses`: user ID, amount, category display value and category ID, date,
  description
- `budgets`: user ID, month, year, amount, timestamps

Foreign keys and uniqueness constraints support ownership, deletion, and
duplicate prevention. Database initialization creates current tables and
indexes, migrates legacy free-text categories, and removes obsolete
subcategory/expense-type columns and subcategory storage from legacy databases.

## Error and empty states

- Invalid form submissions show actionable messages and do not persist invalid
  expense or budget data.
- Missing or invalid login, category, filter, and analytics selections show
  user-facing feedback.
- Empty expense lists and analytics periods render usable empty states.
- Invalid, future, or malformed custom date filters receive user feedback.

## Non-functional requirements

- Keep the interface usable on desktop and narrow screens.
- Use accessible labels, readable feedback, and keyboard-operable controls.
- Keep money calculations decimal-safe and data access user-scoped.
- Keep the implementation within the existing Flask, SQLite, HTML, CSS, and
  JavaScript stack.
