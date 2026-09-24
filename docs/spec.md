# Specification

This specification defines the Expense Tracker based on `requirements.md` and `intent.md`. It describes a simple application for individuals to record and manage personal expenses in one place.

## User authentication

- The user must create an account before using the application.
- The user must log in before managing expenses.
- To log in, the user enters username/email and password, then clicks Login.
- The system checks the credentials.
- If the credentials are valid, the user is allowed to access the application.
- If the credentials are invalid, an error is shown.
- Registration succeeds when the user provides valid details.
- Registration shows an error if the email is missing or already exists.
- Each user can see and manage only their own expenses.
- An expense must belong to a registered user.

## Expense data fields

When adding an expense, the user enters:

- Amount
- Category
- Date
- A short description


When viewing expenses, amount, category, date, and description should be visible.

## Add Expense

- The user selects Add Expense.
- The user enters amount, category, date, and description.
- The user clicks Save.
- The system validates the details.
- If the details are valid, the system saves the expense.
- The amount must be greater than 0.

## View Expense

- The user selects View Expenses.
- The system retrieves the recorded expenses for that user.
- The system displays the expenses in a list or table.
- Amount, category, date, and description are visible.
- The user can view all of their records.

## Edit Expense

- The user selects an existing expense.
- The user clicks Edit.
- The user changes the required details.
- The user clicks Save.
- The system updates the expense.
- Updated details are saved.
- Editing is used when information was entered incorrectly.

## Delete Expense

- The user selects an expense.
- The user clicks Delete.
- The system asks for confirmation.
- After the user confirms, the system removes the expense.
- The deleted expense is removed from the list.
- Deletion is used for incorrect, unwanted, or no longer required records.

## Expense categorization

- The user assigns a category to an expense.
- An expense must have a category.
- Categories help the user understand where money is being spent and keep expenses organized.

## Filtering by category and date

- The user can filter expenses by category and date.
- This supports checking spending based on date or category.

## Total spending

- The user can see the total amount spent.
- The system displays the total expense amount.
- Totals help the user stay aware of expenditure.

## Validation rules

- Expense amount must be greater than 0.
- An expense must have a category.
- An expense must belong to a registered user.
- The expense date must be a valid date.
- Add Expense details are validated before the expense is saved.

## Security requirements

- Users can access only their own expenses.
- User passwords must not be stored as plain text.
- The user must create an account and log in before managing expenses.

## Non-functional requirements

- **Usability:** The application should be simple and easy to use.
- **Performance:** The application should respond within a reasonable time for normal operations.
- **Reliability:** Saved expense data should not be lost during normal application usage.
- **Security:** Users should only be able to access their own expenses. Passwords should not be stored as plain text.

## Acceptance criteria

**User Registration**

- User can register with valid details.
- Error is shown for missing or existing email.

**User Login**

- User can log in with valid credentials.
- Error is shown for invalid credentials.

**Add Expense**

- User can add an expense with valid details.
- Amount must be greater than 0.

**View Expenses**

- User can view their expenses with amount, category, and date.

**Edit Expense**

- User can edit an existing expense.
- Updated details are saved.

**Delete Expense**

- User can delete an expense.
- Deleted expense is removed from the list.

**Filter Expenses**

- User can filter expenses by category and date.

**Total Spending**

- System displays the total expense amount.
