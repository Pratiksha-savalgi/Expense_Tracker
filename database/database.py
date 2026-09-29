from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = os.environ.get(
    "EXPENSE_TRACKER_DB",
    str(PROJECT_ROOT / "database" / "expenses.sqlite3"),
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
                description TEXT NOT NULL DEFAULT ''
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