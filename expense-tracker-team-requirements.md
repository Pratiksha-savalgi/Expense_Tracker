# Expense Tracker: Team Requirements and Module Plan

This document defines the requested base-version improvements while keeping the existing application scope: account access, manual expense tracking, categories and dates, filtering, totals, and monthly budgets. It divides implementation between two team members and does not replace existing project documentation.

## Product Scope

- Account access and user-specific data isolation
- Manual expense entry and management
- Categories, subcategories, dates, and descriptions
- Expense filtering and displayed totals
- Monthly budget tracking
- Dashboard and category analytics visualizations

## Persona Requirements

### Student

- Enter an amount, category, date, and optional description with minimal steps.
- See the expected currency in the amount field; receive useful validation for blank, invalid, zero, or negative amounts and decimal with only two decimal places(ex:32.12,9.00)
- Find expenses by date or category and see a total for the records currently displayed.
- Understand the selected month's budget, amount spent, amount remaining, and warning or exceeded state.
- Record expenses comfortably on a phone.

### Homemaker

- Choose recognizable household categories such as groceries, utilities, transport, and household supplies.
- Use category and date filters easily when reviewing household spending.
- See whether the displayed total represents all expenses or filtered expenses.
- See the selected budget month and year, budget amount, spending, and remaining amount.
- Receive clear save confirmation and actionable validation guidance.
- Confirm before deleting an expense.

### Working Professional

- Record routine expenses quickly, with the date defaulting to today.
- Edit or delete an incorrect expense through clear, consistent controls.
- Identify active date and category filters.
- See monthly budget status without leaving the expense list.
- Read forms and totals on small screens without horizontal scrolling for ordinary tasks.
- Receive clear feedback after signing in or submitting a form.

## Requirements for All Users

- Every field has a clear label; validation errors explain what needs correction.
- Currency formatting is consistent across expenses, totals, and budgets.
- Entered values remain populated when validation fails.
- Empty filter results and unset budgets have clear empty states.
- Expenses, categories, subcategories, and budgets are scoped to the authenticated user.
- Controls work with a keyboard and at mobile viewport sizes.

## Module A: Expenses and Categories

**Owner:** Team Member A

**Purpose:** Own expense entry and management, including user-defined categories and subcategories.

### Functional Requirements

- Support add, view, edit, and delete for a user's expenses.
- Record amount, date, optional description, main category, subcategory, and expense type: `Liability` or `Savings`.
- Default the expense date to today.
- Display the currency expected by the application.
- Reject blank, malformed, zero, decimal greater than 2 places and negative amounts with actionable feedback.
- Require delete confirmation and provide success/error messages after form submission.
- Support category and date filters; the displayed total must reflect the visible records.
- Preserve user-entered values after validation errors.

### Category Entry Requirements

- Provide a category dropdown populated with that user's existing categories.
- Include built-in categories and subcategories: Food (Breakfast, Lunch, Dinner, Groceries, Snacks); Utilities (Electricity, Water, Internet, Gas); Transport (Public transit, Fuel, Vehicle maintenance); Household (Supplies, Repairs, Furniture); Health (Medical, Pharmacy); Shopping (Clothing, Personal care); Education (Books, Fees); Entertainment (Subscriptions, Outings); Bills (Rent, Insurance, Loan payments); and Other (Miscellaneous).
- Include an **Add category** option in the dropdown for creating a custom category.
- After selecting a main category, show its associated subcategories.
- Include an option to add a subcategory when the desired one is not listed.
- Save a new subcategory for an existing category immediately and retain it in that category's future dropdown options. Save a subcategory for a brand-new category together with the expense.
- Normalize capitalization and whitespace so variants such as `Food`, `food`, and ` Food ` do not create duplicate categories.
- Keep category and subcategory data private to the owning user.
- Define how existing expenses with free-text categories are migrated or matched to the new category structure.

### Module A Acceptance Criteria

- A signed-in user can create and later edit an expense with all required fields.
- Liability/Savings type persists and is displayed consistently.
- Selecting a category updates the available subcategories.
- A new category or subcategory can be added during expense entry.
- Case and whitespace variants reuse the same category.
- Category/date filters and displayed totals are correct and user-scoped.
- Deletion asks for confirmation; the expense is removed only after confirmation.
- Forms are keyboard-accessible and usable on phone-sized screens.

### Module A Tests

- Valid and invalid amount, date, category, and subcategory input.
- Category suggestions, creation, and case/whitespace normalization.
- Liability/Savings persistence through create, edit, and list operations.
- Category, date, and combined filters; totals reflect the filtered records.
- Validation errors preserve entered fields.
- Cross-user access is denied for view, edit, and delete operations.
- Mobile form layout and delete confirmation behavior.

## Module B: Budgets and Analytics

**Owner:** Team Member B

**Purpose:** Own monthly budget calculations and dashboard/analytics visualizations.

### Budget Requirements

- Store budgets by user, month, and year; updating the same period replaces the previous amount.
- Display the selected month and year, budget amount, amount spent, amount remaining, and utilization.
- Provide clear no-budget, near-limit, and exceeded states in plain language.
- Keep budget status visible on the homepage and expense overview.
- Recalculate the budget summary when relevant expenses or the budget changes.

### Homepage Visualization Requirements

- Show a pie chart divided into **Expenditure** and **Remaining budget**.
- Show the Liability/Savings breakdown within the Expenditure portion.
- Label the selected month and year and provide readable values alongside the chart.
- Include an accessible text or table alternative to the chart.

### Category Analytics Requirements

- Provide an analytics page with a bar chart of main-category totals for a selected month.
- When a user selects a main category, display a bar chart of its subcategory totals.
- Use only expenses belonging to the signed-in user and selected month.
- Show friendly empty states when there is no budget or no category data.
- Keep charts readable on small screens and provide an accessible non-chart alternative.

### Business Rule to Confirm

Proposed assumption: Liability and Savings entries both count toward the amount allocated against the monthly budget; the pie chart's Expenditure portion is their combined total. Confirm this rule with the product owner before implementation, since Savings might instead be treated separately from spending.

### Module B Acceptance Criteria

- Budget create/update works for a selected month and year without duplicate records.
- Spent, remaining, and utilization values are accurate for the selected period.
- Warning and exceeded states are clearly distinguished and use plain language.
- The homepage chart shows expenditure versus remaining budget, with Liability/Savings breakdown.
- The analytics bar chart shows main-category totals and selecting a category reveals its subcategory totals.
- All metrics use only the signed-in user's records and selected month.
- Empty states render without errors, and chart alternatives are available to assistive technologies.
- Budget and analytics views remain usable at mobile sizes.

### Module B Tests

- Budget create/update, invalid values, month transitions, warning, and exceeded states.
- Pie-chart values for known budgets and expense totals.
- Liability/Savings breakdown and total calculations.
- Main-category and subcategory aggregation and drill-down.
- Empty states, mobile presentation, accessibility alternatives, and user isolation.

## Team Boundaries and Integration

- Team Member A owns expense and category data structures, entry forms, expense CRUD, filtering, and associated tests.
- Team Member B owns budget calculations, analytics aggregation, dashboard charts, and associated tests.
- Agree on the shared expense fields before implementation: amount, date, description, category, subcategory, and type.
- Agree on currency precision, month selection, and the Liability/Savings budget rule before building calculations.
- Keep route and service ownership separate where practical. Coordinate shared dashboard integration to avoid concurrent edits to the same files.
- Integrate only after each module's tests pass, then run end-to-end checks for user isolation and cross-module totals.