from datetime import date

from flask import Blueprint, current_app, jsonify, request, session

from backend.services.ai_service import AIConfigurationError, AIProviderError
from backend.services.chat_service import answer_financial_question
from database.database import database_connection


chat_blueprint = Blueprint("chat_api", __name__)


@chat_blueprint.post("/api/chat")
def chat():
    user_id = session.get("user_id")
    if user_id is None:
        return jsonify(error="Sign in to use SpendWise AI."), 401
    with database_connection() as connection:
        user = connection.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        session.clear()
        return jsonify(error="Your session has expired. Sign in again."), 401

    if not request.is_json:
        return jsonify(error="Send a JSON message to SpendWise AI."), 415
    payload = request.get_json(silent=True)
    message = payload.get("message") if isinstance(payload, dict) else None
    if not isinstance(message, str) or not message.strip() or len(message) > 1000:
        return jsonify(error="Enter a question of 1 to 1,000 characters."), 400

    try:
        response = answer_financial_question(user_id, message.strip(), date.today())
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
    return jsonify(response=response)
