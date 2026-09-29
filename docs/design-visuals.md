# Design Visuals

This file contains the design diagrams and data-flow visuals as wireframe-style pictures for the Expense Tracker project.

## 1. High-Level Architecture for a Small Expense Tracker

![Small App Architecture](visuals/small-app-architecture.svg)

This architecture is designed for a lightweight application and includes only the layers that are actually required:

- Users / Clients
- Frontend Applications
- API Gateway (optional, not required for the direct Flask route design)
- Backend Services
- Business Logic Components
- Databases
- Security and Authorization
- Storage
- Monitoring
- Deployment Environments
- High-Level Technology Stack

## 2. Architecture Diagram

![Architecture Diagram](visuals/architecture-diagram.svg)

## 3. Level 0 DFD — Business Context

![Level 0 DFD](visuals/data-flow-diagrams/context_diagram.svg)

## 4. Level 1 DFD — Business System

![Level 1 DFD](visuals/data-flow-diagrams/level1-expense-tracker-dfd.svg)

## 5. Login Wireframe

![Login Wireframe](visuals/login-wireframe.svg)

## 6. Expense Dashboard Wireframe

![Expense Dashboard Wireframe](visuals/expenses-dashboard-wireframe.svg)

These visuals are intentionally kept simple, presentation-friendly, and aligned with the Expense Tracker business system and its core data flows.

## 7. Version 2 Monthly Budget Tracking Flow

```mermaid
flowchart TD
    A[User opens dashboard] --> B[User sets monthly budget]
    B --> C[Validate budget amount]
    C --> D[Store budget in database]
    D --> E[User adds expenses]
    E --> F[Calculate total monthly spend]
    F --> G{Spend >= budget?}
    G -- No --> H[Show remaining budget and utilization]
    G -- Yes --> I[Show exceeded budget alert]
    H --> J{Spend >= warning threshold?}
    J -- Yes --> K[Show warning banner]
    J -- No --> L[Normal budget status]
    I --> M[Dashboard summary update]
    K --> M
    L --> M
```

This flow explains the user experience for monthly budget configuration,
remaining balance calculation, warning state management, and the final
visual status shown on the dashboard.

## 8. Version 2 Category Analytics Flow

```mermaid
flowchart TD
    A[User opens analytics section] --> B[Select month]
    B --> C[Fetch user expenses for month]
    C --> D[Group by category]
    D --> E[Calculate category totals]
    E --> F[Calculate category contribution percentage]
    F --> G[Find highest and lowest category]
    G --> H[Render chart and category summary]
    H --> I[Display dashboard analytics view]
```

This flow shows how the system aggregates user expenses into category-level
insights, computes percentages, and presents the results in a readable and
decision-supportive dashboard layout.

## 9. Version 2 UI Interpretation

The Version 2 visual design continues the same lightweight and practical
approach as the original project. It adds dashboard cards for budget status,
remaining balance, utilization percentage, and category charts without
changing the basic user interaction style or the core Expense Tracker
workflow.
