# Intent

## What we are building

A simple Expense Tracker application for managing personal expenses. Users can add, view, edit, and delete expenses, organize them by category, check spending by date or category, and see basic totals.

## Why we are building it

People spend money on different things every day but often do not keep track of those expenses, so they may not know how much they are spending or where most of their money is going.

Today, expenses may be written in a notebook, phone notes, Excel, or only remembered. That makes it hard to keep all expenses in one place, calculate total spending, or find a particular expense. Users need a simple place to add and manage expenses, see them, and keep spending organized.

## Who will use it

The application is for individuals who manage and track their personal expenses. That includes:

- **Students**, who manage spending from pocket money or a limited monthly budget
- **Homemakers**, who manage and monitor household expenses
- **Working professionals**, who manage monthly personal expenses

Each user should only see and manage their own expenses.

## Main goal

Give users a simple way to record and manage personal expenses in one place, stay organized, and understand their spending through basic totals and categories.

## Version 2: Why this next step is required

The initial Expense Tracker solves the core problem of recording expenses, but personal financial management becomes much more useful when the user can compare spending to a plan. Version 2 adds monthly budget controls and category-based analysis so the user can move beyond tracking records and begin actively managing financial behavior.

## Business value

Budget tracking and category analytics provide direct business value because they turn the app from a passive log into a decision-support tool. Instead of simply storing historical expenses, the system helps the user detect overspending, understand major spending categories, and plan upcoming monthly costs more effectively.

## User value

Users benefit because they can:

- set a monthly spending limit
- see how much is left to spend
- understand which categories consume the most funds
- monitor whether they are close to or beyond budget
- decide where to reduce spending based on real trend data

## Expected benefits

- Better control of monthly spending
- Reduced risk of accidental overspending
- Faster understanding of spending patterns
- Clearer visibility into the categories that matter most
- More useful dashboard feedback for day-to-day financial decisions

## Success metrics

A successful Version 2 implementation should show that:

- the user can create and update a month budget successfully
- remaining balance and percentage used are accurate
- warning and exceedance states appear at the right thresholds
- cost summaries are correct by category and month
- the dashboard displays financial status clearly without interrupting the normal expense workflow
- users can understand their spending patterns in under a short review cycle

The Version 2 goals extend the original application toward practical personal finance support while preserving the simple and beginner-friendly experience of the existing Expense Tracker.

## Phase 1: AI Assistant Integration

Users should be able to ask natural-language questions about their recorded
spending and budgets and receive useful, contextual financial insights without
manually reviewing every list, table, or chart. The Phase 1 assistant makes
SpendWise's existing information easier to understand and act on while
remaining informational and read-only. Its detailed scope is defined in
[requirements.md](requirements.md).
