"""Approved read-only and feature-gated mutation tools for the assistant."""

from backend.services import retrieval_service
from backend.services.assistant_policy import PERIODS, ToolValidationError
from backend.services.config import feature_enabled
from backend.services.action_service import propose_action


def _property(kind, **options):
    return {"type": kind, **options}


_period = _property("string", enum=list(PERIODS), description="Financial period to retrieve.")
_year = _property("integer", minimum=1900, maximum=2200)
_month = _property("integer", minimum=1, maximum=12)
_limit = _property("integer", minimum=1, maximum=50)


READ_TOOLS = {
    "get_financial_summary": (retrieval_service.get_financial_summary, {"period": _period, "year": _year, "month": _month}, []),
    "get_total_spending": (
        retrieval_service.get_total_spending,
        {"period": _period, "year": _year, "month": _month, "category": _property("string", maxLength=100)},
        [],
    ),
    "get_spending_history": (retrieval_service.get_spending_history, {"period": _period, "year": _year, "month": _month}, []),
    "get_recent_expenses": (retrieval_service.get_recent_expenses, {"limit": _limit, "period": _period}, []),
    "get_top_expenses": (retrieval_service.get_top_expenses, {"limit": _limit, "period": _period, "year": _year, "month": _month}, []),
    "get_category_totals": (
        retrieval_service.get_category_totals,
        {"period": _period, "year": _year, "month": _month, "category": _property("string", maxLength=100)},
        [],
    ),
    "get_category_trends": (retrieval_service.get_category_trends, {"period": _period, "year": _year, "month": _month}, []),
    "get_budget_status": (retrieval_service.get_budget_status, {"period": _period, "year": _year, "month": _month}, []),
    "get_budget_analytics": (retrieval_service.get_budget_analytics, {"year": _year}, []),
    "get_month_comparison": (
        retrieval_service.get_month_comparison,
        {"year": _year, "month": _month, "comparison_year": _year, "comparison_month": _month},
        [],
    ),
    "get_yearly_summary": (retrieval_service.get_yearly_summary, {"year": _year}, []),
    "get_spending_patterns": (retrieval_service.get_spending_patterns, {"period": _period, "year": _year, "month": _month}, []),
}


_CRUD_SCHEMAS = {
    "create_expense": (
        {"amount": _property("string", maxLength=20), "category": _property("string", maxLength=100),
         "date": _property("string", format="date"), "description": _property("string", maxLength=500)},
        ["amount", "category"],
    ),
    "update_expense": (
        {"expense_id": _property("integer", minimum=1), "amount": _property("string", maxLength=20),
         "category": _property("string", maxLength=100), "date": _property("string", format="date"),
         "description": _property("string", maxLength=500)},
        ["expense_id"],
    ),
    "delete_expense": ({"expense_id": _property("integer", minimum=1)}, ["expense_id"]),
    "create_budget": (
        {"amount": _property("string", maxLength=20), "year": _year, "month": _month},
        ["amount", "year", "month"],
    ),
    "update_budget": (
        {"amount": _property("string", maxLength=20), "year": _year, "month": _month},
        ["amount", "year", "month"],
    ),
    "delete_budget": ({"year": _year, "month": _month}, ["year", "month"]),
}


def get_tool_specs(include_mutations=None):
    if include_mutations is None:
        include_mutations = feature_enabled("ENABLE_CRUD_AGENT", default=False)
    tools = {}
    for name, (_, properties, required) in READ_TOOLS.items():
        tools[name] = {"parameters": properties, "required": required}
    if include_mutations:
        for name, (properties, required) in _CRUD_SCHEMAS.items():
            tools[name] = {"parameters": properties, "required": required}
    return tools


def get_groq_tools(include_mutations=None):
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": _description(name),
                "parameters": {
                    "type": "object",
                    "properties": spec["parameters"],
                    "required": spec["required"],
                    "additionalProperties": False,
                },
            },
        }
        for name, spec in get_tool_specs(include_mutations).items()
    ]


def _description(name):
    descriptions = {
        "get_financial_summary": "Summarize the authenticated user's spending, budget, categories, and large purchases. Omit period to use the current month.",
        "get_total_spending": "Calculate the authenticated user's total spending. Omit period to use the current month.",
        "get_category_totals": "Retrieve user-scoped totals by spending category. Omit period to use the current month.",
        "get_spending_history": "Retrieve monthly spending history for a period.",
        "get_recent_expenses": "List recent expenses recorded by the authenticated user.",
        "get_top_expenses": "Retrieve the authenticated user's largest expenses for a period.",
        "create_expense": "Propose a new expense for confirmation. Amount and category are required. Omit date to use today.",
        "update_expense": "Propose an update to one owned expense for confirmation.",
        "delete_expense": "Propose deletion of one owned expense for confirmation.",
        "create_budget": "Propose a new monthly budget for confirmation.",
        "update_budget": "Propose a change to an existing monthly budget for confirmation.",
        "delete_budget": "Propose deletion of one monthly budget for confirmation.",
        "get_category_trends": "Compare category totals with the preceding month.",
        "get_budget_status": "Retrieve the authenticated user's monthly budget and remaining amount.",
        "get_budget_analytics": "Retrieve a year's monthly budgets and spending.",
        "get_month_comparison": "Compare two selected months of user-scoped spending.",
        "get_yearly_summary": "Summarize a calendar year's spending and monthly average.",
        "get_spending_patterns": "Describe spending totals by weekday for a period.",
    }
    return descriptions.get(name, f"Propose the {name.replace('_', ' ')} operation for authenticated-user confirmation.")


def execute_tool(name, arguments, user_id):
    specs = get_tool_specs()
    from backend.services.assistant_policy import validate_tool_request

    validated = validate_tool_request(name, arguments, specs)
    if name in READ_TOOLS:
        handler = READ_TOOLS[name][0]
        return handler(user_id, **validated)
    if name not in _CRUD_SCHEMAS:
        raise ToolValidationError("That assistant tool is not available.")
    return propose_action(user_id, name, validated)
