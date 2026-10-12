import os
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

import httpx
from groq import APIStatusError


_test_database_directory = tempfile.TemporaryDirectory()
os.environ["EXPENSE_TRACKER_DB"] = str(
    Path(_test_database_directory.name) / "chat-tests.sqlite3"
)
os.environ["EXPENSE_TRACKER_SECRET"] = "chat-test-secret-key"

from backend.app import app, database_connection  # noqa: E402
from backend.services.ai_service import (  # noqa: E402
    AIConfigurationError,
    AIProviderError,
    generate_response,
)
from backend.services.chat_service import answer_financial_question  # noqa: E402
from backend.services.config import get_ai_configuration, get_missing_ai_configuration  # noqa: E402
from backend.services.intent_service import detect_intent  # noqa: E402


class ChatAssistantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        suffix = uuid4().hex[:8]
        with database_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (f"assistant_{suffix}", "unused", "Professional"),
            )
            cls.user_id = cursor.lastrowid
            cursor = connection.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (f"other_{suffix}", "unused", "Professional"),
            )
            other_user_id = cursor.lastrowid
            cursor = connection.execute(
                "INSERT INTO categories (user_id, name, normalized_name) VALUES (?, ?, ?)",
                (cls.user_id, "Education", "education"),
            )
            cls.education_id = cursor.lastrowid
            cursor = connection.execute(
                "INSERT INTO categories (user_id, name, normalized_name) VALUES (?, ?, ?)",
                (cls.user_id, "Food & Dining", "food dining"),
            )
            food_id = cursor.lastrowid
            cursor = connection.execute(
                "INSERT INTO categories (user_id, name, normalized_name) VALUES (?, ?, ?)",
                (other_user_id, "Education", "education"),
            )
            other_education_id = cursor.lastrowid
            connection.executemany(
                "INSERT INTO expenses (user_id, amount, category, expense_date, description, category_id) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (cls.user_id, "1000.00", "Education", "2026-10-08", "Books", cls.education_id),
                    (cls.user_id, "200.00", "Food & Dining", "2026-10-09", "Lunch", food_id),
                    (cls.user_id, "800.00", "Education", "2026-09-08", "Course", cls.education_id),
                    (other_user_id, "9999.00", "Education", "2026-10-08", "Private", other_education_id),
                ],
            )
            connection.execute(
                "INSERT INTO budgets (user_id, month, year, budget_amount) VALUES (?, ?, ?, ?)",
                (cls.user_id, 10, 2026, "1500.00"),
            )

    def test_intent_detection_covers_five_intents_and_rejects_mutations(self):
        categories = [{"id": self.education_id, "name": "Education"}]
        self.assertEqual(
            detect_intent("How much did I spend this month?", categories, date(2026, 10, 10))["intent"],
            "TOTAL_SPENDING",
        )
        self.assertEqual(
            detect_intent("How much on Education?", categories, date(2026, 10, 10))["intent"],
            "CATEGORY_SPENDING",
        )
        self.assertEqual(
            detect_intent("Show my top 5 expenses", categories, date(2026, 10, 10))["intent"],
            "TOP_EXPENSES",
        )
        self.assertEqual(
            detect_intent("How much budget is remaining?", categories, date(2026, 10, 10))["intent"],
            "BUDGET_STATUS",
        )
        self.assertEqual(
            detect_intent("Compare October with September", categories, date(2026, 10, 10))["intent"],
            "MONTH_COMPARISON",
        )
        comparison = detect_intent(
            "Did I spend more this month than last month?", categories, date(2026, 10, 10)
        )
        self.assertEqual(comparison["periods"], [(2026, 10), (2026, 9)])
        year_boundary = detect_intent(
            "Compare January with December", categories, date(2026, 10, 10)
        )
        self.assertEqual(year_boundary["periods"], [(2026, 1), (2025, 12)])
        self.assertEqual(
            detect_intent("Delete my expenses", categories, date(2026, 10, 10))["intent"],
            "READ_ONLY_REFUSAL",
        )
        self.assertEqual(
            detect_intent("What is the weather?", categories, date(2026, 10, 10))["intent"],
            "UNSUPPORTED",
        )
        self.assertEqual(
            detect_intent("How much did I spend on Travel?", categories, date(2026, 10, 10))["intent"],
            "CATEGORY_NOT_FOUND",
        )
        self.assertEqual(
            detect_intent(
                "Which category has highest spending this month?",
                categories,
                date(2026, 10, 10),
            )["intent"],
            "CATEGORY_SPENDING",
        )
        overall = detect_intent(
            "Can I know how much did I spend this month and on what categories?",
            categories,
            date(2026, 10, 10),
        )
        self.assertEqual(overall["intent"], "TOTAL_SPENDING")
        self.assertTrue(overall["include_category_breakdown"])

    def test_data_context_contains_only_the_authenticated_users_summaries(self):
        contexts = []
        answer = answer_financial_question(
            self.user_id,
            "How much did I spend on Education this month?",
            date(2026, 10, 10),
            response_generator=lambda _message, context: contexts.append(context) or "You spent ₹1,000.",
        )

        self.assertEqual(answer, "You spent ₹1,000.")
        self.assertEqual(contexts[0]["category"], "Education")
        self.assertEqual(contexts[0]["total"], "1000.00")
        self.assertNotIn("Books", str(contexts[0]))
        self.assertNotIn("9999", str(contexts[0]))

    def test_top_expenses_budget_and_month_comparison_have_summarized_context(self):
        contexts = []
        generate = lambda _message, context: contexts.append(context) or "Answer"
        answer_financial_question(
            self.user_id, "Show my top 2 expenses this month", date(2026, 10, 10), generate
        )
        self.assertEqual([item["amount"] for item in contexts[-1]["expenses"]], ["1000.00", "200.00"])

        answer_financial_question(
            self.user_id, "How much budget is remaining?", date(2026, 10, 10), generate
        )
        self.assertEqual(contexts[-1]["budget"], "1500.00")
        self.assertEqual(contexts[-1]["spent"], "1200.00")
        self.assertEqual(contexts[-1]["remaining"], "300.00")
        self.assertEqual(contexts[-1]["utilization_percent"], "80.0")

        answer_financial_question(
            self.user_id, "Compare October with September", date(2026, 10, 10), generate
        )
        self.assertEqual(contexts[-1]["periods"][0]["total"], "1200.00")
        self.assertEqual(contexts[-1]["periods"][1]["total"], "800.00")
        self.assertEqual(contexts[-1]["percentage_change"], "50.0")

    def test_total_spending_category_question_includes_monthly_category_breakdown(self):
        contexts = []
        answer_financial_question(
            self.user_id,
            "Can I know how much did I spend this month and on what categories?",
            date(2026, 10, 10),
            lambda _message, context: contexts.append(context) or "Summary",
        )
        self.assertEqual(contexts[0]["intent"], "TOTAL_SPENDING")
        self.assertEqual(contexts[0]["total"], "1200.00")
        self.assertEqual(
            contexts[0]["category_breakdown"],
            [
                {"category": "Education", "total": "1000.00"},
                {"category": "Food & Dining", "total": "200.00"},
            ],
        )

    def test_mutation_and_unsupported_requests_never_call_the_model(self):
        generate = Mock()
        refusal = answer_financial_question(
            self.user_id, "Update my budget to 5000", date(2026, 10, 10), generate
        )
        unsupported = answer_financial_question(
            self.user_id, "Tell me a joke", date(2026, 10, 10), generate
        )

        self.assertIn("read-only", refusal)
        self.assertIn("total spending", unsupported)
        generate.assert_not_called()

    def test_chat_endpoint_requires_authentication_and_csrf(self):
        client = app.test_client()
        unauthenticated = client.post("/api/chat", json={"message": "How much did I spend?"})
        self.assertEqual(unauthenticated.status_code, 401)

        with client.session_transaction() as session:
            session["user_id"] = self.user_id
            session["csrf_token"] = "valid-test-csrf"
        rejected = client.post("/api/chat", json={"message": "How much did I spend?"})
        self.assertEqual(rejected.status_code, 400)

        with patch("backend.services.chat_service.generate_response", return_value="You spent ₹1,200."):
            accepted = client.post(
                "/api/chat",
                json={"message": "How much did I spend this month?"},
                headers={"X-CSRF-Token": "valid-test-csrf"},
            )
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(accepted.get_json(), {"response": "You spent ₹1,200."})

    def test_chat_endpoint_surfaces_provider_validation_details(self):
        client = app.test_client()
        with client.session_transaction() as session:
            session["user_id"] = self.user_id
            session["csrf_token"] = "valid-test-csrf"

        with patch(
            "backend.services.chat_service.generate_response",
            side_effect=AIProviderError(
                "AI provider returned HTTP 400: model is not available",
                status_code=400,
            ),
        ):
            response = client.post(
                "/api/chat",
                json={"message": "How much did I spend this month?"},
                headers={"X-CSRF-Token": "valid-test-csrf"},
            )

        self.assertEqual(response.status_code, 502)
        self.assertIn("HTTP 400", response.get_json()["error"])
        self.assertIn("model is not available", response.get_json()["error"])

    def test_assistant_ui_is_available_only_in_authenticated_app_shell(self):
        client = app.test_client()
        public_page = client.get("/login")
        self.assertNotIn(b"Ask SpendWise AI", public_page.data)

        with client.session_transaction() as session:
            session["user_id"] = self.user_id
            session["csrf_token"] = "valid-test-csrf"
        dashboard = client.get("/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn(b"Ask SpendWise AI", dashboard.data)
        self.assertIn(b'data-api-url="/api/chat"', dashboard.data)
        self.assertIn(b'data-ai-dialog', dashboard.data)

    def test_provider_uses_official_groq_sdk_call_and_logs_no_credentials(self):
        completion = Mock()
        completion.choices = [Mock(message=Mock(content="You spent ₹0.00."))]
        client = Mock()
        client.chat.completions.create.return_value = completion
        with (
            patch(
                "backend.services.ai_service.get_ai_configuration",
                return_value={"api_key": "test-secret", "model": "test-model"},
            ),
            patch(
                "backend.services.ai_service.get_missing_ai_configuration",
                return_value=[],
            ),
            patch("backend.services.ai_service.Groq", return_value=client) as groq_client,
            self.assertLogs("backend.services.ai_service", level="INFO") as logs,
        ):
            result = generate_response("How much did I spend?", {"total": "0.00"})

        self.assertEqual(result, "You spent ₹0.00.")
        groq_client.assert_called_once_with(api_key="test-secret")
        call = client.chat.completions.create.call_args
        self.assertEqual(call.kwargs["model"], "test-model")
        self.assertEqual(
            [item["role"] for item in call.kwargs["messages"]],
            ["system", "user"],
        )
        self.assertTrue(
            all(isinstance(item["content"], str) for item in call.kwargs["messages"])
        )
        self.assertEqual(call.kwargs["temperature"], 0.1)
        self.assertEqual(call.kwargs["max_tokens"], 350)
        log_output = "\n".join(logs.output)
        self.assertIn("provider=groq_sdk", log_output)
        self.assertIn("status_code=200", log_output)
        self.assertIn("duration_ms=", log_output)
        self.assertNotIn("test-secret", log_output)

    def test_provider_http_400_surfaces_sanitized_sdk_error(self):
        api_key = "groq-test-api-key"
        body = {"error": {"message": f"Model does not exist; token {api_key}"}}
        response = httpx.Response(
            400,
            request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
        )
        error = APIStatusError("Bad Request", response=response, body=body)
        with (
            patch(
                "backend.services.ai_service.get_ai_configuration",
                return_value={"api_key": api_key, "model": "invalid-model"},
            ),
            patch(
                "backend.services.ai_service.get_missing_ai_configuration",
                return_value=[],
            ),
            patch("backend.services.ai_service.Groq", side_effect=error),
            self.assertLogs("backend.services.ai_service", level="WARNING") as logs,
        ):
            with self.assertRaises(AIProviderError) as raised:
                generate_response("A safe test question", {"total": "0.00"})

        log_output = "\n".join(logs.output)
        self.assertEqual(raised.exception.status_code, 400)
        self.assertIn("HTTP 400", str(raised.exception))
        self.assertIn("Model does not exist", str(raised.exception))
        self.assertNotIn(api_key, str(raised.exception))
        self.assertIn("status_code=400", log_output)
        self.assertIn("invalid-model", log_output)
        self.assertIn("[REDACTED]", log_output)
        self.assertNotIn(api_key, log_output)

    def test_provider_http_403_logs_sanitized_sdk_response_body(self):
        api_key = "groq-test-api-key"
        message = "The site owner has blocked access based on your browser's signature."
        response_body = {"error": {"message": message, "type": "browser_signature_banned"}}
        response = httpx.Response(
            403,
            request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
        )
        error = APIStatusError("Forbidden", response=response, body=response_body)
        with (
            patch(
                "backend.services.ai_service.get_ai_configuration",
                return_value={"api_key": api_key, "model": "test-model"},
            ),
            patch(
                "backend.services.ai_service.get_missing_ai_configuration",
                return_value=[],
            ),
            patch("backend.services.ai_service.Groq", side_effect=error),
            self.assertLogs("backend.services.ai_service", level="WARNING") as logs,
        ):
            with self.assertRaises(AIProviderError) as raised:
                generate_response("A safe test question", {"total": "0.00"})

        log_output = "\n".join(logs.output)
        self.assertEqual(raised.exception.status_code, 403)
        self.assertIn(message, str(raised.exception))
        self.assertIn("status_code=403", log_output)
        self.assertIn(message, log_output)
        self.assertIn("browser_signature_banned", log_output)
        self.assertNotIn(api_key, log_output)

    def test_groq_configuration_loads_from_dotenv_and_reports_missing_values(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / ".env").write_text(
                "GROQ_API_KEY=dotenv-test-key\n"
                "GROQ_MODEL=llama-3.3-70b-versatile\n",
                encoding="utf-8",
            )
            with (
                patch.dict(os.environ, {}, clear=True),
                patch("backend.services.config.PROJECT_ROOT", root),
            ):
                self.assertEqual(
                    get_ai_configuration(),
                    {
                        "api_key": "dotenv-test-key",
                        "model": "llama-3.3-70b-versatile",
                    },
                )
                self.assertEqual(get_missing_ai_configuration(), [])

            with (
                patch.dict(os.environ, {"GROQ_API_KEY": "", "GROQ_MODEL": ""}, clear=True),
                patch("backend.services.config.PROJECT_ROOT", root / "without-env"),
            ):
                self.assertEqual(
                    get_missing_ai_configuration(),
                    ["GROQ_API_KEY", "GROQ_MODEL"],
                )
                with patch(
                    "backend.services.ai_service.get_missing_ai_configuration",
                    return_value=["GROQ_API_KEY", "GROQ_MODEL"],
                ):
                    with self.assertRaisesRegex(
                        AIConfigurationError,
                        "GROQ_API_KEY, GROQ_MODEL",
                    ):
                        generate_response("How much did I spend?", {"total": "0.00"})


if __name__ == "__main__":
    unittest.main()
