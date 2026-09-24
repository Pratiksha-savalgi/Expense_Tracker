# Implementation Plan

This plan describes how to build a simple Expense Tracker for individuals to record and manage personal expenses in one place. It follows `requirements.md`, `intent.md`, `spec.md`, and `tech-stack.md`. The approved technologies are HTML, CSS, JavaScript, Flask, and SQLite only.

The application will let a logged-in user add, view, edit, and delete expenses, assign a category, filter by category and date, and see total spending. Each user will see and manage only their own expenses.

## Proposed project folder and file structure

```
expense_tracker_app/
  requirements.md
  intent.md
  spec.md
  tech-stack.md
  plan.md
  app.py
  static/
    style.css
    script.js
  templates/
    register.html
    login.html
    add_expense.html
    view_expenses.html
    edit_expense.html
```

SQLite will store user accounts and expense records. The database file is created and used by the application when it runs; it is not a source file to write by hand.

## What each file will be responsible for

**`app.py`**  
Flask application. Handles registration, login, credential checks, and all expense operations: add, view, edit, delete, filter by category and date, and total spending. Applies validation and makes sure a user can access only their own expenses.

**`static/style.css`**  
Styles the pages so forms, the expense list or table, errors, and delete confirmation are simple and easy to use.

**`static/script.js`**  
Handles page interactions: form actions, delete confirmation, and filtering by category and date.

**`templates/register.html`**  
Page for creating an account.

**`templates/login.html`**  
Page for logging in with username/email and password.

**`templates/add_expense.html`**  
Page for entering amount, category, date, and a short description, then saving a new expense.

**`templates/view_expenses.html`**  
Page that shows the user’s expenses in a list or table (amount, category, date, and description), filter controls for category and date, total spending, and actions to edit or delete.

**`templates/edit_expense.html`**  
Page for changing an existing expense and saving the updated details.

## Implementation order

1. Create the folders and files listed above, and a Flask app that can show the HTML pages.
2. Connect Flask to SQLite so user accounts and expenses can be stored and kept during normal use.
3. Build registration and login so the user must create an account and log in before managing expenses.
4. Build Add Expense and View Expenses for the logged-in user.
5. Build Edit Expense and Delete Expense (delete asks for confirmation, then removes the record from the list).
6. Add filtering by category and date, and display the total amount spent.
7. Apply CSS so the application stays simple and easy to use.
8. Walk through the manual verification checklist.

## How frontend, Flask, and SQLite work together

```
User (browser)
  HTML pages and forms
  CSS for layout and readability
  JavaScript for interactions
        |
        v
Flask (app.py)
  Checks login
  Validates input
  Add / view / edit / delete
  Filter and total
        |
        v
SQLite
  User accounts
  Expense records
```

- **HTML** structures the screens: register, login, add/edit forms, and the expense list or table with totals and filter controls.
- **CSS** makes those screens readable and easy to follow.
- **JavaScript** supports form actions, showing errors where needed, delete confirmation, and filtering in the list or table.
- **Flask** receives what the user submits, checks credentials, applies rules, reads and writes SQLite, and returns the HTML pages.
- **SQLite** stores accounts and expenses (amount, category, date, description) in one place.

The browser talks to Flask. Flask talks to SQLite. Flask then shows updated pages to the user.

## How user authentication and user-specific expenses will work

1. The user opens the application and creates an account on the registration page with valid details.
2. If the email is missing or already exists, an error is shown and no account is created.
3. The user logs in with username/email and password and clicks Login.
4. Flask checks the credentials against SQLite.
5. Valid credentials allow access to expense pages. Invalid credentials show an error.
6. The user must be logged in before adding, viewing, editing, or deleting expenses.
7. Every expense belongs to a registered user.
8. When Flask retrieves, updates, or deletes expenses, it only uses records that belong to the logged-in user, so one user cannot see or manage another user’s expenses.
9. Passwords are not stored as plain text.

## How add, view, edit, and delete will work

**Add**  
The user selects Add Expense, enters amount, category, date, and a short description, and clicks Save. Flask validates the details. If they are valid, Flask saves the expense in SQLite for that user.

**View**  
The user selects View Expenses. Flask retrieves that user’s recorded expenses from SQLite and displays them in a list or table. Amount, category, date, and description are visible.

**Edit**  
The user selects an expense and clicks Edit, changes the required details, and clicks Save. Flask updates that user’s expense in SQLite. This is for correcting information that was entered incorrectly.

**Delete**  
The user selects an expense and clicks Delete. The application asks for confirmation. After the user confirms, Flask removes that expense from SQLite. The deleted expense is removed from the list. This is for incorrect, unwanted, or no longer required records.

## How category/date filtering and total spending will work

**Category**  
The user assigns a category when adding or editing an expense. An expense must have a category so spending can be organized and understood.

**Filter**  
On the view page, the user can filter expenses by category and date. Flask (and JavaScript for the page interaction) limits the list or table to matching records for that user. This supports checking spending by date or category.

**Total spending**  
The view page shows the total amount spent. Flask calculates the total from the logged-in user’s expenses and the system displays that total expense amount.

## Validation and security considerations

**Validation**

- Expense amount must be greater than 0.
- An expense must have a category.
- The expense date must be a valid date.
- Details are validated before an expense is saved.
- An expense must belong to a registered user.

**Security**

- The user must create an account and log in before managing expenses.
- Users can access only their own expenses.
- Passwords must not be stored as plain text.

**Other quality points from the specification**

- The application should be simple and easy to use.
- It should respond within a reasonable time for normal operations.
- Saved expense data should not be lost during normal application usage.

## Basic manual verification checklist

Use this checklist after the steps above. It matches the specification’s acceptance criteria and related rules.

**Registration**

- [ ] User can register with valid details.
- [ ] Error is shown for missing email.
- [ ] Error is shown for an existing email.

**Login**

- [ ] User can log in with valid credentials.
- [ ] Error is shown for invalid credentials.
- [ ] User cannot manage expenses until logged in.

**Add expense**

- [ ] User can add an expense with amount, category, date, and description.
- [ ] Amount greater than 0 is saved.
- [ ] Amount that is not greater than 0 is not saved.
- [ ] Expense without a category is not saved.
- [ ] Invalid date is not saved.

**View expenses**

- [ ] User can view their expenses in a list or table.
- [ ] Amount, category, date, and description are visible.

**Edit expense**

- [ ] User can edit an existing expense.
- [ ] Updated details are saved.

**Delete expense**

- [ ] Delete asks for confirmation.
- [ ] After confirmation, the expense is deleted.
- [ ] Deleted expense is removed from the list.

**Filter and total**

- [ ] User can filter expenses by category.
- [ ] User can filter expenses by date.
- [ ] System displays the total expense amount.

**User-specific data**

- [ ] A logged-in user sees only their own expenses.
- [ ] A logged-in user cannot view, edit, or delete another user’s expenses.
