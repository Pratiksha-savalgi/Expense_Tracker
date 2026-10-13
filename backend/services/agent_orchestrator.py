"""Select and normalize approved SpendWise tools around the model call."""

import calendar
import re
from datetime import date

from backend.services.action_service import resolve_user_category
from backend.services.assistant_policy import canonicalize_amount, crud_agent_enabled
from backend.services.tool_registry import get_tool_specs
from database.database import database_connection


_MONTH_LOOKUP = {
    name.casefold(): month
    for month in range(1, 13)
    for name in (calendar.month_name[month], calendar.month_abbr[month])
    if name
}

_CONTEXT_REFERENCE = re.compile(
    r"\b(there|that|those|same|it|contributed|was spent)\b",
    re.I,
)
_RANKING = re.compile(
    r"where am i spending|spending most|most of my (?:money|spending)|"
    r"which category|highest category|top category|contributed the most",
    re.I,
)
MUTATION_TOOLS = {
    "create_expense",
    "update_expense",
    "delete_expense",
    "create_budget",
    "update_budget",
    "delete_budget",
}
_CURRENT_MONTH_TOOLS = {
    "get_financial_summary",
    "get_total_spending",
    "get_category_totals",
    "get_category_trends",
    "get_budget_status",
    "get_top_expenses",
    "get_spending_patterns",
}

CRUD_DISABLED_RESPONSE = (
    "I understood that as a change to your records, but assistant editing is currently turned off. "
    "I can still explain your spending and budgets."
)
CRUD_DISABLED_REASON = (
    "ENABLE_CRUD_AGENT is disabled. backend/services/tool_registry.py omits mutation tools "
    "unless that flag is on, and backend/services/config.py feature_enabled defaults it to false. "
    "Groq therefore cannot select create_expense or the other mutation tools, request_tool_call "
    "returns no tool call, and the previous chat handler replaced that with a generic clarification. "
    "Set ENABLE_CRUD_AGENT=1 in the server environment and restart to propose changes. "
    "Each change still requires the same user's CSRF-protected confirmation before it is saved."
)


def is_category_ranking(message):
    return bool(_RANKING.search(message or ""))


def references_context(message):
    return bool(_CONTEXT_REFERENCE.search(message or ""))


def normalize_tool_arguments(name, arguments, message, user_id, focus=None, today=None):
    today = today or date.today()
    arguments = dict(arguments or {})
    if "amount" in arguments:
        arguments["amount"] = canonicalize_amount(arguments["amount"])
    if name == "create_expense" and not arguments.get("date"):
        arguments["date"] = today.isoformat()

    specs = get_tool_specs()
    allowed = set((specs.get(name) or {}).get("parameters", {}))
    if name in _CURRENT_MONTH_TOOLS or name in {
        "get_month_comparison",
        "get_yearly_summary",
        "get_budget_analytics",
        "get_recent_expenses",
        "get_spending_history",
    }:
        explicit = explicit_period(message, today)
        if explicit is None and references_context(message) and focus:
            explicit = {
                key: focus.get("arguments", {}).get(key)
                for key in ("period", "year", "month")
                if focus.get("arguments", {}).get(key) is not None
            } or None
        arguments.pop("period", None)
        arguments.pop("year", None)
        arguments.pop("month", None)
        if name == "get_month_comparison" and explicit is None:
            arguments.pop("comparison_year", None)
            arguments.pop("comparison_month", None)
        applied = False
        if explicit:
            for key, value in explicit.items():
                if key in allowed:
                    arguments[key] = value
                    applied = True
        if not applied and "period" in allowed and name in _CURRENT_MONTH_TOOLS:
            arguments["period"] = "this_month"
        elif not applied and name in {"get_yearly_summary", "get_budget_analytics"} and "year" in allowed:
            arguments["year"] = today.year

        if name in {"get_category_totals", "get_total_spending"} and not is_category_ranking(message):
            category = mentioned_category(message, user_id)
            if category is None and references_context(message) and focus:
                category = focus.get("category") or focus.get("top_category")
            if category and "category" in allowed:
                arguments["category"] = category
            else:
                arguments.pop("category", None)
        elif "category" in arguments and is_category_ranking(message):
            arguments.pop("category", None)

    if allowed:
        arguments = {key: value for key, value in arguments.items() if key in allowed}
    return arguments


def infer_tool_call(message, user_id, focus=None, today=None):
    today = today or date.today()
    kind = _mutation_kind(message)
    if kind:
        if not crud_agent_enabled():
            return {
                "type": "reply",
                "response": CRUD_DISABLED_RESPONSE,
                "fallback_reason": CRUD_DISABLED_REASON,
            }
        return _infer_mutation(kind, message, user_id, today)

    read_tool = _infer_read_tool(message, focus)
    if read_tool:
        return {"type": "tool", "name": read_tool, "arguments": {}}
    return None


def explicit_period(message, today=None):
    today = today or date.today()
    text = (message or "").casefold()
    if re.search(r"\blast month\b|\bprevious month\b", text):
        return {"period": "last_month"}
    if re.search(r"\bthis year\b|\byear to date\b", text):
        return {"period": "this_year"}
    if re.search(r"\blast year\b", text):
        return {"period": "last_year"}
    if re.search(r"\ball time\b|\boverall\b", text):
        return {"period": "all_time"}
    if re.search(r"\bthis month\b|\bcurrent month\b", text):
        return {"period": "this_month"}
    months = _month_matches(text)
    year_match = re.search(r"\b(20\d{2})\b", text)
    if months:
        month = months[0][1]
        if year_match:
            year = int(year_match.group(1))
        else:
            year = today.year if month <= today.month else today.year - 1
        return {"year": year, "month": month}
    if year_match and re.search(r"\b(in|during|for|of)\s+20\d{2}\b", text):
        return {"year": int(year_match.group(1))}
    return None


def parse_amount(message):
    cleaned = (message or "").replace(",", "")
    currency = re.search(r"(?:₹|rs\.?|inr)\s*(\d+(?:\.\d{1,2})?)", cleaned, re.I)
    if currency:
        return canonicalize_amount(currency.group(1))
    for match in re.finditer(r"\b(\d+(?:\.\d{1,2})?)\b", cleaned):
        if re.fullmatch(r"20\d{2}", match.group(1)):
            continue
        return canonicalize_amount(match.group(1))
    return None


def mentioned_category(message, user_id):
    text = (message or "").casefold()
    with database_connection() as connection:
        categories = connection.execute(
            "SELECT name, normalized_name FROM categories WHERE user_id = ? "
            "ORDER BY LENGTH(name) DESC",
            (user_id,),
        ).fetchall()
        for row in categories:
            if re.search(rf"(?<![a-z]){re.escape(row['normalized_name'])}(?![a-z])", text):
                return row["name"]
        for alias, candidates in _alias_items():
            if re.search(rf"(?<![a-z]){re.escape(alias)}(?![a-z])", text):
                for candidate in candidates:
                    for row in categories:
                        if row["normalized_name"] == candidate:
                            return row["name"]
    return None


def build_focus(tool_name, arguments, result):
    categories = []
    if tool_name == "get_financial_summary":
        categories = (result.get("categories") or {}).get("categories") or []
    elif tool_name == "get_category_totals":
        categories = result.get("categories") or []
    top = categories[0]["category"] if categories else None
    stored = {}
    for key in ("period", "year", "month", "category"):
        if arguments.get(key) is not None:
            stored[key] = arguments[key]
    category = arguments.get("category") or result.get("requested_category") or result.get("category") or top
    return {
        "tool": tool_name,
        "arguments": stored,
        "category": category,
        "top_category": top or category,
    }


def _alias_items():
    from backend.services.action_service import _CATEGORY_ALIASES

    return _CATEGORY_ALIASES.items()


def _month_matches(text):
    matches = []
    for name, month in _MONTH_LOOKUP.items():
        match = re.search(rf"(?<![a-z]){re.escape(name)}(?![a-z])", text, re.I)
        if match:
            matches.append((match.start(), month))
    return sorted(matches)


def _mutation_kind(message):
    text = " ".join((message or "").casefold().split())
    if re.search(r"\b(delete|remove)\b", text) and "budget" in text:
        return "delete_budget"
    if re.search(r"\b(delete|remove)\b", text) and "expense" in text:
        return "delete_expense"
    if "budget" in text and re.search(r"\b(set|create|add|update|change|make)\b", text):
        if re.search(r"\b(update|change|modify)\b", text):
            return "update_budget"
        return "set_budget"
    if re.search(r"\b(add|record|create|log|enter|save)\b", text) and re.search(
        r"\b(expense|spent)\b", text
    ):
        return "create_expense"
    if re.search(r"\bi spent\b", text) or re.search(r"\bspent\b.+\bon\b", text):
        return "create_expense"
    return None


def _infer_read_tool(message, focus):
    text = (message or "").casefold()
    if is_category_ranking(message):
        return "get_category_totals"
    if any(word in text for word in ("summary", "overview")) or "how am i doing" in text:
        return "get_financial_summary"
    if "budget" in text and re.search(r"\b(remaining|status|left|exceed|utilization|utilisation)\b", text):
        return "get_budget_status"
    if "top" in text and "expense" in text:
        return "get_top_expenses"
    if re.search(r"\b(compare|comparison|versus|vs)\b", text):
        return "get_month_comparison"
    if re.search(r"\bhow much\b", text) or ("total" in text and "spend" in text):
        return "get_total_spending"
    if references_context(message) and focus:
        if focus.get("category") or focus.get("top_category"):
            return "get_category_totals"
        return focus.get("tool") or "get_total_spending"
    return None


def _infer_mutation(kind, message, user_id, today):
    if kind == "create_expense":
        amount = parse_amount(message)
        subject = _expense_subject(message)
        if not amount or not subject:
            return {
                "type": "reply",
                "response": "Tell me the amount and what you spent it on, for example ₹500 on lunch.",
                "fallback_reason": "The expense request is missing an amount or category.",
            }
        return {
            "type": "tool",
            "name": "create_expense",
            "arguments": {
                "amount": amount,
                "category": subject,
                "date": today.isoformat(),
            },
        }
    if kind == "delete_expense":
        subject = _expense_subject(message)
        if not subject:
            return {
                "type": "reply",
                "response": "Which expense should I delete? You can mention its description or category.",
                "fallback_reason": "The delete request did not identify an expense.",
            }
        matches = _matching_expenses(user_id, subject)
        if not matches:
            return {
                "type": "reply",
                "response": f"I couldn't find a {subject} expense in your records.",
                "fallback_reason": "No user-owned expense matched the delete request.",
            }
        if len(matches) > 1:
            lines = [f"I found more than one {subject} expense. Tell me which one to delete:"]
            for item in matches[:5]:
                lines.append(
                    f"- ₹{item['amount']} {item['category']} on {item['expense_date']}"
                    + (f" ({item['description']})" if item["description"] else "")
                )
            return {
                "type": "reply",
                "response": "\n".join(lines),
                "fallback_reason": "More than one expense matched, so confirmation was not started.",
            }
        return {
            "type": "tool",
            "name": "delete_expense",
            "arguments": {"expense_id": matches[0]["id"]},
        }

    period = _budget_period(message, today)
    if period is None:
        return {
            "type": "reply",
            "response": "Which month should that budget apply to?",
            "fallback_reason": "The budget request did not include a month.",
        }
    year, month = period
    exists = _budget_exists(user_id, year, month)
    if kind == "delete_budget":
        if not exists:
            month_name = calendar.month_name[month]
            return {
                "type": "reply",
                "response": f"You don't have a {month_name} {year} budget to delete.",
                "fallback_reason": "No budget exists for the requested month.",
            }
        return {"type": "tool", "name": "delete_budget", "arguments": {"year": year, "month": month}}

    amount = parse_amount(message)
    if not amount:
        return {
            "type": "reply",
            "response": "What amount should I use for that budget?",
            "fallback_reason": "The budget request did not include an amount.",
        }
    if kind == "update_budget" and not exists:
        month_name = calendar.month_name[month]
        return {
            "type": "reply",
            "response": (
                f"You don't have a {month_name} {year} budget yet. "
                "Ask me to set one and I'll prepare it for confirmation."
            ),
            "fallback_reason": "Update was requested for a month without a budget.",
        }
    tool_name = "update_budget" if exists or kind == "update_budget" else "create_budget"
    return {
        "type": "tool",
        "name": tool_name,
        "arguments": {"amount": amount, "year": year, "month": month},
    }


def _expense_subject(message):
    text = (message or "").casefold()
    patterns = (
        r"(?:₹|rs\.?|inr)?\s*\d[\d,]*(?:\.\d{1,2})?\s+([a-z][a-z &/-]{1,40}?)\s+expense\b",
        r"\b(?:delete|remove)\s+(?:my\s+|the\s+)?([a-z][a-z &/-]{1,40}?)\s+expense\b",
        r"\bspent\b.+?\bon\s+([a-z][a-z &/-]{1,40})",
        r"\bfor\s+([a-z][a-z &/-]{1,40})",
        r"\bon\s+([a-z][a-z &/-]{1,40})",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if not match:
            continue
        subject = re.split(r"\b(today|yesterday|please|now|this month)\b", match.group(1))[0]
        subject = " ".join(subject.split()).strip(" .,-")
        if subject and subject not in {"expense", "expenses", "budget", "my", "the"}:
            return subject
    return None


def _budget_period(message, today):
    months = _month_matches((message or "").casefold())
    if not months:
        return None
    month = months[-1][1]
    year_match = re.search(r"\b(20\d{2})\b", message or "")
    year = int(year_match.group(1)) if year_match else today.year
    return year, month


def _budget_exists(user_id, year, month):
    with database_connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM budgets WHERE user_id = ? AND year = ? AND month = ?",
            (user_id, year, month),
        ).fetchone()
    return row is not None


def _matching_expenses(user_id, subject):
    needle = subject.casefold()
    with database_connection() as connection:
        rows = connection.execute(
            "SELECT id, amount, category, expense_date, description FROM expenses "
            "WHERE user_id = ? ORDER BY expense_date DESC, id DESC LIMIT 100",
            (user_id,),
        ).fetchall()
        resolved = resolve_user_category(user_id, subject, connection)
    matches = []
    for row in rows:
        description = (row["description"] or "").casefold()
        category = (row["category"] or "").casefold()
        description_match = needle in description
        category_match = needle in category or (
            resolved is not None and category == resolved["name"].casefold() and needle in category
        )
        if description_match or (needle in category):
            matches.append(
                {
                    "id": row["id"],
                    "amount": row["amount"],
                    "category": row["category"],
                    "expense_date": row["expense_date"],
                    "description": row["description"] or "",
                }
            )
        elif category_match:
            matches.append(
                {
                    "id": row["id"],
                    "amount": row["amount"],
                    "category": row["category"],
                    "expense_date": row["expense_date"],
                    "description": row["description"] or "",
                }
            )
    return matches
