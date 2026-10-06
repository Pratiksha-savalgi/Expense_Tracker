# Design Visuals

Reference images and diagrams for the current Expense Tracker are stored in
[docs/design/visuals](design/visuals). They illustrate the browser-to-Flask-to-
SQLite architecture and the login, Dashboard, expense entry, Expenses, and
Analytics screens.

The running application and its current behavior are authoritative if an
older visual differs. Current expense entry and display contain amount,
category, date, and optional description only; no subcategory or expense-type
controls are part of the application.

Analytics is limited to the current month and earlier. The Dashboard shows
current-month budget metrics and recent expenses; budgets themselves can be
created for any valid month and year.
