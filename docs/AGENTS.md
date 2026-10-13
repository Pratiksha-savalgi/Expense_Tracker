# Project Guidance

## Goal

Maintain SpendWise: account access, user-scoped expense management, monthly
budgets, category analytics, and the Phase 1 AI Assistant.

## Source of truth

- [requirements.md](requirements.md) defines product scope.
- [spec.md](spec.md) defines behavior, validation, and data rules.
- [design.md](design.md) describes the architecture and current data model.
- [plan.md](plan.md) records the current structure and verification commands.
- [tech-stack.md](tech-stack.md) records the approved technology stack.
- [requirements.md](requirements.md) is the primary source for the Phase 1 AI
  Assistant scope, supported intents, and acceptance criteria.
- [../expense-tracker-team-requirements.md](../expense-tracker-team-requirements.md)
  summarizes the current feature requirements.
- Skill files in [../.cursor/skills](../.cursor/skills) provide layer-specific
  implementation guidance.

Keep all of these documents consistent with the application. If a document
conflicts with current behavior or another source-of-truth document, update the
conflicting documentation rather than preserving contradictory requirements.

## Architecture and scope

- HTML, CSS, and lightweight JavaScript provide the browser interface.
- Flask handles routes, authentication, validation, authorization, and business
  logic.
- SQLite persists user, category, expense, and budget records.
- Expense fields are amount, category, date, and optional description.
- There are no subcategories or Liability/Savings expense types.
- Expenses and categories belong to a user; all reads and writes must enforce
  user ownership.
- Analytics must not allow a future month or year, and expense dates must not
  exceed today.
- Budget entry accepts any valid month/year; the analytics period restriction
  does not limit budgets.
- Phase 1 AI Assistant answers are grounded in the signed-in user's records.
  Expense and budget changes are off unless `ENABLE_CRUD_AGENT=1`, and even
  then each change waits for that user's explicit confirmation. Do not add
  forecasting or autonomous actions through the assistant.
- AI responses must be based only on the authenticated user's data. Query and
  authorize that user's records before composing model context; never expose
  another user's financial information.
- Use Groq as the only AI provider in Phase 1. Send it only the minimum
  summarized context retrieved for the authenticated user; never include
  credentials or another user's financial information.
- Preserve existing authentication, Expense Management, Dashboard, Budget
  Tracking, and Analytics behavior when adding the assistant. See the Phase 1
  requirements for its supported intents and response rules.

## Engineering workflow

1. Read the relevant requirements and specification before changing behavior.
2. Follow the existing backend, database, frontend, and testing patterns.
3. Keep changes focused and avoid adding features outside the documented scope.
4. Validate request data on the server even where browser validation exists.
5. Add or update targeted tests for behavior changes.
6. Run `python -m unittest discover -s tests -q` when application behavior
   changes.
7. Update affected documentation in place; replace obsolete instructions rather
   than appending contradictory corrections.

## Security and quality

- Hash passwords and require a valid session for protected routes.
- Require CSRF protection for state-changing requests.
- Scope SQL reads and writes to the active user.
- Keep database operations parameterized and monetary arithmetic decimal-safe.
- Preserve saved user data during legacy schema migrations.
