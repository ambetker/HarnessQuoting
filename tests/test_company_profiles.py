import pytest

from app import company_profiles, config
from app.company_profiles import CompanyProfile


@pytest.fixture(autouse=True)
def temp_companies_path(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "COMPANIES_PATH", tmp_path / "companies.json")
    yield


def test_seeds_a_starter_company_on_first_load():
    companies, default_index = company_profiles.load_companies()
    assert len(companies) == 1
    assert default_index == 0
    assert companies[0].name  # non-empty seed name
    assert config.COMPANIES_PATH.exists()


def test_save_and_load_roundtrip():
    profiles = [
        CompanyProfile(name="Acme Wire", address_lines=["123 Main St", "Springfield, IL"], phone="555-1234", email="sales@acme.com"),
        CompanyProfile(name="Acme West", address_lines=["456 Coast Rd"], phone="555-5678", email="west@acme.com"),
    ]
    company_profiles.save_companies(profiles, default_index=1)

    loaded, default_index = company_profiles.load_companies()
    assert loaded == profiles
    assert default_index == 1


def test_get_default_company_returns_the_marked_default():
    profiles = [
        CompanyProfile(name="A"),
        CompanyProfile(name="B"),
    ]
    company_profiles.save_companies(profiles, default_index=1)

    assert company_profiles.get_default_company().name == "B"


def test_default_index_clamped_if_out_of_range():
    profiles = [CompanyProfile(name="A")]
    company_profiles.save_companies(profiles, default_index=5)

    _loaded, default_index = company_profiles.load_companies()
    assert default_index == 0
