from datetime import date
from decimal import Decimal, InvalidOperation
from functools import wraps
import hmac
import os
import secrets
import sqlite3
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.database import database_connection, initialize_database

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
        saved_token = session.get("csrf_token", "")
        if not saved_token or not hmac.compare_digest(submitted_token, saved_token):
            abort(400)


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            flash("Sign in to access your expenses.", "error")
            return redirect(url_for("login"))
        return view(**kwargs)

    return wrapped_view


def parse_expense_form(form):
    amount_text = form.get("amount", "").strip()
    category = form.get("category", "").strip()
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

    if not category:
        errors.append("Enter a category.")

    try:
        parsed_date = date.fromisoformat(expense_date)
        if parsed_date.isoformat() != expense_date:
            errors.append("Enter a valid expense date.")
    except ValueError:
        errors.append("Enter a valid expense date.")

    return {
        "amount": format(amount, "f") if amount is not None else amount_text,
        "category": category,
        "expense_date": expense_date,
        "description": description,
    }, errors


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

    conditions = ["user_id = ?"]
    values = [session["user_id"]]
    if category_filter:
        conditions.append("category = ?")
        values.append(category_filter)
    if date_filter:
        conditions.append("expense_date = ?")
        values.append(date_filter)

    with database_connection() as connection:
        expenses = connection.execute(
            "SELECT id, amount, category, expense_date, description "
            f"FROM expenses WHERE {' AND '.join(conditions)} "
            "ORDER BY expense_date DESC, id DESC",
            values,
        ).fetchall()
        categories = connection.execute(
            "SELECT DISTINCT category FROM expenses WHERE user_id = ? ORDER BY category COLLATE NOCASE",
            (session["user_id"],),
        ).fetchall()

    total = sum((Decimal(expense["amount"]) for expense in expenses), Decimal("0"))
    analytics = get_category_analytics(session["user_id"], analytics_month)
    budget = get_budget_summary(session["user_id"], selected_month, selected_year)
    return render_template(
        "view_expenses.html",
        expenses=expenses,
        categories=[row["category"] for row in categories],
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


@app.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    values = {"amount": "", "category": "", "expense_date": date.today().isoformat(), "description": ""}
    if request.method == "POST":
        values, errors = parse_expense_form(request.form)
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("add_expense.html", expense=values), 400

        with database_connection() as connection:
            connection.execute(
                "INSERT INTO expenses (user_id, amount, category, expense_date, description) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    session["user_id"],
                    values["amount"],
                    values["category"],
                    values["expense_date"],
                    values["description"],
                ),
            )
        flash("Expense saved.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_expense.html", expense=values)


@app.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    with database_connection() as connection:
        expense = connection.execute(
            "SELECT id, amount, category, expense_date, description FROM expenses "
            "WHERE id = ? AND user_id = ?",
            (expense_id, session["user_id"]),
        ).fetchone()
        if expense is None:
            abort(404)

        if request.method == "POST":
            values, errors = parse_expense_form(request.form)
            if errors:
                for error in errors:
                    flash(error, "error")
                return render_template("edit_expense.html", expense={**dict(expense), **values}), 400

            connection.execute(
                "UPDATE expenses SET amount = ?, category = ?, expense_date = ?, description = ? "
                "WHERE id = ? AND user_id = ?",
                (
                    values["amount"],
                    values["category"],
                    values["expense_date"],
                    values["description"],
                    expense_id,
                    session["user_id"],
                ),
            )

    if request.method == "POST":
        flash("Expense updated.", "success")
        return redirect(url_for("dashboard"))
    return render_template("edit_expense.html", expense=expense)


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