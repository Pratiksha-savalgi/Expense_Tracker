# Authentication and Authorization

## 1. Purpose

Handle registration, login, logout, session management, and access control for the Expense Tracker. This skill ensures that users can securely create accounts, sign in, and only access their own expense data.

This work must stay aligned with:

- [docs/AGENTS.md](../../docs/AGENTS.md)
- [docs/requirements.md](../../docs/requirements.md)
- [docs/spec.md](../../docs/spec.md)
- [docs/design.md](../../docs/design.md)

## 2. Core Rules

- Use secure session-based authentication.
- Do not store plain-text passwords.
- Keep registration and login validation focused on the approved project requirements.
- Enforce per-user data isolation.
- Reject unauthenticated access to protected expense actions.
- Keep error messages clear and user-friendly without exposing internal implementation details.

## 3. Required Behavior

### Registration
- Accept a valid user registration payload.
- Validate required fields such as email/username and password.
- Reject invalid or duplicate accounts according to the project rules.
- Hash the password before saving.
- Redirect or respond with appropriate success or validation messages.

### Login
- Accept email/username and password.
- Validate the supplied credentials against stored user information.
- Start an authenticated session only for valid credentials.
- Return clear error feedback for invalid login attempts.

### Logout
- End the current user session.
- Redirect unauthenticated users away from protected pages.

### Authorization
- Require the user to be logged in before accessing expense operations.
- Ensure a logged-in user can only access their own records.
- Prevent cross-user viewing, editing, or deletion of expense entries.

## 4. Implementation Guidance

- Use Flask session support for user identity.
- Keep authentication logic in the backend layer, not the browser.
- Use simple, readable validation and response handling.
- Reuse project patterns for redirecting users to the login flow when required.
- Avoid adding admin or multi-user roles beyond the approved scope.

## 5. Output Expectations

The implementation should include:

- secure user registration flow
- secure login flow
- logout behavior
- protected routes for expense management
- consistent validation and error handling

## 6. Quality Standards

- Keep the flow simple and easy to follow.
- Prefer explicit validation and clear session checks.
- Align all authentication behavior with the project design and requirements.
- Do not invent features beyond the approved personal expense tracker scope.
