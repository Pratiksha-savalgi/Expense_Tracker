import calendar
import json
import logging
from datetime import date

from backend.services.agent_orchestrator import (
    CRUD_DISABLED_RESPONSE,
    MUTATION_TOOLS,
    build_focus,
    infer_tool_call,
    is_category_ranking,
    normalize_tool_arguments,
)
from backend.services.ai_service import (
    AIProviderError,
    generate_response,
    generate_tool_answer,
    request_tool_call,
)
from backend.services.assistant_policy import ToolValidationError, crud_agent_enabled
from backend.services.budget_service import build_budget_context, build_comparison_context
from backend.services.config import feature_enabled
from backend.services.expense_service import build_expense_context, get_user_categories
from backend.services.intent_service import detect_intent
from backend.services.memory_service import (
    get_conversation_focus,
    get_conversation_history,
    save_conversation_focus,
    save_conversation_turn,
)
from backend.services.response_composer import compose_response, format_inr, looks_like_report
from backend.services.tool_registry import execute_tool


logger = logging.getLogger("spendwise.agent")


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


def run_assistant(user_id, message):
    if not feature_enabled("ENABLE_RETRIEVAL_AGENT", default=True):
        _log_decision(
            message,
            None,
            None,
            "PASS",
            "ENABLE_RETRIEVAL_AGENT is disabled, so the legacy intent flow handled this request.",
        )
        return {"response": answer_financial_question(user_id, message)}
    if not feature_enabled("ENABLE_TOOL_CALLING", default=True):
        _log_decision(
            message,
            None,
            None,
            "PASS",
            "ENABLE_TOOL_CALLING is disabled, so the legacy intent flow handled this request.",
        )
        return {"response": answer_financial_question(user_id, message)}

    history = get_conversation_history(user_id)
    focus = get_conversation_focus(user_id)
    fallback_reason = None
    validation = "PASS"
    selected = request_tool_call(message, history, focus)
    model_selected = selected is not None
    if selected is None:
        fallback_reason = "The model returned no tool call."
        inferred = infer_tool_call(message, user_id, focus)
        if inferred is None:
            response = (
                "I can help explain your SpendWise spending and budgets. "
                "Please ask a clear question about your records."
            )
            _log_decision(message, None, None, "FAIL", fallback_reason)
            save_conversation_turn(user_id, message, response)
            return {"response": response}
        if inferred["type"] == "reply":
            fallback_reason = inferred.get("fallback_reason") or fallback_reason
            _log_decision(message, None, None, "PASS", fallback_reason)
            save_conversation_turn(user_id, message, inferred["response"])
            return {"response": inferred["response"]}
        tool_name = inferred["name"]
        arguments = inferred["arguments"]
        messages = assistant_message = call_id = None
    else:
        messages, assistant_message, call_id, tool_name, arguments = selected

    if is_category_ranking(message) and tool_name != "get_category_totals":
        tool_name = "get_category_totals"
        arguments = {}
        note = "Routed a category-ranking question to get_category_totals."
        fallback_reason = f"{fallback_reason}; {note}" if fallback_reason else note

    prepared = normalize_tool_arguments(tool_name, arguments, message, user_id, focus)
    if prepared != arguments:
        note = "Normalized incomplete or unspoken period, amount, date, or category arguments."
        fallback_reason = f"{fallback_reason}; {note}" if fallback_reason else note
        arguments = prepared

    if tool_name in MUTATION_TOOLS and not crud_agent_enabled():
        fallback_reason = (
            "ENABLE_CRUD_AGENT is disabled, so the selected mutation tool was not executed."
        )
        _log_decision(message, tool_name, arguments, "FAIL", fallback_reason)
        save_conversation_turn(user_id, message, CRUD_DISABLED_RESPONSE)
        return {"response": CRUD_DISABLED_RESPONSE}

    try:
        tool_result = execute_tool(tool_name, arguments, user_id)
    except ToolValidationError:
        validation = "FAIL"
        inferred = infer_tool_call(message, user_id, focus)
        if inferred and inferred.get("type") == "tool":
            tool_name = inferred["name"]
            arguments = normalize_tool_arguments(
                tool_name, inferred["arguments"], message, user_id, focus
            )
            note = "Retried with an orchestrator-selected tool after validation failed."
            fallback_reason = f"{fallback_reason}; {note}" if fallback_reason else note
            try:
                tool_result = execute_tool(tool_name, arguments, user_id)
                validation = "PASS"
            except ToolValidationError:
                _log_decision(message, tool_name, arguments, "FAIL", fallback_reason)
                raise
            except (TypeError, ValueError) as retry_error:
                _log_decision(message, tool_name, arguments, "FAIL", fallback_reason)
                raise ToolValidationError(
                    "I couldn't validate that request. Please clarify the period or details."
                ) from retry_error
        else:
            _log_decision(message, tool_name, arguments, "FAIL", fallback_reason)
            raise
    except (TypeError, ValueError) as error:
        validation = "FAIL"
        note = f"Tool execution rejected the arguments ({error}). Retried with the current month."
        fallback_reason = f"{fallback_reason}; {note}" if fallback_reason else note
        arguments = normalize_tool_arguments(tool_name, {}, message, user_id, None)
        try:
            tool_result = execute_tool(tool_name, arguments, user_id)
            validation = "PASS"
        except (TypeError, ValueError) as retry_error:
            _log_decision(message, tool_name, arguments, "FAIL", fallback_reason)
            raise ToolValidationError(
                "I couldn't validate that request. Please clarify the period or details."
            ) from retry_error

    _log_decision(message, tool_name, arguments, validation, fallback_reason, tool_result)

    if tool_result.get("pending_confirmation"):
        response = _format_pending_action(tool_result)
        save_conversation_turn(user_id, message, response)
        return {
            "response": response,
            "pending_action": {
                "confirmation_id": tool_result["confirmation_id"],
                "details": tool_result["details"],
            },
        }

    response = _final_response(
        messages,
        assistant_message,
        call_id,
        tool_name,
        arguments,
        tool_result,
        model_selected,
    )
    if tool_name not in MUTATION_TOOLS:
        save_conversation_focus(user_id, build_focus(tool_name, arguments, tool_result))
    save_conversation_turn(user_id, message, response)
    return {"response": response}


def _final_response(messages, assistant_message, call_id, tool_name, arguments, tool_result, model_selected):
    if not model_selected:
        return compose_response(tool_name, tool_result)
    try:
        model_answer = generate_tool_answer(
            messages,
            _retarget_tool_message(assistant_message, call_id, tool_name, arguments),
            call_id,
            tool_name,
            tool_result,
        )
    except AIProviderError:
        logger.warning(
            "Final phrasing call failed for tool %s; using a conversational summary.",
            tool_name,
        )
        return compose_response(tool_name, tool_result)
    if looks_like_report(model_answer):
        logger.warning(
            "Fallback Reason:\nReplaced report-style model text with a conversational summary."
        )
        return compose_response(tool_name, tool_result)
    return model_answer


def _retarget_tool_message(assistant_message, call_id, tool_name, arguments):
    message = dict(assistant_message or {})
    message["role"] = "assistant"
    message["tool_calls"] = [{
        "id": call_id,
        "type": "function",
        "function": {
            "name": tool_name,
            "arguments": json.dumps(arguments, ensure_ascii=False),
        },
    }]
    return message


def _log_decision(message, tool_name, arguments, validation, fallback_reason, retrieval=None):
    flags = (
        f"ENABLE_RETRIEVAL_AGENT={int(feature_enabled('ENABLE_RETRIEVAL_AGENT', default=True))} "
        f"ENABLE_TOOL_CALLING={int(feature_enabled('ENABLE_TOOL_CALLING', default=True))} "
        f"ENABLE_CRUD_AGENT={int(crud_agent_enabled())}"
    )
    retrieval_text = _compact_retrieval(retrieval) if retrieval is not None else "(none)"
    logger.warning(
        "Feature Flags:\n%s\n\nMessage:\n%s\n\nSelected Tool:\n%s\n\nTool Arguments:\n%s\n\n"
        "Validation Result:\n%s\n\nFallback Reason:\n%s\n\nRetrieval Result:\n%s",
        flags,
        message,
        tool_name or "(none)",
        json.dumps(arguments or {}, ensure_ascii=False, sort_keys=True, default=str),
        validation,
        fallback_reason or "(none)",
        retrieval_text,
    )


def _compact_retrieval(result):
    if not isinstance(result, dict):
        return str(result)[:1000]
    compact = {}
    for key, value in result.items():
        if key == "confirmation_id":
            compact[key] = "[redacted]"
            continue
        if isinstance(value, list):
            compact[key] = value[:5]
        elif isinstance(value, dict):
            nested = dict(value)
            if isinstance(nested.get("categories"), list):
                nested["categories"] = nested["categories"][:5]
            compact[key] = nested
        else:
            compact[key] = value
    return json.dumps(compact, ensure_ascii=False, default=str)[:2000]


def _display_date(iso_date):
    if iso_date == date.today().isoformat():
        return "Today"
    return iso_date or ""


def _format_pending_action(pending):
    details = pending["details"]
    action = details["type"]
    if action == "create_expense":
        lines = [
            "I found a new expense:",
            "",
            f"Amount: {format_inr(details.get('amount'))}",
            f"Category: {details.get('category')}",
            f"Date: {_display_date(details.get('date'))}",
        ]
        if details.get("description"):
            lines.append(f"Description: {details['description']}")
        lines.extend(["", "Would you like me to save this expense?"])
        return "\n".join(lines)
    if action == "update_expense":
        before, after = details["before"], details["after"]
        lines = [
            f"I can update expense #{details['expense_id']}:",
            "",
            f"Amount: {format_inr(before['amount'])} → {format_inr(after['amount'])}",
            f"Category: {before['category']} → {after['category']}",
            f"Date: {_display_date(before['date'])} → {_display_date(after['date'])}",
        ]
        if before.get("description") != after.get("description"):
            lines.append(
                f"Description: {before.get('description', '')} → {after.get('description', '')}"
            )
        lines.extend(["", "Would you like me to save this change?"])
        return "\n".join(lines)
    if action == "delete_expense":
        before = details["before"]
        lines = [
            "I found this expense:",
            "",
            f"Amount: {format_inr(before['amount'])}",
            f"Category: {before['category']}",
            f"Date: {_display_date(before['date'])}",
        ]
        if before.get("description"):
            lines.append(f"Description: {before['description']}")
        lines.extend(["", "Would you like me to delete this expense?"])
        return "\n".join(lines)

    month_label = f"{calendar.month_name[details['month']]} {details['year']}"
    if action == "delete_budget":
        return (
            f"I can delete your {month_label} budget of {format_inr(details.get('before'))}.\n\n"
            "Would you like me to delete this budget?"
        )
    if action == "update_budget":
        return (
            f"I can update your {month_label} budget from {format_inr(details.get('before'))} "
            f"to {format_inr(details.get('after'))}.\n\n"
            "Would you like me to save this change?"
        )
    return (
        "I found a new budget:\n\n"
        f"Amount: {format_inr(details.get('after'))}\n"
        f"Month: {month_label}\n\n"
        "Would you like me to save this budget?"
    )
