from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = os.environ.get(
    "EXPENSE_TRACKER_DB",
    str(PROJECT_ROOT / "database" / "expenses.sqlite3"),
)

DEFAULT_CATEGORIES_BY_ROLE = {
    "Student": (
        "Education",
        "Hostel / Rent",
        "Food & Dining",
        "Transportation",
        "Mobile & Internet",
        "Books & Stationery",
        "Entertainment",
        "Shopping",
        "Personal Care",
        "Healthcare",
        "Gifts",
        "Other",
    ),
    "Homemaker": (
        "Groceries",
        "Household",
        "Utilities",
        "Food & Dining",
        "Healthcare",
        "Children & Education",
        "Transportation",
        "Shopping",
        "Personal Care",
        "Gifts & Festivals",
        "Domestic Help",
        "Other",
    ),
    "Professional": (
        "Rent / Housing",
        "Food & Dining",
        "Transportation",
        "Utilities",
        "Mobile & Internet",
        "Work & Professional",
        "Shopping",
        "Entertainment",
        "Healthcare",
        "Personal Care",
        "Travel",
        "Subscriptions",
        "Gifts",
        "Other",
    ),
}
USER_ROLES = tuple(DEFAULT_CATEGORIES_BY_ROLE)


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


def seed_default_categories(connection, user_id, role=None):
    if role is None:
        user = connection.execute(
            "SELECT role FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if user is None:
            raise ValueError("Cannot seed categories for an unknown user.")
        role = user["role"]
    if role not in DEFAULT_CATEGORIES_BY_ROLE:
        raise ValueError("Cannot seed categories for an invalid user role.")

    for category_name in DEFAULT_CATEGORIES_BY_ROLE[role]:
        category_display_name = normalize_category_name(category_name)
        normalized_category = category_display_name.casefold()
        connection.execute(
            "INSERT INTO categories (user_id, name, normalized_name) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id, normalized_name) DO NOTHING",
            (user_id, category_display_name, normalized_category),
        )


def migrate_users_table(connection):
    schema_row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'users'"
    ).fetchone()
    if schema_row is None:
        return

    user_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(users)")
    }
    schema = schema_row["sql"] or ""
    if "role" in user_columns and "COLLATE NOCASE" not in schema.upper():
        return

    connection.commit()
    connection.execute("PRAGMA foreign_keys = OFF")
    try:
        connection.execute("BEGIN IMMEDIATE")
        existing_migration_table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'users_registration_migration'"
        ).fetchone()
        if existing_migration_table is not None:
            raise RuntimeError("A registration schema migration table already exists.")

        role_column = "role" if "role" in user_columns else (
            "user_type" if "user_type" in user_columns else None
        )
        selected_role = role_column if role_column else "'Professional'"
        existing_users = connection.execute(
            "SELECT id, username, password_hash, " + selected_role + " AS saved_role FROM users"
        ).fetchall()

        connection.execute(
            """
            CREATE TABLE users_registration_migration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL COLLATE BINARY UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('Student', 'Homemaker', 'Professional'))
            )
            """
        )
        for user in existing_users:
            role_value = user["saved_role"]
            if role_value == "Working Professional":
                role_value = "Professional"
            if role_value not in DEFAULT_CATEGORIES_BY_ROLE:
                role_value = "Professional"
            connection.execute(
                "INSERT INTO users_registration_migration (id, username, password_hash, role) "
                "VALUES (?, ?, ?, ?)",
                (user["id"], user["username"], user["password_hash"], role_value),
            )

        connection.execute("DROP TABLE users")
        connection.execute(
            "ALTER TABLE users_registration_migration RENAME TO users"
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.execute("PRAGMA foreign_keys = ON")


def initialize_database():
    with database_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL COLLATE BINARY UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'Professional'
                    CHECK (role IN ('Student', 'Homemaker', 'Professional'))
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                UNIQUE(user_id, normalized_name)
            );

            CREATE TABLE IF NOT EXISTS subcategories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                UNIQUE(category_id, normalized_name)
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                amount TEXT NOT NULL,
                category TEXT NOT NULL,
                expense_date TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                category_id INTEGER REFERENCES categories(id) ON DELETE RESTRICT,
                subcategory_id INTEGER REFERENCES subcategories(id) ON DELETE SET NULL,
                expense_type TEXT NOT NULL DEFAULT 'Liability'
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

            CREATE TABLE IF NOT EXISTS assistant_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS assistant_pending_actions (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                action_name TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'confirmed', 'cancelled', 'expired')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT NOT NULL,
                consumed_at TEXT
            );

            CREATE INDEX IF NOT EXISTS expenses_by_user_date
                ON expenses(user_id, expense_date);

            CREATE INDEX IF NOT EXISTS budgets_by_user_month
                ON budgets(user_id, year, month);

            CREATE INDEX IF NOT EXISTS assistant_messages_by_user
                ON assistant_messages(user_id, id);

            CREATE TABLE IF NOT EXISTS assistant_memory_focus (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                focus_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS assistant_pending_by_user
                ON assistant_pending_actions(user_id, status, expires_at);

            CREATE UNIQUE INDEX IF NOT EXISTS assistant_pending_fingerprint
                ON assistant_pending_actions(user_id, fingerprint)
                WHERE status = 'pending';
            """
        )

        migrate_users_table(connection)

        expense_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(expenses)")
        }
        if "category_id" not in expense_columns:
            connection.execute(
                "ALTER TABLE expenses ADD COLUMN category_id INTEGER "
                "REFERENCES categories(id) ON DELETE RESTRICT"
            )
        if "subcategory_id" not in expense_columns:
            connection.execute(
                "ALTER TABLE expenses ADD COLUMN subcategory_id INTEGER "
                "REFERENCES subcategories(id) ON DELETE SET NULL"
            )
        if "expense_type" not in expense_columns:
            connection.execute(
                "ALTER TABLE expenses ADD COLUMN expense_type TEXT NOT NULL DEFAULT 'Liability'"
            )

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