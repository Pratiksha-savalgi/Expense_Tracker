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
- Never make independent assumptions to resolve ambiguities in business behavior, validation rules, or architecture.
- If requirements are unclear, pause and seek explicit approval before proceeding.

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
