from datetime import date
from decimal import Decimal, InvalidOperation
from functools import wraps
import hmac
import os
import secrets
import sqlite3
from pathlib import Path

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.database import database_connection, initialize_database, normalize_category_name, seed_default_categories

PROJECT_ROOT = Path(__file__).resolve().parent.parent


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
    return {
        "csrf_token": csrf_token,
        "format_money": format_money,
    }


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


<<<<<<< HEAD
def get_user_categories(user_id):
    seed_default_categories(user_id)
    with database_connection() as connection:
        rows = connection.execute(
            "SELECT id, name FROM categories WHERE user_id = ? ORDER BY name COLLATE NOCASE",
            (user_id,),
        ).fetchall()
    return [{"id": row["id"], "name": row["name"]} for row in rows]


def parse_expense_form(form, user_id):
    amount_text = form.get("amount", "").strip()
    category_choice = form.get("category_id", "").strip()
    new_category = normalize_category_name(form.get("new_category", ""))
    if not category_choice and form.get("category", "").strip():
        category_choice = "__new__"
        new_category = normalize_category_name(form.get("category", ""))
=======
def parse_expense_form(form):
    amount_text = form.get("amount", "").strip()
    category = form.get("category", "").strip()
>>>>>>> d6b40453c92a130e5b5b7944ca268733689bb73c
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

<<<<<<< HEAD
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
=======
    if not category:
        errors.append("Enter a category.")
>>>>>>> d6b40453c92a130e5b5b7944ca268733689bb73c

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
<<<<<<< HEAD
        "category_id": category_id or category_choice,
        "category_name": category_name,
        "new_category": new_category,
=======
        "category": category,
>>>>>>> d6b40453c92a130e5b5b7944ca268733689bb73c
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


<<<<<<< HEAD
def save_expense(connection, user_id, values, expense_id=None):
    category = (
        connection.execute(
            "SELECT id, name FROM categories WHERE id = ? AND user_id = ?",
            (int(values["category_id"]), user_id),
        ).fetchone()
        if values["category_id"] and values["category_id"] != "__new__"
        else get_or_create_category(connection, user_id, values["category_name"])
    )
    if category is None:
        raise ValueError("Choose a valid category.")

    if expense_id is None:
        connection.execute(
            "INSERT INTO expenses "
            "(user_id, amount, category, expense_date, description, category_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                user_id,
                values["amount"],
                category["name"],
                values["expense_date"],
                values["description"],
                category["id"],
            ),
        )
    else:
        connection.execute(
            "UPDATE expenses SET amount = ?, category = ?, expense_date = ?, description = ?, "
            "category_id = ? WHERE id = ? AND user_id = ?",
            (
                values["amount"],
                category["name"],
                values["expense_date"],
                values["description"],
                category["id"],
                expense_id,
                user_id,
            ),
=======
def get_user_categories(user_id):
    seed_default_categories(user_id)
    with database_connection() as connection:
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


def validate_expense_values(values, user_id):
    errors = []
    if not values["amount"]:
        errors.append("Enter an amount.")
    else:
        try:
            amount = Decimal(values["amount"])
            if not amount.is_finite() or amount <= 0:
                errors.append("Amount must be greater than zero.")
            elif amount.as_tuple().exponent < -2:
                errors.append("Amount must use no more than two decimal places.")
            else:
                values["amount"] = format(amount, ".2f")
        except InvalidOperation:
            errors.append("Enter a valid amount, such as 32.12.")

    try:
        parsed_date = date.fromisoformat(values["expense_date"])
        if parsed_date.isoformat() != values["expense_date"]:
            raise ValueError
    except ValueError:
        errors.append("Enter a valid expense date.")

    if values["expense_type"] not in ("Liability", "Savings"):
        errors.append("Choose Liability or Savings for the expense type.")

    category = None
    if values["category_id"] == "__new__":
        values["new_category"] = normalize_category_name(values["new_category"])
        if not values["new_category"]:
            errors.append("Enter a category name.")
    else:
        try:
            category_id = int(values["category_id"])
        except ValueError:
            category_id = None
        if category_id is None:
            errors.append("Choose a category.")
        else:
            with database_connection() as connection:
                category = connection.execute(
                    "SELECT id, name FROM categories WHERE id = ? AND user_id = ?",
                    (category_id, user_id),
                ).fetchone()
            if category is None:
                errors.append("Choose a category belonging to your account.")

    if values["subcategory_id"] == "__new__":
        values["new_subcategory"] = normalize_category_name(values["new_subcategory"])
        if not values["new_subcategory"]:
            errors.append("Enter a subcategory name.")
    elif values["subcategory_id"]:
        try:
            subcategory_id = int(values["subcategory_id"])
        except ValueError:
            subcategory_id = None
        if category is None or subcategory_id is None:
            errors.append("Choose a subcategory belonging to the selected category.")
        else:
            with database_connection() as connection:
                subcategory = connection.execute(
                    "SELECT id FROM subcategories WHERE id = ? AND category_id = ?",
                    (subcategory_id, category["id"]),
                ).fetchone()
            if subcategory is None:
                errors.append("Choose a subcategory belonging to the selected category.")

    return values, errors


def save_expense_record(user_id, values, expense_id=None):
    with database_connection() as connection:
        if values["category_id"] == "__new__":
            category_name = normalize_category_name(values["new_category"])
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
            category = connection.execute(
                "SELECT id, name FROM categories WHERE id = ? AND user_id = ?",
                (int(values["category_id"]), user_id),
            ).fetchone()

        subcategory_id = None
        if values["subcategory_id"] == "__new__":
            subcategory_name = normalize_category_name(values["new_subcategory"])
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
        elif values["subcategory_id"]:
            subcategory_id = int(values["subcategory_id"])

        if expense_id is None:
            connection.execute(
                "INSERT INTO expenses (user_id, amount, category, expense_date, description, category_id, subcategory_id, expense_type) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, values["amount"], category["name"], values["expense_date"], values["description"], category["id"], subcategory_id, values["expense_type"]),
            )
        else:
            connection.execute(
                "UPDATE expenses SET amount = ?, category = ?, expense_date = ?, description = ?, "
                "category_id = ?, subcategory_id = ?, expense_type = ? WHERE id = ? AND user_id = ?",
                (values["amount"], category["name"], values["expense_date"], values["description"], category["id"], subcategory_id, values["expense_type"], expense_id, user_id),
            )


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
>>>>>>> d6b40453c92a130e5b5b7944ca268733689bb73c
        )
        subcategory = connection.execute(
            "SELECT id, name FROM subcategories WHERE category_id = ? AND normalized_name = ?",
            (category_id, normalized_name),
        ).fetchone()
    return jsonify(id=subcategory["id"], name=subcategory["name"])


<<<<<<< HEAD
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
=======
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
>>>>>>> d6b40453c92a130e5b5b7944ca268733689bb73c


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
<<<<<<< HEAD
        spent_rows = connection.execute(
            "SELECT amount FROM expenses "
            "WHERE user_id = ? AND CAST(strftime('%Y', expense_date) AS INTEGER) = ? "
            "AND CAST(strftime('%m', expense_date) AS INTEGER) = ?",
            (user_id, selected_year, selected_month),
        ).fetchall()

    spent = sum((Decimal(row["amount"]) for row in spent_rows), Decimal("0"))
=======
        expense_rows = connection.execute(
            "SELECT expense_type, amount FROM expenses "
            "WHERE user_id = ? AND expense_date >= ? AND expense_date < ?",
            (user_id, month_start.isoformat(), month_end.isoformat()),
        ).fetchall()

    liability_total = sum((Decimal(row["amount"]) for row in expense_rows if row["expense_type"] == "Liability"), Decimal("0"))
    savings_total = sum((Decimal(row["amount"]) for row in expense_rows if row["expense_type"] == "Savings"), Decimal("0"))
    spent = liability_total + savings_total
>>>>>>> d6b40453c92a130e5b5b7944ca268733689bb73c
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
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        errors = []
        if not username:
            errors.append("Username is required.")
        if not password:
            errors.append("Password is required.")
        if not confirm_password:
            errors.append("Confirm your password.")
        elif password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("register.html", username=username), 400

        try:
            with database_connection() as connection:
                connection.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
        except sqlite3.IntegrityError:
            flash("That username is already taken.", "error")
            return render_template("register.html", username=username), 409

        flash("Account created. Sign in to continue.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", username="")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with database_connection() as connection:
            user = connection.execute(
                "SELECT id, username, password_hash FROM users WHERE username = ? COLLATE NOCASE",
                (username,),
            ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Username or password is incorrect.", "error")
            return render_template("login.html", username=username), 401

        session.clear()
        session["user_id"] = user["id"]
        session["user_username"] = user["username"]
        session["show_add_expense_modal"] = True
        csrf_token()
        return redirect(url_for("dashboard"))

    return render_template("login.html", username="")


@app.post("/logout")
@login_required
def logout():
    session.clear()
    flash("You have signed out.", "success")
    return redirect(url_for("login"))


@app.post("/expenses/modal/dismiss")
@login_required
def dismiss_expense_modal():
    session["show_add_expense_modal"] = False
    session.pop("expense_save_success", None)
    return redirect(url_for("dashboard"))


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
<<<<<<< HEAD
    modal_success = session.pop("expense_save_success", False)
    return _render_dashboard(modal_success=modal_success)
=======
    period = parse_month_period(request.args.get("period"))
    selected_year, selected_month = (int(part) for part in period.split("-"))
    budget = get_budget_summary(session["user_id"], selected_month, selected_year)
    return render_template(
        "dashboard.html",
        budget=budget,
        period=period,
        period_label=date(selected_year, selected_month, 1).strftime("%B %Y"),
        selected_month=selected_month,
        selected_year=selected_year,
    )
>>>>>>> d6b40453c92a130e5b5b7944ca268733689bb73c


@app.get("/expenses")
@login_required
<<<<<<< HEAD
def expenses_page():
    category_filter = request.args.get("category", "").strip()
    categories = get_user_categories(session["user_id"])
    valid_category_ids = {str(category["id"]) for category in categories}
    if category_filter and category_filter not in valid_category_ids:
        flash("Choose a valid category filter.", "error")
        category_filter = ""
=======
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
>>>>>>> d6b40453c92a130e5b5b7944ca268733689bb73c

    conditions = ["e.user_id = ?"]
    values = [session["user_id"]]
    if category_filter:
<<<<<<< HEAD
        conditions.append("e.category_id = ?")
        values.append(category_filter)

    with database_connection() as connection:
        expenses = connection.execute(
            "SELECT e.id, e.amount, e.category, e.category_id, e.expense_date, e.description "
            "FROM expenses e "
            f"WHERE {' AND '.join(conditions)} "
            "ORDER BY e.expense_date DESC, e.id DESC",
=======
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
>>>>>>> d6b40453c92a130e5b5b7944ca268733689bb73c
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
        total=total,
    )


<<<<<<< HEAD
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
=======
@app.get("/budget")
@login_required
def budget_page():
    period = parse_month_period(request.args.get("period"))
    selected_year, selected_month = (int(part) for part in period.split("-"))
    budget = get_budget_summary(session["user_id"], selected_month, selected_year)
    return render_template(
        "budget.html",
        budget=budget,
        period=period,
        period_label=date(selected_year, selected_month, 1).strftime("%B %Y"),
        selected_month=selected_month,
>>>>>>> d6b40453c92a130e5b5b7944ca268733689bb73c
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


@app.get("/analytics")
@login_required
def analytics_page():
    period = parse_month_period(request.args.get("period"))
    analytics = get_category_analytics(session["user_id"], period)
    selected_category_id = request.args.get("category_id", type=int)
    selected_category = next(
        (item for item in analytics["items"] if item["id"] == selected_category_id), None
    )
    return render_template(
        "analytics.html",
        period=analytics["month"],
        period_label=date(*(int(part) for part in analytics["month"].split("-")), 1).strftime("%B %Y"),
        analytics_items=analytics["items"],
        analytics_total=analytics["total"],
        highest_category=analytics["highest_category"],
        lowest_category=analytics["lowest_category"],
        selected_category=selected_category,
    )


@app.post("/budget")
@login_required
def save_budget():
    try:
<<<<<<< HEAD
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
=======
        period = request.form.get("period", "").strip()
        if period:
            parsed_period = parse_month_period(period)
            if parsed_period != period:
                raise ValueError
            period = parsed_period
            year, month = (int(part) for part in period.split("-"))
        else:
            month = int(request.form.get("month", ""))
            year = int(request.form.get("year", ""))
            period = date(year, month, 1).strftime("%Y-%m")
        amount = Decimal(request.form.get("budget_amount", "").strip())
        date(year, month, 1)
        if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
>>>>>>> d6b40453c92a130e5b5b7944ca268733689bb73c
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
<<<<<<< HEAD
    return redirect(url_for("dashboard", month=month, year=year))
=======
    return redirect(url_for("budget_page", period=period))
>>>>>>> d6b40453c92a130e5b5b7944ca268733689bb73c


@app.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
<<<<<<< HEAD
    today = date.today()
    categories = get_user_categories(session["user_id"])
    valid_category_ids = {str(category["id"]) for category in categories}
    values = {
        "amount": "",
        "category_id": "",
        "new_category": "",
        "expense_date": today.isoformat(),
        "description": "",
    }
    if request.method == "POST":
        raw_period = request.form.get("date_period", "").strip()
        raw_date_filter = request.form.get("date", "").strip()
        intent = request.form.get("intent", "save")
        if intent == "modal_save":
            raw_period = "custom"
            raw_date_filter = request.form.get("expense_date", "").strip()
        elif not raw_period and request.form.get("expense_date", "").strip():
            raw_period = "custom"
            raw_date_filter = request.form.get("expense_date", "").strip()
        values.update({
            "amount": request.form.get("amount", "").strip(),
            "category_id": request.form.get("category_id", "").strip(),
            "new_category": request.form.get("new_category", "").strip(),
            "description": request.form.get("description", "").strip(),
        })
    else:
        raw_period = request.args.get("date_period", "").strip()
        raw_date_filter = request.args.get("date", "").strip()
        intent = "save"
        category_query = request.args.get("category", "").strip()
        if category_query and category_query not in valid_category_ids:
            flash("Choose a valid category filter.", "error")
        elif category_query:
            values["category_id"] = category_query

    date_period, date_start, date_end, date_filter, date_error = resolve_expense_date_filter(
        raw_period,
        raw_date_filter,
        today,
    )
    transaction_date = {
        "today": today,
        "yesterday": date_start,
        "last7": today,
        "custom": date_start,
    }[date_period]
    values["expense_date"] = transaction_date.isoformat()

    if date_error and intent != "modal_save":
        flash(date_error, "error")

    category_filter = values["category_id"]
    if category_filter and category_filter not in valid_category_ids:
        if category_filter != "__new__" and intent != "modal_save":
            flash("Choose a valid category filter.", "error")
        category_filter = ""

    conditions = ["e.user_id = ?", "e.expense_date >= ?", "e.expense_date < ?"]
    filter_values = [session["user_id"], date_start.isoformat(), date_end.isoformat()]
    if category_filter:
        conditions.append("e.category_id = ?")
        filter_values.append(category_filter)
    with database_connection() as connection:
        expenses = connection.execute(
            "SELECT e.id, e.amount, e.category, e.category_id, e.expense_date, e.description "
            "FROM expenses e "
            f"WHERE {' AND '.join(conditions)} "
            "ORDER BY e.expense_date DESC, e.id DESC",
            filter_values,
        ).fetchall()

    date_analytics = get_period_analytics(
        session["user_id"],
        date_start.year,
        date_start.month,
        category_id=int(category_filter) if category_filter else None,
        start_date=date_start,
        end_date=date_end,
    )
    total = date_analytics["total"]

    def render_add_expense(status=200):
        return render_template(
            "add_expense.html",
            expense=values,
            categories=categories,
            today=today.isoformat(),
            expenses=expenses,
            category_filter=category_filter,
            date_period=date_period,
            date_filter=date_filter,
            date_label={
                "today": "Today",
                "yesterday": "Yesterday",
                "last7": "Last 7 Days",
                "custom": date_filter,
            }[date_period],
            date_analytics=date_analytics,
            total=total,
        ), status

    if request.method == "POST":
        if intent == "filter":
            return render_add_expense()

        if date_error:
            if intent == "modal_save":
                session["show_add_expense_modal"] = True
                return _render_dashboard(values, [date_error], status=400)
            return render_add_expense(400)

        form_data = request.form.to_dict()
        form_data["expense_date"] = transaction_date.isoformat()
        values, errors = parse_expense_form(form_data, session["user_id"])
=======
    categories = get_user_categories(session["user_id"])
    values = expense_form_values()
    if request.method == "POST":
        values = expense_form_values(request.form)
        values, errors = validate_expense_values(values, session["user_id"])
>>>>>>> d6b40453c92a130e5b5b7944ca268733689bb73c
        if errors:
            if intent == "modal_save":
                session["show_add_expense_modal"] = True
                return _render_dashboard(values, errors, status=400)
            for error in errors:
                flash(error, "error")
            return render_add_expense(400)

<<<<<<< HEAD
        with database_connection() as connection:
            save_expense(connection, session["user_id"], values)
        if intent == "modal_save":
            session["show_add_expense_modal"] = True
            session["expense_save_success"] = True
            return redirect(url_for("dashboard"))
        flash("Expense saved.", "success")
        return redirect(url_for(
            "add_expense",
            date_period=date_period,
            date=date_filter if date_period == "custom" else None,
            category=values["category_id"] if values["category_id"] != "__new__" else None,
        ))
=======
        save_expense_record(session["user_id"], values)
        flash("Expense saved.", "success")
        return redirect(url_for("expenses"))
>>>>>>> d6b40453c92a130e5b5b7944ca268733689bb73c

    return render_add_expense()


@app.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    categories = get_user_categories(session["user_id"])
    with database_connection() as connection:
<<<<<<< HEAD
        expense = connection.execute(
            "SELECT id, amount, category, category_id, expense_date, description "
=======
        expense_row = connection.execute(
            "SELECT id, amount, category_id, subcategory_id, expense_type, expense_date, description "
>>>>>>> d6b40453c92a130e5b5b7944ca268733689bb73c
            "FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, session["user_id"]),
        ).fetchone()
    if expense_row is None:
        abort(404)

<<<<<<< HEAD
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
=======
    saved_expense = dict(expense_row)
    saved_expense["category_id"] = str(saved_expense["category_id"])
    saved_expense["subcategory_id"] = str(saved_expense["subcategory_id"] or "")
    if request.method == "POST":
        values = expense_form_values(request.form)
        values, errors = validate_expense_values(values, session["user_id"])
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("edit_expense.html", expense=values, categories=categories), 400
        save_expense_record(session["user_id"], values, expense_id=expense_id)

    if request.method == "POST":
        flash("Expense updated.", "success")
        return redirect(url_for("expenses"))
    return render_template("edit_expense.html", expense=saved_expense, categories=categories)
>>>>>>> d6b40453c92a130e5b5b7944ca268733689bb73c


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