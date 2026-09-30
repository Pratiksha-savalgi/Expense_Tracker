import re
import unittest
from datetime import date

from backend.app import app
from database.database import database_connection


class BudgetTrackingTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.username = f"budget_user_{abs(hash(date.today().isoformat()))}"
        self.password = "StrongPass123!"

        with database_connection() as connection:
            connection.execute("DELETE FROM budgets WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'budget_user_%')")
            connection.execute("DELETE FROM expenses WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'budget_user_%')")
            connection.execute("DELETE FROM users WHERE username LIKE 'budget_user_%'")

    def _csrf_token_for(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        match = re.search(r'name="csrf_token" value="([^"]+)"', response.get_data(as_text=True))
        self.assertIsNotNone(match)
        return match.group(1)

    def _register_and_login(self):
        csrf = self._csrf_token_for("/register")
        response = self.client.post(
            "/register",
            data={
                "username": self.username,
                "password": self.password,
                "confirm_password": self.password,
                "csrf_token": csrf,
            },
            follow_redirects=False,
        )
        self.assertIn(response.status_code, (200, 302, 303))

        csrf = self._csrf_token_for("/login")
        response = self.client.post(
            "/login",
            data={"username": self.username, "password": self.password, "csrf_token": csrf},
            follow_redirects=False,
        )
        self.assertIn(response.status_code, (200, 302, 303))

    def _user_id(self, username=None):
        with database_connection() as connection:
            row = connection.execute(
                "SELECT id FROM users WHERE username = ?",
                (username or self.username,),
            ).fetchone()
        return row["id"]

    def _add_expense(self, user_id, category_name, amount, expense_type, subcategory_name=None):
        normalized_category = " ".join(category_name.split()).casefold()
        with database_connection() as connection:
            connection.execute(
                "INSERT INTO categories (user_id, name, normalized_name) VALUES (?, ?, ?) "
                "ON CONFLICT(user_id, normalized_name) DO NOTHING",
                (user_id, category_name, normalized_category),
            )
            category = connection.execute(
                "SELECT id FROM categories WHERE user_id = ? AND normalized_name = ?",
                (user_id, normalized_category),
            ).fetchone()
            subcategory_id = None
            if subcategory_name:
                normalized_subcategory = " ".join(subcategory_name.split()).casefold()
                connection.execute(
                    "INSERT INTO subcategories (category_id, name, normalized_name) VALUES (?, ?, ?) "
                    "ON CONFLICT(category_id, normalized_name) DO NOTHING",
                    (category["id"], subcategory_name, normalized_subcategory),
                )
                subcategory_id = connection.execute(
                    "SELECT id FROM subcategories WHERE category_id = ? AND normalized_name = ?",
                    (category["id"], normalized_subcategory),
                ).fetchone()["id"]
            connection.execute(
                "INSERT INTO expenses (user_id, amount, category, expense_date, description, category_id, subcategory_id, expense_type) "
                "VALUES (?, ?, ?, '2026-09-12', '', ?, ?, ?)",
                (user_id, amount, category_name, category["id"], subcategory_id, expense_type),
            )

    def test_monthly_budget_can_be_created_and_updated(self):
        self._register_and_login()

        csrf = self._csrf_token_for("/dashboard")
        response = self.client.post(
            "/budget",
            data={"month": "9", "year": "2026", "budget_amount": "5000", "csrf_token": csrf},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)

        with database_connection() as connection:
            row = connection.execute(
                "SELECT budget_amount FROM budgets WHERE user_id = (SELECT id FROM users WHERE username = ?) AND month = ? AND year = ?",
                (self.username, 9, 2026),
            ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["budget_amount"], "5000")

        csrf = self._csrf_token_for("/dashboard")
        response = self.client.post(
            "/budget",
            data={"month": "9", "year": "2026", "budget_amount": "7200", "csrf_token": csrf},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)

        with database_connection() as connection:
            rows = connection.execute(
                "SELECT budget_amount FROM budgets WHERE user_id = (SELECT id FROM users WHERE username = ?) AND month = ? AND year = ?",
                (self.username, 9, 2026),
            ).fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["budget_amount"], "7200")

    def test_monthly_budget_status_is_shown_on_dashboard(self):
        self._register_and_login()

        csrf = self._csrf_token_for("/budget")
        self.client.post(
            "/budget",
            data={"month": "9", "year": "2026", "budget_amount": "10000", "csrf_token": csrf},
            follow_redirects=False,
        )

        user_id = self._user_id()
        self._add_expense(user_id, "Food", "2000.00", "Liability", "Lunch")
        self._add_expense(user_id, "Food", "500.00", "Savings", "Groceries")

        response = self.client.get("/budget?period=2026-09")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Budget status", body)
        self.assertIn("₹7,500.00", body)
        self.assertIn("25.0%", self.client.get("/dashboard?period=2026-09").get_data(as_text=True))
        self.assertIn("Remaining", body)
        self.assertIn("Utilization", body)

    def test_dashboard_chart_and_category_drilldown_are_user_scoped(self):
        self._register_and_login()
        user_id = self._user_id()
        csrf = self._csrf_token_for("/budget")
        self.client.post(
            "/budget",
            data={"period": "2026-09", "budget_amount": "1000.00", "csrf_token": csrf},
            follow_redirects=False,
        )
        self._add_expense(user_id, "Food", "500.00", "Liability", "Groceries")
        self._add_expense(user_id, "Food", "250.00", "Savings", "Groceries")
        self._add_expense(user_id, "Transport", "100.00", "Liability", "Fuel")

        with database_connection() as connection:
            connection.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, 'unused')",
                (f"other_{self.username}",),
            )
            other_user_id = connection.execute(
                "SELECT id FROM users WHERE username = ?",
                (f"other_{self.username}",),
            ).fetchone()["id"]
        self._add_expense(other_user_id, "Private", "9000.00", "Liability", "Hidden")

        dashboard = self.client.get("/dashboard?period=2026-09")
        dashboard_body = dashboard.get_data(as_text=True)
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn("Monthly budget utilization", dashboard_body)
        self.assertIn("Liability", dashboard_body)
        self.assertIn("Savings", dashboard_body)
        self.assertIn("--liability-end: 60.000%", dashboard_body)
        self.assertIn("--expenditure-end: 85.000%", dashboard_body)
        self.assertNotIn("Add expense", dashboard_body)
        self.assertNotIn("Budget status", dashboard_body)
        self.assertIn("Warning", self.client.get("/budget?period=2026-09").get_data(as_text=True))

        analytics = self.client.get("/analytics?period=2026-09")
        analytics_body = analytics.get_data(as_text=True)
        self.assertEqual(analytics.status_code, 200)
        self.assertIn("₹750.00", analytics_body)
        self.assertIn("Food", analytics_body)
        self.assertIn("Transport", analytics_body)
        self.assertNotIn("Private", analytics_body)

        with database_connection() as connection:
            food_id = connection.execute(
                "SELECT id FROM categories WHERE user_id = ? AND normalized_name = 'food'",
                (user_id,),
            ).fetchone()["id"]
        drilldown = self.client.get(f"/analytics?period=2026-09&category_id={food_id}")
        drilldown_body = drilldown.get_data(as_text=True)
        self.assertEqual(drilldown.status_code, 200)
        self.assertIn("Subcategory totals", drilldown_body)
        self.assertIn("Groceries", drilldown_body)
        self.assertIn("₹750.00", drilldown_body)

    def test_over_budget_state_and_empty_states_render(self):
        self._register_and_login()
        user_id = self._user_id()
        csrf = self._csrf_token_for("/budget")
        self.client.post(
            "/budget",
            data={"period": "2026-09", "budget_amount": "1000.00", "csrf_token": csrf},
            follow_redirects=False,
        )
        self._add_expense(user_id, "Bills", "900.00", "Liability")
        self._add_expense(user_id, "Bills", "200.00", "Savings")

        over_budget = self.client.get("/budget?period=2026-09").get_data(as_text=True)
        self.assertIn("Budget exceeded", over_budget)
        self.assertIn("₹-100.00", over_budget)
        self.assertIn("110.0%", over_budget)

        empty_client = app.test_client()
        empty_username = f"empty_{self.username}"
        empty_register_page = empty_client.get("/register").get_data(as_text=True)
        empty_csrf = re.search(r'name="csrf_token" value="([^"]+)"', empty_register_page).group(1)
        empty_client.post(
            "/register",
            data={
                "username": empty_username,
                "password": self.password,
                "confirm_password": self.password,
                "csrf_token": empty_csrf,
            },
            follow_redirects=False,
        )
        empty_csrf = re.search(
            r'name="csrf_token" value="([^"]+)"',
            empty_client.get("/login").get_data(as_text=True),
        ).group(1)
        empty_client.post(
            "/login",
            data={"username": empty_username, "password": self.password, "csrf_token": empty_csrf},
            follow_redirects=False,
        )
        self.assertIn("No budget set", empty_client.get("/dashboard?period=2026-09").get_data(as_text=True))
        self.assertIn("No category data", empty_client.get("/analytics?period=2026-09").get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
