"""A small list of company letterhead profiles (name/address/phone/email)
the user can pick from when printing a quote. Persisted in companies.json,
gitignored like the SQLite cache — seeded with one starter profile on first
run rather than shipped as hardcoded config, since this is meant to be
edited through the app, not the source.

A quote stores a *copy* of the chosen profile's fields (see Quote's
company_* fields), not a live reference — editing or removing a profile
here doesn't retroactively change quotes already created from it.
"""

import json
from dataclasses import asdict, dataclass, field

from app import config

_SEED_COMPANY = {
    "name": "Ambetker Wire & Cable",
    "address_lines": ["1420 Harborview Industrial Drive", "Ashland, WI 54806"],
    "phone": "715 682 4400",
    "email": "sales@ambetker.com",
}


@dataclass
class CompanyProfile:
    name: str
    address_lines: list[str] = field(default_factory=list)
    phone: str = ""
    email: str = ""


def _seed() -> list[CompanyProfile]:
    return [CompanyProfile(**_SEED_COMPANY)]


def load_companies() -> tuple[list[CompanyProfile], int]:
    """Returns (companies, default_index). Seeds a starter profile the
    first time this is called with no companies.json present yet."""
    if not config.COMPANIES_PATH.exists():
        companies = _seed()
        save_companies(companies, 0)
        return companies, 0

    try:
        data = json.loads(config.COMPANIES_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        companies = _seed()
        save_companies(companies, 0)
        return companies, 0

    raw = data.get("companies", [])
    companies = [
        CompanyProfile(
            name=c.get("name", ""),
            address_lines=list(c.get("address_lines", [])),
            phone=c.get("phone", ""),
            email=c.get("email", ""),
        )
        for c in raw
    ]
    if not companies:
        companies = _seed()

    default_index = data.get("default_index", 0)
    default_index = max(0, min(default_index, len(companies) - 1))
    return companies, default_index


def save_companies(companies: list[CompanyProfile], default_index: int) -> None:
    default_index = max(0, min(default_index, len(companies) - 1)) if companies else 0
    config.COMPANIES_PATH.write_text(
        json.dumps(
            {"companies": [asdict(c) for c in companies], "default_index": default_index},
            indent=2,
        )
    )


def get_default_company() -> CompanyProfile:
    companies, default_index = load_companies()
    return companies[default_index]
