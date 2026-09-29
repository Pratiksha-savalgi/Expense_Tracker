REQUIREMENT ENGINEERING

REQUIREMENT ELICITATION

Problem Understanding

1.1 Problem Statement

People often spend money on different things every day but may not keep
track of all their expenses.

Because of this, they may not know how much they are spending or where
most of their money is going.

1.2 Current Situation

Users may write their expenses in a notebook, phone notes, Excel, or
simply try to remember them.

This can make it difficult to maintain all expenses in one place.

It can also be difficult to calculate total spending or find a
particular expense.

1.3 User Need

The user needs a simple application where they can add and manage their
expenses.

They should be able to see their expenses and check their spending based
on things like date or category.

This helps them keep their expenses organized.

1.4 Objective

To create a simple Expense Tracker for managing personal expenses.

The user should be able to add, view, edit, and delete expenses.

The application should also help the user understand their spending
through basic totals and categories.

REQUIREMENT SPECIFICATION

Stakeholder Identification

2.1 Stakeholders

User - Uses the Expense Tracker to record and manage expenses.

Developer - Develops and maintains the application.

Tester - Tests the application and checks whether it works as
expected.

Manager - Guides the project and reviews the progress.

Client- Provides the requirement and review the application/system.

3.User Personas

Student Description: Manages expenses using pocket money or a
limited monthly budget. Goals: Track spending and stay within
budget. Common Expenses: Food, travel, shopping, subscriptions.

Homemaker Description: Manages and monitors household expenses.
Goals: Track household spending and manage the family budget. Common
Expenses: Groceries, utilities, bills, medical expenses.

Working Professional Description: Earns a regular salary and manages
monthly personal expenses. Goals: Monitor spending, manage budget,
and build savings. Common Expenses: Rent, transport, food,
subscriptions, shopping.

User stories

User-01: Login

As a user, i want to login so that i can access my account.

User-02: add expenses.

As a user, i want to add my expenses along with category, date and
description so that i can record my spending.

User-03: delete expenses.

As a user, i want to delete my expenses so that i can remove incorrect
and unwanted records.

User-04: edit expenses

As a user, i want to edit my expenses so that i don't add incorrect or
unwanted records.

User-05: View expenses

As a user, i want to view all my records so that i can track my
expenditure and savings.

User-06: Categorize Expenses

As a user, I want to categorize my expenses so that I can understand
where my money is being spent.

User-07: Total spending

As a user, i want to see the total amount spend so that i am aware of my
expenditure and savings.

User-08: Set Budget

As a user, I want to set a budget so that I can control my spending and
avoid exceeding my limit.

Use cases

UC-01: Login Actor: User Description: User logs into the Expense Tracker
using their login credentials. Steps:

User enters username/email and password.

User clicks Login.

System checks the credentials.

System allows the user to access the application.

UC-02: Add Expense Actor: User Description: User adds a new expense to
the Expense Tracker. Steps:

User selects Add Expense.

User enters the expense amount, category, date, and description.

User clicks Save.

System validates the details.

System saves the expense.

UC-03: View Expenses Actor: User Description: User views the expenses
that have been recorded. Steps:

User selects View Expenses.

System retrieves the recorded expenses.

System displays the expenses to the user.

UC-04: Edit Expense Actor: User Description: User edits the details of
an existing expense. Steps:

User selects an expense.

User clicks Edit.

User changes the required details.

User clicks Save.

System updates the expense.

UC-05: Delete Expense Actor: User Description: User deletes an expense
that is no longer required or was added incorrectly. Steps:

User selects an expense.

User clicks Delete.

System asks for confirmation.

User confirms the deletion.

System removes the expense.

UC-06: Set Budget Actor: User Description: User sets a budget to keep
track of their spending. Steps:

User selects Set Budget.

User enters the budget amount.

User saves the budget.

System stores the budget amount.

Requirements Gathering

Q1. Who will use the Expense Tracker?

The application will be used by individuals to manage and track their
personal expenses.

Q2. What should the user be able to do?

The user should be able to add, view, edit and delete expenses. The user
should also be able to check their total spending.

Q3. What information should be entered when adding an expense?

The user should enter the amount, category, date and a short description
of the expense. Payment method can also be recorded.

Q4. How should the user view their expenses?

The user should be able to view all their expenses in a list or table.
The details such as amount, category, date and description should be
visible.

Q5. Should the user be able to edit or delete an expense?

Yes. The user should be able to edit an expense if any information was
entered incorrectly and delete an expense when it is no longer required.

Q6. Should the user be able to filter or search expenses?

Yes. The user should be able to filter expenses by category and date. A
search option can also be provided if required.

Q7. Does the application require login?

Yes. The user should create an account and log in before managing
expenses. Each user should only be able to see and manage their own
expenses.

Functional Requirements

FR-01: User Registration : The user should be able to create an account.

FR-02: User Login: The user should be able to log in using their
account.

FR-03: Add Expense: The user should be able to add a new expense by
entering the required details.

FR-04: View Expenses: The user should be able to view their recorded
expenses.

FR-05: Edit Expense: The user should be able to edit an existing
expense.

FR-06: Delete Expense: The user should be able to delete an existing
expense.

FR-07: Categorize Expense: The user should be able to assign a category
to an expense.

FR-08: Filter Expenses: The user should be able to filter expenses based
on category and date.

FR-09: View Total Spending: The user should be able to see the total
amount spent.

Non-Functional Requirements

NFR-01: Security: Users should only be able to access their own
expenses.

## Version 2 Requirements (Budget Tracking and Category Analytics)

### 2.2 Version 2 Scope

The Version 2 release extends the Expense Tracker from basic expense
recording into a monthly personal budget and analytics dashboard.

It adds two major capabilities:

1. Monthly Budget Tracking
2. Category-wise Analytics

These features build on the existing login, expense CRUD, and user
scoping model without removing or replacing the Version 1 functionality.

### Version 2 Functional Requirements

FR-10: Monthly Budget Configuration: The user should be able to set a
monthly budget amount for a specific month.

FR-11: Update Monthly Budget: The user should be able to update an
existing monthly budget without losing previous budget history.

FR-12: View Remaining Budget: The user should be able to see how much of
budget remains after spending.

FR-13: View Budget Utilization: The user should be able to see the
percentage of budget used.

FR-14: Budget Comparison: The user should be able to compare current
monthly spending against the configured budget.

FR-15: Budget Warning: The system should notify the user when spending is
approaching the budget limit.

FR-16: Budget Exceeded Alert: The system should notify the user when
spending exceeds the budget.

FR-17: Persist Budget Data: Budget values should be stored in the
application database so they remain available across sessions.

FR-18: Dashboard Budget Status: The user should see budget status on the
main dashboard or relevant screens.

FR-19: Category Contribution: The user should be able to see category
contribution percentages for monthly spending.

FR-20: Monthly Analytics: The user should be able to view analytics for a
selected month.

FR-21: Identify Spending Extremes: The user should be able to identify
highest-spending and lowest-spending categories.

FR-22: Graphical Summary: The user should be able to view a chart or
visual representation of category spending.

### Version 2 Non-Functional Requirements

NFR-02: Budget Awareness: The system should provide clear and timely
visual feedback when spending is approaching or exceeding budget.

NFR-03: Data Accuracy: Category totals and percentages must accurately
reflect the user’s actual expense records.

NFR-04: Dashboard Usability: Budget and analytics information should be
presented clearly without disrupting existing expense workflows.

NFR-05: Performance: Budget and analytics calculations should remain fast
for typical monthly datasets.

### Version 2 User Stories

User-09: Monthly Budget Tracking

As a user, I want to set a monthly budget so that I can control my
spending and know how much I have left.

User-10: Budget Alerts

As a user, I want warnings when I am close to or over budget so that I
can adjust my spending.

User-11: Category Analytics

As a user, I want to see my spending by category so that I can identify
where most of my money is going.

User-12: Monthly Comparison

As a user, I want to compare my monthly spending against my budget so that
I can plan better for the month.

User-13: Dashboard Review

As a user, I want budget and analytics information available on the
dashboard so that I can review my financial status quickly.

### Version 2 Acceptance Criteria

AC-21: Monthly budget can be configured and stored for the logged-in user.

AC-22: Existing monthly budget can be updated and saved successfully.

AC-23: Remaining budget is calculated correctly after expenses are
entered.

AC-24: Budget utilization percentage is displayed correctly.

AC-25: Warning is shown when spending reaches a defined threshold near the
budget limit.

AC-26: Alert is shown when actual spending exceeds the configured budget.

AC-27: Category totals are calculated correctly for the selected month.

AC-28: Category contribution percentages are calculated correctly.

AC-29: The highest and lowest spending categories are identified.

AC-30: Analytics display remains visible without blocking expense records
or CRUD operations.

### Version 2 Assumptions

- Each user maintains an independent budget and analytics view.
- The system evaluates budget against the user’s own recorded expenses.
- Monthly budget values are stored by month and year.
- Categories are shared across the user’s expense records.
- Chart display may be simplified to a bar or percentage view if a complex
  chart library is not required.

### Version 2 Constraints

- The project must remain within the approved stack unless a lightweight
  visualization dependency is absolutely necessary.
- Budget and analytic features must enhance the existing app without
  disrupting the current login and expense workflows.
- Budget operations must respect the same user-scoping model used for
  expense data.
- A budget should be calculated from the logged-in user’s records only.

### Version 2 Dependencies

- Existing user records and authentication model
- Existing expense records and category fields
- Monthly date handling and financial calculations
- Updated dashboard and template rendering flow
- Optional charting support for data visualization if approved later

### Version 2 Data and Validation Requirements

- A budget amount must be greater than zero.
- Budget records must be linked to a valid user.
- Budget records must be tracked by month and year.
- Category totals must match the sum of that user’s expenses for the
  selected month.
- Percentages must be calculated from total monthly expenditure and not
  from unrelated records.
- Empty datasets must show either a blank state or zero-value summary
  without errors.

### Version 2 Summary

This extended release keeps the Expense Tracker useful for daily expense
recording, while adding the financial planning features needed for better
monthly control and clearer category-based understanding of spending.

NFR-02: Password Security: User passwords should not be stored as plain
text.

NFR-03: Usability: The application should be simple and easy to use.

NFR-04: Performance: The application should respond within a reasonable
time for normal operations.

NFR-05: Reliability: Saved expense data should not be lost during normal
application usage.

Rules/Constraints

R-01: Expense amount must be greater than 0.

R-02: An expense must have a category.

R-03: An expense must belong to a registered user.

R-06: The expense date should be a valid date.

Acceptance criteria

01: User Registration

User can register with valid details.

Error is shown for missing or existing email.

02: User Login

User can log in with valid credentials.

Error is shown for invalid credentials.

03: Add Expense

User can add an expense with valid details.

Amount must be greater than 0.

04: View Expenses

User can view their expenses with amount, category and date.

05: Edit Expense

User can edit an existing expense.

Updated details are saved.

06: Delete Expense

User can delete an expense.

Deleted expense is removed from the list.

07: Filter Expenses

User can filter expenses by category and date.

08: Total Spending

System displays the total expense amount.