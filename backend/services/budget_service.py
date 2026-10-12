import calendar
from decimal import Decimal

from database.database import database_connection
from backend.services.expense_service import get_category_totals, get_month_total


def build_budget_context(user_id, year, month):
    with database_connection() as connection:
        budget_row = connection.execute(
            "SELECT budget_amount FROM budgets WHERE user_id = ? AND year = ? AND month = ?",
            (user_id, year, month),
        ).fetchone()
    spent = get_month_total(user_id, year, month)
    budget = Decimal(budget_row["budget_amount"]) if budget_row else None
    remaining = budget - spent if budget is not None else None
    utilization = (spent / budget * 100) if budget else None
    status = (
        "not_set" if budget is None
        else "exceeded" if spent > budget
        else "warning" if utilization >= Decimal("80")
        else "on_track"
    )
    return {
        "intent": "BUDGET_STATUS",
        "period": f"{calendar.month_name[month]} {year}",
        "budget": format(budget, "f") if budget is not None else None,
        "spent": format(spent, "f"),
        "remaining": format(remaining, "f") if remaining is not None else None,
        "utilization_percent": format(utilization, ".1f") if utilization is not None else None,
        "status": status,
    }


def build_comparison_context(user_id, periods):
    period_contexts = []
    category_totals = []
    for year, month in periods:
        totals = get_month_total(user_id, year, month)
        period_contexts.append({
            "period": f"{calendar.month_name[month]} {year}",
            "total": totals,
        })
        category_totals.append(get_category_totals(user_id, year, month))

    difference = period_contexts[0]["total"] - period_contexts[1]["total"]
    previous_total = period_contexts[1]["total"]
    percentage = (difference / previous_total * 100) if previous_total else None
    highlights = []
    category_names = set(category_totals[0]) | set(category_totals[1])
    for name in category_names:
        change = category_totals[0].get(name, Decimal("0")) - category_totals[1].get(name, Decimal("0"))
        if change:
            highlights.append({"category": name, "difference": format(change, "f")})
    highlights.sort(key=lambda item: abs(Decimal(item["difference"])), reverse=True)

    return {
        "intent": "MONTH_COMPARISON",
        "periods": [
            {"period": item["period"], "total": format(item["total"], "f")}
            for item in period_contexts
        ],
        "difference": format(difference, "f"),
        "percentage_change": format(percentage, ".1f") if percentage is not None else None,
        "category_highlights": highlights[:3],
    }
