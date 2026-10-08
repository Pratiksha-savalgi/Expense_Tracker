# Expense Tracker Design

## Overview

The application is a small server-rendered personal expense tracker using
Flask, SQLite, HTML, CSS, and lightweight JavaScript.

## Architecture

1. The browser renders Flask templates and submits forms.
2. Flask handles authentication, CSRF checks, validation, ownership checks,
   calculations, and route behavior.
3. SQLite stores users, categories, expenses, and budgets.

The browser does not access SQLite directly.

## Data model

- **User**: case-sensitive unique username, password hash, and role (Student,
  Homemaker, or Professional).
- **Category**: user-owned display name and normalized comparison name.
- **Expense**: user, amount, category ID and display name, ISO date, optional
  description.
- **Budget**: user, month, year, amount, creation and update timestamps.



## Presentation

- Login and Register provide account access.
- Dashboard displays current-month budget metrics, status, recent expenses, and
  budget controls.

- Add Expense is a shared popup opened after login and from authenticated
  Add Expense actions. It follows the AddExpense visual: Amount, role-specific
  Category dropdown, Today/Yesterday/custom Date controls, optional
  Description, and Save.
- Expenses provides the complete unfiltered ledger, category filter, and
  expense list.

- Selecting an expense displays the available expense actions:
  - Edit
  - Delete

- Edit opens the Add Expense page with the selected expense's existing
  amount, category, date, and description pre-populated for modification.

- Delete displays a confirmation dialog before the expense is permanently
  removed.

- After a successful edit or delete operation, the expense list refreshes
  automatically while preserving active filters.
- Analytics provides year/month/day/category selection, a category
  distribution, and a selectable full-month comparison with the month before
  the chosen comparison month.

### Add Expense popup hierarchy

1. Popup heading and close action.
2. Amount and the signed-in user's role-specific Category dropdown.
3. Date controls with only Today, Yesterday, and a custom date picker; Today is
   active by default.
4. Optional Description and Save action.
5. Validation feedback remains in the popup; a successful save displays a
   confirmation and resets the form after acknowledgment.

No subcategory, category-creation, or Last 7 Days controls are shown. The popup
uses the shared green theme and remains usable on desktop and mobile layouts.

All authenticated pages share the same navigation and responsive styling.

## Validation and business rules

- Amounts must be finite, positive, and have at most two decimal places.
- Expense dates must be valid and no later than today. Both browser and server
  enforce this restriction.
- Analytics year/month selections cannot be later than the current month/year;
  day selection must be a valid date no later than today.
- Category and date filters accept only valid user-scoped selections.
- Budgets require a valid month/year and positive amount with at most two decimal
  places. There is no future-period restriction on budget entry.
- Monetary totals use `Decimal`; user IDs scope expense, category, and budget
  data.

## Budget status

For a configured budget, spending greater than the budget is exceeded;
utilization from 80% up to and including 100% is warning; lower utilization is
on track. A missing budget has a not-set state.

## Local execution

Install dependencies with `python -m pip install -r requirements.txt` and start
the app from the repository root with `python -m backend.app`. The development
server listens on port 5000.



# Visual Design Reference

The current application uses the reference assets in this folder's `visuals`
directory. Both web and mobile mockups are provided and should be treated as
the primary visual references for implementation. The running templates and CSS
are authoritative if a reference image does not exactly match current behavior.

## Design Assets

The `visuals` directory contains:

- Web mockups
- Mobile mockups
- Application flow diagrams
- Data flow diagrams

All pages must follow the provided web and mobile designs for layout,
responsiveness, navigation, spacing, and interactions.

### Login

#### Web

[visuals/Login_web.png](docs\design\visuals\Login_web.png)

#### Mobile

[visuals/Login_mobile.png](docs\design\visuals\Login_mobile.png)

Sign-in uses username and password. Registration is available from the login
flow. Users who are not authenticated are redirected to the login page when
attempting to access protected pages.

### Register

#### Web

[visuals/Register_web.png](docs\design\visuals\Register_web.png)

#### Mobile

![visuals/Register_mobile1.png](docs\design\visuals\Register_mobile1.png)

![visuals/Register_mobile2.png](docs\design\visuals\Register_mobile2.png)

Registration requires a username, role, password, and password confirmation.
Users must choose one of the following roles:

- Student
- Homemaker
- Professional

The selected role is stored with the user profile and determines the default
category set assigned to the user.

### Dashboard

#### Web

[visuals/Dashboard.png]

Dashboard displays budget amount, expense total, remaining budget, utilization,
budget status, recent expenses, and budget controls.

The Recent Expenses section provides:

- Month filter
- Year filter
- Day filter

Changing a filter refreshes only the displayed expense list for the selected period.

New users have a default budget value of 0 until a budget is created or updated
using the Edit Budget action.

### Expense Entry

#### Web

![visuals/Add_expense1.jpg](docs\design\visuals\Add_expense1.jpg)

![visuals/Add_expense2.jpg](docs\design\visuals\Add_expense2.jpg)

#### Mobile

![visuals/Add_expense_mobile1.png](docs\design\visuals\Add_expense_mobile1.jpg)

![visuals/Add_expense_mobile2.png](docs\design\visuals\Add_expense_mobile2.jpg)

The Add Expense form places Amount across the full width of the form, Category
beside the Date presets/custom picker, followed by Description and Save.

The selected date determines the date saved for the new expense. The category
dropdown contains only the defaults assigned to the signed-in user's role.



### Expenses

#### Web

visuals/Expenses.png

The Expenses page lists amount, category, date, and description with category
filtering.

Selecting an expense displays the available actions:

- Edit
- Delete

Edit opens the Add Expense page with the selected expense's existing amount,
category, date, and description pre-populated.

Delete displays a confirmation dialog before the expense is permanently
removed.

After a successful edit or delete operation, the expense list refreshes while
preserving active filters.

### Analytics

Reference screenshots are available in the `visuals/Analytics/` folder.

Analytics provides Year, Month, Day, and Category filters; a category
distribution and spending summary; and comparison with the previous full month.

Future months and years are unavailable. Invalid period selections are rejected
and reset to a valid period with user feedback.