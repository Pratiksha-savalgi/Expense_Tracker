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
- extra fields not described in the requirements

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
- category
- date
- description

Validation rules:

- amount must be greater than 0
- category is required
- date must be valid
- values must be validated before saving

### 7.4 View expenses

The logged-in user can view their expenses.

The page displays:

- amount
- category
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
- amount: numeric value
- category: text value, required
- expense_date: valid date
- description: short description
- created_at: optional timestamp

Notes:

- each expense must belong to a registered user
- every query must include the logged-in user’s id to prevent cross-user access

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
  - form for amount, category, date, and description
- View Expenses page
  - displays expenses for the logged-in user
  - includes filter controls and total amount
- Edit Expense page
  - form prefilled with existing values
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

- amount must be greater than 0
- category must be present
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
