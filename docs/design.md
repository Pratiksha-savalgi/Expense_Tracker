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

- **User**: case-insensitively unique username and password hash.
- **Category**: user-owned display name and normalized comparison name.
- **Expense**: user, amount, category ID and display name, ISO date, optional
  description.
- **Budget**: user, month, year, amount, creation and update timestamps.

No subcategory or expense-type attribute is part of the current data model.
Legacy databases are migrated to the current expense columns while retaining
expense records and normalizing their categories.

## Presentation

- Login and Register provide account access.
- Dashboard displays current-month budget metrics, status, recent expenses, and
  budget controls.
- Expenses provides the complete unfiltered ledger, category filter, and
  expense actions.
- Add Expense follows the AddExpense visual: Amount full width; Category and
  single-choice Date controls side by side; Description; Save. The selected
  date period sets the new expense date and filters the existing-record list,
  summary, and category analytics.
- Edit Expense uses the same amount/category/date/description model.
- Analytics provides year/month/day/category selection, a category
  distribution, and a selectable full-month comparison with the month before
  the chosen comparison month.

### Add Expense date-filter hierarchy

1. Add Expense heading and link back to the unfiltered Expenses ledger.
2. Expense-entry form with Amount, Category, Date controls, Description, and
   Save.
3. Date controls are Today, Yesterday, Last 7 Days, and a custom picker. Today
   is the default. Quick presets choose the saved expense date; custom date
   chooses the exact saved date.
4. Filtered summary cards and category analytics, with a link to open the same
   date window on Analytics.
5. Matching existing expense list.

Today is active on initial load. Quick filter controls use a visually distinct
active state. Selecting a custom date activates the date picker and clears
quick-filter state. A selected date period and category drive both the new
expense fields and the existing-record preview, so the page has one source of
truth and no duplicate date/category filters. Changing a selection refreshes
the list and all date-scoped summary/analytics values without saving a record.
The controls wrap on tablets and use a compact grid on narrow mobile screens.

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
