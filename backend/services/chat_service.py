from datetime import date

from backend.services.ai_service import generate_response
from backend.services.budget_service import build_budget_context, build_comparison_context
from backend.services.expense_service import build_expense_context, get_user_categories
from backend.services.intent_service import detect_intent


READ_ONLY_RESPONSE = (
    "I can only answer read-only questions about your SpendWise spending and budgets. "
    "I can't make changes to your account or records."
)
UNSUPPORTED_RESPONSE = (
    "I can help with total spending, category spending, top expenses, budget status, "
    "or comparing months. Ask a question about your SpendWise data."
)


def answer_financial_question(user_id, message, today=None, response_generator=None):
    today = today or date.today()
    categories = get_user_categories(user_id)
    intent = detect_intent(message, categories, today)
    if intent["intent"] == "READ_ONLY_REFUSAL":
        return READ_ONLY_RESPONSE
    if intent["intent"] == "UNSUPPORTED":
        return UNSUPPORTED_RESPONSE
    if intent["intent"] == "CATEGORY_NOT_FOUND":
        return (
            "I couldn't find that category in your SpendWise categories. "
            "Check the category name and try again."
        )

    if intent["intent"] == "MONTH_COMPARISON":
        context = build_comparison_context(user_id, intent["periods"])
    elif intent["intent"] == "BUDGET_STATUS":
        context = build_budget_context(user_id, intent["year"], intent["month"])
    else:
        context = build_expense_context(user_id, intent)

    generate = response_generator or generate_response
    return generate(message, context)
