"""Validated, confirmation-gated assistant mutations."""

import hashlib
import json
import re
import secrets
from contextlib import nullcontext
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from backend.services.assistant_policy import ToolValidationError
from backend.services.config import feature_enabled
from backend.services.memory_service import save_conversation_turn
from database.database import (
    DEFAULT_CATEGORIES_BY_ROLE,
    database_connection,
    normalize_category_name,
)


PENDING_ACTION_TTL_MINUTES = 10

_CATEGORY_ALIASES = {
    "lunch": ("food & dining",),
    "dinner": ("food & dining",),
    "breakfast": ("food & dining", "groceries"),
    "coffee": ("food & dining",),
    "cafe": ("food & dining",),
    "tea": ("food & dining",),
    "snack": ("food & dining",),
    "snacks": ("food & dining",),
    "food": ("food & dining", "groceries"),
    "dining": ("food & dining",),
    "restaurant": ("food & dining",),
    "grocery": ("groceries", "shopping", "household", "food & dining"),
    "groceries": ("groceries", "shopping", "household", "food & dining"),
    "books": ("books & stationery", "education", "shopping", "other"),
    "book": ("books & stationery", "education", "shopping", "other"),
    "stationery": ("books & stationery",),
    "education": ("education", "children & education"),
    "medical": ("healthcare",),
    "medicine": ("healthcare",),
    "doctor": ("healthcare",),
    "health": ("healthcare",),
    "healthcare": ("healthcare",),
    "rent": ("rent / housing", "hostel / rent"),
    "transport": ("transportation",),
    "cab": ("transportation",),
    "fuel": ("transportation",),
    "shopping": ("shopping",),
    "entertainment": ("entertainment",),
}


def resolve_user_category(user_id, spoken, connection):
    categories = connection.execute(
        "SELECT id, name, normalized_name FROM categories WHERE user_id = ? "
        "ORDER BY name COLLATE NOCASE",
        (user_id,),
    ).fetchall()
    spoken_name = normalize_category_name(spoken)
    spoken_key = spoken_name.casefold()
    if not spoken_key:
        return None
    for row in categories:
        if row["normalized_name"] == spoken_key or row["name"].casefold() == spoken_key:
            return row
    for candidate in _CATEGORY_ALIASES.get(spoken_key, ()):
        for row in categories:
            if row["normalized_name"] == candidate:
                return row
    for row in categories:
        normalized = row["normalized_name"]
        if spoken_key in normalized or normalized in spoken_key:
            return row
    return None


def propose_action(user_id, action_name, arguments):
    if not feature_enabled("ENABLE_CRUD_AGENT", default=False):
        raise ToolValidationError("Account changes through the assistant are disabled.")
    validated = _validate_action(user_id, action_name, arguments, None)
    details = _confirmation_details(action_name, validated)
    payload = json.dumps(validated, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    fingerprint = hashlib.sha256(f"{action_name}:{payload}".encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)
    expires = (now + timedelta(minutes=PENDING_ACTION_TTL_MINUTES)).isoformat(timespec="seconds")
    with database_connection() as connection:
        connection.execute(
            "UPDATE assistant_pending_actions SET status = 'expired' "
            "WHERE user_id = ? AND status = 'pending' AND expires_at <= ?",
            (user_id, now.isoformat(timespec="seconds")),
        )
        existing = connection.execute(
            "SELECT id, expires_at FROM assistant_pending_actions "
            "WHERE user_id = ? AND fingerprint = ? AND status = 'pending' AND expires_at > ?",
            (user_id, fingerprint, now.isoformat(timespec="seconds")),
        ).fetchone()
        if existing:
            action_id, expires_at = existing["id"], existing["expires_at"]
        else:
            other_pending = connection.execute(
                "SELECT 1 FROM assistant_pending_actions "
                "WHERE user_id = ? AND status = 'pending' LIMIT 1",
                (user_id,),
            ).fetchone()
            if other_pending:
                raise ToolValidationError(
                    "A change is already awaiting confirmation. Confirm or cancel it first."
                )
            action_id = secrets.token_urlsafe(32)
            expires_at = expires
            connection.execute(
                "INSERT INTO assistant_pending_actions "
                "(id, user_id, action_name, payload_json, fingerprint, expires_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (action_id, user_id, action_name, payload, fingerprint, expires),
            )
    return {
        "pending_confirmation": True,
        "confirmation_id": action_id,
        "action": action_name,
        "details": details,
        "expires_at": expires_at,
    }


def confirm_action(user_id, confirmation_id):
    if not feature_enabled("ENABLE_CRUD_AGENT", default=False):
        raise ToolValidationError("Assistant changes are disabled.")
    if not isinstance(confirmation_id, str) or not 20 <= len(confirmation_id) <= 128:
        raise ToolValidationError("This confirmation is invalid or has expired.")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with database_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT action_name, payload_json, expires_at, status "
            "FROM assistant_pending_actions WHERE id = ? AND user_id = ?",
            (confirmation_id, user_id),
        ).fetchone()
        if row is None or row["status"] != "pending" or row["expires_at"] <= now:
            raise ToolValidationError("This confirmation is invalid, expired, or already used.")
        payload = json.loads(row["payload_json"])
        _validate_action(user_id, row["action_name"], payload, connection)
        _execute_action(connection, user_id, row["action_name"], payload)
        changed = connection.execute(
            "UPDATE assistant_pending_actions SET status = 'confirmed', consumed_at = ? "
            "WHERE id = ? AND user_id = ? AND status = 'pending'",
            (now, confirmation_id, user_id),
        ).rowcount
        if changed != 1:
            raise ToolValidationError("This confirmation has already been used.")
        response = f"Confirmed. {_success_message(row['action_name'], payload)}"
        save_conversation_turn(
            user_id,
            "Confirmed the proposed account change.",
            response,
            connection,
        )
    return response


def cancel_action(user_id, confirmation_id):
    if not feature_enabled("ENABLE_CRUD_AGENT", default=False):
        raise ToolValidationError("Assistant changes are disabled.")
    if not isinstance(confirmation_id, str) or not 20 <= len(confirmation_id) <= 128:
        raise ToolValidationError("This confirmation is invalid or has expired.")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with database_connection() as connection:
        changed = connection.execute(
            "UPDATE assistant_pending_actions SET status = 'cancelled', consumed_at = ? "
            "WHERE id = ? AND user_id = ? AND status = 'pending' AND expires_at > ?",
            (now, confirmation_id, user_id, now),
        ).rowcount
        if changed == 1:
            save_conversation_turn(
                user_id,
                "Cancelled the proposed account change.",
                "The proposed change was cancelled.",
                connection,
            )
    if changed != 1:
        raise ToolValidationError("This confirmation is invalid, expired, or already used.")
    return "The proposed change was cancelled."


def get_pending_action(user_id):
    if not feature_enabled("ENABLE_CRUD_AGENT", default=False):
        return None
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with database_connection() as connection:
        connection.execute(
            "UPDATE assistant_pending_actions SET status = 'expired' "
            "WHERE user_id = ? AND status = 'pending' AND expires_at <= ?",
            (user_id, now),
        )
        row = connection.execute(
            "SELECT id, action_name, payload_json, expires_at FROM assistant_pending_actions "
            "WHERE user_id = ? AND status = 'pending' ORDER BY rowid DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    if row is None:
        return None
    return {
        "confirmation_id": row["id"],
        "details": _confirmation_details(row["action_name"], json.loads(row["payload_json"])),
        "expires_at": row["expires_at"],
    }


def _validate_action(user_id, action_name, values, connection):
    allowed_fields = {
        "create_expense": {"amount", "category", "date", "description"},
        "update_expense": {"expense_id", "amount", "category", "date", "description"},
        "delete_expense": {"expense_id"},
        "create_budget": {"amount", "year", "month"},
        "update_budget": {"amount", "year", "month"},
        "delete_budget": {"year", "month"},
    }
    if action_name not in allowed_fields:
        raise ToolValidationError("That change is not available.")
    accepted_fields = set(allowed_fields[action_name])
    if connection is not None:
        accepted_fields.update({"expected", "expected_budget", "category_id"})
    if set(values) - accepted_fields:
        raise ToolValidationError("The proposed change contains unsupported fields.")
    if "user_id" in values:
        raise ToolValidationError("The assistant cannot select an account owner.")
    if "amount" in values:
        amount_text = str(values["amount"])
        if not re.fullmatch(r"(?:\d+(?:\.\d{1,2})?|\.\d{1,2})", amount_text):
            raise ToolValidationError("Enter a positive amount with no more than two decimal places.")
        try:
            amount = Decimal(amount_text)
        except InvalidOperation as error:
            raise ToolValidationError("Enter a valid positive amount.") from error
        if not amount.is_finite() or amount <= 0:
            raise ToolValidationError("Enter a valid positive amount.")
        values["amount"] = format(amount, "f")
    if "year" in values or "month" in values:
        try:
            date(int(values["year"]), int(values["month"]), 1)
        except (TypeError, ValueError, KeyError) as error:
            raise ToolValidationError("Choose a valid budget month and year.") from error
    if "date" in values:
        try:
            selected = date.fromisoformat(values["date"])
            if selected.isoformat() != values["date"] or selected > date.today():
                raise ValueError
        except (TypeError, ValueError) as error:
            raise ToolValidationError("Choose a valid expense date no later than today.") from error
    if "description" in values and (not isinstance(values["description"], str) or len(values["description"]) > 500):
        raise ToolValidationError("Expense descriptions must be 500 characters or fewer.")

    if action_name == "create_expense" and not values.get("date"):
        values["date"] = date.today().isoformat()

    if action_name in {"create_expense", "update_expense"} and "category" in values:
        spoken = values["category"]
        with database_connection() if connection is None else nullcontext(connection) as db:
            category = resolve_user_category(user_id, spoken, db)
            if category is not None and action_name == "create_expense":
                user = db.execute(
                    "SELECT role FROM users WHERE id = ?",
                    (user_id,),
                ).fetchone()
                allowed_names = {
                    normalize_category_name(name).casefold()
                    for name in DEFAULT_CATEGORIES_BY_ROLE.get(user["role"], ())
                } if user else set()
                if category["normalized_name"] not in allowed_names:
                    category = None
            if category is None:
                choices = db.execute(
                    "SELECT name FROM categories WHERE user_id = ? ORDER BY name COLLATE NOCASE LIMIT 8",
                    (user_id,),
                ).fetchall()
                names = ", ".join(row["name"] for row in choices)
                detail = f" Choose one of: {names}." if names else ""
                raise ToolValidationError(f"Choose one of your SpendWise categories.{detail}")
            category = {
                "id": category["id"],
                "name": category["name"],
                "normalized_name": category["normalized_name"],
            }
        if (
            action_name == "create_expense"
            and spoken
            and str(spoken).strip().casefold() != category["name"].casefold()
            and not str(values.get("description") or "").strip()
        ):
            values["description"] = str(spoken).strip()[:500]
        values["category_id"] = category["id"]
        values["category"] = category["name"]

    if action_name in {"update_expense", "delete_expense"}:
        expense_id = values.get("expense_id")
        if isinstance(expense_id, bool) or not isinstance(expense_id, int) or expense_id < 1:
            raise ToolValidationError("Choose a valid expense.")
        with database_connection() if connection is None else nullcontext(connection) as db:
            expense = db.execute(
                "SELECT amount, category, expense_date, description, category_id FROM expenses "
                "WHERE id = ? AND user_id = ?",
                (expense_id, user_id),
            ).fetchone()
        if expense is None:
            raise ToolValidationError("That expense does not belong to your account.")
        expected = {
            "amount": expense["amount"],
            "category": expense["category"],
            "date": expense["expense_date"],
            "description": expense["description"],
            "category_id": expense["category_id"],
        }
        if "expected" in values and values["expected"] != expected:
            raise ToolValidationError("That expense changed after the proposal. Please review a new proposal.")
        values["expected"] = expected
        if action_name == "update_expense" and not set(values).intersection({"amount", "category", "date", "description"}):
            raise ToolValidationError("Provide at least one expense field to update.")

    if action_name in {"create_budget", "update_budget", "delete_budget"}:
        with database_connection() if connection is None else nullcontext(connection) as db:
            budget = db.execute(
                "SELECT budget_amount FROM budgets WHERE user_id = ? AND year = ? AND month = ?",
                (user_id, values["year"], values["month"]),
            ).fetchone()
        if action_name == "create_budget" and budget is not None:
            raise ToolValidationError("A budget already exists for that month; ask to update it instead.")
        if action_name in {"update_budget", "delete_budget"} and budget is None:
            raise ToolValidationError("There is no budget for that month to change.")
        expected_budget = budget["budget_amount"] if budget else None
        if "expected_budget" in values and values["expected_budget"] != expected_budget:
            raise ToolValidationError("That budget changed after the proposal. Please review a new proposal.")
        values["expected_budget"] = expected_budget
    return values


def _execute_action(connection, user_id, action_name, values):
    if action_name == "create_expense":
        connection.execute(
            "INSERT INTO expenses (user_id, amount, category, expense_date, description, category_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, values["amount"], values["category"], values["date"], values.get("description", ""), values["category_id"]),
        )
    elif action_name == "update_expense":
        existing = connection.execute(
            "SELECT amount, category, expense_date, description, category_id FROM expenses "
            "WHERE id = ? AND user_id = ?",
            (values["expense_id"], user_id),
        ).fetchone()
        fields = {
            "amount": values.get("amount", existing["amount"]),
            "category": values.get("category", existing["category"]),
            "expense_date": values.get("date", existing["expense_date"]),
            "description": values.get("description", existing["description"]),
            "category_id": values.get("category_id", existing["category_id"]),
        }
        connection.execute(
            "UPDATE expenses SET amount = ?, category = ?, expense_date = ?, description = ?, category_id = ? "
            "WHERE id = ? AND user_id = ?",
            (*fields.values(), values["expense_id"], user_id),
        )
    elif action_name == "delete_expense":
        connection.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (values["expense_id"], user_id))
    elif action_name in {"create_budget", "update_budget"}:
        connection.execute(
            "INSERT INTO budgets (user_id, month, year, budget_amount) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(user_id, month, year) DO UPDATE SET "
            "budget_amount = excluded.budget_amount, updated_at = CURRENT_TIMESTAMP",
            (user_id, values["month"], values["year"], values["amount"]),
        )
    elif action_name == "delete_budget":
        connection.execute(
            "DELETE FROM budgets WHERE user_id = ? AND year = ? AND month = ?",
            (user_id, values["year"], values["month"]),
        )


def _confirmation_details(action_name, values):
    if action_name.endswith("_expense"):
        details = {
            "type": action_name,
            "amount": values.get("amount"),
            "category": values.get("category"),
            "date": values.get("date"),
            "expense_id": values.get("expense_id"),
            "description": values.get("description"),
        }
        if action_name != "create_expense":
            expected = values["expected"]
            details["before"] = {
                "amount": expected["amount"],
                "category": expected["category"],
                "date": expected["date"],
                "description": (expected["description"] or "")[:500],
            }
            if action_name == "update_expense":
                details["after"] = {
                    "amount": values.get("amount", expected["amount"]),
                    "category": values.get("category", expected["category"]),
                    "date": values.get("date", expected["date"]),
                    "description": values.get("description", expected["description"]),
                }
        return details
    details = {
        "type": action_name,
        "amount": values.get("amount"),
        "year": values["year"],
        "month": values["month"],
    }
    details["before"] = values.get("expected_budget")
    details["after"] = (
        None if action_name == "delete_budget" else values.get("amount")
    )
    return details


def _success_message(action_name, values):
    if action_name.endswith("_expense"):
        if action_name.startswith("delete"):
            return "Expense deleted."
        return "Expense saved."
    if action_name.startswith("delete"):
        return "Budget deleted."
    return f"Budget saved for {calendar_month(values['month'])} {values['year']}."


def calendar_month(month):
    import calendar

    return calendar.month_name[month]
