from flask import Blueprint, current_app, jsonify, request, session

from backend.services.ai_service import AIConfigurationError, AIProviderError
from backend.services.action_service import cancel_action, confirm_action, get_pending_action
from backend.services.assistant_policy import ToolValidationError
from backend.services.chat_service import run_assistant
from backend.services.config import feature_enabled
from backend.services.memory_service import get_conversation_history
from database.database import database_connection


chat_blueprint = Blueprint("chat_api", __name__)


@chat_blueprint.route("/api/chat", methods=["GET", "POST"])
def chat():
    user_id = session.get("user_id")
    if user_id is None:
        return jsonify(error="Sign in to use SpendWise AI."), 401
    with database_connection() as connection:
        user = connection.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        session.clear()
        return jsonify(error="Your session has expired. Sign in again."), 401

    if request.method == "GET":
        response = jsonify(
            messages=get_conversation_history(user_id),
            pending_action=get_pending_action(user_id),
        )
        response.headers["Cache-Control"] = "no-store"
        return response

    if not request.is_json:
        return jsonify(error="Send a JSON message to SpendWise AI."), 415
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Send a JSON message to SpendWise AI."), 400

    if "confirmation_id" in payload:
        if not feature_enabled("ENABLE_CRUD_AGENT", default=False):
            return jsonify(error="Assistant changes are disabled."), 403
        decision = payload.get("decision")
        if set(payload) - {"confirmation_id", "decision"} or decision not in {"confirm", "cancel"}:
            return jsonify(error="Choose whether to confirm or cancel the proposed change."), 400
        try:
            response = (
                confirm_action(user_id, payload["confirmation_id"])
                if decision == "confirm"
                else cancel_action(user_id, payload["confirmation_id"])
            )
        except ToolValidationError as error:
            return jsonify(error=str(error)), 400
        return jsonify(response=response)

    message = payload.get("message")
    if not isinstance(message, str) or not message.strip() or len(message) > 1000:
        return jsonify(error="Enter a question of 1 to 1,000 characters."), 400

    try:
        result = run_assistant(user_id, message.strip())
    except ToolValidationError as error:
        return jsonify(error=str(error)), 400
    except AIConfigurationError as error:
        return jsonify(
            error=(
                f"SpendWise AI configuration error: {error}"
            )
        ), 503
    except AIProviderError as error:
        current_app.logger.warning(
            "SpendWise AI request failed status_code=%s",
            error.status_code or "connection_error",
        )
        return jsonify(error=str(error)), 502
    return jsonify(**result)
