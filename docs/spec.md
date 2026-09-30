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
- Main category
- Optional subcategory
- Date
- Expense type: Liability or Savings
- A short description


When viewing expenses, amount, main category, optional subcategory, date,
expense type, and description should be visible.

## Add Expense

- The user selects Add Expense.
- The user enters amount, main category, optional subcategory, date, expense
  type, and description.
- The user clicks Save.
- The system validates the details.
- If the details are valid, the system saves the expense.
- The amount must be greater than 0 and have no more than two decimal places.
- The selected category and subcategory must belong to the logged-in user.

## View Expense

- The user selects View Expenses.
- The system retrieves the recorded expenses for that user.
- The system displays the expenses in a list or table.
- Amount, category, subcategory when present, date, expense type, and
  description are visible.
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

- The user selects a main category from a dropdown populated with common
  defaults and that user's custom categories.
- Default categories include Food, Utilities, Transport, Household, Health,
  Shopping, Education, Entertainment, Bills, and Other.
- Their built-in subcategories are Food (Breakfast, Lunch, Dinner, Groceries,
  Snacks); Utilities (Electricity, Water, Internet, Gas); Transport (Public
  transit, Fuel, Vehicle maintenance); Household (Supplies, Repairs,
  Furniture); Health (Medical, Pharmacy); Shopping (Clothing, Personal care);
  Education (Books, Fees); Entertainment (Subscriptions, Outings); Bills
  (Rent, Insurance, Loan payments); and Other (Miscellaneous).
- Selecting a main category presents its suggested and previously saved
  subcategories.
- The user can add a custom category or subcategory from the expense form.
- A subcategory added under an existing category is saved immediately and
  appears in subsequent dropdowns. A subcategory for a new category is saved
  when the expense is saved.
- Category names are normalized for case and whitespace to avoid duplicates.
- An expense must have a category.
- An expense must be classified as Liability or Savings.
- Categories help the user understand where money is being spent and keep expenses organized.

## Filtering by category and date

- The user can filter expenses by category and date.
- This supports checking spending based on date or category.

## Total spending

- The user can see the total amount spent.
- The system displays the total expense amount.
- Totals help the user stay aware of expenditure.

## Validation rules

- Expense amount must be greater than 0 and use no more than two decimal places.
- Expense amount must have no more than two decimal places.
- An expense must have a category.
- Expense type must be Liability or Savings.
- Optional subcategories must belong to the selected category.
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
- Amount must be positive and use no more than two decimal places.
- User can select default or custom categories and subcategories.
- User can add a subcategory that remains available for later expense entry.
- Liability/Savings type is saved and shown with the expense.

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

**Expense Categories and Type**

- Common categories and their subcategories are available in the expense form.
- Custom categories and subcategories can be added by the signed-in user.
- New subcategories for existing categories are saved immediately and
  available in later forms.
- Category and subcategory data is isolated by user.

## Version 2 Feature Specification

### Monthly Budget Tracking

#### Feature description

The monthly budget feature allows a logged-in user to define a financial
limit for a specific month and compare future spending against that limit.
The system stores a budget entry for the relevant month and year, then
calculates the user’s remaining budget and percentage used.

#### Workflow definition

1. The user selects a month and enters a budget amount.
2. The system validates the amount and saves the budget to the database.
3. The user continues adding expenses for that month.
4. The system calculates total spending for the month.
5. The system compares actual spending to the budget.
6. If spending reaches a warning threshold, a warning is displayed.
7. If spending exceeds the budget, an alert is shown.
8. The result is shown on the dashboard and relevant expense views.

#### Validation rules

- Budget amount must be greater than 0.
- A budget must be associated with a valid logged-in user.
- A budget must belong to a month and year.
- Duplicate entries for the same month and user should be handled by
  update-in-place instead of creating overlapping budget records.
- Invalid or empty values must be rejected with a clear message.

#### Business rules

- Budget is calculated per user and per month.
- Budget should be independent from individual expense records.
- Expenses outside the selected month are excluded from monthly budget
  calculations.
- The warning threshold may be defined as a percentage of the budget, for
  example 80% or 90%.
- The alert state is triggered when actual spending exceeds the monthly
  budget.

#### Error handling

- Invalid numeric values show an error and do not save the budget.
- Missing budget data shows an empty or zero-state summary.
- If no budget is configured for the selected month, the dashboard should
  show a default message rather than a broken value.
- If category totals are empty, the analytics page should still render a
  valid empty-state message.

#### Database impacts

- A new budget table should store budget amount, user ID, month, year, and
  timestamps.
- Budget data should be keyed by user and month to prevent duplicate
  overlapping records.
- The system should support updating the same month’s budget without
  creating duplicate rows.

#### UI impacts

- Budget entry controls appear in the dashboard or settings panel.
- Remaining amount and utilization percentage are visible.
- Warning and exceeded messages appear in a clear status banner or panel.
- Budget status should not block normal expense entry or viewing.

### Category-wise Analytics

#### Feature description

The analytics feature summarizes expense data by category for a selected
month. It helps the user understand where the majority of spending occurs
and which categories are most or least expensive.

#### Workflow definition

1. The user opens the dashboard or analytics section.
2. The system selects the current month or a chosen month from the UI.
3. The system groups the user’s expenses by category.
4. The system calculates total spending per category.
5. The system calculates each category’s contribution percentage.
6. The dashboard displays totals and visual summaries.
7. The user can identify the highest- and lowest-spending categories.

#### Validation rules

- Category totals are derived from valid expenses only.
- Expenses without a valid user or category must be excluded from the
  summary.
- The analytics view must respect the selected month and the user’s owned
  records.
- Category percentages must be based on the visible total for the selected
  month.

#### Business rules

- The system should aggregate by category only for the logged-in user.
- The grand total for the selected month is the denominator for category
  percentages.
- Categories with zero spend should not appear as positive contribution
  values unless intentionally displayed as empty state items.
- The dashboard should still allow standard CRUD actions outside the
  analytics section.

#### Error handling

- No data for the selected month should display a friendly empty state.
- Invalid month filters should be rejected and reset to the current month.
- Analytics calculations should fail gracefully without affecting the main
  expense workflow.

#### Database impacts

- Analytics queries will use expense records and category values already
  stored for the user.
- It is recommended to identify categories using the existing expense
  table and to aggregate with GROUP BY category, user_id, and month.
- The dashboard should not require a separate analytics warehouse for the
  initial Version 2 design.

#### UI impacts

- A summary panel shows category totals and percentages.
- Charts or horizontal bars display category contribution visually.
- A selected month filter updates analytics without reloading the full
  application experience.
- The screen should remain readable and lightweight for personal use.

## Version 2 Security and Access Rules

- Budget and analytics data must be user-scoped.
- A user cannot view another user’s budget or category summaries.
- Budget and analytics calculations must use only authenticated session
  data.
- The app must continue to enforce password hashing and user-specific
  access rules.

## Version 2 Acceptance Criteria Summary

- Users can set and update monthly budgets.
- Remaining budget and utilization percentages are accurate.
- Users receive warnings when near or over budget.
- Monthly category totals and percentages are calculated correctly.
- The highest and lowest spending categories are visible.
- Budget and analytics views integrate smoothly with the existing dashboard
  and expense management flow.
