# Design Document

## 1. Overview

This project is a simple Expense Tracker web application for individuals to record and manage personal expenses. The system allows users to create an account, log in, add expenses, view their records, edit them, delete them, filter by category and date, and see the total amount spent.

The project follows the source documentation in this repository and stays within the approved technology stack:

- HTML
- CSS
- JavaScript
- Flask
- SQLite

The application is intentionally simple, beginner-friendly, and focused only on the features described in the project requirements and specification.

---

## 2. Project goals

The main goals are:

- let a user create an account and log in
- let the user add, view, edit, and delete expenses
- organize expenses using categories and dates
- display total spending for the logged-in user
- ensure each user can only access their own expenses
- keep the app simple and easy to use

---

## 3. Scope

### In scope

- user registration
- user login
- secure session-based access
- add new expenses
- view all expenses for the logged-in user
- edit an existing expense
- delete an expense after confirmation
- filter expenses by category and date
- display total spending
- enforce user-specific access control
- validation for invalid input

### Out of scope

- budget management
- payment method tracking
- search by keyword
- multi-user admin functionality
- advanced analytics or graphs
- external libraries or frameworks beyond the approved stack
- payment-method tracking
- fields not described in the requirements; Module A now explicitly includes subcategory and Liability/Savings

---

## 4. System context

The application follows a simple client-server architecture:

1. User interacts with browser pages and forms.
2. HTML provides page structure.
3. CSS handles styling and layout.
4. JavaScript supports interaction details such as delete confirmation and UI filtering.
5. Flask handles authentication, validation, routing, business logic, and data access.
6. SQLite stores user accounts and expense records.

The browser communicates with Flask. Flask communicates with SQLite. The browser does not talk directly to the database.

---

## 5. Architectural design

### 5.1 Presentation layer

This layer includes the HTML templates and static assets:

- templates/register.html
- templates/login.html
- templates/add_expense.html
- templates/view_expenses.html
- templates/edit_expense.html
- static/style.css
- static/script.js

Responsibilities:

- render forms and pages
- show validation messages and errors
- allow user interaction with expense actions
- collect user input for registration, login, and expense forms
- support delete confirmation and filtering in the browser

### 5.2 Application layer

The Flask app is the core application logic component.

Responsibilities:

- route registration and request handling
- user authentication and session handling
- validation of all input values
- database read/write logic
- expense CRUD operations
- filtering logic by category and date
- total calculation for the logged-in user
- authorization checks to prevent cross-user access

### 5.3 Data layer

SQLite is used to persist data.

Responsibilities:

- store user accounts
- store expense records
- store user-owned categories and category-owned subcategories
- keep records linked to the owning user
- allow retrieval and manipulation of only the logged-in user’s data

---

## 6. Business data flow analysis

The system-level DFD for the Expense Tracker is based on the actual business behavior of the application and excludes project-management documentation, lifecycle activities, and implementation architecture.

### External entities

- User

### Core business processes

- Register User
- Authenticate User (access control only)
- Maintain Expense Records
- View Expense Records
- Filter Expense Records
- Calculate Total Spending

Authentication is treated as an access-control process and is kept separate from the main business data flow for expense management.

### Data stores

- User Accounts
- Expense Records

### Major data flows

- Registration details flow from the User to the Register User process.
- Login credentials flow from the User to the Authenticate User process.
- Authentication status and validation results return to the User.
- Expense details flow from the User to the Maintain Expense Records process.
- Expense records are stored in the Expense Records data store.
- Expense queries and filtered requests are routed through the View Expense Records and Filter Expense Records processes.
- Total expense values are produced by the Calculate Total Spending process and returned to the User.

The business DFDs are stored here:

- [Level 0 DFD](visuals/data-flow-diagrams/context_diagram.svg)
- [Level 1 DFD](visuals/data-flow-diagrams/level1-expense-tracker-dfd.svg)

---

## 7. Functional design

### 7.1 User registration

The user lands on the registration page and submits details.

Required behavior:

- valid details are accepted
- missing email is rejected
- duplicate email is rejected
- registered user is saved securely
- password is not stored as plain text

### 7.2 User login

The user enters their login credentials on the login page.

Required behavior:

- valid credentials allow access
- invalid credentials show an error
- unauthenticated users cannot access expense pages

### 7.3 Add expense

The logged-in user opens the Add Expense page and submits expense details.

Fields:

- amount
- main category
- optional subcategory
- date
- expense type (Liability or Savings)
- description

Validation rules:

- amount must be greater than 0 and use no more than two decimal places
- category is required
- expense type must be Liability or Savings
- date must be valid
- values must be validated before saving

The category dropdown contains built-in categories and per-user custom
categories. Selecting a category updates its subcategory choices. A custom
subcategory for an existing category can be saved directly from the form;
when its category is also new, both are created with the expense.

### 7.4 View expenses

The logged-in user can view their expenses.

The page displays:

- amount
- category
- subcategory when present
- Liability/Savings type
- date
- description

The user sees only their own records.

### 7.5 Edit expense

The user selects an existing expense and edits its details.

Behavior:

- valid changed data is saved
- invalid data is rejected
- only the logged-in user’s record can be edited

### 7.6 Delete expense

The user selects an expense to delete.

Behavior:

- system asks for confirmation before deletion
- if confirmed, the record is removed
- deleted expense disappears from the current list
- no other user’s expenses can be deleted

### 7.7 Filtering

The user can filter expenses by category and date.

Behavior:

- list updates to only matching records
- filter works for the current user only
- clearing filters restores the full list for that user

### 7.8 Total spending

The application calculates the total of the current user’s expenses.

Behavior:

- total updates after add, edit, or delete
- total is shown on the expense view page
- totals are based on the logged-in user’s data only

---

## 8. Version 2 Design Extensions

### 8.1 Monthly Budget Tracking Design

#### Budget storage strategy

The system stores monthly budget information separately from individual
expense records. A dedicated budget table is recommended so that budget
values can be managed independently and updated without altering the
expense record history.

Recommended fields:

- id
- user_id
- month
- year
- budget_amount
- created_at
- updated_at

This supports one budget per user per month, which avoids duplicate budget
entries and keeps comparisons clear.

#### Budget calculation logic

For a given user and selected month, the system should: 

1. read the budget value for that month
2. sum all expense amounts for the same user and month
3. calculate remaining balance = budget_amount - total_spent
4. calculate utilization percentage = (total_spent / budget_amount) * 100

If the user has not configured a budget for that month, the system should
show a default empty-state message rather than calculate a misleading value.

#### Remaining balance calculations

remaining_balance = configured_budget - total_monthly_spending

The remaining balance is shown in the dashboard and relevant budget panel.
If the value is negative, the system should display it as overspent and
highlight the state as exceeded.

#### Warning threshold logic

The system should evaluate a warning threshold as a ratio of actual spend vs
budget. A common design is to warn when utilization is at or above 80% or
90% of the configured monthly budget. This should be configurable in the
backend logic but easy to display in the UI.

Example:

- warning threshold = 80%
- budget = ₹20,000
- spend = ₹16,500
- utilization = 82.5%
- result = warning banner displayed

#### Exceeded budget logic

If total_monthly_spending > budget_amount, the status should change to
exceeded. The alert should be visible in the dashboard and can also be used
in the budget summary box. This is useful for highlighting overspending at a
glance.

### 8.2 Analytics Design

#### Category aggregation flow

The analytics module should retrieve all valid expenses for the logged-in
user and selected month. It then groups those records by category and sums
their amounts.

Flow:

1. User selects a month.
2. Flask queries expenses for that month and user.
3. The backend groups by category.
4. The backend calculates total monthly spend.
5. Each category total is converted into a contribution percentage.
6. Results are sent to the dashboard template for rendering.

#### Analytics computation logic

For each category:

category_total = sum of expense amounts for that category
category_percentage = (category_total / total_monthly_spend) * 100

The dashboard can then show:

- category name
- total spent in the category
- percentage share of total monthly spend
- highlighted highest and lowest categories

#### Dashboard integration

The budget and analytics panels should be integrated into the main dashboard
or expense summary page. This keeps the user in the normal workflow while
allowing quick review of their spending. The pages should remain simple and
not require complex navigation.

#### Visualization requirements

Visualization is recommended in a lightweight form for a small personal
application. Simple bar charts, progress bars, or donut-style summary cards
are enough to meet the requirement without adding unnecessary complexity.

The UI should support:

- category totals
- percentage bars
- monthly comparison against budget
- empty-state handling when no expense data exists

### 8.3 Data Model Design

The data model uses `users`, `expenses`, `categories`, and `subcategories`
for Module A, plus `budgets` for Version 2.

#### Core entities

- `users`: stores account and authentication data
- `expenses`: stores user-owned entries, amount, category reference, optional
  subcategory reference, Liability/Savings type, date, and description
- `categories`: stores normalized category names per user
- `subcategories`: stores normalized subcategory names per category
- `budgets`: stores month-based budget limits per user

Category names are normalized by trimming and collapsing whitespace and by
case-folding the comparison key. The display name is retained separately.
Built-in categories and subcategories are added idempotently for each user;
custom names remain user-scoped. Existing free-text categories are migrated
to per-user category rows without dropping expense records. Existing rows
default to Liability and have no subcategory until one is selected.

#### Budget table design

```sql
CREATE TABLE budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    budget_amount TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, month, year),
    FOREIGN KEY(user_id) REFERENCES users(id)
);
```

This model keeps the budget data separate from the expense log, lets the
system support one active budget per month, and makes budget updates easy to
control.

#### Query requirements for analytics

The following analytical queries are required:

- total expense by category for a user and month
- percentage contribution by category
- monthly category summary for dashboard display
- budget vs actual spend calculation
- highest-spending and lowest-spending category detection

Example query patterns:

```sql
SELECT category, SUM(amount) AS total
FROM expenses
WHERE user_id = ? AND expense_date BETWEEN ? AND ?
GROUP BY category
ORDER BY total DESC;
```

```sql
SELECT SUM(amount) AS monthly_total
FROM expenses
WHERE user_id = ? AND expense_date BETWEEN ? AND ?;
```

```sql
SELECT month, year, budget_amount
FROM budgets
WHERE user_id = ?
ORDER BY year DESC, month DESC;
```

These queries should be used in the Flask backend to produce summary
values for the dashboard and analytics panel.

### 8.4 Route and Page Design

The Version 2 design should extend the current application flow without
changing the basic user journey.

#### Route design

- `GET /dashboard` or equivalent dashboard view: displays the monthly budget card, remaining amount, utilization percentage, and spending summary.
- `POST /budget` or similar: creates or updates a month budget.
- `GET /analytics`: shows category totals, percentages, and visual summary for the selected month.
- `GET /expenses` or related expense listing: keeps the original expense list and filters available.

#### Page design

- Budget panel on the dashboard: shows current month budget, remaining amount, and status indicator.
- Analytics panel: shows category totals and percentage bars or chart blocks.
- Filter controls: selected month dropdown or date selector for analytics.
- Empty-state blocks: shown when no data exists for a selected month.

This maintains a simple layout where the user remains in the same workflow:
login, view expenses, review budget, analyze categories, and continue working
with expense records.

### 8.5 Security Design

The Version 2 features must follow the same access-control model as the base
application.

Key rules:

- budget records belong to the logged-in user
- analytics data is limited to the current user’s expenses
- a user cannot view another user’s monthly budget or category totals
- all budget and analytics routes must require active authentication
- no personally sensitive financial data should be exposed outside the
  authenticated session

The user-specific access model remains identical to the base Expense Tracker
and is not expanded beyond the logged-in user scope.

### 8.6 Validation Design

Validation is required for both budget management and analytics presentation.

#### Budget validation

- amount must be greater than zero
- month and year must be valid
- duplicate month entries for the same user should be handled by update
- empty or invalid values must trigger user-friendly messages

#### Analytics validation

- totals are computed only for valid expenses for the selected month
- invalid month values are rejected or reset to the current month
- empty categories and empty months show a clean no-data message
- calculations must avoid division by zero when total spend is zero

### 8.7 User Experience Design

The user experience should remain clear and lightweight.

Design goals:

- show budget status without overwhelming the user
- keep per-month financial summaries visible and understandable
- highlight warning and exceeded states with color and text labels
- use simple category bars or summary cards instead of complex interfaces
- keep expense entry and dashboard review in the same workflow

This approach matches the project’s beginner-friendly positioning while still
providing useful monthly planning and analytics insights.

### 8.8 Database Design Changes

The current SQLite design should be extended with a budget table and a
limited analytics query approach. No full redesign of the existing
architecture is required.

#### Recommended schema additions

```sql
CREATE TABLE budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    budget_amount TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, month, year),
    FOREIGN KEY(user_id) REFERENCES users(id)
);
```

The `budget_amount` should be stored as a decimal-friendly value in SQLite,
matching the existing expense amount behavior. The user_id and month/year
combination ensures one active budget per user per month.

#### Query requirements for analytics

The following analytical queries are required:

- total expense by category for a user and month
- percentage contribution by category
- monthly category summary for dashboard display
- budget vs actual spend calculation
- highest-spending and lowest-spending category detection

Example query patterns:

```sql
SELECT category, SUM(amount) AS total
FROM expenses
WHERE user_id = ? AND expense_date BETWEEN ? AND ?
GROUP BY category
ORDER BY total DESC;
```

```sql
SELECT SUM(amount) AS monthly_total
FROM expenses
WHERE user_id = ? AND expense_date BETWEEN ? AND ?;
```

```sql
SELECT month, year, budget_amount
FROM budgets
WHERE user_id = ?
ORDER BY year DESC, month DESC;
```

These queries should be used in the Flask backend to produce summary
values for the dashboard and analytics panel.

### 8.9 Version 2 Design Summary

The Version 2 design intentionally extends but does not replace the current
Expense Tracker model. It adds user-specific budget tracking and lightweight
category analytics while maintaining the clean architecture already used by
Flask and SQLite.

---

## 7. Data model

### 7.1 Users table

The users table stores account information.

Suggested fields:

- id: primary key
- username: unique, required
- password_hash: hashed password value
- created_at: optional timestamp

Notes:

- username is used as the unique login identifier
- password is stored using a secure hash, not plain text

### 7.2 Expenses table

The expenses table stores each expense entry.

Suggested fields:

- id: primary key
- user_id: foreign key to users.id
- amount: positive decimal value with no more than two fractional digits
- category_id: foreign key to the owning user's category
- category: canonical display value retained for compatibility
- subcategory_id: optional foreign key to a subcategory of category_id
- expense_type: required Liability or Savings value; legacy rows default to Liability
- expense_date: valid date
- description: short description
- created_at: optional timestamp

Notes:

- each expense must belong to a registered user
- every query must include the logged-in user’s id to prevent cross-user access

### 7.3 Categories and subcategories

- `categories` stores a name, normalized comparison name, and owning user ID.
- `subcategories` stores a name, normalized comparison name, and parent category ID.
- Category names are trimmed, whitespace-collapsed, and case-folded for matching.
- Built-in categories/subcategories are seeded idempotently for each user; custom values remain private to that user.
- Existing expense category text is migrated to category records without dropping expense rows.

---

## 8. Route and page design

### 8.1 Authentication pages

- Register page
  - allows account creation
  - validates email and password requirements
- Login page
  - authenticates the user
  - redirects to the expense area after success

### 8.2 Expense pages

- Add Expense page
  - form for amount, main category, optional subcategory, date, Liability/Savings type, and optional description
  - common category/subcategory defaults and custom-add choices
  - immediate save action for a custom subcategory under an existing category
- View Expenses page
  - displays the logged-in user's expenses, including category, optional subcategory, and type
  - includes filter controls and total amount
- Edit Expense page
  - form prefilled with existing expense, category, subcategory, and type values
  - saves modifications

### 8.3 Flask route responsibilities

Suggested route structure:

- GET /register
- POST /register
- GET /login
- POST /login
- POST /logout
- GET /expenses
- GET /expenses/add
- POST /expenses/add
- GET /expenses/<id>/edit
- POST /expenses/<id>/edit
- POST /expenses/<id>/delete
- POST /categories/<category_id>/subcategories (authenticated, CSRF-protected)

All expense routes should require authentication and ensure the user is only working with their own records.

---

## 9. Security design

The application must protect user and expense data.

### Security rules

- users must register and log in before accessing expense features
- only authenticated users can create or manage expenses
- each user can access only their own expenses
- passwords are never stored in plain text
- database queries must use the logged-in user id as a filter
- invalid user input is rejected before saving
- application should not expose another user’s records through URLs or forms

---

## 10. Validation design

Validation is required before saving data.

### Expense validation

- amount must be greater than 0 and use no more than two decimal places
- category must be present
- expense type must be Liability or Savings
- selected category must belong to the authenticated user
- selected subcategory must belong to the selected category
- date must be a valid date
- description is accepted as entered, but should be treated as a short text value

### User validation

- email must be present
- duplicate email should be rejected
- login credentials must match an existing stored user

---

## 11. User experience design

The application should be simple and easy to use.

Design principles:

- clear forms for registration, login, add, and edit
- minimal confusion in the user flow
- visible action buttons for add, edit, and delete
- straightforward list or table layout for expenses
- simple filtering controls for category and date
- dropdown-based category and dependent subcategory selection, with custom-add actions
- clear total spending summary
- plain error messages for invalid input

---

## 12. Non-functional requirements

### Usability

The application should be easy for a normal user to understand and operate.

### Performance

The app should respond quickly for normal operations such as login, adding an expense, and listing expenses.

### Reliability

Saved expense data should not be lost during normal usage.

### Security

The app must restrict user data access and avoid storing passwords in plain text.

---

## 13. Implementation constraints

The following constraints are mandatory:

- use only HTML, CSS, JavaScript, Flask, and SQLite
- do not add unrelated features or technologies
- keep the app simple and beginner-friendly
- keep frontend, backend, and database responsibilities separate
- follow the project plan and implementation order
- do not modify the source requirements unless explicitly requested

---

## 14. Testing and acceptance criteria mapping

The design supports the acceptance requirements in the project documentation:

- registration works with valid details
- invalid or duplicate email is rejected
- login works with valid credentials
- invalid credentials fail gracefully
- users can add, view, edit, and delete expenses
- filtering by category and date works correctly
- total spending is displayed accurately
- each user sees only their own expense records

---

## 15. Summary

The Expense Tracker is a small Flask + SQLite web application designed for personal expense management. It combines HTML pages, CSS styling, JavaScript interaction support, and server-side Flask logic to provide a secure, user-specific expense management experience. The design stays within the approved requirements and keeps the system simple, practical, and easy to extend only within the documented scope.
