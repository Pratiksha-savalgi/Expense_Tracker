from datetime import date
from decimal import Decimal, InvalidOperation
from functools import wraps
import hmac
import os
import re
import secrets
import sqlite3
from pathlib import Path

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.database import (
    database_connection,
    initialize_database,
    normalize_category_name,
    seed_default_categories,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
app = Flask(
    __name__,
    static_url_path="/static",
    static_folder=str(PROJECT_ROOT / "frontend" / "static"),
    template_folder=str(PROJECT_ROOT / "frontend" / "templates"),
)
app.config.update(
    SECRET_KEY=os.environ.get("EXPENSE_TRACKER_SECRET") or secrets.token_hex(32),
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
        if not submitted_token and request.is_json:
            submitted_token = request.headers.get("X-CSRF-Token", "")
        saved_token = session.get("csrf_token", "")
        if not saved_token or not hmac.compare_digest(submitted_token, saved_token):
            abort(400)


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        user_id = session.get("user_id")
        if user_id is None:
            flash("Sign in to access your expenses.", "error")
            return redirect(url_for("login"))
        with database_connection() as connection:
            user = connection.execute(
                "SELECT id FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        if user is None:
            session.clear()
            flash("Your session is no longer valid. Please sign in again.", "error")
            return redirect(url_for("login"))
        return view(**kwargs)

    return wrapped_view


def get_user_categories(user_id):
    seed_default_categories(user_id)
    with database_connection() as connection:
        rows = connection.execute(
            "SELECT c.id AS category_id, c.name AS category_name, "
            "s.id AS subcategory_id, s.name AS subcategory_name "
            "FROM categories c LEFT JOIN subcategories s ON s.category_id = c.id "
            "WHERE c.user_id = ? ORDER BY c.name COLLATE NOCASE, s.name COLLATE NOCASE",
            (user_id,),
        ).fetchall()

    categories_by_id = {}
    for row in rows:
        category = categories_by_id.setdefault(
            row["category_id"],
            {"id": row["category_id"], "name": row["category_name"], "subcategories": []},
        )
        if row["subcategory_id"] is not None:
            category["subcategories"].append(
                {"id": row["subcategory_id"], "name": row["subcategory_name"]}
            )
    return list(categories_by_id.values())


def parse_expense_form(form, user_id):
    amount_text = form.get("amount", "").strip()
    category_choice = form.get("category_id", "").strip()
    new_category = normalize_category_name(form.get("new_category", ""))
    if not category_choice and form.get("category", "").strip():
        category_choice = "__new__"
        new_category = normalize_category_name(form.get("category", ""))
    subcategory_choice = form.get("subcategory_id", "").strip()
    new_subcategory = normalize_category_name(form.get("new_subcategory", ""))
    expense_date = form.get("expense_date", "").strip()
    description = form.get("description", "").strip()
    expense_type = form.get("expense_type", "Liability").strip().casefold()
    errors = []

    amount = None
    if not amount_text:
        errors.append("Enter an amount.")
    else:
        try:
            amount = Decimal(amount_text)
            if not amount.is_finite():
                errors.append("Enter a valid amount.")
            elif amount <= 0:
                errors.append("Amount must be greater than zero.")
            elif not re.fullmatch(r"(?:\d+(?:\.\d{0,2})?|\.\d{1,2})", amount_text):
                errors.append("Amount must use no more than two decimal places.")
        except InvalidOperation:
            errors.append("Enter a valid amount, such as 32.12.")

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

    subcategory_id = None
    subcategory_name = ""
    if subcategory_choice == "__new__":
        if not new_subcategory:
            errors.append("Enter a name for the new subcategory.")
        else:
            subcategory_name = new_subcategory
            if category_id is not None:
                with database_connection() as connection:
                    subcategory = connection.execute(
                        "SELECT id, name FROM subcategories "
                        "WHERE category_id = ? AND normalized_name = ?",
                        (int(category_id), new_subcategory.casefold()),
                    ).fetchone()
                if subcategory is not None:
                    subcategory_id = str(subcategory["id"])
                    subcategory_name = subcategory["name"]
                    new_subcategory = ""
    elif subcategory_choice:
        try:
            selected_subcategory_id = int(subcategory_choice)
        except ValueError:
            selected_subcategory_id = None
        if selected_subcategory_id is None or category_id is None:
            errors.append("Choose a subcategory belonging to the selected category.")
        else:
            with database_connection() as connection:
                subcategory = connection.execute(
                    "SELECT id, name FROM subcategories WHERE id = ? AND category_id = ?",
                    (selected_subcategory_id, int(category_id)),
                ).fetchone()
            if subcategory is None:
                errors.append("Choose a subcategory belonging to the selected category.")
            else:
                subcategory_id = str(subcategory["id"])
                subcategory_name = subcategory["name"]

    if expense_type not in {"liability", "savings"}:
        errors.append("Choose whether this entry is a liability or savings.")
    else:
        expense_type = expense_type.title()

    try:
        parsed_date = date.fromisoformat(expense_date)
        if parsed_date.isoformat() != expense_date:
            errors.append("Enter a valid expense date.")
    except ValueError:
        errors.append("Enter a valid expense date.")

    return {
        "amount": format(amount, "f") if amount is not None else amount_text,
        "category_id": category_id or category_choice,
        "category_name": category_name,
        "new_category": new_category,
        "subcategory_id": subcategory_id or subcategory_choice,
        "subcategory_name": subcategory_name,
        "new_subcategory": new_subcategory,
        "expense_type": expense_type or "Liability",
        "expense_date": expense_date,
        "description": description,
    }, errors


def get_or_create_category(connection, user_id, category_name):
    category_name = normalize_category_name(category_name)
    normalized_name = category_name.casefold()
    connection.execute(
        "INSERT INTO categories (user_id, name, normalized_name) VALUES (?, ?, ?) "
        "ON CONFLICT(user_id, normalized_name) DO NOTHING",
        (user_id, category_name, normalized_name),
    )
    return connection.execute(
        "SELECT id, name FROM categories WHERE user_id = ? AND normalized_name = ?",
        (user_id, normalized_name),
    ).fetchone()


def get_or_create_subcategory(connection, category_id, subcategory_name):
    subcategory_name = normalize_category_name(subcategory_name)
    normalized_name = subcategory_name.casefold()
    connection.execute(
        "INSERT INTO subcategories (category_id, name, normalized_name) VALUES (?, ?, ?) "
        "ON CONFLICT(category_id, normalized_name) DO NOTHING",
        (category_id, subcategory_name, normalized_name),
    )
    return connection.execute(
        "SELECT id, name FROM subcategories WHERE category_id = ? AND normalized_name = ?",
        (category_id, normalized_name),
    ).fetchone()


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

    if values["subcategory_id"] == "__new__" and values["new_subcategory"]:
        subcategory = get_or_create_subcategory(connection, category["id"], values["new_subcategory"])
        subcategory_id = subcategory["id"]
        subcategory_name = subcategory["name"]
    elif values["subcategory_id"]:
        subcategory = connection.execute(
            "SELECT id, name FROM subcategories WHERE id = ? AND category_id = ?",
            (int(values["subcategory_id"]), category["id"]),
        ).fetchone()
        if subcategory is None:
            raise ValueError("Choose a subcategory belonging to the selected category.")
        subcategory_id = subcategory["id"]
        subcategory_name = subcategory["name"]
    else:
        subcategory_id = None
        subcategory_name = ""

    if expense_id is None:
        connection.execute(
            "INSERT INTO expenses "
            "(user_id, amount, category, expense_date, description, category_id, subcategory_id, expense_type) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                values["amount"],
                category["name"],
                values["expense_date"],
                values["description"],
                category["id"],
                subcategory_id,
                values["expense_type"],
            ),
        )
    else:
        connection.execute(
            "UPDATE expenses SET amount = ?, category = ?, expense_date = ?, description = ?, "
            "category_id = ?, subcategory_id = ?, expense_type = ? "
            "WHERE id = ? AND user_id = ?",
            (
                values["amount"],
                category["name"],
                values["expense_date"],
                values["description"],
                category["id"],
                subcategory_id,
                values["expense_type"],
                expense_id,
                user_id,
            ),
        )


def get_category_analytics(user_id, target_month):
    if not target_month:
        target_month = date.today().strftime("%Y-%m")

    try:
        year, month = (int(part) for part in target_month.split("-"))
        if month < 1 or month > 12:
            raise ValueError
        date(year, month, 1)
    except (ValueError, TypeError):
        target_month = date.today().strftime("%Y-%m")

    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT category, SUM(CAST(amount AS REAL)) AS total
            FROM expenses
            WHERE user_id = ? AND substr(expense_date, 1, 7) = ?
            GROUP BY category
            ORDER BY total DESC, category COLLATE NOCASE ASC
            """,
            (user_id, target_month),
        ).fetchall()

    analytics = []
    month_total = Decimal("0")
    for row in rows:
        row_total = Decimal(str(row["total"]))
        month_total += row_total
        analytics.append({
            "category": row["category"],
            "total": row_total,
        })

    if analytics:
        for item in analytics:
            item["percentage"] = (item["total"] / month_total * Decimal("100")) if month_total > 0 else Decimal("0")
    else:
        for item in analytics:
            item["percentage"] = Decimal("0")

    highest_category = None
    lowest_category = None
    if analytics:
        highest_category = max(analytics, key=lambda item: item["total"])
        lowest_category = min(analytics, key=lambda item: item["total"])

    return {
        "month": target_month,
        "items": analytics,
        "total": month_total,
        "highest_category": highest_category,
        "lowest_category": lowest_category,
    }


def get_budget_summary(user_id, month=None, year=None):
    selected_month = int(month) if month is not None else date.today().month
    selected_year = int(year) if year is not None else date.today().year

    with database_connection() as connection:
        budget = connection.execute(
            "SELECT id, budget_amount FROM budgets WHERE user_id = ? AND month = ? AND year = ?",
            (user_id, selected_month, selected_year),
        ).fetchone()
        total_spent_row = connection.execute(
            "SELECT COALESCE(SUM(CAST(amount AS REAL)), 0) AS total_spent FROM expenses "
            "WHERE user_id = ? AND CAST(strftime('%Y', expense_date) AS INTEGER) = ? "
            "AND CAST(strftime('%m', expense_date) AS INTEGER) = ?",
            (user_id, selected_year, selected_month),
        ).fetchone()

    spent = Decimal(str(total_spent_row["total_spent"])) if total_spent_row and total_spent_row["total_spent"] is not None else Decimal("0")
    budget_amount = Decimal(str(budget["budget_amount"])) if budget else None

    if budget_amount is None:
        return {
            "month": selected_month,
            "year": selected_year,
            "budget_amount": None,
            "total_spent": spent,
            "remaining": None,
            "utilization": Decimal("0"),
            "status": "not_set",
            "status_label": "No budget set",
            "message": "Set a monthly budget to track your spending.",
        }

    remaining = budget_amount - spent
    utilization = (spent / budget_amount * Decimal("100")) if budget_amount else Decimal("0")

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
        "remaining": remaining,
        "utilization": utilization,
        "status": status,
        "status_label": status_label,
        "message": message,
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
        csrf_token()
        return redirect(url_for("dashboard"))

    return render_template("login.html", username="")


@app.post("/logout")
@login_required
def logout():
    session.clear()
    flash("You have signed out.", "success")
    return redirect(url_for("login"))


@app.get("/dashboard")
@login_required
def dashboard():
    category_filter = request.args.get("category", "").strip()
    date_filter = request.args.get("date", "").strip()
    analytics_month = request.args.get("analytics_month", date.today().strftime("%Y-%m")).strip()
    if date_filter:
        try:
            parsed_date = date.fromisoformat(date_filter)
            if parsed_date.isoformat() != date_filter:
                raise ValueError
        except ValueError:
            flash("Choose a valid date to filter expenses.", "error")
            date_filter = ""

    try:
        year, month = (int(part) for part in analytics_month.split("-"))
        if month < 1 or month > 12:
            raise ValueError
        date(year, month, 1)
    except (ValueError, TypeError):
        flash("Choose a valid month for category analytics.", "error")
        analytics_month = date.today().strftime("%Y-%m")

    try:
        selected_month = int(request.args.get("month", date.today().month))
        selected_year = int(request.args.get("year", date.today().year))
        if selected_month < 1 or selected_month > 12:
            raise ValueError
        date(selected_year, selected_month, 1)
    except (ValueError, TypeError):
        flash("Choose a valid month and year for budget tracking.", "error")
        selected_month = date.today().month
        selected_year = date.today().year

    categories = get_user_categories(session["user_id"])
    valid_category_ids = {str(category["id"]) for category in categories}
    if category_filter and category_filter not in valid_category_ids:
        flash("Choose a valid category filter.", "error")
        category_filter = ""

    conditions = ["e.user_id = ?"]
    values = [session["user_id"]]
    if category_filter:
        conditions.append("e.category_id = ?")
        values.append(category_filter)
    if date_filter:
        conditions.append("e.expense_date = ?")
        values.append(date_filter)

    with database_connection() as connection:
        expenses = connection.execute(
            "SELECT e.id, e.amount, e.category, e.category_id, e.subcategory_id, "
            "COALESCE(s.name, '') AS subcategory, e.expense_date, e.description, e.expense_type "
            "FROM expenses e LEFT JOIN subcategories s ON s.id = e.subcategory_id "
            f"WHERE {' AND '.join(conditions)} "
            "ORDER BY e.expense_date DESC, e.id DESC",
            values,
        ).fetchall()

    total = sum((Decimal(expense["amount"]) for expense in expenses), Decimal("0"))
    analytics = get_category_analytics(session["user_id"], analytics_month)
    budget = get_budget_summary(session["user_id"], selected_month, selected_year)
    return render_template(
        "view_expenses.html",
        expenses=expenses,
        categories=categories,
        category_filter=category_filter,
        date_filter=date_filter,
        total=total,
        analytics_month=analytics["month"],
        analytics_items=analytics["items"],
        highest_category=analytics["highest_category"],
        lowest_category=analytics["lowest_category"],
        budget=budget,
        selected_month=selected_month,
        selected_year=selected_year,
    )


@app.post("/budget")
@login_required
def save_budget():
    try:
        month = int(request.form.get("month", ""))
        year = int(request.form.get("year", ""))
        amount = Decimal(request.form.get("budget_amount", "").strip())
        date(year, month, 1)
        if not amount.is_finite() or amount <= 0:
            raise ValueError
    except (InvalidOperation, ValueError, TypeError):
        flash("Enter a valid month, year, and budget amount greater than zero.", "error")
        return redirect(url_for("dashboard"))

    with database_connection() as connection:
        connection.execute(
            "INSERT INTO budgets (user_id, month, year, budget_amount) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(user_id, month, year) DO UPDATE SET "
            "budget_amount = excluded.budget_amount, updated_at = CURRENT_TIMESTAMP",
            (session["user_id"], month, year, format(amount, "f")),
        )

    flash("Monthly budget saved.", "success")
    return redirect(url_for("dashboard", month=month, year=year))


@app.post("/categories/<int:category_id>/subcategories")
@login_required
def add_subcategory(category_id):
    payload = request.get_json(silent=True) or {}
    subcategory_name = normalize_category_name(payload.get("name", ""))
    if not subcategory_name:
        return jsonify(error="Enter a subcategory name."), 400

    with database_connection() as connection:
        category = connection.execute(
            "SELECT id FROM categories WHERE id = ? AND user_id = ?",
            (category_id, session["user_id"]),
        ).fetchone()
        if category is None:
            abort(404)

        subcategory = get_or_create_subcategory(connection, category_id, subcategory_name)

    return jsonify(id=subcategory["id"], name=subcategory["name"])


@app.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    values = {
        "amount": "",
        "category_id": "",
        "new_category": "",
        "subcategory_id": "",
        "new_subcategory": "",
        "expense_type": "Liability",
        "expense_date": date.today().isoformat(),
        "description": "",
    }
    categories = get_user_categories(session["user_id"])
    if request.method == "POST":
        values, errors = parse_expense_form(request.form, session["user_id"])
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("add_expense.html", expense=values, categories=categories), 400

        with database_connection() as connection:
            save_expense(connection, session["user_id"], values)
        flash("Expense saved.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_expense.html", expense=values, categories=categories)


@app.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    categories = get_user_categories(session["user_id"])
    with database_connection() as connection:
        expense = connection.execute(
            "SELECT id, amount, category, category_id, subcategory_id, expense_type, "
            "expense_date, description FROM expenses WHERE id = ? AND user_id = ?",
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
                ), 400

            save_expense(connection, session["user_id"], values, expense_id)

    if request.method == "POST":
        flash("Expense updated.", "success")
        return redirect(url_for("dashboard"))
    return render_template("edit_expense.html", expense=expense, categories=categories)


@app.post("/expenses/<int:expense_id>/delete")
@login_required
def delete_expense(expense_id):
    with database_connection() as connection:
        connection.execute(
            "DELETE FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, session["user_id"]),
        )
    flash("Expense deleted.", "success")
    return redirect(url_for("dashboard"))


initialize_database()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")