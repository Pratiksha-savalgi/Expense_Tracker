"""Allow-list and validate model-selected SpendWise tool requests."""

import re
from datetime import date
from decimal import Decimal, InvalidOperation

from backend.services.config import feature_enabled


PERIODS = ("this_month", "last_month", "this_year", "last_year", "all_time")
MAX_TOOL_ARGUMENTS = 16


class ToolValidationError(ValueError):
    """Raised when a model requests an unknown or invalid tool operation."""


def canonicalize_amount(value):
    if isinstance(value, bool) or value is None:
        raise ToolValidationError("Enter a valid positive amount.")
    if isinstance(value, int):
        value = str(value)
    elif isinstance(value, float):
        try:
            value = format(Decimal(str(value)).quantize(Decimal("0.01")), "f")
        except InvalidOperation as error:
            raise ToolValidationError("Enter a valid positive amount.") from error
    if not isinstance(value, str):
        raise ToolValidationError("Enter a valid positive amount.")
    cleaned = value.strip().replace("₹", "").replace(",", "").replace(" ", "")
    cleaned = re.sub(r"(?i)^(?:rs\.?|inr)", "", cleaned)
    if not re.fullmatch(r"(?:\d+(?:\.\d{1,2})?|\.\d{1,2})", cleaned):
        raise ToolValidationError("Enter an amount with at most two decimal places.")
    try:
        amount = Decimal(cleaned)
    except InvalidOperation as error:
        raise ToolValidationError("Enter a valid positive amount.") from error
    if not amount.is_finite() or amount <= 0:
        raise ToolValidationError("Enter a valid positive amount.")
    return format(amount, "f")


def validate_tool_request(name, arguments, allowed_tools):
    if name not in allowed_tools:
        raise ToolValidationError("That assistant tool is not available.")
    if not isinstance(arguments, dict) or len(arguments) > MAX_TOOL_ARGUMENTS:
        raise ToolValidationError("The assistant returned invalid tool arguments.")
    if "user_id" in arguments or any(key not in allowed_tools[name]["parameters"] for key in arguments):
        raise ToolValidationError("The assistant returned unsupported tool arguments.")

    schema = allowed_tools[name]["parameters"]
    validated = {}
    for key, value in arguments.items():
        rule = schema[key]
        if key == "amount":
            validated[key] = canonicalize_amount(value)
            continue
        if rule["type"] == "integer" and isinstance(value, str) and re.fullmatch(r"-?\d+", value.strip()):
            value = int(value.strip())
        if rule["type"] == "string":
            if not isinstance(value, str) or len(value) > rule.get("maxLength", 200):
                raise ToolValidationError(f"Invalid {key} value.")
            if "enum" in rule and value not in rule["enum"]:
                raise ToolValidationError(f"Invalid {key} value.")
            if rule.get("format") == "date":
                try:
                    parsed = date.fromisoformat(value)
                    if parsed.isoformat() != value or parsed > date.today():
                        raise ValueError
                except ValueError as error:
                    raise ToolValidationError(f"Invalid {key} date.") from error
        elif rule["type"] == "integer":
            if isinstance(value, bool) or not isinstance(value, int):
                raise ToolValidationError(f"Invalid {key} value.")
            if not rule.get("minimum", 1) <= value <= rule.get("maximum", 9999):
                raise ToolValidationError(f"Invalid {key} value.")
        elif rule["type"] == "number":
            if not isinstance(value, (float, int)) or isinstance(value, bool):
                raise ToolValidationError(f"Invalid {key} value.")
            if not rule.get("minimum", 0) < value <= rule.get("maximum", 1_000_000_000):
                raise ToolValidationError(f"Invalid {key} value.")
        validated[key] = value

    required = set(allowed_tools[name]["required"])
    if not required.issubset(validated):
        raise ToolValidationError("The assistant omitted required tool arguments.")
    if "period" in validated and validated["period"] not in PERIODS:
        raise ToolValidationError("Unsupported financial period.")
    if "amount" in validated:
        amount = validated["amount"]
        if not re.fullmatch(r"(?:\d+(?:\.\d{1,2})?|\.\d{1,2})", str(amount)):
            raise ToolValidationError("Enter an amount with at most two decimal places.")
    return validated


def crud_agent_enabled():
    return feature_enabled("ENABLE_CRUD_AGENT", default=False)
