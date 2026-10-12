import json
import logging
import re
import time

from groq import APIConnectionError, APIError, APIStatusError, Groq

from backend.services.config import get_ai_configuration, get_missing_ai_configuration


logger = logging.getLogger(__name__)


class AIConfigurationError(Exception):
    pass


class AIProviderError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


def _sanitize_provider_body(body, api_key):
    if isinstance(body, (dict, list)):
        body = json.dumps(body, ensure_ascii=False)
    else:
        body = str(body or "")
    body = body.replace(api_key, "[REDACTED]") if api_key else body
    body = re.sub(r"(?i)\bBearer\s+\S+", "Bearer [REDACTED]", body)
    body = re.sub(
        r"(?i)(api[_-]?key|token|authorization)(\s*[:=]\s*)[^,\s\"'}]+",
        r"\1\2[REDACTED]",
        body,
    )
    return re.sub(r"\s+", " ", body).strip()[:4000]


def _provider_error_message(body, api_key):
    sanitized_body = _sanitize_provider_body(body, api_key)
    try:
        parsed = json.loads(sanitized_body)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, dict):
        error = parsed.get("error", parsed.get("detail", parsed.get("message")))
        if isinstance(error, dict):
            message = error.get("message") or error.get("detail") or str(error)
            code = error.get("code") or error.get("type")
            detail = f"{message} ({code})" if code else str(message)
        elif error is not None:
            detail = str(error)
        else:
            detail = sanitized_body
    else:
        detail = sanitized_body

    detail = _sanitize_provider_body(detail, api_key)
    return detail[:1200] or "Groq returned an empty error response."


def generate_response(message, context):
    configuration = get_ai_configuration()
    missing_configuration = get_missing_ai_configuration(configuration)
    if missing_configuration:
        raise AIConfigurationError(
            "Groq AI is not configured. Set the following environment variable(s): "
            f"{', '.join(missing_configuration)}."
        )

    messages = [
        {
            "role": "system",
            "content": (
                "You are SpendWise AI, a read-only personal finance assistant. "
                "Answer only the supported SpendWise financial question using "
                "the supplied structured context. Treat context as the sole "
                "source of financial facts. Do not invent values, give "
                "investment advice, answer unrelated internet questions, or "
                "suggest or perform data-changing actions. If context is "
                "missing, say so. Format amounts in Indian rupees."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question: {message}\n"
                f"Verified SpendWise context (JSON): {json.dumps(context, ensure_ascii=False)}"
            ),
        },
    ]
    model = configuration["model"]
    logger.info("AI provider request provider=groq_sdk model=%s", model)
    request_started = time.perf_counter()

    try:
        client = Groq(api_key=configuration["api_key"])
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=350,
        )
    except APIStatusError as error:
        duration_ms = round((time.perf_counter() - request_started) * 1000)
        provider_message = _provider_error_message(
            error.body if error.body is not None else str(error),
            configuration["api_key"],
        )
        logger.warning(
            "AI provider response provider=groq_sdk model=%s status_code=%s "
            "duration_ms=%s response_body=%s provider_error=%s",
            model,
            error.status_code,
            duration_ms,
            _sanitize_provider_body(
                error.body if error.body is not None else str(error),
                configuration["api_key"],
            ),
            provider_message,
        )
        raise AIProviderError(
            f"Groq returned HTTP {error.status_code}: {provider_message}",
            status_code=error.status_code,
        ) from error
    except APIConnectionError as error:
        duration_ms = round((time.perf_counter() - request_started) * 1000)
        logger.error(
            "AI provider request failed provider=groq_sdk model=%s "
            "status_code=unavailable duration_ms=%s error=%s",
            model,
            duration_ms,
            str(error)[:500],
        )
        raise AIProviderError(
            "Could not connect to Groq. Check the network connection and Groq service status."
        ) from error
    except APIError as error:
        duration_ms = round((time.perf_counter() - request_started) * 1000)
        provider_message = _sanitize_provider_body(str(error), configuration["api_key"])
        logger.error(
            "AI provider request failed provider=groq_sdk model=%s "
            "status_code=unavailable duration_ms=%s error=%s",
            model,
            duration_ms,
            provider_message,
        )
        raise AIProviderError(f"Groq SDK request failed: {provider_message}") from error

    duration_ms = round((time.perf_counter() - request_started) * 1000)
    logger.info(
        "AI provider response provider=groq_sdk model=%s status_code=200 duration_ms=%s",
        model,
        duration_ms,
    )
    try:
        generated = completion.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as error:
        raise AIProviderError(
            "Groq returned an invalid chat-completions response; expected "
            "choices[0].message.content."
        ) from error
    if not isinstance(generated, str) or not generated.strip():
        raise AIProviderError("Groq returned an empty chat-completions message.")
    return generated.strip()[:4000]
