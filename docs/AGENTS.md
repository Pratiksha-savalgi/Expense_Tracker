# AGENTS.md

## Project goal

This repository implements a simple Expense Tracker for individuals to record, manage, and review personal spending in one place.

The project is intended to help users:

- create an account and sign in
- record daily expenses with category, date, and description
- view their own expense records
- edit or delete incorrect entries
- filter by category and date
- see total spending for their own records

## High-level system overview

The project follows a small web application architecture based on the repository design documents:

- Browser-based UI for user interaction
- Flask application for routing, validation, authentication, authorization, and business logic
- SQLite database for storing user and expense data

The browser communicates with Flask. Flask communicates with SQLite. The browser does not talk directly to the database.

## Source of truth

The implementation must stay aligned with the repository’s approved project documents. These are the reference materials for what the project is and how it should be designed:

- [requirements.md](requirements.md) — problem, user need, goals, and functional expectations
- [spec.md](spec.md) — behavioral requirements, validation rules, and acceptance criteria
- [design.md](design.md) — architecture, system context, data model, and functional design
- [tech-stack.md](tech-stack.md) — approved technologies and responsibilities
- [plan.md](plan.md) — implementation scope and sequencing
- [design-visuals.md](design-visuals.md) and [visuals](visuals) — GUI and architecture visuals

If these documents conflict, follow the project requirements and design intent first, then the technical stack and delivery plan.

## Layered guidance model

This repository uses a three-layer operating model for agents and contributors:

1. Project goal and operating rules: this file defines the overall mission, allowed scope, source-of-truth documents, and required behavior for any work.
2. Reference documents: the repository design and requirement documents define what the product should do and how it should be implemented.
3. Task-specific skills: skill files define the exact execution patterns for specialized work such as authentication, data persistence, web pages, or project layout.

This separation is intentional. High-level policy belongs in AGENTS.md, implementation guidance belongs in task-specific skills, and product and technical requirements belong in the reference documents.

## Required SDLC workflow

Perform every task in the repository according to the following lifecycle sequence and always reference the relevant approved documents before implementation decisions are made:

1. Requirements and analysis
   - Read [requirements.md](requirements.md) and [spec.md](spec.md) first.
   - Confirm the exact functional and non-functional requirements for the task.
   - If the requirement is ambiguous, stop and ask the developer for clarification before proceeding.

2. Design and architecture
   - Use [design.md](design.md), [design-visuals.md](design-visuals.md), and [tech-stack.md](tech-stack.md) to understand the architecture, data model, and approved stack.
   - Ensure any design decision is consistent with the approved project structure and scope.

3. Implementation
   - Apply the relevant task-specific skill file in [.cursor/skills](../.cursor/skills) for the required work.
   - Example: use the authentication skill for login logic, the database skill for persistence design, and the web-page skill for page creation.
   - Keep the implementation minimal, readable, and aligned with the repository design.

4. Verification and acceptance
   - Verify the result against the acceptance criteria and project requirements before considering the work complete.
   - Confirm behavior matches the documented user flows, data rules, and security constraints.

## Functional requirements summary

The Expense Tracker must support:

- user registration
- user login and logout
- secure session-based access
- add, view, edit, and delete expenses
- category assignment for expenses
- filtering by category and date
- display of total spending
- strict per-user data isolation

## Non-functional requirements summary

The solution should be:

- simple and easy to use
- reliable for normal daily expense tracking
- responsive enough for typical browser usage
- secure with proper authentication and authorization
- maintainable within the approved technology stack

## Scope boundaries

Keep the implementation focused on the approved personal expense tracker scope. Do not introduce unrelated features or unsupported complexity such as:

- advanced budgeting tools
- payment-method tracking
- keyword search beyond the approved scope
- admin functions for multiple users
- analytics dashboards or external frameworks
- extra fields or features not described in the project documents

## Architecture and design requirements

The project should follow the design described in the repository:

- HTML provides page structure and forms
- CSS implements the user interface styling and layout
- JavaScript handles lightweight UI interactions
- Flask handles business logic, validation, authentication, routing, and data access
- SQLite stores users and expenses

The design should stay beginner-friendly and aligned with the approved system architecture.

## Validation and security rules

The implementation must enforce the requirements already documented by the project:

- expenses require valid amount, category, and date values
- amount must be greater than zero
- an expense must belong to a registered user
- user must log in before managing expenses
- passwords must not be stored in plain text
- users can only access their own data
- no cross-user viewing, editing, or deletion of records

## Working rule for agents

- Do not invent requirements beyond the repository documents.
- Keep the solution aligned with the project’s purpose, architecture, and design.
- Prefer simple, readable implementations over broader or more complex alternatives.
- If requirements are unclear, ambiguous, or open to interpretation, stop and ask the developers for clarification before making a decision.
- If requirements are unclear, pause and seek explicit approval before proceeding.
- Before making implementation decisions, consult the relevant requirement and design documents for the task.
- Use the relevant project-specific skill files to follow the approved execution pattern for that task.
- Keep any task-specific solution scoped to the repository’s approved architecture and feature set.
- Consult the developer whenever clarification is needed; do not silently choose a behavior that changes project scope or security expectations.

## Verification

Before considering work complete, verify the behavior against the documented requirements and acceptance criteria:

- valid registration and login
- invalid credentials and invalid form handling
- add, view, edit, and delete expense actions
- filtering by category and date
- correct total spending calculation
- user-specific access enforcement

## Documentation guidance

This file defines the project purpose, scope, and source-of-truth references. It should remain a high-level guide. Low-level implementation details belong in the project-specific skills and implementation files, not in this overview document.
