# Web Page Development

## Purpose

Build the Expense Tracker interface using Flask templates, HTML, CSS, and
lightweight JavaScript. Follow the current behavior in
Use the screenshots in the /design/visuals folder as the source of truth for UI implementation and responsiveness.
[docs/requirements.md](../../docs/requirements.md),
[docs/spec.md](../../docs/spec.md), and [docs/design.md](../../docs/design.md).

## Pages

- **Login/Register:** username/password access with clear feedback.
- **Dashboard:** current-month budget amount, spending, remaining amount,
  utilization, status, budget controls, and recent expenses.
- **Expenses:** user-owned unfiltered expense list, category filter, add, edit,
  and delete actions.
- **Add Expense:** amount, category, date presets/custom picker, optional
  description, and a preview of matching existing expenses and analytics.
- **Edit Expense:** amount, category, date, optional description.
- **Analytics:** year, month, day, and category filters; period summary,
  category distribution, empty state, and yearly spending-versus-budget chart
  with hover/focus or touch chart-point details.

There are no subcategory or expense-type controls or displays.

## Phase 1 AI Assistant

The assistant chat interface supports the five read-only intents
defined in [docs/requirements.md](../../../docs/requirements.md): Total Spending,
Category Spending, Top Expenses, Budget Status, and Month Comparison. Keep
questions and responses conversational, show history for the current session,
and do not add UI actions that create, update, or delete expenses or budgets.
Responses must use only authenticated-user data; preserve all existing
SpendWise pages and interactions.

## Add Expense date-filter component

- Match `docs/design/visuals/AddExpense.jpg`: amount across the form, category
  beside the date controls, then description and save. Do not add separate
  transaction-date or filter inputs.
- The one selected period drives both the saved expense date and the filtered
  existing-record preview: Today=today, Yesterday=yesterday, Last 7 Days=today,
  Custom=the selected date. Category is likewise the new expense category and
  preview filter.
- Today is active on initial page load.
- Exactly one quick option is active at a time. Use a visible active treatment
  and update `aria-pressed` consistently.
- Selecting a custom date submits immediately, activates the picker, and clears
  the quick-option active state. Selecting any quick option clears the custom
  date state.
- Submit filters immediately without requiring a separate Apply button.
- Preserve unsaved amount/description when date or category selection changes;
  a filter submission must never save an expense. Preserve filters after a
  valid save.
- Keep the integrated controls usable at desktop, tablet, and mobile widths;
  allow wrapping or a compact grid without horizontal overflow. Do not
  duplicate filter state or inputs.
- Refresh the matching existing-expense list, summary cards, and category
  analytics from the server for the active filter. The Analytics link carries
  the active date window and category. Keep the separate Expenses page as the
  unfiltered ledger.

## Form and interaction rules

- Mark required fields and describe validation failures clearly.
- Expense amount must be positive with no more than two decimal places.
- Expense date inputs have a maximum of today and client-side checks; server
  validation remains authoritative.
- Preserve user-entered values when server validation fails.
- Analytics year/month choices cannot extend beyond the current month/current
  year. Day options must reflect the selected month and year; reject future days.
- Category choices and filters contain only the current user's categories.
- Custom expense-list dates must be valid and no later than today.
- Confirm delete actions in the browser; submit through the protected POST
  route.
- Keep all controls keyboard accessible and layouts responsive.

## Integration and quality

Use the established Flask routes and template data. JavaScript provides
convenience and does not replace server-side validation. Reuse shared styles
and UI patterns; do not add frameworks or libraries without an approved need.
