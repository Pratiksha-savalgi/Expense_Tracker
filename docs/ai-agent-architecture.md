# SpendWise AI Agent Architecture

SpendWise AI keeps the existing authenticated Flask chat API and Groq SDK
integration, while replacing regex intent routing as the primary path with
tool selection, backend retrieval, and a separate final-answer generation.

## Data flow

1. The authenticated browser sends a message to `POST /api/chat` with the
   existing session cookie and CSRF header. Client-supplied history is ignored.
2. The API validates the session against `users`, loads bounded conversation
   memory for that user, and sends the question plus approved tool definitions
   to Groq.
3. Groq can select one named tool and structured arguments. It cannot submit
   SQL, choose `user_id`, or directly access SQLite.
4. The policy and registry reject unknown tools, extra arguments, invalid
   periods, and malformed values. Backend code injects the authenticated user
   ID into every service call.
5. Retrieval services perform parameterized user-scoped queries and return
   JSON-compatible structured results. When the user does not name a period,
   the orchestrator uses the current month instead of asking for clarification.
   The selected result is returned to Groq as untrusted data for a grounded
   explanation. Report-style model text (tables, HTML, or headings) is replaced
   with a short conversational summary before it reaches the chat.
6. The assistant response is stored with the user message, then returned to
   the browser. The chat UI uses `textContent` to display model and data text.

## Retrieval and tool registry

`backend/services/retrieval_service.py` provides financial summary, total
spending, history, recent and top expenses, category totals and trends, budget
status and analytics, month comparison, yearly summary, and spending patterns.
Expense descriptions and other user-created values are treated as untrusted
data, not policy or instructions. Monetary totals use `Decimal`; list-like
results and tool output sizes are bounded.

`backend/services/tool_registry.py` publishes only the approved schemas to
Groq. `backend/services/assistant_policy.py` validates the returned name and
arguments before dispatch. The model never generates SQL, and no raw database
connection or credentials are placed in tool results or prompts.

## Conversation memory

`backend/services/memory_service.py` persists user/assistant pairs in the
additive `assistant_messages` table and a user-scoped focus row in
`assistant_memory_focus` (last tool, period, and category). Queries always
filter by the authenticated user ID. The default context is the latest 10
messages (five turns); configure
`SPENDWISE_MEMORY_MAX_MESSAGES` from 2 to 20 and retention in days with
`SPENDWISE_MEMORY_RETENTION_DAYS` from 1 to 365. Memory is supplementary
context and is never trusted as instructions. The browser cannot supply or
override it.

## Mutations and confirmation workflow

Expense and budget CRUD schemas are registered only when
`ENABLE_CRUD_AGENT=1`. CRUD is disabled by default. The backend validates
amounts, dates, category ownership, record ownership, and budget periods, then
stores a canonical pending action with a short expiry. The user sees the
proposed change and must explicitly confirm or cancel it.

Confirmation requires the same authenticated user and CSRF-protected API.
The backend revalidates the current records, acquires a SQLite write
transaction, applies the mutation and consumes the one-time confirmation
token atomically. Tokens are user-scoped, expire after 10 minutes, and cannot
be replayed. Identical pending requests are deduplicated, and only one distinct
action may be awaiting confirmation for a user at a time. The model does not
receive the confirmation token.

## Security and compatibility

- Existing session authentication, `users` validation, ownership rules, and
  CSRF middleware remain in place for chat and confirmation.
- Every retrieval query is scoped to the authenticated user and uses bound
  parameters; expense/category joins include matching ownership.
- API keys remain server-side. Provider errors continue to be sanitized.
- Prompt text, memory, descriptions, category names, notes, and tool results
  are untrusted. The system policy does not treat retrieved content as
  instructions.
- The existing expense/budget tables and normal UI routes are unchanged.
  Database initialization adds only assistant memory and pending-action
  tables/indexes, preserving existing records and schemas.
- If retrieval or tool calling is disabled, the existing intent-based,
  read-only assistant path remains available during migration.

## Feature flags

| Variable | Default | Purpose |
| --- | --- | --- |
| `ENABLE_RETRIEVAL_AGENT` | `1` | Use retrieval-agent chat orchestration. |
| `ENABLE_TOOL_CALLING` | `1` | Enable Groq function/tool selection. |
| `ENABLE_CRUD_AGENT` | `0` | Register and enable confirmed expense/budget mutations. |

`ENABLE_CRUD_AGENT` is off unless the server environment sets it to `1`.
While it is off, mutation tools are not registered, so Groq cannot select
`create_expense` or the other mutation tools. Clear change requests then
explain that assistant editing is turned off. Set `ENABLE_CRUD_AGENT=1` and
restart the server to propose changes. Confirmation, CSRF, ownership checks,
and the one-time expiry remain in force either way.

Copy `.env.example` to `.env` and configure `GROQ_API_KEY` and `GROQ_MODEL` on
the server. Validate retrieval, provider behavior, authorization, and
confirmation flows before enabling CRUD in any deployment.

## Migration notes

Existing chat clients continue posting to `/api/chat`; no client-provided
history is required. The server exposes bounded memory through authenticated
`GET /api/chat`. Existing `answer_financial_question` and intent utilities
remain for compatibility and for disabling the new orchestrator. New database
tables are created with `CREATE TABLE IF NOT EXISTS`; no existing table is
rewritten.
