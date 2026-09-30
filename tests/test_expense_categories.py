import re
import sqlite3
import tempfile
import unittest
import uuid
from datetime import date
from pathlib import Path

from backend.app import app
from database import database as database_module
from database.database import database_connection


class ExpenseCategoryTestCase(unittest.TestCase):
    def setUp(self):
        self.original_database_path = database_module.DATABASE_PATH
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = str(Path(self.temporary_directory.name) / "test.sqlite3")
        database_module.DATABASE_PATH = self.database_path
        database_module.initialize_database()
        self.client = app.test_client()
        self.username = f"module_a_{uuid.uuid4().hex}"
        self.password = "StrongPass123!"
        self._register_and_login(self.client, self.username)

    def tearDown(self):
        database_module.DATABASE_PATH = self.original_database_path
        self.temporary_directory.cleanup()

    def _csrf_token(self, client, url):
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        match = re.search(r'name="csrf_token" value="([^"]+)"', response.get_data(as_text=True))
        self.assertIsNotNone(match)
        return match.group(1)

    def _register_and_login(self, client, username):
        csrf = self._csrf_token(client, "/register")
        response = client.post(
            "/register",
            data={
                "username": username,
                "password": self.password,
                "confirm_password": self.password,
                "csrf_token": csrf,
            },
        )
        self.assertEqual(response.status_code, 302)

        csrf = self._csrf_token(client, "/login")
        response = client.post(
            "/login",
            data={"username": username, "password": self.password, "csrf_token": csrf},
        )
        self.assertEqual(response.status_code, 302)

    def _submit_expense(self, data, url="/expenses/add"):
        csrf = self._csrf_token(self.client, url)
        response = self.client.post(url, data={**data, "csrf_token": csrf})
        return response

    def _base_expense(self, **values):
        return {
            "amount": "32.12",
            "category_id": "__new__",
            "new_category": "Food",
            "subcategory_id": "",
            "new_subcategory": "",
            "expense_type": "Liability",
            "expense_date": date.today().isoformat(),
            "description": "Test expense",
            **values,
        }

    def test_adds_category_subcategory_and_expense_type(self):
        response = self._submit_expense(
            self._base_expense(
                subcategory_id="__new__",
                new_subcategory="Dinner",
                expense_type="Savings",
            )
        )
        self.assertEqual(response.status_code, 302)

        with database_connection() as connection:
            expense = connection.execute(
                "SELECT e.amount, e.category, e.expense_type, c.name AS category_name, "
                "s.name AS subcategory_name FROM expenses e "
                "JOIN categories c ON c.id = e.category_id "
                "JOIN subcategories s ON s.id = e.subcategory_id "
                "WHERE e.user_id = (SELECT id FROM users WHERE username = ?)",
                (self.username,),
            ).fetchone()
        self.assertEqual(expense["amount"], "32.12")
        self.assertEqual(expense["category"], "Food")
        self.assertEqual(expense["category_name"], "Food")
        self.assertEqual(expense["subcategory_name"], "Dinner")
        self.assertEqual(expense["expense_type"], "Savings")

        dashboard = self.client.get("/dashboard").get_data(as_text=True)
        self.assertIn("Food", dashboard)
        self.assertIn("Dinner", dashboard)
        self.assertIn("Savings", dashboard)

    def test_new_user_sees_default_categories_and_custom_add_options(self):
        body = self.client.get("/expenses/add").get_data(as_text=True)

        self.assertIn(">Food</option>", body)
        self.assertIn(">Transport</option>", body)
        self.assertIn("Groceries", body)
        self.assertIn("Breakfast", body)
        self.assertIn("+ Add category...", body)
        self.assertIn("+ Add subcategory...", body)

    def test_category_names_are_normalized_and_per_user(self):
        self.assertEqual(
            self._submit_expense(self._base_expense(new_category="Private Category")).status_code,
            302,
        )
        self.assertEqual(
            self._submit_expense(self._base_expense(new_category="  private  category  ")).status_code,
            302,
        )

        with database_connection() as connection:
            categories = connection.execute(
                "SELECT id, name FROM categories WHERE user_id = "
                "(SELECT id FROM users WHERE username = ?) AND normalized_name = 'private category'",
                (self.username,),
            ).fetchall()
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0]["name"], "Private Category")

        other_client = app.test_client()
        other_username = f"module_a_other_{uuid.uuid4().hex}"
        self._register_and_login(other_client, other_username)
        other_form = self._base_expense(category_id=str(categories[0]["id"]), new_category="")
        csrf = self._csrf_token(other_client, "/expenses/add")
        response = other_client.post(
            "/expenses/add",
            data={**other_form, "csrf_token": csrf},
        )
        self.assertEqual(response.status_code, 400)

        other_page = other_client.get("/expenses/add").get_data(as_text=True)
        self.assertNotIn(">Private Category</option>", other_page)

    def test_edit_updates_category_subcategory_and_type(self):
        self._submit_expense(self._base_expense())
        with database_connection() as connection:
            expense_id = connection.execute(
                "SELECT id FROM expenses WHERE user_id = "
                "(SELECT id FROM users WHERE username = ?)",
                (self.username,),
            ).fetchone()["id"]
            category_id = connection.execute(
                "SELECT id FROM categories WHERE user_id = "
                "(SELECT id FROM users WHERE username = ?) AND normalized_name = 'food'",
                (self.username,),
            ).fetchone()["id"]

        response = self._submit_expense(
            self._base_expense(
                amount="9.00",
                category_id=str(category_id),
                new_category="",
                subcategory_id="__new__",
                new_subcategory="Groceries",
                expense_type="Savings",
            ),
            f"/expenses/{expense_id}/edit",
        )
        self.assertEqual(response.status_code, 302)

        with database_connection() as connection:
            expense = connection.execute(
                "SELECT amount, category, subcategory_id, expense_type FROM expenses WHERE id = ?",
                (expense_id,),
            ).fetchone()
            subcategory = connection.execute(
                "SELECT name FROM subcategories WHERE id = ?",
                (expense["subcategory_id"],),
            ).fetchone()
        self.assertEqual(expense["amount"], "9.00")
        self.assertEqual(expense["category"], "Food")
        self.assertEqual(subcategory["name"], "Groceries")
        self.assertEqual(expense["expense_type"], "Savings")

    def test_rejects_invalid_amount_precision_and_preserves_values(self):
        self.client.get("/expenses/add")
        with database_connection() as connection:
            initial_category_count = connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        for amount, expected_message in (
            ("", "Enter an amount."),
            ("0", "Amount must be greater than zero."),
            ("-1.00", "Amount must be greater than zero."),
            ("12.345", "Amount must use no more than two decimal places."),
            ("invalid", "Enter a valid amount, such as 32.12."),
        ):
            with self.subTest(amount=amount):
                response = self._submit_expense(self._base_expense(amount=amount))
                body = response.get_data(as_text=True)
                self.assertEqual(response.status_code, 400)
                self.assertIn(expected_message, body)
                self.assertIn("selected>Food</option>", body)
                with database_connection() as connection:
                    count = connection.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
                    category_count = connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
                self.assertEqual(count, 0)
                self.assertEqual(category_count, initial_category_count)

    def test_category_and_date_filters_update_the_visible_total(self):
        today = date.today().isoformat()
        earlier = date.fromordinal(date.today().toordinal() - 1).isoformat()
        self._submit_expense(self._base_expense(amount="15.00", description="Today food", expense_date=today))
        with database_connection() as connection:
            food_id = connection.execute(
                "SELECT id FROM categories WHERE user_id = "
                "(SELECT id FROM users WHERE username = ?) AND normalized_name = 'food'",
                (self.username,),
            ).fetchone()["id"]
        self._submit_expense(
            self._base_expense(
                amount="10.00",
                category_id=str(food_id),
                new_category="",
                description="Earlier food",
                expense_date=earlier,
            )
        )
        self._submit_expense(
            self._base_expense(
                amount="5.00",
                new_category="Transport",
                description="Today transport",
                expense_date=today,
            )
        )

        response = self.client.get(f"/dashboard?category={food_id}&date={today}")
        body = response.get_data(as_text=True)
        ledger = body.split('aria-labelledby="records-title">', 1)[1]
        self.assertEqual(response.status_code, 200)
        self.assertIn("1 record matching filters", body)
        self.assertIn("₹15.00", body)
        self.assertIn("Today food", ledger)
        self.assertNotIn("Earlier food", ledger)
        self.assertNotIn("Today transport", ledger)

    def test_migrates_legacy_categories_without_losing_expenses(self):
        legacy_path = str(Path(self.temporary_directory.name) / "legacy.sqlite3")
        connection = sqlite3.connect(legacy_path)
        connection.executescript(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL
            );
            CREATE TABLE expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                amount TEXT NOT NULL,
                category TEXT NOT NULL,
                expense_date TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT ''
            );
            INSERT INTO users (username, password_hash) VALUES ('legacy_user', 'hash');
            INSERT INTO expenses (user_id, amount, category, expense_date) VALUES
                (1, '10.00', '  Food  ', '2026-09-01'),
                (1, '20.00', 'food', '2026-09-02');
            """
        )
        connection.close()

        database_module.DATABASE_PATH = legacy_path
        database_module.initialize_database()
        with database_connection() as connection:
            expenses = connection.execute(
                "SELECT category, category_id, expense_type FROM expenses ORDER BY id"
            ).fetchall()
            categories = connection.execute("SELECT name FROM categories").fetchall()
        self.assertEqual(len(expenses), 2)
        self.assertEqual(len(categories), 1)
        self.assertEqual([row["category"] for row in expenses], ["Food", "Food"])
        self.assertEqual(expenses[0]["category_id"], expenses[1]["category_id"])
        self.assertEqual([row["expense_type"] for row in expenses], ["Liability", "Liability"])

    def test_stale_session_redirects_to_login(self):
        with self.client.session_transaction() as user_session:
            user_session["user_id"] = -1
            user_session["user_username"] = "removed-user"

        response = self.client.get("/expenses/add")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")
        with self.client.session_transaction() as user_session:
            self.assertNotIn("user_id", user_session)


if __name__ == "__main__":
    unittest.main()