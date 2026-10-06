import re
import sqlite3
import tempfile
import unittest
import uuid
from datetime import date
from pathlib import Path

from backend.app import app, load_or_create_secret_key
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
            "expense_date": date.today().isoformat(),
            "description": "Test expense",
            **values,
        }

    def test_generated_secret_key_persists_across_app_starts(self):
        secret_path = Path(self.temporary_directory.name) / "instance" / "secret_key"
        first_key = load_or_create_secret_key(secret_path)
        second_key = load_or_create_secret_key(secret_path)
        self.assertEqual(first_key, second_key)
        self.assertEqual(len(first_key), 64)

    def test_expired_form_session_redirects_to_sign_in(self):
        response = self.client.post("/expenses/add", data={})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")
        body = self.client.get(response.headers["Location"]).get_data(as_text=True)
        self.assertIn("Your session expired. Please sign in again.", body)

    def test_adds_expense_with_category_and_date(self):
        response = self._submit_expense(self._base_expense())
        self.assertEqual(response.status_code, 302)

        with database_connection() as connection:
            expense = connection.execute(
                "SELECT e.amount, e.category, c.name AS category_name FROM expenses e "
                "JOIN categories c ON c.id = e.category_id "
                "WHERE e.user_id = (SELECT id FROM users WHERE username = ?)",
                (self.username,),
            ).fetchone()
        self.assertEqual(expense["amount"], "32.12")
        self.assertEqual(expense["category"], "Food")
        self.assertEqual(expense["category_name"], "Food")

    def test_new_user_sees_default_categories(self):
        body = self.client.get("/expenses/add").get_data(as_text=True)
        self.assertIn(">Food</option>", body)
        self.assertIn(">Transport</option>", body)
        self.assertIn("+ Add category...", body)

    def test_login_opens_expense_modal_and_dismissal_is_remembered(self):
        body = self.client.get("/dashboard").get_data(as_text=True)
        self.assertIn('data-expense-modal data-auto-open="true"', body)
        self.assertIn('action="/expenses/add" data-modal-expense-form', body)
        self.assertIn('data-modal-date-period="today" aria-pressed="true">Today', body)
        self.assertIn('data-modal-date-period="yesterday" aria-pressed="false">Yesterday', body)
        self.assertIn('data-modal-date-period="last7" aria-pressed="false">−7 days', body)
        self.assertIn('id="modal-expense-date" name="expense_date" type="date"', body)
        self.assertIn('data-modal-date-picker', body)

        csrf = self._csrf_token(self.client, "/dashboard")
        response = self.client.post(
            "/expenses/modal/dismiss",
            data={"csrf_token": csrf},
        )
        self.assertEqual(response.status_code, 302)
        body = self.client.get("/dashboard").get_data(as_text=True)
        self.assertIn('data-expense-modal data-auto-open="false"', body)

    def test_modal_expense_save_validates_and_shows_success_with_reset_form(self):
        csrf = self._csrf_token(self.client, "/dashboard")
        invalid_response = self.client.post(
            "/expenses/add",
            data={
                "csrf_token": csrf,
                "intent": "modal_save",
                "amount": "",
                "category_id": "",
                "expense_date": date.today().isoformat(),
            },
        )
        self.assertEqual(invalid_response.status_code, 400)
        invalid_body = invalid_response.get_data(as_text=True)
        self.assertIn("Enter an amount.", invalid_body)
        self.assertIn("Choose a category or add a new one.", invalid_body)
        self.assertIn('data-expense-modal data-auto-open="true"', invalid_body)
        with database_connection() as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM expenses").fetchone()[0], 0)

        missing_date_response = self.client.post(
            "/expenses/add",
            data={
                "csrf_token": csrf,
                "intent": "modal_save",
                "amount": "12.50",
                "category_id": "__new__",
                "new_category": "Missing Date",
                "expense_date": "",
            },
        )
        self.assertEqual(missing_date_response.status_code, 400)
        self.assertIn(
            "Choose a valid date no later than today.",
            missing_date_response.get_data(as_text=True),
        )
        with database_connection() as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM expenses").fetchone()[0], 0)

        response = self.client.post(
            "/expenses/add",
            data={
                "csrf_token": csrf,
                "intent": "modal_save",
                "amount": "12.50",
                "category_id": "__new__",
                "new_category": "Modal Test",
                "expense_date": date.today().isoformat(),
                "description": "Modal saved expense",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/dashboard")
        body = self.client.get("/dashboard").get_data(as_text=True)
        self.assertIn("Expense saved successfully.", body)
        self.assertIn('data-expense-modal data-auto-open="true"', body)
        self.assertIn('name="amount" type="number" min="0.01" step="0.01" inputmode="decimal" required value=""', body)
        self.assertIn('id="modal-category" name="category_id" required data-modal-category', body)
        self.assertIn('name="description" rows="2" placeholder="What was this expense for?"></textarea>', body)
        with database_connection() as connection:
            saved = connection.execute(
                "SELECT amount, description FROM expenses WHERE user_id = "
                "(SELECT id FROM users WHERE username = ?) AND description = ?",
                (self.username, "Modal saved expense"),
            ).fetchone()
        self.assertIsNotNone(saved)
        self.assertEqual(saved["amount"], "12.50")

    def test_category_names_are_normalized_and_per_user(self):
        self.assertEqual(database_module.normalize_category_name("  private  category  "), "Private Category")
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

    def test_category_and_date_filters_preserve_the_form_without_extra_panels(self):
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

        response = self.client.get(
            f"/expenses/add?category={food_id}&date_period=custom&date={today}"
        )
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('class="entry-form add-expense-form"', body)
        self.assertIn(f'value="{food_id}" selected', body)
        self.assertIn('class="date-picker-option is-active"', body)
        self.assertNotIn("add-expense-overview", body)
        self.assertNotIn("expense-date-analytics", body)
        self.assertNotIn('class="records-section"', body)

    def test_date_filter_is_on_add_expense_and_expenses_remains_unfiltered(self):
        today = date.today()
        yesterday = date.fromordinal(today.toordinal() - 1)
        for expense_date, description in (
            (today, "Today expense"),
            (yesterday, "Yesterday expense"),
        ):
            self._submit_expense(
                self._base_expense(
                    expense_date=expense_date.isoformat(),
                    description=description,
                )
            )

        expenses_page = self.client.get("/expenses").get_data(as_text=True)
        self.assertNotIn("data-date-filter-form", expenses_page)
        self.assertIn("Today expense", expenses_page)
        self.assertIn("Yesterday expense", expenses_page)

        add_page = self.client.get("/expenses/add").get_data(as_text=True)
        self.assertEqual(add_page.count("data-custom-date-picker"), 1)
        self.assertIn('data-date-period="today" aria-pressed="true"', add_page)
        self.assertIn('name="expense_date" value=', add_page)
        self.assertIn('class="field field-wide">\n        <label for="amount"', add_page)
        self.assertLess(add_page.index('id="category"'), add_page.index('data-date-period="today"'))
        self.assertNotIn("add-expense-overview", add_page)
        self.assertNotIn("expense-date-analytics", add_page)
        self.assertNotIn('class="records-section"', add_page)
        entry_form = add_page.split('class="entry-form add-expense-form"', 1)[1].split("</form>", 1)[0]
        self.assertIn('id="custom-expense-date"', entry_form)
        self.assertNotIn('id="expense_date"', entry_form)
        self.assertEqual(entry_form.count('name="date_period"'), 1)

    def test_saving_expense_preserves_add_page_date_filter(self):
        yesterday = date.fromordinal(date.today().toordinal() - 1)
        self._submit_expense(
            self._base_expense(
                amount="8.00",
                expense_date=yesterday.isoformat(),
                description="Earlier expense",
            )
        )

        csrf = self._csrf_token(
            self.client,
            f"/expenses/add?date_period=yesterday",
        )
        response = self.client.post(
            "/expenses/add?date_period=yesterday",
            data={
                **self._base_expense(
                    amount="12.00",
                    expense_date=yesterday.isoformat(),
                    description="New filtered expense",
                ),
                "date_period": "yesterday",
                "date": "",
                "csrf_token": csrf,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/expenses/add?date_period=yesterday", response.headers["Location"])
        body = self.client.get(response.headers["Location"]).get_data(as_text=True)
        self.assertIn('data-date-period="yesterday" aria-pressed="true"', body)
        self.assertNotIn('class="records-section"', body)

    def test_filter_submission_does_not_save_and_presets_set_transaction_date(self):
        yesterday = date.fromordinal(date.today().toordinal() - 1)
        baseline = self._submit_expense(
            self._base_expense(
                amount="8.00",
                expense_date=yesterday.isoformat(),
                description="Yesterday record",
            )
        )
        self.assertEqual(baseline.status_code, 302)

        csrf = self._csrf_token(self.client, "/expenses/add")
        response = self.client.post(
            "/expenses/add",
            data={
                "csrf_token": csrf,
                "intent": "filter",
                "date_period": "yesterday",
                "date": "",
                "expense_date": yesterday.isoformat(),
                "amount": "19.00",
                "category_id": "",
                "description": "Unsaved draft",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('value="19.00"', body)
        self.assertNotIn('class="records-section"', body)
        with database_connection() as connection:
            saved_count = connection.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
        self.assertEqual(saved_count, 1)

        for period, selected_date, expected_date in (
            ("today", "", date.today()),
            ("yesterday", "", yesterday),
            ("last7", "", date.today()),
            ("custom", yesterday.isoformat(), yesterday),
        ):
            with self.subTest(period=period):
                csrf = self._csrf_token(
                    self.client,
                    f"/expenses/add?date_period={period}&date={selected_date}",
                )
                response = self.client.post(
                    f"/expenses/add?date_period={period}&date={selected_date}",
                    data={
                        "csrf_token": csrf,
                        "intent": "save",
                        "date_period": period,
                        "date": selected_date,
                        "expense_date": expected_date.isoformat(),
                        "amount": "19.00",
                        "category_id": "__new__",
                        "new_category": "Filter Date Test",
                        "description": f"Saved {period}",
                    },
                )
                self.assertEqual(response.status_code, 302)
                with database_connection() as connection:
                    saved = connection.execute(
                        "SELECT expense_date FROM expenses WHERE description = ?",
                        (f"Saved {period}",),
                    ).fetchone()
                self.assertIsNotNone(saved)
                self.assertEqual(saved["expense_date"], expected_date.isoformat())

    def test_add_page_date_quick_filters_select_period_without_extra_panels(self):
        today = date.today()
        dates_and_amounts = (
            (today, "10.00", "Today record"),
            (date.fromordinal(today.toordinal() - 1), "20.00", "Yesterday record"),
            (date.fromordinal(today.toordinal() - 6), "30.00", "Seven-day boundary record"),
            (date.fromordinal(today.toordinal() - 7), "40.00", "Outside seven days"),
        )
        for expense_date, amount, description in dates_and_amounts:
            self._submit_expense(
                self._base_expense(
                    amount=amount,
                    expense_date=expense_date.isoformat(),
                    description=description,
                )
            )

        for period in ("today", "yesterday", "last7"):
            with self.subTest(period=period):
                response = self.client.get(f"/expenses/add?date_period={period}")
                body = response.get_data(as_text=True)
                self.assertEqual(response.status_code, 200)
                self.assertIn(f'data-date-period="{period}" aria-pressed="true"', body)
                self.assertNotIn("add-expense-overview", body)
                self.assertNotIn("expense-date-analytics", body)
                self.assertNotIn('class="records-section"', body)

        analytics = self.client.get("/analytics?date_period=last7")
        analytics_body = analytics.get_data(as_text=True)
        self.assertEqual(analytics.status_code, 200)
        self.assertIn("₹60.00", analytics_body)
        self.assertIn("Last 7 Days", analytics_body)
        self.assertIn("Category-wise distribution", analytics_body)

    def test_add_page_custom_date_filter_selects_calendar_without_extra_panels(self):
        today = date.today()
        yesterday = date.fromordinal(today.toordinal() - 1)
        self._submit_expense(
            self._base_expense(amount="12.00", expense_date=today.isoformat(), description="Today only")
        )
        self._submit_expense(
            self._base_expense(amount="18.00", expense_date=yesterday.isoformat(), description="Custom day")
        )

        response = self.client.get(
            f"/expenses/add?date_period=custom&date={yesterday.isoformat()}"
        )
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('class="date-picker-option is-active"', body)
        self.assertIn('data-date-period="today" aria-pressed="false"', body)
        self.assertIn(f'name="expense_date" value="{yesterday.isoformat()}"', body)
        self.assertIn(
            f'id="custom-expense-date" type="date" value="{yesterday.isoformat()}"',
            body,
        )
        self.assertNotIn("add-expense-overview", body)
        self.assertNotIn("expense-date-analytics", body)
        self.assertNotIn('class="records-section"', body)

        analytics = self.client.get(
            f"/analytics?date_period=custom&date={yesterday.isoformat()}"
        )
        analytics_body = analytics.get_data(as_text=True)
        self.assertEqual(analytics.status_code, 200)
        self.assertIn("₹18.00", analytics_body)
        self.assertIn(yesterday.isoformat(), analytics_body)
        self.assertIn("Category-wise distribution", analytics_body)

    def test_expenses_date_filter_defaults_to_today_and_rejects_invalid_custom_date(self):
        today = date.today().isoformat()
        response = self.client.get("/expenses/add")
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('data-date-period="today" aria-pressed="true"', body)
        self.assertIn(
            f'id="custom-expense-date" type="date" value="{today}" max="{today}"',
            body,
        )

        response = self.client.get("/expenses/add?date_period=custom&date=not-a-date")
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Choose a valid date no later than today.", body)
        self.assertIn('data-date-period="today" aria-pressed="true"', body)

        future_date = date.fromordinal(date.today().toordinal() + 1).isoformat()
        response = self.client.get(
            f"/expenses/add?date_period=custom&date={future_date}"
        )
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Choose a valid date no later than today.", body)
        self.assertIn('data-date-period="today" aria-pressed="true"', body)
        self.assertIn(f'value="{today}"', body)

    def test_analytics_rejects_future_month_and_year(self):
        tomorrow = date.today().replace(day=1)
        future_year = tomorrow.year + 1
        future_month = tomorrow.month + 1 if tomorrow.month < 12 else 1

        response = self.client.get(f"/analytics?year={future_year}&month=1")
        self.assertEqual(response.status_code, 200)
        self.assertIn("current month and year", response.get_data(as_text=True))

        response = self.client.get(f"/analytics?year={date.today().year}&month={date.today().month + 1}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("current month and year", response.get_data(as_text=True))

    def test_analytics_compares_selected_month_with_its_previous_month(self):
        today = date.today()
        comparison_month = today.month - 2
        comparison_year = today.year
        if comparison_month <= 0:
            comparison_month += 12
            comparison_year -= 1
        comparison_date = date(comparison_year, comparison_month, 1)

        previous_month = comparison_month - 1 or 12
        previous_year = comparison_year - 1 if comparison_month == 1 else comparison_year
        previous_date = date(previous_year, previous_month, 1)

        self._submit_expense(
            self._base_expense(
                amount="90.00",
                expense_date=comparison_date.isoformat(),
                description="Selected comparison month",
            )
        )
        self._submit_expense(
            self._base_expense(
                amount="30.00",
                expense_date=previous_date.isoformat(),
                description="Previous comparison month",
            )
        )

        response = self.client.get(
            f"/analytics?comparison_month={comparison_year:04d}-{comparison_month:02d}"
        )
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="comparison_month" type="month"', body)
        self.assertIn(f"{comparison_date.strftime('%B')} {comparison_year} compared with", body)
        self.assertIn("₹90.00", body)
        self.assertIn("₹30.00", body)
        self.assertNotIn("Selected Period Spending", body)
        self.assertNotIn("Highest Spending Category", body)
        self.assertNotIn("Average Expense Value", body)

        invalid_response = self.client.get("/analytics?comparison_month=not-a-month")
        self.assertIn(
            "Choose a valid comparison month up to the current month.",
            invalid_response.get_data(as_text=True),
        )

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
                "SELECT category, category_id FROM expenses ORDER BY id"
            ).fetchall()
            categories = connection.execute("SELECT name FROM categories").fetchall()
        self.assertEqual(len(expenses), 2)
        self.assertEqual(len(categories), 1)
        self.assertEqual([row["category"] for row in expenses], ["Food", "Food"])
        self.assertEqual(expenses[0]["category_id"], expenses[1]["category_id"])

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