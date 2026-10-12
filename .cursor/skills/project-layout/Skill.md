# Project Layout and Structure

## 1. Purpose

Defines the repository structure and file responsibilities for the Expense Tracker so that implementation work remains organized, consistent, and aligned with the project design and Version 2 feature scope.

This work must stay aligned with:

- [docs/AGENTS.md](../../docs/AGENTS.md)
- [docs/design.md](../../docs/design.md)
- [docs/plan.md](../../docs/plan.md)
- [docs/requirements.md](../../docs/requirements.md)
- [docs/spec.md](../../docs/spec.md)

## 2. Expected Repository Layout

Use the project layout described by the repository structure:

- backend/ — Flask application and route/business logic
- database/ — database connection and persistence logic
- frontend/ — templates and static assets for UI
- docs/ — product requirements, design, plans, and project reference documents
- .cursor/skills/ — task-specific implementation guidance
- requirements.txt — Python dependencies

## 3. Structural Rules

- Keep domain logic separate from presentation logic.
- Put persistent storage concerns in the database layer.
- Keep frontend templates and static files in frontend/.
- Keep project documents in docs/ and do not mix product requirements with implementation code.
- Keep task-specific guidance in .cursor/skills/ rather than embedding detailed implementation instructions in the project overview.
- Follow the established separation between backend logic, database logic, UI, and documentation.

## 4. Implementation Guidance

When creating or editing code, place work in the appropriate layer rather than adding unrelated code to a different directory.

Examples:

- user authentication logic belongs in backend/
- SQL and table definitions belong in database/
- HTML/CSS/JS belongs in frontend/
- monthly budget and analytics logic belongs in backend/ with database support
- project intent and acceptance criteria remain in docs/

## Phase 1 AI Assistant

Treat the assistant as an extension of the existing application layers: chat
presentation in the frontend, authenticated request and response handling in
the Flask backend, and read-only user-scoped financial retrieval through the
existing database layer. Keep the AI integration replaceable and preserve the
Phase 1 limits in [docs/requirements.md](../../../docs/requirements.md); do not
place financial data access or authorization in the browser.

## 5. Version 2 Layout Expectations

The Version 2 work should remain consistent with the same structure:

- `/dashboard`, `/expenses`, `/analytics`, and budget write routes stay in the backend layer
- budget persistence and user-scoped period/category data access stay in the database layer
- the Dashboard, Expenses, and Analytics templates and responsive summaries stay in the frontend layer
- design decisions and requirement references stay in docs/

## 6. Quality Standard

The repository should remain easy to navigate for a beginner-friendly project, with each area clearly responsible for one part of the application.
