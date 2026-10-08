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

### User Types

- Student
- Homemaker
- Working Professional

- A user must select a user type during registration.
- The selected user type is stored in the user's profile.

## Categories

### Default Categories by User Type

#### Student

- Education
- Books
- Transport
- Food
- Entertainment
- Mobile Recharge
- Other

#### Homemaker

- Groceries
- Utilities
- Household
- Health
- Education
- Bills
- Other

#### Working Professional

- Food
- Transport
- Bills
- Shopping
- Health
- Investments
- Entertainment
- Other

### Constraints

- Users can select only from categories available to their user type.
- Categories are automatically assigned when a user registers.
- A user's categories remain private and visible only to that user.

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



### Expenses and Add Expense filters

- The Expenses page shows amount, category, date, and description.
- Records are shown newest first.
- The Expenses page provides the unfiltered expense ledger and category filter.
- The Add Expense page uses the AddExpense visual hierarchy: Amount spans the
  form; Category and Date controls share a row; Description and Save follow.
- The Date controls provide Today, Yesterday and a custom date picker. Today is selected by default.  - This single selected period controls the existing-record preview and the date saved for the new
  expense.
- Today saves today's date; Yesterday saves yesterday's date Custom saves the selected calendar date.
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
-- A newly registered user has a default budget of 0 for the current month.
- Users can create or update the budget using the Edit Budget action. 
- A user can create or update a budget for a selected month and year.
- A budget amount must be positive and use no more than two decimal places.
- There is one budget per user, month, and year; saving the same period updates
  its existing budget.
- Budget status is “not set” when no budget exists, “warning” when utilization
  is at least 80% and spending does not exceed the budget, “exceeded” when
  spending is greater than the budget, and “on track” otherwise.
- Budgets are stored separately from expenses.

### Recent Expenses

- The Dashboard displays a Recent Expenses section.
- The Recent Expenses section provides Year, Month, and Day filters.
- The expense list refreshes automatically when a filter changes.
- Only expenses belonging to the signed-in user are displayed.
- Records are displayed newest first.
- Future years and future months are not allowed.
- A selected day must be valid and cannot be later than today.
- Empty periods display a useful empty state.




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

### Registration

- A new user can register with a unique username.
- Duplicate usernames are rejected.
- Password and password confirmation must match.
- A user type (Student, Homemaker, or Working Professional) must be selected during registration.
- The selected user type is stored successfully.
- The user receives the correct default categories based on the selected user type.

### Login and Logout

- A registered user can sign in using valid credentials.
- Invalid credentials are rejected with an appropriate error message.
- Protected pages redirect unauthenticated users to the sign-in page.
- A signed-in user can sign out successfully.
- Signed-out users cannot access protected pages without signing in again.

### Add Expense

- A valid expense can be created successfully.
- Amounts must be positive and contain no more than two decimal places.
- Future dates are rejected.
- Only categories belonging to the signed-in user can be selected.
- A success message is displayed after saving an expense.
- After successful save and acknowledgment, the expense form resets for a new entry.
- Active filters remain unchanged after saving.

### Expense Management

- Users can view their own expenses.
- Users can edit their own expenses successfully.
- Users can delete their own expenses after confirmation.
- Changes are reflected immediately in the expense list.
- Users cannot access, edit, or delete expenses belonging to other users.

### Expense Filters

- Category filtering returns only matching user-owned expenses.
- Date quick filters (Today, Yesterday, Last 7 Days) return correct results.
- Custom date filtering returns correct results.
- Summary values and expense previews update automatically when filters change.
- Invalid dates and future dates are rejected.

### Dashboard

- The dashboard displays budget, expenses, remaining budget, utilization, and status correctly.
- New users see a default budget value of 0 when no budget has been set.
- Users can create or update a budget using the Edit Budget action.
- Dashboard values reflect the signed-in user's data only.
- Budget status is calculated according to the defined rules.

### Dashboard Recent Expenses Filters

- The Recent Expenses section displays only the signed-in user's expenses.
- Year, Month, and Day filters return the correct expense records.
- Changing a filter refreshes the expense list automatically.
- Future years, future months, and invalid dates are rejected.
- Empty filter results display a useful empty state.

## Budget Management
 
- Users can create a budget for a selected month and year.
- Budget amounts must be positive and contain no more than two decimal places.
- Saving a budget for an existing month and year updates the existing budget.
- Budget calculations correctly reflect expenses for the selected period.
- Budget utilization and status are calculated accurately.
 
## Analytics
 
- Analytics display spending, expense count, average expense, category totals, and category percentages correctly.
- Analytics display the highest-spending category for the selected period.
- Year, Month, Day, and Category filters return accurate results.
- Previous-month comparisons use the correct user-scoped data.
- Future years, future months, and invalid dates are rejected.
- Empty periods display a useful empty state.
 
## User Types and Categories
 
- Student users receive the Student default category set.
- Homemaker users receive the Homemaker default category set.
- Working Professional users receive the Working Professional default category set.
- Users can add custom categories.
- Category names are normalized to prevent duplicates.
- Users can access only their own categories.
 
## Security and Data Protection
 
- Passwords are stored as hashes and never as plain text.
- State-changing requests require valid CSRF protection.
- All expenses, categories, budgets, and analytics are scoped to the authenticated user.
- Users cannot access data belonging to other users.
- Application data persists correctly in SQLite.
 
## Responsive User Interface
 
- Registration, Login, Dashboard, Expenses, Budget, and Analytics pages remain fully functional on desktop devices.
- Registration, Login, Dashboard, Expenses, Budget, and Analytics pages remain fully functional on mobile devices.
- Responsive layouts match the approved UI designs in the design folder.
- Core functionality remains accessible across supported screen sizes.