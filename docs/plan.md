# Implementation Plan

This plan describes how to build a simple Expense Tracker for individuals to record and manage personal expenses in one place. It follows `requirements.md`, `intent.md`, `spec.md`, and `tech-stack.md`. The approved technologies are HTML, CSS, JavaScript, Flask, and SQLite only.

The application lets a logged-in user add, view, edit, and delete expenses; select a main category and optional subcategory; classify each entry as Liability or Savings; filter by category and date; and see total spending. Each user sees and manages only their own expense and category data.

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

SQLite stores user accounts, expenses, per-user categories and subcategories, and monthly budgets. The database file is created and used by the application when it runs; it is not a source file to write by hand.

## What each file will be responsible for

**`app.py`**  
Flask application. Handles registration, login, credential checks, expense CRUD, category/subcategory resolution, filtering, and totals. Validates positive amounts to two decimal places and ensures a user can access only their own data.

**`static/style.css`**  
Styles the pages so forms, the expense list or table, errors, and delete confirmation are simple and easy to use.

**`static/script.js`**  
Handles page interactions: delete confirmation, filtering, dependent subcategory options, and immediate saving of custom subcategories for existing categories.

**`templates/register.html`**  
Page for creating an account.

**`templates/login.html`**  
Page for logging in with username/email and password.

**`templates/add_expense.html`**  
Page for entering amount, category, optional subcategory, date, Liability/Savings type, and optional description. Includes built-in category suggestions and custom-add controls.

**`templates/view_expenses.html`**  
Page that shows the user’s expenses (amount, category, optional subcategory, type, date, and description), category/date filters, total spending, and edit/delete actions.

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
- **SQLite** stores accounts, expenses, user-owned category/subcategory options, and monthly budgets.

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
The user selects Add Expense, enters amount, main category, optional subcategory, date, Liability/Savings type, and optional description, then clicks Save. Flask validates the details. Built-in category/subcategory choices and the user's custom choices are available. A custom subcategory for an existing category can be saved to its dropdown immediately; a new category and its subcategory are persisted when the expense is saved.

**View**  
The user selects View Expenses. Flask retrieves that user’s recorded expenses from SQLite and displays amount, category, optional subcategory, Liability/Savings type, date, and description.

**Edit**  
The user selects an expense and clicks Edit, changes the required details, and clicks Save. Flask updates that user’s expense in SQLite. This is for correcting information that was entered incorrectly.

**Delete**  
The user selects an expense and clicks Delete. The application asks for confirmation. After the user confirms, Flask removes that expense from SQLite. The deleted expense is removed from the list. This is for incorrect, unwanted, or no longer required records.

## How category/date filtering and total spending will work

**Category**
The user selects a built-in or previously saved category, or adds a custom category. Each category has suggested and user-defined subcategories. Category and subcategory names are normalized for case and whitespace, and each user's custom values remain private to that user.

**Filter**  
On the view page, the user can filter expenses by category and date. Flask (and JavaScript for the page interaction) limits the list or table to matching records for that user. This supports checking spending by date or category.

**Total spending**  
The view page shows the total amount spent. Flask calculates the total from the logged-in user’s expenses and the system displays that total expense amount.

## Version 2 Implementation Roadmap

The Version 2 release extends the app with monthly budget management and category-wise analytics while preserving the original workflow.

### Phase 1: Database enhancement

- Add a `budgets` table to store user-specific monthly budget values.
- Ensure budget rows are linked to user ID, month, and year.
- Confirm schema supports one active budget per user and month.
- Validate that the existing `expenses` table continues to support category aggregation queries.

### Phase 2: Budget tracking backend

- Build backend logic for budget creation and update.
- Add calculation for remaining budget and month-wise total spend.
- Implement warning threshold checks and exceeded-budget logic.
- Ensure each calculation is scoped to the logged-in user.

### Phase 3: Budget tracking frontend

- Add a dashboard budget card or management form.
- Display remaining amount and percentage utilized.
- Show warning and exceeded states clearly on relevant screens.
- Add empty-state handling when no monthly budget is configured.

### Phase 4: Analytics backend

- Create summary queries for total spend by category.
- Add monthly filtering logic for category analysis.
- Calculate category percentages and identify highest and lowest categories.
- Ensure analytics use authenticated user records only.

### Phase 5: Analytics frontend

- Add category summary cards and visual components.
- Render bar charts or percentage blocks for categories.
- Include a month selector for analytics review.
- Keep the dashboard simple and readable for everyday use.

### Phase 6: Testing

- Test budget set/update flows.
- Test remaining budget and utilization calculations.
- Test warning and exceed states.
- Test category aggregation temperature and percentage logic.
- Test empty and invalid data behavior.

### Phase 7: Integration validation

- Verify that expense CRUD still works after budget and analytics are added.
- Confirm dashboard and analytics display do not break session behavior.
- Validate user-specific visibility and access restrictions.
- Run end-to-end acceptance checks for both Version 1 and Version 2 flows.

### Phase 8: Release preparation

- Review the updated documentation for consistency.
- Confirm database schema, UI changes, and route design are aligned.
- Validate release readiness for budget and analytics functionality.
- Prepare release notes covering new features and usage examples.

## Version 2 milestones and priorities

**Priority 1:** Monthly budget tracking foundation and backend logic.

**Priority 2:** Dashboard visibility for remaining budget and warning states.

**Priority 3:** Category analytics backend and dashboard summary.

**Priority 4:** Testing, validation, and release documentation.

## Validation and security considerations

**Validation**

- Expense amount must be greater than 0 and use no more than two decimal places.
- An expense must have a category.
- Expense type must be Liability or Savings.
- A selected subcategory must belong to the selected category.
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

- [ ] User can add an expense with amount, category, optional subcategory, date, type, and description.
- [ ] Built-in categories/subcategories and custom-add choices appear in the form.
- [ ] A custom subcategory under an existing category is saved immediately and remains in the dropdown.
- [ ] Liability/Savings type is retained in the expense list.
- [ ] Amount greater than 0 with at most two decimal places is saved.
- [ ] Amount that is not greater than 0 is not saved.
- [ ] Amount with more than two decimal places is rejected with entered values preserved.
- [ ] Expense without a category is not saved.
- [ ] Invalid date is not saved.

**View expenses**

- [ ] User can view their expenses in a list or table.
- [ ] Amount, category, optional subcategory, type, date, and description are visible.

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
