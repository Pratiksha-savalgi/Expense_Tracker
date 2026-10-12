# Technology Stack Selection

## 1. Purpose

Enables the choice of required technology stack elements to implement the project.

This skill defines the approved technologies for the Expense Tracker and ensures that implementation decisions stay aligned with the project’s requirements, design, and intended architecture.

This work must stay aligned with:

- [docs/AGENTS.md](../../docs/AGENTS.md)
- [docs/requirements.md](../../docs/requirements.md)
- [docs/spec.md](../../docs/spec.md)
- [docs/design.md](../../docs/design.md)
- [docs/tech-stack.md](../../docs/tech-stack.md)

## 2. Core Rule

Use only the technologies approved for this project unless the project documentation explicitly authorizes a change.

## 3. Approved Stack

- HTML for page structure and forms
- CSS for styling and layout
- JavaScript for lightweight client-side interactions
- Flask for server-side routes, business logic, and session handling
- SQLite for data persistence and user/expense storage

## 4. Decision Guidance

- Prefer the simplest technology that satisfies the requirement.
- Keep implementation beginner-friendly and consistent with project scope.
- Do not introduce frameworks, libraries, or services that are not described in the approved project documents.
- For the current Version 2 scope, the existing stack is sufficient for monthly budget tracking and category analytics.
- If a technology choice would affect architecture, security, or scope, pause and confirm with the project requirements before proceeding.

## Phase 1 AI Assistant

Phase 1 extends rather than replaces the approved stack with a Flask chat API
and a dedicated Groq service layer. Use Groq's OpenAI-compatible
chat-completions API and the `llama-3.3-70b-versatile` model by default,
configured through server-side `GROQ_API_KEY` and `GROQ_MODEL` values. Keep
the assistant read-only, base responses on authenticated-user data, and limit
it to Total Spending, Category Spending, Top Expenses, Budget Status, and
Month Comparison as defined in
[docs/requirements.md](../../../docs/requirements.md).

## 5. Version 2 Stack Review

The current stack remains sufficient for the Version 2 release. Monthly budget tracking and category analytics can be implemented using the existing Flask backend, SQLite data layer, and HTML/CSS/JavaScript frontend without changing the project’s core technology decisions.

Recommended approach:

- Keep Flask for all server-side calculations and route logic.
- Keep SQLite for budget persistence and analytics queries.
- Use simple HTML/CSS/JavaScript for dashboard panels, budget status, and category summaries.
- Avoid introducing a chart library unless it is explicitly required later.

## 6. Quality Standard

The technology selection should support a maintainable, secure, and straightforward expense tracking application without unnecessary complexity.
