# Test Cases Development Plan

## 1. Purpose

This document defines the test strategy and execution plan for the Expense Tracker application described in the project documentation. It is based on the requirements, specification, intent, and technology choices in the docs folder and is intended to support the validation of the application before release.

The goal is to ensure the system works correctly for:

- user registration and login
- adding, viewing, editing, and deleting expenses
- category-based and date-based filtering
- total spending calculation
- secure, user-specific data access

---

## 2. Source of truth

The plan follows the documented requirements from:

- [docs/requirements.md](../requirements.md)
- [docs/spec.md](../spec.md)
- [docs/intent.md](../intent.md)
- [docs/tech-stack.md](../tech-stack.md)
- [docs/plan.md](../plan.md)

This test plan does not add new product requirements beyond those already documented.

---

## 3. Scope of testing

### Functional scope

- User registration
- User login
- Add expense
- View expenses
- Edit expense
- Delete expense
- Filter by category
- Filter by date
- Display total spending
- Restrict each user to their own data

### Non-functional scope

- Usability and simplicity
- Basic validation for incorrect inputs
- Reasonable application responsiveness
- Data preservation during normal use
- Password safety and secure access control

---

## 4. Test strategy

### 4.1 Test levels

1. Unit testing
   - Validate helper logic such as date validation, amount validation, total calculation, and user lookup.
2. Integration testing
   - Verify Flask routes work correctly with SQLite storage for registration, login, and expense CRUD operations.
3. UI testing
   - Confirm forms, navigation, error messages, confirmation prompts, and filtering controls behave as expected.
4. Security/access testing
   - Confirm that one user cannot access, edit, or delete another user’s expenses.
5. Acceptance testing
   - Run the end-to-end scenarios that match the acceptance criteria in the specification.

### 4.2 Test data strategy

Use a mix of:

- valid user data
- invalid email and password combinations
- boundary values for amounts such as 0, negative values, decimals, and large values
- valid and invalid dates
- expenses across multiple categories and dates
- multiple users to verify isolation of records

---

## 5. Test case groups

### Group A: Authentication

1. Register with valid details
2. Register with missing email
3. Register with duplicate email
4. Login with valid credentials
5. Login with invalid password
6. Login with non-existent user
7. Access expense pages without login

### Group B: Expense creation

8. Add expense with valid amount, category, date, and description
9. Add expense with amount equal to 0
10. Add expense with negative amount
11. Add expense with missing category
12. Add expense with invalid date
13. Add expense without description
14. Add expense by logged-in user only

### Group C: Expense viewing

15. View all expenses for the logged-in user
16. View empty expense list when no expenses exist
17. Confirm all required fields are shown in the list/table
18. Confirm expense list updates after add/edit/delete

### Group D: Expense editing

19. Edit an existing expense successfully
20. Edit with valid updated fields
21. Edit with invalid amount
22. Edit with missing category
23. Edit with invalid date
24. Edit another user’s expense via URL or action

### Group E: Expense deletion

25. Delete an expense after confirmation
26. Cancel delete action and confirm record remains
27. Delete an expense and verify it disappears from the list
28. Delete another user’s expense

### Group F: Filtering and totals

29. Filter by category
30. Filter by date
31. Filter by category and date together
32. Clear filters and return to full list
33. Total spending updates after add/edit/delete
34. Total spending for the correct user only

### Group G: Security and data isolation

35. User A cannot see User B’s expenses
36. User A cannot edit User B’s expense
37. User A cannot delete User B’s expense
38. Password is not stored in plain text
39. Authentication is required before any expense operation

---

## 6. Detailed test case design

### TC-01: User registration with valid details

- Input: valid email, password, and user details
- Expected result: account is created and user can proceed to login

### TC-02: User registration with missing email

- Input: password only or blank email field
- Expected result: validation error shown; account is not created

### TC-03: Duplicate email registration

- Input: same email used twice
- Expected result: error shown; second registration rejected

### TC-04: User login with valid credentials

- Input: registered email and matching password
- Expected result: user logs in successfully

### TC-05: User login with invalid credentials

- Input: valid email but incorrect password
- Expected result: login fails, error displayed

### TC-06: Unauthenticated access blocked

- Input: open expense pages without login
- Expected result: user is redirected or denied access

### TC-07: Add valid expense

- Input: amount > 0, valid category, valid date, description
- Expected result: expense is saved and visible in the list

### TC-08: Add expense with invalid amount

- Input: amount 0 or negative
- Expected result: expense is rejected; error displayed

### TC-09: Add expense with missing category

- Input: category blank or not selected
- Expected result: expense is rejected

### TC-10: Add expense with invalid date

- Input: invalid date format or impossible date
- Expected result: expense is rejected

### TC-11: Edit expense with valid data

- Input: update amount/category/date/description
- Expected result: changes persist and list updates

### TC-12: Edit expense with invalid input

- Input: invalid amount/date/category
- Expected result: update is rejected and original data stays intact

### TC-13: Delete expense after confirmation

- Input: click Delete and confirm
- Expected result: record is removed from storage and UI

### TC-14: Delete expense cancelled

- Input: click Delete but cancel operation
- Expected result: record remains unchanged

### TC-15: Filter by category

- Input: select category from filter dropdown
- Expected result: only matching category records are displayed

### TC-16: Filter by date

- Input: choose a specific date or date range if supported
- Expected result: only matching date records are displayed

### TC-17: Combined filter

- Input: category + date criteria together
- Expected result: results match both conditions

### TC-18: Total spending calculation

- Input: multiple valid expenses
- Expected result: total is the sum of the user’s expenses only

### TC-19: Data isolation between users

- Input: User A and User B add expenses
- Expected result: User A sees only A’s data and User B sees only B’s data

---

## 7. Version 2 Test Cases

### TC-V2-01: Create monthly budget

- Test ID: TC-V2-01
- Objective: Validate that a logged-in user can create a monthly budget.
- Preconditions: User is authenticated and has no existing budget for the selected month.
- Steps:
  1. Open the budget section.
  2. Select a month and enter a valid budget amount.
  3. Save the budget.
- Expected Result: Budget is saved successfully and appears in the dashboard summary.

### TC-V2-02: Update monthly budget

- Test ID: TC-V2-02
- Objective: Validate that an existing budget amount can be updated without creating a duplicate row.
- Preconditions: User has an existing budget for the selected month.
- Steps:
  1. Open the budget section.
  2. Change the current budget amount to a new value.
  3. Save the updated value.
- Expected Result: The existing monthly record is updated, the month remains uniquely tracked, and the remaining budget recalculates correctly.

### TC-V2-03: Replace budget entry when a new value is submitted for the same month

- Test ID: TC-V2-03
- Objective: Validate the system replaces the previous budget entry for the same user and month when a new value is submitted.
- Preconditions: User has one previously saved budget record for a selected month.
- Steps:
  1. Submit a second budget value for the same month and year.
  2. Save the new budget.
- Expected Result: Only one budget record remains for that user and month, and it reflects the latest submitted value.

### TC-V2-04: Budget utilization calculation

- Test ID: TC-V2-04
- Objective: Validate that utilization percentage is calculated correctly.
- Preconditions: User has a valid monthly budget and recorded expenses.
- Steps:
  1. Add expenses for the month.
  2. Review the budget card.
- Expected Result: The system displays the correct utilization percentage based on monthly spend divided by the budget.

### TC-V2-05: Remaining budget calculation

- Test ID: TC-V2-05
- Objective: Validate that remaining budget is computed accurately.
- Preconditions: User has budget and actual spending entries for the same month.
- Steps:
  1. Add one or more expenses.
  2. View the budget summary.
- Expected Result: Remaining budget equals budget minus actual spend and displays a negative value if overspent.

### TC-V2-06: Budget warning threshold

- Test ID: TC-V2-06
- Objective: Validate that warning state appears near the budget limit.
- Preconditions: Budget amount is configured and spending is near the threshold.
- Steps:
  1. Add expenses that reach the warning threshold.
  2. View the dashboard.
- Expected Result: Warning alert is displayed when threshold conditions are met.

### TC-V2-07: Budget exceeded scenario

- Test ID: TC-V2-07
- Objective: Validate that over-budget status is visible to the user.
- Preconditions: Budget and expenses are set so total spend exceeds budget.
- Steps:
  1. Enter expenses beyond the configured budget.
  2. View the dashboard summary.
- Expected Result: Exceeded budget alert is displayed and remaining balance is negative.

### TC-V2-08: Invalid budget values

- Test ID: TC-V2-08
- Objective: Validate that invalid budget inputs are rejected.
- Preconditions: Budget form is open.
- Steps:
  1. Enter 0, negative numbers, or blank budget values.
  2. Save the form.
- Expected Result: Validation error is shown and no invalid budget is stored.

### TC-V2-09: Month transition handling

- Test ID: TC-V2-09
- Objective: Validate that budget and analytics calculations reset correctly for a new month.
- Preconditions: Budget is configured for the previous month and expenses exist in both months.
- Steps:
  1. Select a different month in the dashboard or analytics filter.
  2. Compare totals.
- Expected Result: Only the selected month is included in budget and category calculations.

### TC-V2-10: Category aggregation

- Test ID: TC-V2-10
- Objective: Validate that expenses are aggregated correctly by category.
- Preconditions: User has multiple expenses under different categories for the selected month.
- Steps:
  1. Open the category analytics section.
  2. Select the month.
- Expected Result: Each category shows the correct total spend for that month.

### TC-V2-11: Category percentage calculation

- Test ID: TC-V2-11
- Objective: Validate that category contribution percentages are accurate.
- Preconditions: User has multiple category totals for the month.
- Steps:
  1. View analytics summary.
- Expected Result: Category percentage reflects the share of the selected month’s total spending.

### TC-V2-12: Monthly filtering for analytics

- Test ID: TC-V2-12
- Objective: Validate analytics respect the selected month.
- Preconditions: Expenses exist in more than one month.
- Steps:
  1. Select a month from the filter.
  2. Review summary.
- Expected Result: Only expenses for that month contribute to the metric and chart.

### TC-V2-13: Empty dataset behavior

- Test ID: TC-V2-13
- Objective: Validate that no-data states are handled gracefully.
- Preconditions: User has no expenses for the selected month.
- Steps:
  1. Open budget and analytics views.
- Expected Result: Empty-state message is shown and no crash or incorrect values are displayed.

### TC-V2-14: Multiple category validation

- Test ID: TC-V2-14
- Objective: Validate correct handling of multiple categories in a single month.
- Preconditions: User has expenses across several categories.
- Steps:
  1. Review the analytics summary.
- Expected Result: All categories are listed correctly and totals match actual records.

### TC-V2-15: Analytics accuracy

- Test ID: TC-V2-15
- Objective: Validate that total and category values are identical to actual stored data.
- Preconditions: User has a known set of expenses.
- Steps:
  1. Compute totals manually or compare against database records.
  2. Review analytics output.
- Expected Result: All category totals and percentages match the stored data accurately.

### TC-V2-16: Visualization rendering

- Test ID: TC-V2-16
- Objective: Validate that budget and category charts render correctly.
- Preconditions: User has valid budget and expense data.
- Steps:
  1. Open the dashboard or analytics page.
- Expected Result: Summary bars or chart visuals display without breaking the layout.

### TC-V2-17: Dashboard analytics display

- Test ID: TC-V2-17
- Objective: Validate that budget and analytics information are visible on the dashboard without interrupting expense operations.
- Preconditions: User is logged in and has budget plus category data.
- Steps:
  1. Load the dashboard.
  2. Review budget card and analytics section.
- Expected Result: Dashboard displays status and analytics clearly while existing expense actions still function.

---

## 8. Acceptance checklist mapping

The test plan directly covers the acceptance criteria in the specification:

- Registration with valid details
- Error for missing or existing email
- Login with valid credentials
- Error for invalid credentials
- Add expense with valid data
- Amount greater than 0 requirement
- View expenses for logged-in user
- Edit existing expense
- Delete expense after confirmation
- Filter by category and date
- Display total expense amount
- Restrict access to the logged-in user’s records only

---

## 8. Execution order

1. Authentication tests
2. Expense create and validation tests
3. Expense view tests
4. Expense edit tests
5. Expense delete tests
6. Filter and total tests
7. Security and user-isolation tests
8. Final acceptance run

---

## 9. Exit criteria

The application is considered ready for acceptance when:

- all critical registration and login tests pass
- all expense CRUD tests pass
- filtering and total calculation pass
- all user-isolation and security tests pass
- no high-priority validation failures remain

---

## 10. Recommended testing workflow for the project team

- Start with validation and login flows
- Move to add/view/edit/delete flows
- Then test filtering, totals, and security
- End with end-to-end regression checks before sign-off

This ensures the system is built and checked in the same order as the product requirements and avoids testing features before the foundational authentication and data flows are working.
