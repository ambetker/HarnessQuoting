"""Generates quote numbers like Q-AB26081601 (initials + YYMMDD + a
2-digit sequence that resets daily). The sequence state persists in
quote_counter.json so numbers stay unique across app restarts.

Call next_quote_number() exactly once per quote actually created (New
Quote, Reset, initial launch) — never on a re-render/refresh, or the
counter burns numbers for no reason.
"""

import json
from datetime import date

from app import config


def _load_counter_state() -> dict:
    if not config.QUOTE_COUNTER_PATH.exists():
        return {}
    try:
        return json.loads(config.QUOTE_COUNTER_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save_counter_state(state: dict) -> None:
    config.QUOTE_COUNTER_PATH.write_text(json.dumps(state, indent=2))


def next_sequence_for_today(today: date | None = None) -> int:
    """Next sequence number for the given date (default: today). Resets to
    1 whenever the stored date isn't today."""
    today = today or date.today()
    today_str = today.isoformat()

    state = _load_counter_state()
    seq = state.get("last_seq", 0) + 1 if state.get("date") == today_str else 1

    _save_counter_state({"date": today_str, "last_seq": seq})
    return seq


def next_quote_number(initials: str, today: date | None = None) -> str:
    today = today or date.today()
    seq = next_sequence_for_today(today)
    initials_part = (initials or "XX").strip().upper() or "XX"
    return f"Q-{initials_part}{today.strftime('%y%m%d')}{seq:02d}"
