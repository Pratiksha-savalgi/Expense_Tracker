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