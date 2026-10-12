# Authentication and Authorization

## Purpose

Implement account access and ownership checks for the current Expense Tracker.
Align behavior with [docs/requirements.md](../../docs/requirements.md) and
[docs/spec.md](../../docs/spec.md).

### Required behavior

- Register using username, role-based access, password, and password confirmation.
- Enforce case-sensitive unique usernames.
- Enforce username and password validation rules defined in the Authentication and authorization section.
- Hash passwords before persistence and verify hashes on login.
- Create a session only after valid credentials and clear it on logout.
- Require authentication for Dashboard, Expenses, Analytics, expense actions, and budget actions.
- Clear invalid user sessions and redirect to login.
- Scope every expense, category, budget, filter, and analytics operation to the active user.
- Protect POST form submissions with the existing CSRF token validation.
- A user must provide a valid username and password to sign in.
- The username comparison is case sensitive.
- Login is successful only when the provided credentials match a registered user's credentials.
- Invalid or missing credentials must prevent login and display an appropriate error message.
- A successful login creates an authenticated session for the user.
- A user can sign out, which clears the authenticated session.
- An unauthenticated user attempting to access protected pages or actions must be redirected to the Login page.
- Protected access includes Dashboard, Expenses, Analytics, expense actions, and budget actions.
- Each authenticated user can access only their own expenses, categories, and budgets.
- Invalid or expired user sessions must be cleared and the user must be redirected to the Login page.

## Phase 1 AI Assistant

The assistant is available only to an authenticated user and must use that
user's records exclusively. Apply the existing session and ownership checks to
all assistant data retrieval; never include another user's financial data in
the response context. Phase 1 is read-only; see
[docs/requirements.md](../../../docs/requirements.md) for the feature scope.

## Scope

The account identifier is username, not email. Expense data consists of amount,
category, date, and optional description; there is no subcategory or expense
type. Do not implement authorization or persistence paths for those removed
fields.

## Quality

Keep backend session and authorization checks authoritative. Do not expose
password hashes or internal errors in user-facing messages. Test unauthenticated
access and cross-user record operations.
