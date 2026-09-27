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

## 7. Acceptance checklist mapping

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
