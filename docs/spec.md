# Expense Tracker Specification

This specification describes the current implementation. [requirements.md](requirements.md)
defines the product scope; this document defines its observable behavior and
data rules.

## Authentication and authorization

- Registration collects username, password, role and password confirmation.
- Usernames are stored uniquely with case-insensitive comparison.
- Passwords are hashed before storage.
- Login uses username and password. Invalid credentials produce an error.
- Logout clears the session.
- Dashboard, Expenses, Analytics, budget actions, and expense actions require a
  valid signed-in user.
- Every data operation is scoped to that user. A record belonging to another
  user cannot be viewed, edited, or deleted through an identifier.
- POST forms include a session CSRF token; requests without the valid token are
  rejected.

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

- Categories are user-owned records with a display name and normalized unique
  name.
- The seeded defaults are Food, Utilities, Transport, Household, Health,
  Shopping, Education, Entertainment, Bills, and Other.
- The form's custom-category option creates or reuses a normalized category
  when a valid expense is saved.
- Category normalization collapses whitespace and standardizes capitalization.
- Legacy free-text expense categories are normalized and linked to a user-owned
  category during database initialization without discarding expense rows.

### Create and edit

- Create and edit forms default new expense dates to today and render a browser
  maximum-date constraint.
- JavaScript checks date input and provides immediate browser validation.
- The backend independently parses and validates amount, category, and date
  before saving.
- Validation failures return the form with user feedback and preserve entered
  values where possible.
- Successful create/edit operations redirect to the Dashboard.

### List, filters, totals, analytics, and deletion

- The Expenses page lists a user's records newest first, with amount, category,
  date, description, and edit/delete actions.
- The Expenses page is the unfiltered ledger, optionally filtered by category.
- The Add Expense page follows the AddExpense visual hierarchy: Amount,
  Category and Date controls side by side, Description, and Save. The Date
  controls provide Today, Yesterday, Last 7 Days, and a custom date picker.
  Today is selected by default. The active date period drives both the date
  used for the new expense and the existing-record preview; there is no second
  transaction-date input or duplicate date filter.
- Today saves today's date; Yesterday saves the previous calendar date; Last 7
  Days saves today's date; Custom saves the selected date. The Category choice
  is used both for the new expense and for the existing-record preview.
- Today includes only today. Yesterday includes only the preceding calendar
  day. Last 7 Days includes today and the preceding six calendar days. Custom
  Date includes only the selected calendar date.
- Selecting a date preset or changing category submits a filter-only request
  immediately, preserves unsaved values, and never saves the expense. The
  selected date and category update the existing-record preview and summary.
- A custom date must be valid and not later than today. Invalid dates are
  reported and the page safely falls back to Today.
- The total, record count, average, highest-spending category, and category
  breakdown on Add Expense are computed from the same filtered existing records.
- Saving a new expense uses the selected period's corresponding date and
  category, then refreshes matching existing records and summaries.
- The selected date window is passed to Analytics. Analytics applies it to the
  selected-period summary and category distribution; its existing current vs
  previous full-month comparison remains unchanged.
- Quick-filter active styling and accessible pressed state on Add Expense represent exactly
  one selected period. Choosing a custom date clears the quick-filter active
  state; choosing a quick filter clears custom selection state.
- The integrated date controls wrap appropriately on tablet and mobile Add
  Expense layouts.
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
- An optional date period passed from Add Expense (`today`, `yesterday`,
  `last7`, or `custom` with `date`) narrows the selected-period summary and
  category distribution; it does not narrow the yearly chart's full-month
  values.
- Invalid period selections show feedback and fall back to the current month;
  an invalid day is cleared. An unowned category is cleared with feedback.
- Year choices include the current year and years with the user's expenses,
  excluding future years.
- The selected-period summary and category distribution honor day and category
  filters. The yearly monthly-spending chart honors the selected year and
  category filter, but each chart point represents a full calendar month and
  does not use the selected day.
- The yearly chart includes January through the current month for the current
  year, and January through December for a past year. Monthly budget amounts are
  plotted against monthly spending. Hovering or keyboard-focusing a desktop
  month point, or tapping a touch-screen point, reveals its budget, spent,
  remaining, and budget-status details.
- Empty category data is rendered as an empty state, not as an error.

## AI Agent assistant

The Phase 1 assistant is a signed-in user's conversational, read-only way to
ask about their own financial records. The detailed scope and security
requirements are in [requirements.md](requirements.md).

### User interactions

- The user opens the assistant from its chat entry point, reads messages from
  the current session, enters a natural-language question, and receives a
  response in the conversation.
- The conversation supports questions about total spending, spending by
  category, top expenses, budget status, and comparisons between months.
- When a question is unclear or the requested information is unavailable, the
  assistant asks for clarification or explains that it cannot answer from the
  available records. A missing period defaults to the current month.
- Answers are short chat paragraphs. Tables, HTML, and report headings are not
  used.

### Request and response behavior

- Groq selects a backend-approved retrieval tool; the backend validates its
  arguments, injects the signed-in user, executes parameterized reads, and
  supplies structured results for a grounded response.
- Server-side memory is bounded, user-scoped, and supplementary context only.
- Expense descriptions, categories, notes, memory, and retrieval output are
  untrusted data and never override system policy.
- The assistant cannot generate SQL or choose a user ID.
- CRUD tools exist behind `ENABLE_CRUD_AGENT=0` by default. When enabled,
  every mutation is validated and requires a one-use, expiring confirmation.
- Existing expense/budget routes and the intent-based read-only path remain
  available for migration and rollback.
- See [ai-agent-architecture.md](ai-agent-architecture.md) for the full data
  flow, tool registry, confirmation workflow, memory, and security model.

## Persistence

SQLite stores:

- `users`: unique username and password hash
- `categories`: user ID, display name, normalized name
- `expenses`: user ID, amount, category display value and category ID, date,
  description
- `budgets`: user ID, month, year, amount, timestamps
- `assistant_messages`: bounded user/assistant history, scoped by user ID
- `assistant_pending_actions`: expiring, single-use, user-scoped confirmations

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
