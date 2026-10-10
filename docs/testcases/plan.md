# Test Plan

## Purpose and source documents

This plan covers the current application behavior described in
[requirements.md](../requirements.md) and [spec.md](../spec.md). It adds no
product behavior beyond those documents.

## Test scope

- Registration, login, logout, and authentication protection
- Expense create, view, edit, delete, validation, and user isolation
- User-owned categories, default seeding, custom category normalization, and legacy migration
- Add Expense date/category filters and filtered totals; unfiltered Expenses ledger
- Budget create/update, validation, calculations, and status
- Analytics filters, current-period limits, category calculations, empty states, and month comparison
- Browser interaction and responsive/accessible presentation

## Test strategy

- Use Python `unittest` and Flask's test client for backend and integration behavior.
- Use temporary SQLite databases for isolated schema and migration tests where appropriate.
- Use browser checks for frontend constraints, navigation, layout, and delete confirmation.
- Test user isolation with at least two independently authenticated users.

## Core cases

### Authentication and access

- TS-01: Registration and Login with Valid Details
  - Verify user can register with valid username, password, confirm password, and role.
  - Verify registered user can log in with valid credentials.
  - Verify user is redirected to the appropriate page after login.

- TS-02: Role Selection Validation
  - Verify role selection is mandatory during registration.
  - Verify registration fails when no role is selected.

- TS-03: Role-Based Category Availability
  - Verify Student users see Student categories after login.
  - Verify Homemaker users see Homemaker categories after login.
  - Verify Working Professional users see Working Professional categories after login.

- TS-04: Duplicate Username and Invalid Credential Validation
  - Verify registration fails with an existing username.
  - Verify login fails with incorrect password.
  - Verify login fails with a non-existing username.

- TS-05: Required Field Validation
  - Verify registration fails when username is empty.
  - Verify registration fails when password is empty.
  - Verify registration fails when confirm password is empty.
  - Verify login fails when username is empty.
  - Verify login fails when password is empty.

- TS-06: Password Confirmation Validation
  - Verify registration fails when password and confirm password do not match.

- TS-07: Username and Password Length Validation
  - Verify registration fails when username is below minimum length.
  - Verify registration fails when username exceeds maximum length.
  - Verify registration fails when password is below minimum length.
  - Verify registration fails when password exceeds maximum length.

- TS-08: Protected Route Access Validation
  - Verify unauthenticated users are redirected to login when accessing protected pages.

- TS-09: Session Management Validation
  - Verify logged-out users cannot access protected pages using old sessions.
  - Verify expired sessions cannot access protected resources.

- TS-10: User Data Isolation Validation
  - Verify users cannot view another user's expenses.
  - Verify users cannot edit another user's expenses.
  - Verify users cannot delete another user's expenses.
  - Verify users cannot access another user's categories or budgets.

- TS-11: Security Validation
  - Verify passwords are stored in hashed format.
  - Verify POST requests require valid CSRF tokens.

#### Detailed authentication and access test cases

| TC ID | Test Steps | Test Data | Expected Result | Priority |
| --- | --- | --- | --- | --- |
| AUTH-01 | 1. Open the registration page. 2. Enter a valid unique username, select a role, enter a valid password that matches confirmation. 3. Submit the form. 4. Sign in with the same username and password. | Username: `alice_01`; Role: `Student`; Password: `Pass@1234`; Confirm Password: `Pass@1234` | Registration succeeds, the user is created, the password is stored as a hash, and login succeeds. The user is redirected to the dashboard or landing authenticated page. | P1 |
| AUTH-02 | 1. Open registration. 2. Leave the role dropdown unselected. 3. Fill the other fields with valid data. 4. Submit the form. | Username: `bob_02`; Role: `None`; Password: `Bob@2024`; Confirm Password: `Bob@2024` | Registration is rejected and the user is not created. A validation message indicates that a role selection is required. | P1 |
| AUTH-03 | 1. Attempt registration with a username below minimum length. 2. Attempt registration with a username above maximum length. 3. Attempt registration with spaces or missing required special characters. 4. Attempt registration with a valid username to confirm pass. | Invalid usernames: `ab`, `averylongusername123`, `john doe`, `john`; Valid username: `john_01` | The app rejects invalid usernames and shows clear validation feedback. A valid username is accepted and the account is created. | P1 |
| AUTH-04 | 1. Fill all registration fields with mismatched passwords. 2. Try to paste into password and confirm password fields. 3. Submit the form. 4. Repeat with valid matching values. | Password: `Strong@123`; Confirm Password: `Strong@124`; prohibited paste action on password fields | Registration fails when the passwords do not match. Password and confirm-password fields reject paste actions, and valid matching credentials are accepted. | P1 |
| AUTH-05 | 1. Register a user with a unique username. 2. Attempt to register again with the same username in a different case. 3. Attempt login with a wrong password. 4. Attempt login with a username that does not exist. | Existing username: `sam_77`; Duplicate case variant: `SAM_77`; Wrong password: `Wrong@999`; Non-existent username: `unknown_99` | Duplicate usernames are rejected, case-insensitive duplicates are prevented, wrong-password login fails, and non-existent-user login fails with a clear error. | P1 |
| AUTH-06 | 1. Open a protected route such as Dashboard, Expenses, or Analytics without signing in. 2. Check the browser URL and session state. | Direct URL access to `/dashboard`, `/expenses`, or `/analytics` with no session | The user is redirected to the login page and cannot access protected content without authentication. | P1 |
| AUTH-07 | 1. Sign in with valid credentials. 2. Click Sign Out. 3. Attempt to refresh or revisit a protected route. 4. Reuse the old session if applicable. | User: `admin_01`; Password: `Admin@123` | Sign-out clears the session. The user is not able to access protected pages after logout, and old sessions are invalidated. | P1 |
| AUTH-08 | 1. Register and sign in as User A. 2. Create an expense or view a resource. 3. Log out. 4. Register and sign in as User B. 5. Attempt to access User A's records by directly changing the URL or using a known ID. | User A: `userA_01`; User B: `userB_02`; User A expense ID: `EXP-1001` | User B cannot view, edit, or delete User A's data. The application returns authorization errors or hides the resource. | P1 |
| AUTH-09 | 1. Submit a POST form without a valid CSRF token. 2. Create a user or modify protected data via HTTP request. 3. Repeat with a valid CSRF token. | No CSRF token, then valid session token | Requests without a valid CSRF token are rejected. Requests with a valid token succeed. | P1 |
| AUTH-10 | 1. Register users with each available role. 2. Sign in as each user. 3. Verify the default categories visible in the form after login. | Roles: `Student`, `Homemaker`, `Professional` | Each role sees only its own assigned default categories, and no category from another role is available. | P2 |
| AUTH-11 | 1. Open the login page. 2. Enter a valid username and password. 3. Confirm the Sign In button is disabled when a field is blank or invalid. 4. Confirm the button is enabled only when all conditions are satisfied. | Username: `validuser_1`; Password: `Valid@123`; Empty fields and invalid format states | The Sign In button remains disabled until requirements are met and becomes enabled when valid login credentials are entered. | P1 |
| AUTH-12 | 1. Open the registration page. 2. Verify the Create Account button remains disabled while requirements are unmet. 3. Enter valid values step-by-step and verify the button enables only at the end. | Username: `new_user_1`; Password: `Valid@123`; Confirm Password: `Valid@123`; Role: `Professional` | Registration button state is correctly controlled, preventing invalid account creation and enabling only when all criteria are satisfied. | P1 |

### Expense Management

- TS-12: Expense Creation Validation
  - Verify expense can be created with valid amount, category, date, and description.
  - Verify expense can be created without a description.

- TS-13: Amount Validation
  - Verify expense creation fails when amount is empty.
  - Verify expense creation fails with malformed amount values.
  - Verify expense creation fails with zero amount.
  - Verify expense creation fails with negative amount.
  - Verify expense creation fails with non-finite values.
  - Verify expense creation fails when decimal precision exceeds limit.

- TS-14: Date Validation
  - Verify expense creation fails with invalid dates.
  - Verify expense creation fails with future dates.
  - Verify expense editing fails with future dates.

- TS-15: Category Validation
  - Verify category selection is mandatory.
  - Verify custom categories are normalized correctly.
  - Verify custom categories are user-specific.

- TS-16: Validation Error Handling
  - Verify entered values are preserved after validation errors during creation.
  - Verify entered values are preserved after validation errors during editing.

- TS-17: Expense Edit Functionality
  - Verify owned expenses can be edited successfully.
  - Verify users cannot edit expenses they do not own.

- TS-18: Expense Deletion Functionality
  - Verify delete confirmation is displayed.
  - Verify users can delete their own expenses.
  - Verify users cannot delete another user's expenses.

- TS-19: Expense Listing Validation
  - Verify expenses are displayed correctly.
  - Verify expenses are sorted newest first.
  - Verify empty state is displayed when no expenses exist.

- TS-20: Unsupported Field Validation
  - Verify subcategory field is not available.
  - Verify expense type field is not available.

### Filtering and totals

- TS-21: Add Expense Layout Validation
  - Verify Amount field occupies full width.
  - Verify Category and Date controls appear side-by-side.
  - Verify Description and Save controls are displayed correctly.

- TS-22: Default Filter Validation
  - Verify Today filter is selected by default.
  - Verify only today's expenses are displayed initially.

- TS-23: Date Control Validation
  - Verify only one date filter control exists.
  - Verify only one custom date picker exists.

- TS-24: Quick Date Filter Validation
  - Verify Today filter saves today's date.
  - Verify Yesterday filter saves yesterday's date.
  - Verify Last 7 Days filter saves today's date.
  - Verify Custom filter saves selected date.

- TS-25: Yesterday Filter Validation
  - Verify only previous day's expenses are displayed.

- TS-26: Last 7 Days Filter Validation
  - Verify expenses from today and previous six days are displayed.
  - Verify expenses older than seven days are excluded.

- TS-27: Custom Date Filter Validation
  - Verify only selected date records are shown.
  - Verify custom date clears active quick filters.

- TS-28: Filter Interaction Validation
  - Verify selecting a quick filter clears custom date selection.
  - Verify only one quick filter remains active.

- TS-29: Category and Date Filter Combination
  - Verify category filtering works with all date filters.

- TS-30: Invalid Date Filter Validation
  - Verify malformed custom dates are rejected.
  - Verify future dates are rejected.
  - Verify system falls back to Today filter.

- TS-31: Totals and Analytics Recalculation
  - Verify summary cards recalculate after filter changes.
  - Verify category analytics recalculate after filter changes.

- TS-32: Analytics Navigation Validation
  - Verify selected filter is passed to Analytics page.
  - Verify Analytics reflects the selected filter correctly.

- TS-33: User-Specific Filtered Results
  - Verify totals include only logged-in user's records.
  - Verify list displays only logged-in user's records.

- TS-34: Unsaved Data Preservation
  - Verify changing filters does not save expense data.
  - Verify entered values remain intact.

- TS-35: Expense Save with Active Filters
  - Verify saved expense uses selected date.
  - Verify saved expense uses selected category.
  - Verify records and analytics refresh correctly.

- TS-36: Responsive and Accessibility Validation
  - Verify date filters work on tablet devices.
  - Verify date filters work on mobile devices.
  - Verify keyboard accessibility.
  - Verify screen-reader accessibility.

### Budgets and Dashboard

- TS-37: Budget Creation and Update Validation
  - Verify monthly budget can be created.
  - Verify existing budget can be updated.
  - Verify duplicate budget records are not created.

- TS-38: Budget Validation
  - Verify invalid month values are rejected.
  - Verify invalid year values are rejected.
  - Verify non-positive budget amounts are rejected.
  - Verify malformed amounts are rejected.
  - Verify over-precision amounts are rejected.

- TS-39: Budget Status Calculation Validation
  - Verify Not Set status.
  - Verify On Track status.
  - Verify Warning status (≥ 80% usage).
  - Verify Exceeded status (spending exceeds budget).

- TS-40: Dashboard Data Isolation
  - Verify expenses from other users are excluded.
  - Verify expenses from other periods are excluded.

- TS-41: Future Budget Validation
  - Verify future-period budgets can be created successfully.

### Analytics

- TS-42: Default Analytics Period Validation
  - Verify current month is selected by default.
  - Verify available years are populated correctly.

- TS-43: Valid Period Selection
  - Verify past months can be selected.
  - Verify current month can be selected.

- TS-44: Future Period Restriction Validation
  - Verify future years are rejected.
  - Verify future months are rejected.
  - Verify fallback behavior and validation message.

- TS-45: Date Validation in Analytics
  - Verify invalid months are rejected.
  - Verify invalid years are rejected.
  - Verify invalid selected days are rejected.
  - Verify future selected days are rejected.

- TS-46: Analytics Calculation Validation
  - Verify category ownership validation.
  - Verify total spend calculation.
  - Verify expense count calculation.
  - Verify average spend calculation.
  - Verify category amount calculation.
  - Verify percentage calculation.
  - Verify highest category calculation.

- TS-47: Day and Category Filter Validation
  - Verify selected day filters summary data.
  - Verify comparison metrics remain month-based.
  - Verify category filtering applies consistently across comparisons.

- TS-48: Comparison and Empty State Validation
  - Verify month boundary comparisons.
  - Verify year boundary comparisons.
  - Verify empty-data states are displayed correctly.
