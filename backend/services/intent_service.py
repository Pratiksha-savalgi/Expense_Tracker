import calendar
import re
from datetime import date


_MONTH_LOOKUP = {
    name.casefold(): month
    for month in range(1, 13)
    for name in (calendar.month_name[month], calendar.month_abbr[month])
}


def _month_matches(message):
    matches = []
    for name, month in _MONTH_LOOKUP.items():
        match = re.search(rf"(?<![a-z]){re.escape(name)}(?![a-z])", message, re.I)
        if match:
            matches.append((match.start(), month))
    return sorted(matches)


def _period(message, today, month=None):
    year_match = re.search(r"\b(20\d{2})\b", message)
    year = int(year_match.group(1)) if year_match else today.year
    if "yesterday" in message:
        selected = date.fromordinal(today.toordinal() - 1)
        return selected.year, selected.month, selected.isoformat(), today.isoformat()
    if "today" in message:
        return today.year, today.month, today.isoformat(), date.fromordinal(
            today.toordinal() + 1
        ).isoformat()
    if "last month" in message or "previous month" in message:
        selected = date(today.year, today.month, 1)
        previous = date.fromordinal(selected.toordinal() - 1)
        return previous.year, previous.month, None, None

    if month is None:
        matches = _month_matches(message)
        month = matches[0][1] if matches else None
    month = month or today.month
    if year_match is None and month > today.month:
        year -= 1
    return year, month, None, None


def detect_intent(message, categories, today=None):
    today = today or date.today()
    normalized = message.casefold()

    if re.search(
        r"\b(add|create|edit|update|delete|remove|set|change|modify)\b"
        r".*\b(expense|expenses|budget|profile)\b",
        normalized,
    ):
        return {"intent": "READ_ONLY_REFUSAL"}

    comparison = any(
        term in normalized
        for term in ("compare", "comparison", "versus", " vs ", "than last month")
    )
    month_matches = _month_matches(normalized)
    if comparison:
        if len(month_matches) >= 2:
            year_match = re.search(r"\b(20\d{2})\b", normalized)
            months = [month for _, month in month_matches[:2]]
            if year_match:
                first_year = second_year = int(year_match.group(1))
            else:
                first_year, second_year = (
                    today.year - (months[0] > today.month),
                    today.year - (months[1] > today.month),
                )
            return {
                "intent": "MONTH_COMPARISON",
                "periods": [(first_year, months[0]), (second_year, months[1])],
            }
        current_period = (today.year, today.month)
        previous = date(current_period[0], current_period[1], 1)
        previous_month = date.fromordinal(previous.toordinal() - 1)
        return {
            "intent": "MONTH_COMPARISON",
            "periods": [
                (current_period[0], current_period[1]),
                (previous_month.year, previous_month.month),
            ],
        }

    budget_question = (
        re.search(r"\b(remaining|utilization|utilisation|exceed|exceeded|over budget)\b", normalized)
        or re.search(
            r"\b(how much|what is|what's|show|check|status)\b.*\bbudget\b"
            r"|\bbudget\b.*\b(remaining|status|spent|utilization|utilisation)\b",
            normalized,
        )
    )
    if budget_question:
        year, month, _, _ = _period(normalized, today)
        return {"intent": "BUDGET_STATUS", "year": year, "month": month}

    matched_category = next(
        (
            category
            for category in sorted(categories, key=lambda item: len(item["name"]), reverse=True)
            if re.search(
                rf"(?<!\w){re.escape(category['name'].casefold())}(?!\w)",
                normalized,
            )
        ),
        None,
    )
    if re.search(
        r"\b(which|what|top|highest)\b.*\b(categories|category)\b"
        r"|\b(categories|category)\b.*\b(highest|most|top)\b",
        normalized,
    ) and not re.search(r"\b(how much|how many)\b.*\b(spend|spent|spending)\b", normalized):
        year, month, start_date, end_date = _period(normalized, today)
        return {
            "intent": "CATEGORY_SPENDING",
            "year": year,
            "month": month,
            "start_date": start_date,
            "end_date": end_date,
            "category_id": None,
            "category_name": None,
            "highest_category": True,
        }

    if matched_category:
        year, month, start_date, end_date = _period(normalized, today)
        return {
            "intent": "CATEGORY_SPENDING",
            "year": year,
            "month": month,
            "start_date": start_date,
            "end_date": end_date,
            "category_id": matched_category["id"] if matched_category else None,
            "category_name": matched_category["name"] if matched_category else None,
            "highest_category": False,
        }

    category_phrase = re.search(
        r"\b(?:on|for)\s+(.+?)(?=\s+(?:this|last|in|during)\b|[?.!,]|$)",
        normalized,
    )
    missing_category = (
        category_phrase
        and not re.fullmatch(r"(?:what|which)\s+categories?", category_phrase.group(1).strip())
        and not _month_matches(category_phrase.group(1))
    )
    if missing_category:
        return {"intent": "CATEGORY_NOT_FOUND"}

    if re.search(
        r"\b(spend|spent|spending)\b"
        r"|\b(how much|total|amount)\b.*\b(expense|expenses)\b",
        normalized,
    ):
        year, month, start_date, end_date = _period(normalized, today)
        return {
            "intent": "TOTAL_SPENDING",
            "year": year,
            "month": month,
            "start_date": start_date,
            "end_date": end_date,
            "include_category_breakdown": bool(
                re.search(r"\b(categories|category|breakdown)\b", normalized)
            ),
        }

    if re.search(r"\b(top|largest|highest)\b.*\b(expense|expenses|transaction|transactions)\b", normalized):
        count_match = re.search(r"\btop\s+(\d{1,2})\b", normalized)
        limit = min(int(count_match.group(1)), 10) if count_match else 5
        year, month, start_date, end_date = _period(normalized, today)
        return {
            "intent": "TOP_EXPENSES",
            "year": year,
            "month": month,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
        }

    return {"intent": "UNSUPPORTED"}
