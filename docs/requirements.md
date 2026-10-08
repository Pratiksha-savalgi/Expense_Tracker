# Expense Tracker Requirements

## Purpose

The Expense Tracker is a web application for individuals to record, organize,
and review personal expenses. It also provides monthly budget tracking and
category-based spending analytics.

### Users and access

- A user can register with a username, role-based access, password, and password confirmation.
- Usernames are unique with regard to letter case (must be case sensitive).
- Usernames must be 3–15 characters long, contain no spaces, and must include a combination of letters, numbers, and at least one allowed special character (`_` or `@`).
- Usernames may contain uppercase letters, lowercase letters, numbers, underscores, and the at-rate symbol (`@`).
- Passwords must be 8–36 characters long, contain no spaces, and must include a combination of uppercase letters, lowercase letters, numbers, and special symbols.
- Passwords should not be common or easily guessable.
- Password and password confirmation must match.
- Users must not be allowed to copy and paste into the password and password confirmation fields.
- A user signs in with their username and password, they can sign out.
- A user must be signed in to access the Dashboard, Expenses, Analytics, and
  expense or budget actions.
- Each user can access only their own expenses, categories, and budgets.
- The "Create Account" button must be enabled only when all the conditions are met.
- The "Sign In" button must be enabled nly when all the conditions are met in the Login Page.

### Role

- Student
- Homemaker
- Professional

- A user must select a user type during registration.
- The selected user type is stored in the user's profile.

## Categories

### Default Categories by User Type

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
- Categories are automatically assigned when a user registers.
- A user's categories remain private and visible only to that user.

## Expense management

An expense consists of:

- A positive amount and must be greater than zero, entered with no more than two decimal places
- One category owned by the signed-in user
- A date that is not later than today
- An optional description

Users can add, view, edit, and delete their own expenses. The date defaults to
today when creating an expense. Deletion requires browser confirmation.




### Expenses and Add Expense filters

- The Expenses page shows amount, category, date, and description.
- Records are shown newest first.
- The Expenses page provides the unfiltered expense ledger and category filter.
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
- A custom date must be a valid date no later than today.
- The popup remains usable on mobile, tablet, and desktop layouts.



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

- The popup opens after login and from authenticated Add Expense actions.
- A valid expense can be created successfully.
- Amounts must be positive and contain no more than two decimal places.
- Future dates are rejected.
- Only the signed-in user's role-specific default categories can be selected.
- The date choices are Today, Yesterday, and Custom; there is no Last 7 Days
  option or subcategory field.
- A success message is displayed after saving an expense.
- After successful save and acknowledgment, the expense form resets for a new entry.

### Expense Management

- Users can view their own expenses.
- Users can edit their own expenses successfully.
- Users can delete their own expenses after confirmation.
- Changes are reflected immediately in the expense list.
- Users cannot access, edit, or delete expenses belonging to other users.

### Expense Filters

- Category and date filters on the Expenses page return matching user-owned
  expenses.
- Date choices (Today, Yesterday, and Custom) save the correct date.
- Custom dates are validated and cannot be later than today.
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