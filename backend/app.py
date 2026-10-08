from datetime import date
from decimal import Decimal, InvalidOperation
from functools import wraps
import hmac
import os
import re
import secrets
import sqlite3
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.database import (
    USER_ROLES,
    DEFAULT_CATEGORIES_BY_ROLE,
    database_connection,
    initialize_database,
    normalize_category_name,
    seed_default_categories,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
USERNAME_PATTERN = re.compile(r"(?=.*[A-Za-z])(?=.*[0-9])(?=.*[_@])[A-Za-z0-9_@]{3,15}")
PASSWORD_PATTERN = re.compile(r"(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[^A-Za-z0-9\s])\S{8,36}")
COMMON_PASSWORDS = {
    "password123!",
    "password1!",
    "qwerty123!",
    "letmein123!",
    "welcome123!",
    "admin123!",
    "iloveyou1!",
    "changeme123!",
    "p@ssw0rd123!",
    "qwertyuiop1!",
}


def load_or_create_secret_key(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="ascii") as secret_file:
            secret_key = secrets.token_hex(32)
            secret_file.write(secret_key)
            return secret_key
    except FileExistsError:
        secret_key = path.read_text(encoding="ascii").strip()
        if len(secret_key) < 32:
            raise RuntimeError(f"Application secret key file is empty or invalid: {path}")
        return secret_key


app = Flask(
    __name__,
    static_url_path="/static",
    static_folder=str(PROJECT_ROOT / "frontend" / "static"),
    template_folder=str(PROJECT_ROOT / "frontend" / "templates"),
)
app.config.update(
    SECRET_KEY=os.environ.get("EXPENSE_TRACKER_SECRET")
    or load_or_create_secret_key(PROJECT_ROOT / "instance" / "secret_key"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

def csrf_token():
    token = session.get("csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def format_money(value):
    amount = Decimal(str(value))
    decimal_places = max(2, -amount.as_tuple().exponent)
    return f"₹{amount:,.{decimal_places}f}"


@app.context_processor
def template_helpers():
    template_context = {
        "csrf_token": csrf_token,
        "format_money": format_money,
    }
    user_id = session.get("user_id")
    if user_id is None:
        return template_context

    current_date = date.today()
    today = current_date.isoformat()
    template_context.update({
        "modal_categories": get_user_role_categories(user_id),
        "modal_expense": session.pop("modal_expense", {
            "amount": "",
            "category_id": "",
            "expense_date": today,
            "description": "",
            "date_period": "today",
        }),
        "modal_errors": session.pop("modal_errors", []),
        "modal_success": session.pop("modal_success", False),
        "show_expense_modal": session.pop("show_add_expense_modal", False),
        "modal_return_to": session.pop(
            "modal_return_to",
            request.full_path.rstrip("?"),
        ),
        "today": today,
        "yesterday": date.fromordinal(current_date.toordinal() - 1).isoformat(),
    })
    return template_context


@app.before_request
def protect_form_submissions():
    if request.method == "POST":
        submitted_token = request.form.get("csrf_token", "")
        saved_token = session.get("csrf_token", "")
        if not saved_token or not hmac.compare_digest(submitted_token, saved_token):
            if request.is_json:
                abort(400)
            session.clear()
            flash("Your session expired. Please sign in again.", "error")
            return redirect(url_for("login"))


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        user_id = session.get("user_id")
        if user_id is None:
            flash("Sign in to access your expenses.", "error")
            return redirect(url_for("login"))
        with database_connection() as connection:
            user = connection.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if user is None:
            session.clear()
            flash("Your session has expired. Sign in again.", "error")
            return redirect(url_for("login"))
        return view(**kwargs)

    return wrapped_view



def get_user_categories(user_id):
    with database_connection() as connection:
        seed_default_categories(connection, user_id)
        category_rows = connection.execute(
            "SELECT id, name FROM categories WHERE user_id = ? ORDER BY name COLLATE NOCASE",
            (user_id,),
        ).fetchall()
        categories = []
        for category in category_rows:
            subcategories = connection.execute(
                "SELECT id, name FROM subcategories WHERE category_id = ? ORDER BY name COLLATE NOCASE",
                (category["id"],),
            ).fetchall()
            categories.append({
                "id": category["id"],
                "name": category["name"],
                "subcategories": [dict(row) for row in subcategories],
            })
    return categories


def get_user_role_categories(user_id):
    with database_connection() as connection:
        user = connection.execute(
            "SELECT role FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if user is None:
            raise ValueError("Cannot load categories for an unknown user.")
        role_categories = DEFAULT_CATEGORIES_BY_ROLE.get(user["role"])
        if role_categories is None:
            raise ValueError("Cannot load categories for an invalid user role.")

        seed_default_categories(connection, user_id, user["role"])
        placeholders = ", ".join("?" for _ in role_categories)
        rows = connection.execute(
            "SELECT id, name FROM categories "
            f"WHERE user_id = ? AND name IN ({placeholders}) "
            "ORDER BY CASE WHEN name = 'Other' THEN 1 ELSE 0 END, name COLLATE NOCASE",
            (user_id, *role_categories),
        ).fetchall()
    return [dict(row) for row in rows]


def safe_return_path(path):
    if not path or not path.startswith("/") or path.startswith("//") or "\\" in path:
        return url_for("dashboard")
    parsed = urlsplit(path)
    if parsed.scheme or parsed.netloc or parsed.path == url_for("add_expense"):
        return url_for("dashboard")
    return path


def parse_expense_form(form, user_id):
    amount_text = form.get("amount", "").strip()
    category_choice = form.get("category_id", "").strip()
    new_category = normalize_category_name(form.get("new_category", ""))
    if not category_choice and form.get("category", "").strip():
        category_choice = "__new__"
        new_category = normalize_category_name(form.get("category", ""))
    expense_date = form.get("expense_date", "").strip()
    description = form.get("description", "").strip()
    errors = []

    try:
        amount = Decimal(amount_text)
        if not amount.is_finite() or amount <= 0:
            errors.append("Amount must be greater than zero.")
    except InvalidOperation:
        amount = None
        errors.append("Enter a valid amount greater than zero.")

    category_id = None
    category_name = ""
    if category_choice == "__new__":
        if not new_category:
            errors.append("Enter a name for the new category.")
        else:
            normalized_name = new_category.casefold()
            with database_connection() as connection:
                category = connection.execute(
                    "SELECT id, name FROM categories WHERE user_id = ? AND normalized_name = ?",
                    (user_id, normalized_name),
                ).fetchone()
            if category is not None:
                category_id = str(category["id"])
                category_name = category["name"]
                new_category = ""
            else:
                category_name = new_category
    else:
        try:
            selected_category_id = int(category_choice)
        except ValueError:
            selected_category_id = None
        if selected_category_id is None:
            errors.append("Choose a category or add a new one.")
        else:
            with database_connection() as connection:
                category = connection.execute(
                    "SELECT id, name FROM categories WHERE id = ? AND user_id = ?",
                    (selected_category_id, user_id),
                ).fetchone()
            if category is None:
                errors.append("Choose a valid category.")
            else:
                category_id = str(category["id"])
                category_name = category["name"]

    try:
        parsed_date = date.fromisoformat(expense_date)
        if parsed_date.isoformat() != expense_date:
            errors.append("Enter a valid expense date.")
        elif parsed_date > date.today():
            errors.append("Expense date cannot be in the future.")
    except ValueError:
        errors.append("Enter a valid expense date.")

    return {
        "amount": format(amount, "f") if amount is not None else amount_text,
        "category_id": category_id or category_choice,
        "category_name": category_name,
        "new_category": new_category,
        "expense_date": expense_date,
        "description": description,
    }, errors


def expense_form_values(form=None):
    form = form or {}
    return {
        "amount": form.get("amount", "").strip(),
        "category_id": form.get("category_id", "").strip(),
        "new_category": form.get("new_category", "").strip(),
        "subcategory_id": form.get("subcategory_id", "").strip(),
        "new_subcategory": form.get("new_subcategory", "").strip(),
        "expense_type": form.get("expense_type", "Liability").strip(),
        "expense_date": form.get("expense_date", date.today().isoformat()).strip(),
        "description": form.get("description", "").strip(),
    }


def save_expense(connection, user_id, values, expense_id=None):
    category_id = values.get("category_id", "")
    category_name = values.get("category_name", "")
    category = None
    if category_id == "__new__":
        category_name = normalize_category_name(values.get("new_category", ""))
        if not category_name:
            raise ValueError("Enter a category name.")
        normalized_category = category_name.casefold()
        connection.execute(
            "INSERT INTO categories (user_id, name, normalized_name) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id, normalized_name) DO NOTHING",
            (user_id, category_name, normalized_category),
        )
        category = connection.execute(
            "SELECT id, name FROM categories WHERE user_id = ? AND normalized_name = ?",
            (user_id, normalized_category),
        ).fetchone()
    else:
        try:
            category_id = int(category_id)
        except (TypeError, ValueError):
            raise ValueError("Choose a valid category.")
        category = connection.execute(
            "SELECT id, name FROM categories WHERE id = ? AND user_id = ?",
            (category_id, user_id),
        ).fetchone()

    if category is None:
        raise ValueError("Choose a valid category.")

    subcategory_id = None
    if values.get("subcategory_id") == "__new__":
        subcategory_name = normalize_category_name(values.get("new_subcategory", ""))
        if not subcategory_name:
            raise ValueError("Enter a subcategory name.")
        normalized_subcategory = subcategory_name.casefold()
        connection.execute(
            "INSERT INTO subcategories (category_id, name, normalized_name) VALUES (?, ?, ?) "
            "ON CONFLICT(category_id, normalized_name) DO NOTHING",
            (category["id"], subcategory_name, normalized_subcategory),
        )
        subcategory_id = connection.execute(
            "SELECT id FROM subcategories WHERE category_id = ? AND normalized_name = ?",
            (category["id"], normalized_subcategory),
        ).fetchone()["id"]
    elif values.get("subcategory_id"):
        try:
            subcategory_id = int(values["subcategory_id"])
        except (TypeError, ValueError):
            raise ValueError("Choose a valid subcategory.")

    if expense_id is None:
        connection.execute(
            "INSERT INTO expenses (user_id, amount, category, expense_date, description, category_id, subcategory_id, expense_type) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                values["amount"],
                category["name"],
                values["expense_date"],
                values["description"],
                category["id"],
                subcategory_id,
                values.get("expense_type", "Liability"),
            ),
        )
    else:
        connection.execute(
            "UPDATE expenses SET amount = ?, category = ?, expense_date = ?, description = ?, "
            "category_id = ?, subcategory_id = ?, expense_type = ? WHERE id = ? AND user_id = ?",
            (
                values["amount"],
                category["name"],
                values["expense_date"],
                values["description"],
                category["id"],
                subcategory_id,
                values.get("expense_type", "Liability"),
                expense_id,
                user_id,
            ),
        )


def save_expense_record(user_id, values, expense_id=None):
    with database_connection() as connection:
        save_expense(connection, user_id, values, expense_id)


@app.post("/categories/<int:category_id>/subcategories")
@login_required
def add_subcategory(category_id):
    submitted_token = request.headers.get("X-CSRF-Token", "")
    saved_token = session.get("csrf_token", "")
    if not saved_token or not hmac.compare_digest(submitted_token, saved_token):
        abort(400)

    data = request.get_json(silent=True) or {}
    name = normalize_category_name(data.get("name", ""))
    if not name:
        return jsonify(error="Enter a subcategory name."), 400

    with database_connection() as connection:
        category = connection.execute(
            "SELECT id FROM categories WHERE id = ? AND user_id = ?",
            (category_id, session["user_id"]),
        ).fetchone()
        if category is None:
            abort(404)

        normalized_name = name.casefold()
        connection.execute(
            "INSERT INTO subcategories (category_id, name, normalized_name) VALUES (?, ?, ?) "
            "ON CONFLICT(category_id, normalized_name) DO NOTHING",
            (category_id, name, normalized_name),
        )
        subcategory = connection.execute(
            "SELECT id, name FROM subcategories WHERE category_id = ? AND normalized_name = ?",
            (category_id, normalized_name),
        ).fetchone()
    return jsonify(id=subcategory["id"], name=subcategory["name"])


def get_period_analytics(user_id, year, month, day=None, category_id=None, start_date=None, end_date=None):
    period_start = start_date or date(year, month, day or 1)
    if end_date is not None:
        period_end = end_date
    elif day:
        period_end = date.fromordinal(period_start.toordinal() + 1)
    elif month == 12:
        period_end = date(year + 1, 1, 1)
    else:
        period_end = date(year, month + 1, 1)

    conditions = ["user_id = ?", "expense_date >= ?", "expense_date < ?"]
    parameters = [user_id, period_start.isoformat(), period_end.isoformat()]
    if category_id is not None:
        conditions.append("category_id = ?")
        parameters.append(category_id)

    with database_connection() as connection:
        rows = connection.execute(
            "SELECT category, amount FROM expenses WHERE " + " AND ".join(conditions),
            parameters,
        ).fetchall()

    category_totals = {}
    total = Decimal("0")
    for row in rows:
        amount = Decimal(row["amount"])
        category_totals[row["category"]] = category_totals.get(row["category"], Decimal("0")) + amount
        total += amount

    chart_colors = ["#159447", "#f47b20", "#2167d5", "#009b8a", "#d95643", "#b28a16", "#7956a8"]
    items = []
    chart_stops = []
    position = Decimal("0")
    for index, (category, category_total) in enumerate(
        sorted(category_totals.items(), key=lambda item: (-item[1], item[0].casefold()))
    ):
        percentage = category_total / total * Decimal("100") if total else Decimal("0")
        next_position = position + percentage
        color = chart_colors[index % len(chart_colors)]
        items.append({
            "category": category,
            "total": category_total,
            "percentage": percentage,
            "color": color,
        })
        chart_stops.append(f"{color} {position:.2f}% {next_position:.2f}%")
        position = next_position

    return {
        "items": items,
        "total": total,
        "count": len(rows),
        "average": total / len(rows) if rows else Decimal("0"),
        "highest_category": items[0] if items else None,
        "chart_background": "conic-gradient(" + ", ".join(chart_stops) + ")" if chart_stops else "",
    }


def resolve_expense_date_filter(period, selected_date, today):
    period = period or ("custom" if selected_date else "today")
    if period == "today":
        return period, today, date.fromordinal(today.toordinal() + 1), today.isoformat(), None
    if period == "yesterday":
        yesterday = date.fromordinal(today.toordinal() - 1)
        return period, yesterday, today, "", None
    if period == "last7":
        start_date = date.fromordinal(today.toordinal() - 6)
        return period, start_date, date.fromordinal(today.toordinal() + 1), "", None
    if period == "custom":
        try:
            parsed_date = date.fromisoformat(selected_date)
            if parsed_date.isoformat() != selected_date or parsed_date > today:
                raise ValueError
        except ValueError:
            return "today", today, date.fromordinal(today.toordinal() + 1), today.isoformat(), (
                "Choose a valid date no later than today."
            )
        return period, parsed_date, date.fromordinal(parsed_date.toordinal() + 1), selected_date, None
    return "today", today, date.fromordinal(today.toordinal() + 1), today.isoformat(), (
        "Choose a valid date filter."
    )


def get_category_analytics(user_id, target_month):
    target_month = parse_month_period(target_month)
    year, month = (int(part) for part in target_month.split("-"))
    month_start = date(year, month, 1)
    month_end = date(year + (month == 12), 1 if month == 12 else month + 1, 1)

    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT e.category_id, c.name AS category, s.name AS subcategory, e.amount
            FROM expenses e
            JOIN categories c ON c.id = e.category_id AND c.user_id = e.user_id
            LEFT JOIN subcategories s ON s.id = e.subcategory_id AND s.category_id = c.id
            WHERE e.user_id = ? AND e.expense_date >= ? AND e.expense_date < ?
            ORDER BY c.name COLLATE NOCASE, s.name COLLATE NOCASE
            """,
            (user_id, month_start.isoformat(), month_end.isoformat()),
        ).fetchall()

    categories = {}
    month_total = Decimal("0")
    for row in rows:
        amount = Decimal(row["amount"])
        month_total += amount
        category = categories.setdefault(
            row["category_id"],
            {"id": row["category_id"], "category": row["category"], "total": Decimal("0"), "subcategories": {}},
        )
        category["total"] += amount
        subcategory_name = row["subcategory"] or "No subcategory"
        subcategory = category["subcategories"].setdefault(
            subcategory_name,
            {"subcategory": subcategory_name, "total": Decimal("0")},
        )
        subcategory["total"] += amount

    analytics = list(categories.values())
    for item in analytics:
        item["percentage"] = item["total"] / month_total * Decimal("100") if month_total else Decimal("0")
        item["subcategories"] = sorted(
            item["subcategories"].values(), key=lambda entry: (-entry["total"], entry["subcategory"].casefold())
        )
        for subcategory in item["subcategories"]:
            subcategory["percentage"] = (
                subcategory["total"] / item["total"] * Decimal("100") if item["total"] else Decimal("0")
            )
    analytics.sort(key=lambda item: (-item["total"], item["category"].casefold()))

    return {
        "month": target_month,
        "items": analytics,
        "total": month_total,
        "highest_category": analytics[0] if analytics else None,
        "lowest_category": analytics[-1] if analytics else None,
    }


def parse_month_period(period):
    try:
        year, month = (int(part) for part in (period or "").split("-"))
        selected = date(year, month, 1)
    except (ValueError, TypeError):
        selected = date.today().replace(day=1)
    return selected.strftime("%Y-%m")


def get_budget_summary(user_id, month=None, year=None):
    selected_month = int(month) if month is not None else date.today().month
    selected_year = int(year) if year is not None else date.today().year
    month_start = date(selected_year, selected_month, 1)
    month_end = date(selected_year + (selected_month == 12), 1 if selected_month == 12 else selected_month + 1, 1)

    with database_connection() as connection:
        budget = connection.execute(
            "SELECT id, budget_amount FROM budgets WHERE user_id = ? AND month = ? AND year = ?",
            (user_id, selected_month, selected_year),
        ).fetchone()
        expense_rows = connection.execute(
            "SELECT expense_type, amount FROM expenses "
            "WHERE user_id = ? AND expense_date >= ? AND expense_date < ?",
            (user_id, month_start.isoformat(), month_end.isoformat()),
        ).fetchall()

    liability_total = sum((Decimal(row["amount"]) for row in expense_rows if row["expense_type"] == "Liability"), Decimal("0"))
    savings_total = sum((Decimal(row["amount"]) for row in expense_rows if row["expense_type"] == "Savings"), Decimal("0"))
    spent = liability_total + savings_total
    budget_amount = Decimal(str(budget["budget_amount"])) if budget else None

    if budget_amount is None:
        return {
            "month": selected_month,
            "year": selected_year,
            "budget_amount": None,
            "total_spent": spent,
            "liability_total": liability_total,
            "savings_total": savings_total,
            "remaining": None,
            "utilization": Decimal("0"),
            "status": "not_set",
            "status_label": "No budget set",
            "message": "Set a monthly budget to track your spending.",
            "liability_chart_end": Decimal("0"),
            "expenditure_chart_end": Decimal("0"),
        }

    remaining = budget_amount - spent
    utilization = (spent / budget_amount * Decimal("100")) if budget_amount else Decimal("0")
    chart_scale = max(budget_amount, spent)
    liability_chart_end = liability_total / chart_scale * Decimal("100") if chart_scale else Decimal("0")
    expenditure_chart_end = spent / chart_scale * Decimal("100") if chart_scale else Decimal("0")

    if spent > budget_amount:
        status = "exceeded"
        status_label = "Budget exceeded"
        message = "You have spent more than your monthly budget."
    elif utilization >= Decimal("80"):
        status = "warning"
        status_label = "Warning"
        message = "You are close to your monthly budget limit."
    else:
        status = "healthy"
        status_label = "On track"
        message = "You are within your monthly budget."

    return {
        "month": selected_month,
        "year": selected_year,
        "budget_amount": budget_amount,
        "total_spent": spent,
        "liability_total": liability_total,
        "savings_total": savings_total,
        "remaining": remaining,
        "utilization": utilization,
        "status": status,
        "status_label": status_label,
        "message": message,
        "liability_chart_end": liability_chart_end,
        "expenditure_chart_end": expenditure_chart_end,
    }


@app.get("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "")
        role = request.form.get("role", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        registration_errors = {}
        if not username:
            registration_errors["username"] = "Enter a username."
        elif not USERNAME_PATTERN.fullmatch(username):
            registration_errors["username"] = (
                "Use 3–15 letters, numbers, underscores, or @, including at least "
                "one letter, one number, and one underscore or @."
            )
        if role not in USER_ROLES:
            registration_errors["role"] = "Choose your role."
        if not password:
            registration_errors["password"] = "Enter a password."
        elif not PASSWORD_PATTERN.fullmatch(password):
            registration_errors["password"] = (
                "Use 8–36 characters with uppercase and lowercase letters, a number, "
                "and a symbol. Spaces are not allowed."
            )
        elif password.casefold() in COMMON_PASSWORDS:
            registration_errors["password"] = "Choose a less common password."
        if not confirm_password:
            registration_errors["confirm_password"] = "Confirm your password."
        elif password != confirm_password:
            registration_errors["confirm_password"] = "Passwords do not match."

        if registration_errors:
            return render_template(
                "register.html",
                username=username,
                role=role,
                registration_errors=registration_errors,
            ), 400

        try:
            with database_connection() as connection:
                cursor = connection.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, generate_password_hash(password), role),
                )
                seed_default_categories(connection, cursor.lastrowid, role)
        except sqlite3.IntegrityError:
            registration_errors["username"] = "That username is already taken."
            return render_template(
                "register.html",
                username=username,
                role=role,
                registration_errors=registration_errors,
            ), 409

        flash("Account created. Sign in to continue.", "success")
        return redirect(url_for("login"))

    return render_template(
        "register.html",
        username="",
        role="",
        registration_errors={},
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        login_errors = {}
        if not username:
            login_errors["username"] = "Enter your username."
        if not password:
            login_errors["password"] = "Enter your password."
        if login_errors:
            return render_template(
                "login.html",
                username=username,
                login_errors=login_errors,
            ), 400

        with database_connection() as connection:
            user = connection.execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?",
                (username,),
            ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template(
                "login.html",
                username=username,
                login_errors={},
                login_error="Username or password is incorrect. Check your details and try again.",
            ), 401

        session.clear()
        session["user_id"] = user["id"]
        session["user_username"] = user["username"]
        session["show_add_expense_modal"] = True
        csrf_token()
        return redirect(url_for("dashboard"))

    return render_template("login.html", username="", login_errors={})


@app.post("/logout")
@login_required
def logout():
    session.clear()
    flash("You have signed out.", "success")
    return redirect(url_for("login"))


@app.post("/expenses/modal/dismiss")
@login_required
def dismiss_expense_modal():
    return_to = safe_return_path(request.form.get("return_to", ""))
    session["show_add_expense_modal"] = False
    session.pop("modal_expense", None)
    session.pop("modal_errors", None)
    session.pop("modal_success", None)
    session.pop("modal_return_to", None)
    return redirect(return_to)


def _render_dashboard(expense=None, modal_errors=None, modal_success=False, status=200):
    today = date.today()
    budget = get_budget_summary(session["user_id"], today.month, today.year)
    with database_connection() as connection:
        recent_expenses = connection.execute(
            "SELECT e.id, e.amount, e.category, e.expense_date, e.description "
            "FROM expenses e WHERE e.user_id = ? ORDER BY e.expense_date DESC, e.id DESC LIMIT 6",
            (session["user_id"],),
        ).fetchall()
    return render_template(
        "dashboard.html",
        budget=budget,
        recent_expenses=recent_expenses,
        categories=get_user_categories(session["user_id"]),
        expense=expense or {
            "amount": "",
            "category_id": "",
            "new_category": "",
            "expense_date": today.isoformat(),
            "description": "",
        },
        today=today.isoformat(),
        show_expense_modal=session.get("show_add_expense_modal", False),
        modal_errors=modal_errors or [],
        modal_success=modal_success,
    ), status


@app.get("/dashboard")
@login_required
def dashboard():
    period = parse_month_period(request.args.get("period"))
    selected_year, selected_month = (int(part) for part in period.split("-"))
    budget = get_budget_summary(session["user_id"], selected_month, selected_year)
    with database_connection() as connection:
        recent_expenses = connection.execute(
            "SELECT e.id, e.amount, COALESCE(c.name, e.category) AS category, "
            "e.expense_date, e.description "
            "FROM expenses e LEFT JOIN categories c ON c.id = e.category_id AND c.user_id = e.user_id "
            "WHERE e.user_id = ? ORDER BY e.expense_date DESC, e.id DESC LIMIT 6",
            (session["user_id"],),
        ).fetchall()
    recent_expenses = [
        {
            **dict(expense),
            "display_date": date.fromisoformat(expense["expense_date"])
            .strftime("%b %d, %Y")
            .replace(" 0", " "),
        }
        for expense in recent_expenses
    ]
    return render_template(
        "dashboard.html",
        budget=budget,
        recent_expenses=recent_expenses,
        period=period,
        period_label=date(selected_year, selected_month, 1).strftime("%B %Y"),
        selected_month=selected_month,
        selected_year=selected_year,
    )


@app.get("/expenses")
@login_required
def expenses():
    category_filter = request.args.get("category", "").strip()
    date_filter = request.args.get("date", "").strip()
    if date_filter:
        try:
            parsed_date = date.fromisoformat(date_filter)
            if parsed_date.isoformat() != date_filter:
                raise ValueError
        except ValueError:
            flash("Choose a valid date to filter expenses.", "error")
            date_filter = ""

    conditions = ["e.user_id = ?"]
    values = [session["user_id"]]
    if category_filter:
        try:
            category_id = int(category_filter)
        except ValueError:
            category_id = None
        if category_id is None:
            flash("Choose a valid category to filter expenses.", "error")
            category_filter = ""
        else:
            conditions.append("e.category_id = ?")
            values.append(category_id)
    if date_filter:
        conditions.append("e.expense_date = ?")
        values.append(date_filter)

    with database_connection() as connection:
        expenses = connection.execute(
            "SELECT e.id, e.amount, COALESCE(c.name, e.category) AS category, "
            "s.name AS subcategory, e.expense_type, e.expense_date, e.description "
            "FROM expenses e LEFT JOIN categories c ON c.id = e.category_id AND c.user_id = e.user_id "
            "LEFT JOIN subcategories s ON s.id = e.subcategory_id AND s.category_id = c.id "
            f"WHERE {' AND '.join(conditions)} ORDER BY e.expense_date DESC, e.id DESC",
            values,
        ).fetchall()
        categories = connection.execute(
            "SELECT id, name FROM categories WHERE user_id = ? ORDER BY name COLLATE NOCASE",
            (session["user_id"],),
        ).fetchall()

    total = sum((Decimal(expense["amount"]) for expense in expenses), Decimal("0"))
    return render_template(
        "view_expenses.html",
        expenses=expenses,
        categories=categories,
        category_filter=category_filter,
        date_filter=date_filter,
        total=total,
    )


@app.get("/analytics")
@login_required
def analytics_page():
    today = date.today()
    date_period = request.args.get("date_period", "").strip()
    date_filter = request.args.get("date", "").strip()
    date_range = None
    date_label = ""
    if date_period or date_filter:
        date_period, range_start, range_end, date_filter, date_error = resolve_expense_date_filter(
            date_period,
            date_filter,
            today,
        )
        if date_error:
            flash(date_error, "error")
        date_range = (range_start, range_end)
        date_label = {
            "today": "Today",
            "yesterday": "Yesterday",
            "last7": "Last 7 Days",
            "custom": date_filter,
        }[date_period]
    analytics_period = (
        date.fromordinal(date_range[1].toordinal() - 1) if date_range else today
    )
    try:
        selected_year = int(request.args.get("year", analytics_period.year))
        selected_month = int(request.args.get("month", analytics_period.month))
        if selected_year < 1 or selected_year > 9999:
            raise ValueError
        if selected_year > today.year or (selected_year == today.year and selected_month > today.month):
            raise ValueError
        date(selected_year, selected_month, 1)
    except (ValueError, TypeError):
        flash("Analytics can only be viewed up to the current month and year.", "error")
        selected_year, selected_month = today.year, today.month

    raw_day = "" if date_range else request.args.get("day", "").strip()
    try:
        selected_day = int(raw_day) if raw_day else None
        if selected_day is not None:
            date(selected_year, selected_month, selected_day)
            if date(selected_year, selected_month, selected_day) > today:
                raise ValueError
    except (ValueError, TypeError):
        flash("Choose a valid day for analytics.", "error")
        selected_day = None

    categories = get_user_categories(session["user_id"])
    category_filter = request.args.get("category", "").strip()
    category_ids = {str(category["id"]) for category in categories}
    if category_filter and category_filter not in category_ids:
        flash("Choose a valid category filter.", "error")
        category_filter = ""
    selected_category_id = int(category_filter) if category_filter else None

    analytics = get_period_analytics(
        session["user_id"],
        selected_year,
        selected_month,
        selected_day if date_range is None else None,
        selected_category_id,
        start_date=date_range[0] if date_range else None,
        end_date=date_range[1] if date_range else None,
    )

    comparison_month_value = request.args.get("comparison_month", "").strip()
    if comparison_month_value:
        try:
            if not re.fullmatch(r"\d{4}-\d{2}", comparison_month_value):
                raise ValueError
            comparison_year, comparison_month = map(int, comparison_month_value.split("-"))
            date(comparison_year, comparison_month, 1)
            if comparison_year > today.year or (
                comparison_year == today.year and comparison_month > today.month
            ):
                raise ValueError
        except (ValueError, TypeError):
            flash("Choose a valid comparison month up to the current month.", "error")
            comparison_year, comparison_month = selected_year, selected_month
    else:
        comparison_year, comparison_month = selected_year, selected_month

    previous_month = comparison_month - 1 or 12
    previous_year = comparison_year - 1 if comparison_month == 1 else comparison_year
    comparison_budget = get_budget_summary(session["user_id"], comparison_month, comparison_year)
    previous_budget = get_budget_summary(session["user_id"], previous_month, previous_year)
    comparison_analytics = get_period_analytics(
        session["user_id"], comparison_year, comparison_month, category_id=selected_category_id
    )
    previous_comparison = get_period_analytics(
        session["user_id"], previous_year, previous_month, category_id=selected_category_id
    )
    with database_connection() as connection:
        years = connection.execute(
            "SELECT DISTINCT CAST(substr(expense_date, 1, 4) AS INTEGER) AS year "
            "FROM expenses WHERE user_id = ? ORDER BY year DESC",
            (session["user_id"],),
        ).fetchall()
    year_options = sorted({year for year in [today.year, selected_year, *(row["year"] for row in years)] if year <= today.year}, reverse=True)

    return render_template(
        "analytics.html",
        categories=categories,
        category_filter=category_filter,
        selected_year=selected_year,
        selected_month=selected_month,
        selected_day=selected_day,
        comparison_year=comparison_year,
        comparison_month=comparison_month,
        comparison_month_value=f"{comparison_year:04d}-{comparison_month:02d}",
        current_month_value=f"{today.year:04d}-{today.month:02d}",
        year_options=year_options,
        analytics=analytics,
        comparison_analytics=comparison_analytics,
        previous_comparison=previous_comparison,
        comparison_budget=comparison_budget,
        previous_budget=previous_budget,
        previous_month=previous_month,
        previous_year=previous_year,
        date_period=date_period,
        date_filter=date_filter,
        date_label=date_label,
    )


@app.get("/budget")
@login_required
def budget_page():
    period = parse_month_period(request.args.get("period"))
    year, month = (int(part) for part in period.split("-"))
    return render_template(
        "budget.html",
        budget=get_budget_summary(session["user_id"], month, year),
        period=period,
        period_label=date(year, month, 1).strftime("%B %Y"),
    )


@app.post("/budget")
@login_required
def save_budget():
    try:
        period = request.form.get("period", "").strip()
        if period:
            if not re.fullmatch(r"\d{4}-\d{2}", period):
                raise ValueError
            year, month = (int(part) for part in period.split("-"))
            date(year, month, 1)
        else:
            month = int(request.form.get("month", ""))
            year = int(request.form.get("year", ""))
        amount_text = request.form.get("budget_amount", "").strip()
        amount = Decimal(amount_text)
        date(year, month, 1)
        if (
            not amount.is_finite()
            or amount <= 0
            or not re.fullmatch(r"(?:\d+(?:\.\d{0,2})?|\.\d{1,2})", amount_text)
        ):
            raise ValueError
    except (InvalidOperation, ValueError, TypeError):
        flash("Enter a valid month, year, and budget amount with no more than two decimal places.", "error")
        return redirect(url_for("budget_page"))

    with database_connection() as connection:
        connection.execute(
            "INSERT INTO budgets (user_id, month, year, budget_amount) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(user_id, month, year) DO UPDATE SET "
            "budget_amount = excluded.budget_amount, updated_at = CURRENT_TIMESTAMP",
            (session["user_id"], month, year, format(amount, "f")),
        )

    flash("Monthly budget saved.", "success")
    return redirect(url_for("dashboard", period=f"{year:04d}-{month:02d}"))


@app.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    today = date.today()
    return_to = safe_return_path(request.form.get("return_to", ""))

    if request.method == "GET":
        session["show_add_expense_modal"] = True
        return redirect(url_for("dashboard"))

    user_id = session["user_id"]
    categories = get_user_role_categories(user_id)
    allowed_category_ids = {str(category["id"]) for category in categories}
    amount_text = request.form.get("amount", "").strip()
    category_id = request.form.get("category_id", "").strip()
    description = request.form.get("description", "").strip()
    date_period = request.form.get("date_period", "").strip()
    submitted_date = request.form.get("expense_date", "").strip()
    errors = []

    if date_period == "today":
        expense_date = today
    elif date_period == "yesterday":
        expense_date = date.fromordinal(today.toordinal() - 1)
    elif date_period == "custom":
        try:
            expense_date = date.fromisoformat(submitted_date)
            if expense_date.isoformat() != submitted_date or expense_date > today:
                raise ValueError
        except ValueError:
            expense_date = today
            errors.append("Choose a valid custom date no later than today.")
    else:
        expense_date = today
        errors.append("Choose Today, Yesterday, or a valid custom date.")

    amount_format_invalid = bool(
        amount_text
        and not re.fullmatch(r"(?:\d+(?:\.\d{1,2})?|\.\d{1,2})", amount_text)
    )
    if amount_format_invalid:
        errors.append("Enter a positive amount with no more than two decimal places.")
    category_invalid = category_id not in allowed_category_ids
    if category_invalid:
        errors.append("Choose a category assigned to your role.")

    form_data = {
        "amount": amount_text,
        "category_id": category_id,
        "expense_date": expense_date.isoformat(),
        "description": description,
    }
    values, validation_errors = parse_expense_form(form_data, user_id)
    for error in validation_errors:
        if amount_format_invalid and error.startswith(("Enter a valid amount", "Amount must")):
            continue
        if category_invalid and error.startswith(("Choose a valid category", "Choose a category or")):
            continue
        errors.append(error)
    errors = list(dict.fromkeys(errors))

    session["modal_return_to"] = return_to
    if errors:
        session["modal_expense"] = {
            "amount": amount_text,
            "category_id": category_id,
            "expense_date": submitted_date if date_period == "custom" else expense_date.isoformat(),
            "description": description,
            "date_period": date_period if date_period in {"today", "yesterday", "custom"} else "today",
        }
        session["modal_errors"] = errors
        session["show_add_expense_modal"] = True
        return redirect(return_to)

    with database_connection() as connection:
        save_expense(connection, user_id, values)

    session["modal_expense"] = {
        "amount": "",
        "category_id": "",
        "expense_date": today.isoformat(),
        "description": "",
        "date_period": "today",
    }
    session["modal_errors"] = []
    session["modal_success"] = True
    session["show_add_expense_modal"] = True
    return redirect(return_to)


@app.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    categories = get_user_categories(session["user_id"])
    with database_connection() as connection:
        expense = connection.execute(
            "SELECT id, amount, category, category_id, expense_date, description "
            "FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, session["user_id"]),
        ).fetchone()
    if expense is None:
        abort(404)

        if request.method == "POST":
            values, errors = parse_expense_form(request.form, session["user_id"])
            if errors:
                for error in errors:
                    flash(error, "error")
                return render_template(
                    "edit_expense.html",
                    expense={**dict(expense), **values},
                    categories=categories,
                    today=date.today().isoformat(),
                ), 400

            save_expense(connection, session["user_id"], values, expense_id)

    if request.method == "POST":
        flash("Expense updated.", "success")
        return redirect(url_for("dashboard"))
    return render_template("edit_expense.html", expense=expense, categories=categories, today=date.today().isoformat())


@app.post("/expenses/<int:expense_id>/delete")
@login_required
def delete_expense(expense_id):
    with database_connection() as connection:
        connection.execute(
            "DELETE FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, session["user_id"]),
        )
    flash("Expense deleted.", "success")
    return redirect(url_for("expenses"))


initialize_database()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")