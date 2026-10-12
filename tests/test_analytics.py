import os
from pathlib import Path
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch


_test_database_directory = tempfile.TemporaryDirectory()
os.environ["EXPENSE_TRACKER_DB"] = str(
    Path(_test_database_directory.name) / "analytics-tests.sqlite3"
)
os.environ["EXPENSE_TRACKER_SECRET"] = "analytics-test-secret-key"

from backend.app import (  # noqa: E402
    app,
    database_connection,
    get_annual_spending_chart,
    get_period_analytics,
    resolve_expense_date_filter,
)

class FrozenDate(date):
    @classmethod
    def today(cls):
        return cls(2026, 10, 10)


class AnalyticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with database_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("analytics_test_user", "unused", "Professional"),
            )
            cls.user_id = cursor.lastrowid
            cursor = connection.execute(
                "INSERT INTO categories (user_id, name, normalized_name) VALUES (?, ?, ?)",
                (cls.user_id, "Food", "food"),
            )
            cls.food_id = cursor.lastrowid
            cursor = connection.execute(
                "INSERT INTO categories (user_id, name, normalized_name) VALUES (?, ?, ?)",
                (cls.user_id, "Travel", "travel"),
            )
            cls.travel_id = cursor.lastrowid

            rows = [
                (cls.user_id, "100.10", "Food", "2026-01-10", "", cls.food_id),
                (cls.user_id, "200.20", "Food", "2026-01-20", "", cls.food_id),
                (cls.user_id, "50.00", "Travel", "2026-01-10", "", cls.travel_id),
                (cls.user_id, "25.25", "Food", "2026-10-10", "", cls.food_id),
                (cls.user_id, "80.00", "Travel", "2026-10-10", "", cls.travel_id),
                (cls.user_id, "500.00", "Travel", "2026-10-08", "", cls.travel_id),
                (cls.user_id, "19800.00", "Food", "2026-06-15", "", cls.food_id),
                (cls.user_id, "999.99", "Food", "2026-11-01", "", cls.food_id),
                (cls.user_id, "75.00", "Food", "2025-12-01", "", cls.food_id),
            ]
            connection.executemany(
                "INSERT INTO expenses (user_id, amount, category, expense_date, description, category_id) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                rows,
            )
            connection.executemany(
                "INSERT INTO budgets (user_id, month, year, budget_amount) VALUES (?, ?, ?, ?)",
                [
                    (cls.user_id, 1, 2026, "500.00"),
                    (cls.user_id, 6, 2026, "18000.00"),
                    (cls.user_id, 10, 2026, "100.00"),
                ],
            )

    def test_period_summary_filters_by_day_and_category_with_decimal_totals(self):
        summary = get_period_analytics(
            self.user_id,
            2026,
            1,
            day=10,
            category_id=self.food_id,
        )

        self.assertEqual(summary["total"],  Decimal("100.10"))
        self.assertEqual(summary["count"], 1)
        self.assertEqual(summary["average"], Decimal("100.10"))
        self.assertEqual(summary["highest_category"]["category"], "Food")

    def test_current_year_chart_stops_at_current_month_and_filters_category(self):
        chart = get_annual_spending_chart(
            self.user_id,
            2026,
            date(2026, 10, 10),
            self.food_id,
        )

        self.assertEqual(len(chart["months"]), 10)
        self.assertEqual(chart["months"][-1]["month"], 10)
        self.assertEqual(chart["months"][-1]["spending"], Decimal("25.25"))
        self.assertEqual(chart["months"][-1]["budget"], Decimal("100.00"))
        self.assertEqual(chart["months"][-1]["status"], "under")

    def test_over_budget_chart_point_calculates_negative_remaining(self):
        chart = get_annual_spending_chart(self.user_id, 2026, date(2026, 10, 10))
        june = chart["months"][5]

        self.assertEqual(june["spending"], Decimal("19800"))
        self.assertEqual(june["remaining"], Decimal("-1800.00"))
        self.assertEqual(june["status"], "over")

    def test_last_seven_days_filter_includes_six_prior_calendar_days(self):
        period, start, end, _, error = resolve_expense_date_filter(
            "last7",
            "",
            date(2026, 10, 10),
        )

        self.assertIsNone(error)
        self.assertEqual(period, "last7")
        self.assertEqual(start, date(2026, 10, 4))
        self.assertEqual(end, date(2026, 10, 11))

    def test_past_year_chart_includes_all_months_and_missing_budgets(self):
        chart = get_annual_spending_chart(self.user_id, 2025, date(2026, 10, 10))

        self.assertEqual(len(chart["months"]), 12)
        self.assertEqual(chart["months"][-1]["month"], 12)
        self.assertEqual(chart["months"][-1]["spending"], Decimal("75"))
        self.assertIsNone(chart["months"][-1]["budget"])
        self.assertEqual(chart["months"][-1]["status"], "not-set")

    def test_custom_date_period_limits_summary_not_monthly_chart(self):
        client = app.test_client()
        with client.session_transaction() as session:
            session["user_id"] = self.user_id
            session["csrf_token"] = "test-token"

        with patch("backend.app.date", FrozenDate):
            response = client.get(
                "/analytics?date_period=custom&date=2026-10-10"
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"\xe2\x82\xb9105.25", response.data)
        self.assertIn(b"Oct 2026: spent \xe2\x82\xb9605.25", response.data)

    def test_authenticated_analytics_page_renders_month_points(self):
        client = app.test_client()
        with client.session_transaction() as session:
            session["user_id"] = self.user_id
            session["csrf_token"] = "test-token"

        with patch("backend.app.date", FrozenDate):
            response = client.get("/analytics?year=2026&month=10")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Monthly spending vs budget", response.data)
        self.assertIn(b"Category-wise distribution", response.data)
        self.assertEqual(response.data.count(b"data-month-point"), 10)

    def test_future_year_is_rejected_with_feedback(self):
        client = app.test_client()
        with client.session_transaction() as session:
            session["user_id"] = self.user_id
            session["csrf_token"] = "test-token"

        with patch("backend.app.date", FrozenDate):
            response = client.get("/analytics?year=9999&month=1")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Analytics can only be viewed up to the current month and year.", response.data)


if __name__ == "__main__":
    unittest.main()
