import json
import sys
from pathlib import Path

def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
CONFIG_DIR = BASE_DIR / "settings"
CONFIG_FILE = CONFIG_DIR / "keys.json"

def ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def config_exists() -> bool:
    return CONFIG_FILE.exists()

def save_api_keys(
    openrouter_api_key: str | None = None,
    serpapi_api_key: str | None = None
) -> None:
    """
    Saves API keys into config/api_keys.json
    Only overwrites keys that are provided.
    """

    ensure_config_dir()

    data: dict = {}

    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    if openrouter_api_key is not None:
        data["openrouter_api_key"] = openrouter_api_key.strip()

    if serpapi_api_key is not None:
        data["serpapi_api_key"] = serpapi_api_key.strip()

    CONFIG_FILE.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8"
    )

def load_api_keys() -> dict:
    if not CONFIG_FILE.exists():
        return {}

    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ Failed to load api_keys.json: {e}")
        return {}

def get_openrouter_key() -> str | None:
    return load_api_keys().get("openrouter_api_key")


def get_serpapi_key() -> str | None:
    return load_api_keys().get("serpapi_api_key")

def is_openrouter_configured() -> bool:
    key = get_openrouter_key()
    return bool(key and len(key) > 15)


def is_serpapi_configured() -> bool:
    key = get_serpapi_key()
    return bool(key and len(key) > 10)


def is_fully_configured() -> bool:
    return is_openrouter_configured() and is_serpapi_configured()
