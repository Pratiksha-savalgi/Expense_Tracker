# Web Page Development

## 1. Purpose

Build the frontend pages for the Expense Tracker using simple, maintainable HTML, CSS, and JavaScript, rendered through Flask templates. The goal is to create a clean, form-driven interface for users to register, sign in, manage their expenses, and navigate the application without adding unnecessary complexity.

This work should follow the project architecture and the visual design documented in:

- [docs/design-visuals.md](../../docs/design-visuals.md)
- [docs/visuals/login-wireframe.svg](../../docs/visuals/login-wireframe.svg)
- [docs/visuals/expenses-dashboard-wireframe.svg](../../docs/visuals/expenses-dashboard-wireframe.svg)
- [docs/visuals/data-flow-diagram.svg](../../docs/visuals/data-flow-diagram.svg)
- [docs/design.md](../../docs/design.md)

## 2. Technologies to Use

Use only the approved frontend stack for the project:

- HTML
- CSS
- JavaScript
- Flask Templates

Do not introduce additional frameworks or libraries unless explicitly approved by the project requirements.

## 3. Pages to Build

Create pages that match the Expense Tracker flow and UI structure:

### Login
- Render a clean login form with email/username and password fields.
- Add a link or alternate action for registration.
- Show validation or authentication errors returned by Flask.

### Register
- Create a registration form with required user details.
- Validate fields before submission.
- Display clear error messages when the input is invalid or duplicate.

### Dashboard
- Show the authenticated user’s main expense management area.
- Include navigation to add, edit, view, and delete expense actions.
- Display summary information such as total spending where appropriate.

### Add Expense
- Create a simple form for amount, category, date, and description.
- Submit the form to a Flask route that validates and saves the record.
- Show success or error feedback to the user.

### Edit Expense
- Render a pre-filled form for an existing expense record.
- Allow the user to update the same fields.
- Submit the update to the backend and confirm the result.

## 4. UI Guidelines

Keep the layout simple and consistent with the repository’s visual design.

- Use a clean, readable layout.
- Keep styling consistent across all pages.
- Prefer a straightforward form-based design.
- Maintain spacing, alignment, and readable typography.
- Keep the interface focused on core expense-tracking actions.
- Match the visual intent from the design visuals in the project.

## 5. Form Rules

Follow consistent form behavior across the frontend:

- Mark all required fields clearly.
- Use basic client-side validation for common issues like empty fields or invalid date formats.
- Show clear error messages to the user.
- Keep validation simple and helpful, without replacing backend validation.
- Ensure forms are easy to complete on both desktop and smaller screens.

## 6. Navigation Rules

The page flow should be straightforward:

- Login → Dashboard
- Dashboard → Add Expense / Edit Expense / View Records
- Dashboard → Logout support
- Each page should provide clear navigation or return paths.
- Ensure authenticated users can access expense functionality and unauthenticated users are redirected appropriately.

## 7. Flask Integration

The frontend must integrate with the Flask application using standard route-based behavior:

- Render templates using Flask routes.
- Submit forms to backend routes for login, registration, add, edit, and delete actions.
- Display server-side messages, form errors, and validation feedback.
- Use data returned by Flask to render dynamic lists, summaries, and form values.
- Keep the browser layer focused on presentation and user interaction, while the backend enforces logic.

## 8. Expected Output

The deliverable should include:

- HTML templates for login, register, dashboard, add expense, and edit expense views
- CSS files for the shared styling and layout
- JavaScript files only if lightweight client-side behavior is needed
- Simple, reusable structure suitable for the Expense Tracker project

## 9. Implementation Standards

- Keep code readable and beginner-friendly.
- Follow Flask template conventions and keep page structure organized.
- Reuse common UI patterns where possible.
- Avoid unnecessary visual complexity.
- Keep the implementation aligned with the project’s architecture, design, and accepted feature scope.
