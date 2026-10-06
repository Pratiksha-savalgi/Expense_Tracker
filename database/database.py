from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = os.environ.get(
    "EXPENSE_TRACKER_DB",
    str(PROJECT_ROOT / "database" / "expenses.sqlite3"),
)

DEFAULT_CATEGORIES = (
    "Food",
    "Utilities",
    "Transport",
    "Household",
    "Health",
    "Shopping",
    "Education",
    "Entertainment",
    "Bills",
    "Other",
)


@contextmanager
def database_connection():
    os.makedirs(os.path.dirname(DATABASE_PATH) or ".", exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def normalize_category_name(name):
    cleaned = " ".join((name or "").split())
    if not cleaned:
        return ""
    return " ".join(part[:1].upper() + part[1:].lower() for part in cleaned.split())


def seed_default_categories(user_id):
    with database_connection() as connection:
        for category_name in DEFAULT_CATEGORIES:
            category_display_name = normalize_category_name(category_name)
            normalized_category = category_display_name.casefold()
            connection.execute(
                "INSERT INTO categories (user_id, name, normalized_name) VALUES (?, ?, ?) "
                "ON CONFLICT(user_id, normalized_name) DO NOTHING",
                (user_id, category_display_name, normalized_category),
            )


def initialize_database():
    with database_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                amount TEXT NOT NULL,
                category TEXT NOT NULL,
                expense_date TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                category_id INTEGER REFERENCES categories(id) ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                UNIQUE(user_id, normalized_name)
            );

            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                budget_amount TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, month, year)
            );

            CREATE INDEX IF NOT EXISTS expenses_by_user_date
                ON expenses(user_id, expense_date);

            CREATE INDEX IF NOT EXISTS budgets_by_user_month
                ON budgets(user_id, year, month);
            """
        )

        expense_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(expenses)")
        }
        if "category_id" not in expense_columns:
            connection.execute(
                "ALTER TABLE expenses ADD COLUMN category_id INTEGER "
                "REFERENCES categories(id) ON DELETE RESTRICT"
            )
        if "subcategory_id" in expense_columns or "expense_type" in expense_columns:
            connection.execute("ALTER TABLE expenses RENAME TO expenses_old")
            connection.execute(
                """
                CREATE TABLE expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    amount TEXT NOT NULL,
                    category TEXT NOT NULL,
                    expense_date TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    category_id INTEGER REFERENCES categories(id) ON DELETE RESTRICT
                )
                """
            )
            connection.execute(
                "INSERT INTO expenses (id, user_id, amount, category, expense_date, description, category_id) "
                "SELECT id, user_id, amount, category, expense_date, description, category_id FROM expenses_old"
            )
            connection.execute("DROP TABLE expenses_old")

        table_names = {
            row["name"] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        if "subcategories" in table_names:
            connection.execute("DROP TABLE subcategories")

        legacy_expenses = connection.execute(
            "SELECT id, user_id, category FROM expenses "
            "WHERE category_id IS NULL ORDER BY id"
        ).fetchall()
        for expense in legacy_expenses:
            category_name = normalize_category_name(expense["category"]) or "Uncategorized"
            normalized_name = category_name.casefold()
            category = connection.execute(
                "SELECT id, name FROM categories WHERE user_id = ? AND normalized_name = ?",
                (expense["user_id"], normalized_name),
            ).fetchone()
            if category is None:
                connection.execute(
                    "INSERT INTO categories (user_id, name, normalized_name) VALUES (?, ?, ?)",
                    (expense["user_id"], category_name, normalized_name),
                )
                category = connection.execute(
                    "SELECT id, name FROM categories WHERE user_id = ? AND normalized_name = ?",
                    (expense["user_id"], normalized_name),
                ).fetchone()
            connection.execute(
                "UPDATE expenses SET category_id = ?, category = ? WHERE id = ?",
                (category["id"], category["name"], expense["id"]),
            )

        connection.executescript(
            """
            CREATE INDEX IF NOT EXISTS categories_by_user
                ON categories(user_id, normalized_name);
            CREATE INDEX IF NOT EXISTS expenses_by_category
                ON expenses(user_id, category_id);
            """
        )