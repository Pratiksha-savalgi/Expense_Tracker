import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_environment():
    env_path = PROJECT_ROOT / ".env"
    if not env_path.is_file():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not key or key.startswith("#") or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ[key] = value


def get_ai_configuration():
    load_environment()
    return {
        "api_key": os.environ.get("GROQ_API_KEY", "").strip(),
        "model": os.environ.get("GROQ_MODEL", "").strip(),
    }


def get_missing_ai_configuration(configuration=None):
    configuration = configuration or get_ai_configuration()
    return [
        variable
        for variable, setting in (
            ("GROQ_API_KEY", configuration["api_key"]),
            ("GROQ_MODEL", configuration["model"]),
        )
        if not setting
    ]


def feature_enabled(name, default=False):
    load_environment()
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "on"}


def bounded_setting(name, default, minimum, maximum):
    load_environment()
    try:
        value = int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default
    return min(max(value, minimum), maximum)
