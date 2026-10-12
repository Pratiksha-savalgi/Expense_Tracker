import calendar
from datetime import date
from decimal import Decimal

from database.database import database_connection


def get_user_categories(user_id):
    with database_connection() as connection:
        return [
            {"id": row["id"], "name": row["name"]}
            for row in connection.execute(
                "SELECT id, name FROM categories WHERE user_id = ? ORDER BY name COLLATE NOCASE",
                (user_id,),
            ).fetchall()
        ]


def get_period_bounds(year, month, start_date=None, end_date=None):
    if start_date and end_date:
        return start_date, end_date
    start = date(year, month, 1)
    end = date(
        year + (month == 12),
        1 if month == 12 else month + 1,
        1,
    )
    return start.isoformat(), end.isoformat()


def get_period_label(year, month, start_date=None):
    if start_date:
        selected_date = date.fromisoformat(start_date)
        return f"{calendar.month_name[selected_date.month]} {selected_date.day}, {selected_date.year}"
    return f"{calendar.month_name[month]} {year}"


def get_expense_rows(user_id, year, month, category_id=None, start_date=None, end_date=None):
    start, end = get_period_bounds(year, month, start_date, end_date)
    conditions = ["e.user_id = ?", "e.expense_date >= ?", "e.expense_date < ?"]
    parameters = [user_id, start, end]
    if category_id is not None:
        conditions.append("e.category_id = ?")
        parameters.append(category_id)
    with database_connection() as connection:
        return connection.execute(
            "SELECT e.amount, e.expense_date, e.category_id, "
            "COALESCE(c.name, e.category) AS category "
            "FROM expenses e LEFT JOIN categories c "
            "ON c.id = e.category_id AND c.user_id = e.user_id "
            f"WHERE {' AND '.join(conditions)} ORDER BY e.expense_date DESC, e.id DESC",
            parameters,
        ).fetchall()


def get_month_total(user_id, year, month):
    rows = get_expense_rows(user_id, year, month)
    return sum((Decimal(row["amount"]) for row in rows), Decimal("0"))


def get_category_totals(user_id, year, month, start_date=None, end_date=None):
    rows = get_expense_rows(
        user_id, year, month, start_date=start_date, end_date=end_date
    )
    totals = {}
    for row in rows:
        category = row["category"]
        totals[category] = totals.get(category, Decimal("0")) + Decimal(row["amount"])
    return totals


def build_expense_context(user_id, intent):
    intent_name = intent["intent"]
    year, month = intent["year"], intent["month"]
    if intent_name == "TOTAL_SPENDING":
        rows = get_expense_rows(
            user_id, year, month, start_date=intent["start_date"], end_date=intent["end_date"]
        )
        total = sum((Decimal(row["amount"]) for row in rows), Decimal("0"))
        context = {
            "intent": intent_name,
            "period": get_period_label(year, month, intent["start_date"]),
            "total": format(total, "f"),
            "expense_count": len(rows),
        }
        if intent.get("include_category_breakdown"):
            category_totals = {}
            for row in rows:
                category = row["category"]
                category_totals[category] = (
                    category_totals.get(category, Decimal("0")) + Decimal(row["amount"])
                )
            context["category_breakdown"] = [
                {"category": category, "total": format(amount, "f")}
                for category, amount in sorted(
                    category_totals.items(), key=lambda item: item[1], reverse=True
                )
            ]
        return context

    if intent_name == "CATEGORY_SPENDING":
        if intent["highest_category"]:
            totals = get_category_totals(
                user_id,
                year,
                month,
                intent["start_date"],
                intent["end_date"],
            )
            highest = max(totals.items(), key=lambda item: item[1], default=None)
            return {
                "intent": intent_name,
                "period": get_period_label(year, month, intent["start_date"]),
                "highest_category": (
                    {"name": highest[0], "total": format(highest[1], "f")}
                    if highest else None
                ),
            }
        rows = get_expense_rows(
            user_id,
            year,
            month,
            category_id=intent["category_id"],
            start_date=intent["start_date"],
            end_date=intent["end_date"],
        )
        total = sum((Decimal(row["amount"]) for row in rows), Decimal("0"))
        return {
            "intent": intent_name,
            "period": get_period_label(year, month, intent["start_date"]),
            "category": intent["category_name"],
            "total": format(total, "f"),
            "expense_count": len(rows),
        }

    rows = get_expense_rows(
        user_id,
        year,
        month,
        start_date=intent["start_date"],
        end_date=intent["end_date"],
    )
    rows = sorted(rows, key=lambda row: Decimal(row["amount"]), reverse=True)
    return {
        "intent": intent_name,
        "period": get_period_label(year, month, intent["start_date"]),
        "expenses": [
            {
                "amount": format(Decimal(row["amount"]), "f"),
                "category": row["category"],
                "date": row["expense_date"],
            }
            for row in rows[:intent["limit"]]
        ],
    }
