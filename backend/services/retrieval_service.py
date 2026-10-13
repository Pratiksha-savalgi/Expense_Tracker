"""User-scoped, read-only finance retrieval tools for SpendWise AI."""

import calendar
from datetime import date
from decimal import Decimal

from database.database import database_connection


MAX_RESULT_LIMIT = 50
MAX_HISTORY_MONTHS = 120


def _period_bounds(period="this_month", year=None, month=None, today=None):
    today = today or date.today()
    if month is not None and year is None:
        month = int(month)
        if not 1 <= month <= 12:
            raise ValueError("A valid month is required.")
        year = today.year if month <= today.month else today.year - 1
    if year is not None and month is not None:
        if not 1 <= int(month) <= 12:
            raise ValueError("A valid year and month are required together.")
        start = date(int(year), int(month), 1)
        selected_year, selected_month = start.year, start.month
        end = date(
            selected_year + (selected_month == 12),
            1 if selected_month == 12 else selected_month + 1,
            1,
        )
    elif year is not None:
        selected_year = int(year)
        if not 1900 <= selected_year <= 2200:
            raise ValueError("Unsupported financial period.")
        start = date(selected_year, 1, 1)
        end = date(selected_year + 1, 1, 1)
        return start.isoformat(), end.isoformat(), selected_year, None
    elif period in {"this_month", "last_month"}:
        start = date(today.year, today.month, 1)
        if period == "last_month":
            start = date.fromordinal(start.toordinal() - 1)
            start = date(start.year, start.month, 1)
        selected_year, selected_month = start.year, start.month
        end = date(
            selected_year + (selected_month == 12),
            1 if selected_month == 12 else selected_month + 1,
            1,
        )
    elif period in {"this_year", "last_year"}:
        selected_year = today.year if period == "this_year" else today.year - 1
        selected_month = None
        start = date(selected_year, 1, 1)
        end = date(selected_year + 1, 1, 1)
    elif period == "all_time":
        return None, None, None, None
    else:
        raise ValueError("Unsupported financial period.")
    return start.isoformat(), end.isoformat(), selected_year, selected_month


def _money(value):
    return format(Decimal(value or "0"), "f")


def _expense_totals(user_id, start, end, category=None):
    conditions = ["e.user_id = ?"]
    parameters = [user_id]
    join = ""
    if start is not None:
        conditions.extend(["e.expense_date >= ?", "e.expense_date < ?"])
        parameters.extend([start, end])
    if category:
        join = (
            " LEFT JOIN categories c "
            "ON c.id = e.category_id AND c.user_id = e.user_id "
        )
        conditions.append("LOWER(COALESCE(c.name, e.category)) = ?")
        parameters.append(category.casefold())
    with database_connection() as connection:
        rows = connection.execute(
            "SELECT e.amount FROM expenses e" + join + " WHERE " + " AND ".join(conditions),
            parameters,
        )
        total = Decimal("0")
        count = 0
        for row in rows:
            total += Decimal(row["amount"])
            count += 1
    return {"total": total, "expense_count": count}


def get_total_spending(user_id, period="this_month", year=None, month=None, category=None):
    start, end, selected_year, selected_month = _period_bounds(period, year, month)
    row = _expense_totals(user_id, start, end, category)
    result = {
        "period": _period_name(period, selected_year, selected_month),
        "total": format(row["total"], "f"),
        "expense_count": row["expense_count"],
    }
    if category:
        result["category"] = category
    return result


def _period_name(period, year, month):
    if year is None:
        return "all_time"
    if month is None:
        return str(year)
    return f"{calendar.month_name[month]} {year}"


def get_spending_history(user_id, period="this_year", year=None, month=None):
    start, end, selected_year, selected_month = _period_bounds(period, year, month)
    conditions = ["user_id = ?"]
    parameters = [user_id]
    if start is not None:
        conditions.extend(["expense_date >= ?", "expense_date < ?"])
        parameters.extend([start, end])
    totals = {}
    with database_connection() as connection:
        rows = connection.execute(
            "SELECT substr(expense_date, 1, 7) AS month, amount FROM expenses WHERE "
            + " AND ".join(conditions) + " ORDER BY month",
            parameters,
        )
        for row in rows:
            bucket = totals.setdefault(row["month"], [Decimal("0"), 0])
            bucket[0] += Decimal(row["amount"])
            bucket[1] += 1
    return {
        "period": _period_name(period, selected_year, selected_month),
        "month_count": len(totals),
        "truncated": len(totals) > MAX_HISTORY_MONTHS,
        "months": [
            {"month": key, "total": format(value[0], "f"), "expense_count": value[1]}
            for key, value in sorted(totals.items())[-MAX_HISTORY_MONTHS:]
        ],
    }


def get_recent_expenses(user_id, limit=10, period="all_time"):
    limit = _validated_limit(limit)
    start, end, _, _ = _period_bounds(period)
    conditions = ["e.user_id = ?"]
    parameters = [user_id]
    if start is not None:
        conditions.extend(["e.expense_date >= ?", "e.expense_date < ?"])
        parameters.extend([start, end])
    with database_connection() as connection:
        rows = connection.execute(
            "SELECT e.id, e.amount, e.expense_date, "
            "COALESCE(c.name, e.category) AS category, e.description "
            "FROM expenses e LEFT JOIN categories c "
            "ON c.id = e.category_id AND c.user_id = e.user_id WHERE "
            + " AND ".join(conditions)
            + " ORDER BY e.expense_date DESC, e.id DESC LIMIT ?",
            (*parameters, limit),
        ).fetchall()
    return {
        "expenses": [
            {
                "id": row["id"],
                "amount": _money(row["amount"]),
                "date": row["expense_date"],
                "category": row["category"],
                "description": (row["description"] or "")[:500],
            }
            for row in rows
        ],
        "returned_count": len(rows),
        "limit": limit,
    }


def get_top_expenses(user_id, limit=5, period="this_month", year=None, month=None):
    limit = _validated_limit(limit)
    start, end, _, _ = _period_bounds(period, year, month)
    conditions = ["e.user_id = ?"]
    parameters = [user_id]
    if start is not None:
        conditions.extend(["e.expense_date >= ?", "e.expense_date < ?"])
        parameters.extend([start, end])
    with database_connection() as connection:
        rows = connection.execute(
            "SELECT e.id, e.amount, e.expense_date, "
            "COALESCE(c.name, e.category) AS category, e.description "
            "FROM expenses e LEFT JOIN categories c "
            "ON c.id = e.category_id AND c.user_id = e.user_id WHERE "
            + " AND ".join(conditions)
            + " ORDER BY CAST(e.amount AS NUMERIC) DESC, e.expense_date DESC, e.id DESC LIMIT ?",
            (*parameters, limit),
        ).fetchall()
    return {
        "expenses": [
            {
                "id": row["id"],
                "amount": _money(row["amount"]),
                "date": row["expense_date"],
                "category": row["category"],
                "description": (row["description"] or "")[:500],
            }
            for row in rows
        ],
        "returned_count": len(rows),
        "limit": limit,
    }


def get_category_totals(user_id, period="this_month", year=None, month=None, category=None):
    start, end, selected_year, selected_month = _period_bounds(period, year, month)
    conditions = ["e.user_id = ?"]
    parameters = [user_id]
    if start is not None:
        conditions.extend(["e.expense_date >= ?", "e.expense_date < ?"])
        parameters.extend([start, end])
    totals = {}
    with database_connection() as connection:
        rows = connection.execute(
            "SELECT COALESCE(c.name, e.category) AS category, e.amount "
            "FROM expenses e LEFT JOIN categories c "
            "ON c.id = e.category_id AND c.user_id = e.user_id WHERE "
            + " AND ".join(conditions)
            + " ORDER BY category COLLATE NOCASE",
            parameters,
        )
        for row in rows:
            bucket = totals.setdefault(row["category"], [Decimal("0"), 0])
            bucket[0] += Decimal(row["amount"])
            bucket[1] += 1
    categories = sorted(totals.items(), key=lambda item: (-item[1][0], item[0].casefold()))
    rows = [
        {"category": name, "total": format(values[0], "f"), "expense_count": values[1]}
        for name, values in categories[:MAX_RESULT_LIMIT]
    ]
    result = {
        "period": _period_name(period, selected_year, selected_month),
        "categories": rows,
    }
    if category:
        needle = str(category).casefold()
        matched = [row for row in rows if row["category"].casefold() == needle]
        result["requested_category"] = category
        result["category_total"] = matched[0]["total"] if matched else None
    return result


def get_category_trends(user_id, period="this_month", year=None, month=None):
    current = get_category_totals(user_id, period, year, month)["categories"]
    _, _, current_year, current_month = _period_bounds(period, year, month)
    if current_month is None:
        return {"period": period, "trends": []}
    prior = date.fromordinal(date(current_year, current_month, 1).toordinal() - 1)
    previous = get_category_totals(user_id, year=prior.year, month=prior.month)["categories"]
    previous_by_name = {row["category"]: Decimal(row["total"]) for row in previous}
    trends = []
    for row in current:
        before = previous_by_name.get(row["category"], Decimal("0"))
        now = Decimal(row["total"])
        trends.append({
            "category": row["category"],
            "current_total": format(now, "f"),
            "previous_total": format(before, "f"),
            "change": format(now - before, "f"),
            "change_percent": format((now - before) / before * 100, ".1f") if before else None,
        })
    return {"period": _period_name(period, current_year, current_month), "trends": trends}


def get_budget_status(user_id, period="this_month", year=None, month=None):
    _, _, selected_year, selected_month = _period_bounds(period, year, month)
    if selected_year is None or selected_month is None:
        selected = date.today()
        selected_year, selected_month = selected.year, selected.month
    start, end, _, _ = _period_bounds("this_month", selected_year, selected_month)
    with database_connection() as connection:
        budget = connection.execute(
            "SELECT budget_amount FROM budgets WHERE user_id = ? AND year = ? AND month = ?",
            (user_id, selected_year, selected_month),
        ).fetchone()
        spending = connection.execute(
            "SELECT amount FROM expenses WHERE user_id = ? AND expense_date >= ? AND expense_date < ?",
            (user_id, start, end),
        )
        spent = Decimal("0")
        expense_count = 0
        for row in spending:
            spent += Decimal(row["amount"])
            expense_count += 1
    amount = Decimal(budget["budget_amount"]) if budget else None
    remaining = amount - spent if amount is not None else None
    utilization = spent / amount * 100 if amount else None
    return {
        "period": _period_name(period, selected_year, selected_month),
        "budget": format(amount, "f") if amount is not None else None,
        "spent": format(spent, "f"),
        "remaining": format(remaining, "f") if remaining is not None else None,
        "utilization_percent": format(utilization, ".1f") if utilization is not None else None,
        "status": "not_set" if amount is None else (
            "exceeded" if spent > amount else
            "warning" if utilization >= Decimal("80") else "on_track"
        ),
        "expense_count": expense_count,
    }


def get_budget_analytics(user_id, year=None):
    selected_year = int(year or date.today().year)
    if not 1900 <= selected_year <= date.today().year + 100:
        raise ValueError("Choose a valid budget year.")
    start = f"{selected_year:04d}-01-01"
    end = f"{selected_year + 1:04d}-01-01"
    with database_connection() as connection:
        budgets = connection.execute(
            "SELECT month, budget_amount FROM budgets WHERE user_id = ? AND year = ? "
            "ORDER BY month LIMIT 12",
            (user_id, selected_year),
        ).fetchall()
        expenses = connection.execute(
            "SELECT CAST(substr(expense_date, 6, 2) AS INTEGER) AS month, amount FROM expenses "
            "WHERE user_id = ? AND expense_date >= ? AND expense_date < ? "
            "ORDER BY month",
            (user_id, start, end),
        )
        expense_by_month = {}
        for row in expenses:
            expense_by_month[row["month"]] = expense_by_month.get(row["month"], Decimal("0")) + Decimal(row["amount"])
    budget_by_month = {row["month"]: Decimal(row["budget_amount"]) for row in budgets}
    return {
        "year": selected_year,
        "months": [
            {
                "month": month,
                "label": calendar.month_name[month],
                "budget": format(budget_by_month[month], "f") if month in budget_by_month else None,
                "spent": format(expense_by_month.get(month, Decimal("0")), "f"),
            }
            for month in range(1, 13)
        ],
    }


def get_month_comparison(user_id, year=None, month=None, comparison_year=None, comparison_month=None):
    today = date.today()
    current_year, current_month = int(year or today.year), int(month or today.month)
    previous = date.fromordinal(date(current_year, current_month, 1).toordinal() - 1)
    other_year = int(comparison_year or previous.year)
    other_month = int(comparison_month or previous.month)
    current = get_total_spending(user_id, year=current_year, month=current_month)
    prior = get_total_spending(user_id, year=other_year, month=other_month)
    current_categories = get_category_totals(user_id, year=current_year, month=current_month)["categories"]
    prior_categories = get_category_totals(user_id, year=other_year, month=other_month)["categories"]
    current_by_name = {row["category"]: Decimal(row["total"]) for row in current_categories}
    prior_by_name = {row["category"]: Decimal(row["total"]) for row in prior_categories}
    changes = [
        {"category": name, "change": format(current_by_name.get(name, Decimal("0")) - prior_by_name.get(name, Decimal("0")), "f")}
        for name in current_by_name.keys() | prior_by_name.keys()
    ]
    changes.sort(key=lambda item: abs(Decimal(item["change"])), reverse=True)
    difference = Decimal(current["total"]) - Decimal(prior["total"])
    previous_total = Decimal(prior["total"])
    return {
        "current": current,
        "comparison": prior,
        "difference": format(difference, "f"),
        "change_percent": format(difference / previous_total * 100, ".1f") if previous_total else None,
        "category_changes": changes[:10],
    }


def get_yearly_summary(user_id, year=None):
    selected_year = int(year or date.today().year)
    start, end = date(selected_year, 1, 1).isoformat(), date(selected_year + 1, 1, 1).isoformat()
    with database_connection() as connection:
        rows = connection.execute(
            "SELECT substr(expense_date, 1, 7) AS month, amount "
            "FROM expenses WHERE user_id = ? AND expense_date >= ? AND expense_date < ? "
            "ORDER BY month",
            (user_id, start, end),
        )
        monthly = {}
        for row in rows:
            bucket = monthly.setdefault(row["month"], [Decimal("0"), 0])
            bucket[0] += Decimal(row["amount"])
            bucket[1] += 1
        annual_rows = connection.execute(
            "SELECT substr(expense_date, 1, 4) AS year, amount FROM expenses "
            "WHERE user_id = ? ORDER BY expense_date",
            (user_id,),
        )
        annual_totals = {}
        for row in annual_rows:
            annual_totals[row["year"]] = annual_totals.get(row["year"], Decimal("0")) + Decimal(row["amount"])
    total = sum((values[0] for values in monthly.values()), Decimal("0"))
    average_yearly = (
        sum(annual_totals.values(), Decimal("0")) / len(annual_totals)
        if annual_totals else Decimal("0")
    )
    return {
        "year": selected_year,
        "total": format(total, "f"),
        "monthly_average": format(total / 12, "f"),
        "average_yearly_spending": format(average_yearly, "f"),
        "years_with_spending": len(annual_totals),
        "months_with_expenses": len(monthly),
        "months": [
            {"month": key, "total": format(values[0], "f"), "expense_count": values[1]}
            for key, values in sorted(monthly.items())
        ],
    }


def get_spending_patterns(user_id, period="this_year", year=None, month=None):
    start, end, selected_year, selected_month = _period_bounds(period, year, month)
    conditions = ["e.user_id = ?"]
    parameters = [user_id]
    if start is not None:
        conditions.extend(["e.expense_date >= ?", "e.expense_date < ?"])
        parameters.extend([start, end])
    with database_connection() as connection:
        rows = connection.execute(
            "SELECT e.expense_date, e.amount FROM expenses e WHERE "
            + " AND ".join(conditions)
            + " ORDER BY e.expense_date",
            parameters,
        )
        by_weekday = {}
        for row in rows:
            weekday = date.fromisoformat(row["expense_date"]).weekday()
            bucket = by_weekday.setdefault(weekday, [Decimal("0"), 0])
            bucket[0] += Decimal(row["amount"])
            bucket[1] += 1
    return {
        "period": _period_name(period, selected_year, selected_month),
        "weekday_totals": [
            {
                "weekday": calendar.day_name[index],
                "expense_count": by_weekday[index][1],
                "total": format(by_weekday[index][0], "f"),
            }
            for index in by_weekday
        ],
        "observations": "Descriptive historical patterns only; not financial advice.",
    }


def get_financial_summary(user_id, period="this_month", year=None, month=None):
    return {
        "spending": get_total_spending(user_id, period, year, month),
        "categories": get_category_totals(user_id, period, year, month),
        "budget": get_budget_status(user_id, period, year, month),
        "largest_expenses": [
            {key: item[key] for key in ("amount", "date", "category")}
            for item in get_top_expenses(user_id, 3, period, year, month)["expenses"]
        ],
    }


def _validated_limit(limit):
    if isinstance(limit, bool):
        raise ValueError("Result limit must be an integer.")
    try:
        parsed = int(limit)
    except (TypeError, ValueError) as error:
        raise ValueError("Result limit must be an integer.") from error
    if parsed < 1 or parsed > MAX_RESULT_LIMIT:
        raise ValueError(f"Result limit must be between 1 and {MAX_RESULT_LIMIT}.")
    return parsed
