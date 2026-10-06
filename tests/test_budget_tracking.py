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
        today = date.today()

        csrf = self._csrf_token_for("/dashboard")
        self.client.post(
            "/budget",
            data={"month": str(today.month), "year": str(today.year), "budget_amount": "10000", "csrf_token": csrf},
            follow_redirects=False,
        )

        csrf = self._csrf_token_for("/expenses/add")
        self.client.post(
            "/expenses/add",
            data={
                "amount": "2500",
                "category": "Food",
                "expense_date": today.isoformat(),
                "description": "Lunch",
                "csrf_token": csrf,
            },
            follow_redirects=False,
        )

        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Monthly budget", body)
        self.assertIn("Current Month Expenses", body)
        self.assertIn("₹10,000.00", body)
        self.assertIn("₹2,500.00", body)
        self.assertIn("₹7,500.00", body)
        self.assertIn("25.0%", body)


if __name__ == "__main__":
    unittest.main()
