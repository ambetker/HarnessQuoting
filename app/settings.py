"""App-level local preferences (not per-quote data) — currently just the
user's initials, used in generated quote numbers. Stored in settings.json
next to the project, gitignored like the SQLite cache."""

import json
from dataclasses import asdict, dataclass

from app import config


@dataclass
class AppSettings:
    initials: str = ""


def load_settings() -> AppSettings:
    if not config.SETTINGS_PATH.exists():
        return AppSettings()
    try:
        data = json.loads(config.SETTINGS_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return AppSettings()
    return AppSettings(initials=data.get("initials", ""))


def save_settings(settings: AppSettings) -> None:
    config.SETTINGS_PATH.write_text(json.dumps(asdict(settings), indent=2))
