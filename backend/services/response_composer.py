"""Turn structured retrieval results into short chat replies."""

import calendar
import re
from datetime import date
from decimal import Decimal, InvalidOperation


def format_inr(value):
    if value is None:
        return None
    try:
        amount = Decimal(str(value))
    except InvalidOperation:
        return str(value)
    negative = amount < 0
    quantized = abs(amount).quantize(Decimal("0.01"))
    whole, _, fraction = f"{quantized:.2f}".partition(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.append(head[-2:])
            head = head[:-2]
        if head:
            groups.append(head)
        whole = ",".join(reversed(groups)) + "," + tail
    number = whole if fraction == "00" else f"{whole}.{fraction}"
    return f"{'-' if negative else ''}₹{number}"


def format_percent(value):
    if value is None:
        return None
    number = Decimal(str(value))
    if number == number.to_integral_value():
        return f"{int(number)}%"
    return f"{number.quantize(Decimal('0.1'))}%"


def looks_like_report(text):
    if not isinstance(text, str) or not text.strip():
        return True
    if re.search(r"</?[a-z][^>]*>", text, re.I):
        return True
    if re.search(r"^\s*\|.+\|\s*$", text, re.M):
        return True
    if "|" in text and re.search(r"-{3,}", text):
        return True
    if re.search(r"^#{1,6}\s+\S", text, re.M):
        return True
    return False


def period_phrase(label, today=None):
    today = today or date.today()
    current = f"{calendar.month_name[today.month]} {today.year}"
    previous_month = today.month - 1 or 12
    previous_year = today.year if today.month > 1 else today.year - 1
    previous = f"{calendar.month_name[previous_month]} {previous_year}"
    if label in {None, "", "this_month", current}:
        return "this month"
    if label in {"last_month", previous}:
        return "last month"
    if label in {"this_year", str(today.year)}:
        return "this year"
    if label in {"last_year", str(today.year - 1)}:
        return "last year"
    if label == "all_time":
        return "overall"
    return f"in {label}"


def compose_response(tool_name, result, today=None):
    if not isinstance(result, dict):
        return "I couldn't find matching SpendWise records for that question."
    composers = {
        "get_financial_summary": _compose_financial_summary,
        "get_total_spending": _compose_total_spending,
        "get_category_totals": _compose_category_totals,
        "get_budget_status": _compose_budget_status,
        "get_top_expenses": _compose_top_expenses,
        "get_recent_expenses": _compose_recent_expenses,
        "get_month_comparison": _compose_month_comparison,
        "get_yearly_summary": _compose_yearly_summary,
        "get_spending_history": _compose_spending_history,
        "get_category_trends": _compose_category_trends,
        "get_spending_patterns": _compose_spending_patterns,
        "get_budget_analytics": _compose_budget_analytics,
    }
    composer = composers.get(tool_name, _compose_generic)
    return composer(result, today)


def _plain(value):
    return " ".join(str(value or "").split())


def _category_list(rows):
    labels = [
        f"{row['category']} ({format_inr(row['total'])})"
        for row in rows[:3]
        if row.get("category") is not None
    ]
    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]}, followed by {labels[1]}"
    return f"{labels[0]}, followed by {labels[1]} and {labels[2]}"


def _compose_financial_summary(result, today):
    spending = result.get("spending") or {}
    budget = result.get("budget") or {}
    phrase = period_phrase(spending.get("period") or budget.get("period"), today)
    spent = format_inr(spending.get("total", "0"))
    paragraphs = []
    if budget.get("budget"):
        remaining = Decimal(str(budget.get("remaining") or "0"))
        status = {
            "on_track": "on track",
            "warning": "close to your limit",
            "exceeded": "over budget",
        }.get(budget.get("status"), "on track")
        utilization = format_percent(budget.get("utilization_percent"))
        if remaining < 0:
            paragraphs.append(
                f"You've spent {spent} {phrase}, which is {format_inr(abs(remaining))} "
                f"over your {format_inr(budget['budget'])} budget. "
                f"Your current budget utilization is {utilization}."
            )
        else:
            paragraphs.append(
                f"You've spent {spent} {phrase} out of your {format_inr(budget['budget'])} budget, "
                f"leaving {format_inr(budget.get('remaining'))} remaining. "
                f"Your current budget utilization is {utilization}, so you're {status}."
            )
    else:
        count = int(spending.get("expense_count") or 0)
        noun = "expense" if count == 1 else "expenses"
        paragraphs.append(
            f"You've spent {spent} {phrase} across {count} {noun}. "
            f"There's no budget set for {phrase} yet."
        )

    categories = (result.get("categories") or {}).get("categories") or []
    category_text = _category_list(categories)
    if category_text:
        paragraphs.append(f"Most of your spending has been in {category_text}.")

    largest = result.get("largest_expenses") or []
    if largest:
        top = largest[0]
        paragraphs.append(
            f"Your largest expense {phrase} was {format_inr(top.get('amount'))} "
            f"in {top.get('category')}."
        )
    return "\n\n".join(paragraphs)


def _compose_total_spending(result, today):
    phrase = period_phrase(result.get("period"), today)
    amount = format_inr(result.get("total", "0"))
    if result.get("category"):
        if result.get("expense_count") == 0:
            return f"I don't see any {result['category']} spending {phrase}."
        return f"You spent {amount} on {result['category']} {phrase}."
    count = int(result.get("expense_count") or 0)
    noun = "expense" if count == 1 else "expenses"
    return f"You spent {amount} {phrase} across {count} {noun}."


def _compose_category_totals(result, today):
    phrase = period_phrase(result.get("period"), today)
    if result.get("requested_category"):
        if result.get("category_total") is None:
            return f"I don't see any {result['requested_category']} spending {phrase}."
        return (
            f"You spent {format_inr(result['category_total'])} "
            f"on {result['requested_category']} {phrase}."
        )
    rows = result.get("categories") or []
    if not rows:
        return f"I don't see any spending {phrase}."
    return f"Most of your spending {phrase} is in {_category_list(rows)}."


def _compose_budget_status(result, today):
    phrase = period_phrase(result.get("period"), today)
    if not result.get("budget"):
        return (
            f"You've spent {format_inr(result.get('spent', '0'))} {phrase}. "
            f"There's no budget set for {phrase} yet."
        )
    status = {
        "on_track": "on track",
        "warning": "close to your limit",
        "exceeded": "over budget",
    }.get(result.get("status"), "on track")
    return (
        f"You've spent {format_inr(result.get('spent'))} {phrase} out of your "
        f"{format_inr(result.get('budget'))} budget, leaving {format_inr(result.get('remaining'))} "
        f"remaining. Your current budget utilization is {format_percent(result.get('utilization_percent'))}, "
        f"so you're {status}."
    )


def _compose_top_expenses(result, today):
    expenses = result.get("expenses") or []
    if not expenses:
        return "I don't see any expenses for that period."
    lines = ["Your largest expenses are:"]
    for item in expenses[:5]:
        description = _plain(item.get("description"))
        detail = f" ({description})" if description else ""
        lines.append(
            f"- {format_inr(item.get('amount'))} in {item.get('category')} "
            f"on {item.get('date')}{detail}"
        )
    return "\n".join(lines)


def _compose_recent_expenses(result, today):
    expenses = result.get("expenses") or []
    if not expenses:
        return "I don't see any recent expenses."
    lines = ["Here are your most recent expenses:"]
    for item in expenses[:5]:
        description = _plain(item.get("description"))
        detail = f" ({description})" if description else ""
        lines.append(
            f"- {format_inr(item.get('amount'))} in {item.get('category')} "
            f"on {item.get('date')}{detail}"
        )
    return "\n".join(lines)


def _compose_month_comparison(result, today):
    current = result.get("current") or {}
    prior = result.get("comparison") or {}
    difference = Decimal(str(result.get("difference") or "0"))
    direction = "more" if difference > 0 else "less" if difference < 0 else "the same"
    sentence = (
        f"You spent {format_inr(current.get('total', '0'))} in {current.get('period', 'the current month')} "
        f"and {format_inr(prior.get('total', '0'))} in {prior.get('period', 'the earlier month')}."
    )
    if difference == 0:
        sentence += " That's the same amount."
    else:
        sentence += f" That's {format_inr(abs(difference))} {direction}."
    changes = result.get("category_changes") or []
    if changes:
        top = changes[0]
        sentence += (
            f" The biggest category change was {top.get('category')} "
            f"({format_inr(top.get('change'))})."
        )
    return sentence


def _compose_yearly_summary(result, today):
    year = result.get("year")
    return (
        f"In {year} you've recorded {format_inr(result.get('total', '0'))} "
        f"across {result.get('months_with_expenses', 0)} months, about "
        f"{format_inr(result.get('monthly_average', '0'))} a month."
    )


def _compose_spending_history(result, today):
    months = result.get("months") or []
    if not months:
        return "I don't see spending history for that period."
    recent = months[-3:]
    parts = [f"{item['month']} ({format_inr(item['total'])})" for item in recent]
    return f"Your recent monthly totals are {', '.join(parts)}."


def _compose_category_trends(result, today):
    trends = result.get("trends") or []
    phrase = period_phrase(result.get("period"), today)
    if not trends:
        return f"I don't see category changes {phrase}."
    lead = trends[0]
    change = Decimal(str(lead.get("change") or "0"))
    direction = "up" if change > 0 else "down" if change < 0 else "unchanged"
    return (
        f"The largest category change {phrase} is {lead.get('category')}, "
        f"{direction} by {format_inr(abs(change))}."
    )


def _compose_spending_patterns(result, today):
    rows = result.get("weekday_totals") or []
    phrase = period_phrase(result.get("period"), today)
    if not rows:
        return f"I don't see weekday spending {phrase}."
    top = max(rows, key=lambda item: Decimal(str(item.get("total") or "0")))
    return (
        f"{phrase.capitalize()}, {top.get('weekday')} is your highest spending day "
        f"at {format_inr(top.get('total'))}."
    )


def _compose_budget_analytics(result, today):
    months = [
        item for item in result.get("months") or []
        if Decimal(str(item.get("spent") or "0")) > 0 or item.get("budget")
    ]
    if not months:
        return f"I don't see budget activity for {result.get('year')}."
    recent = months[-1]
    budget = (
        f" against a {format_inr(recent['budget'])} budget"
        if recent.get("budget") else ""
    )
    return (
        f"In {recent.get('label')} {result.get('year')} you spent "
        f"{format_inr(recent.get('spent'))}{budget}."
    )


def _compose_generic(result, today):
    return "I pulled your SpendWise records, but I don't have a short summary for that view yet."
