from datetime import date

import pytest

from app import config, quote_numbering


@pytest.fixture(autouse=True)
def temp_counter_path(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "QUOTE_COUNTER_PATH", tmp_path / "quote_counter.json")
    yield


def test_first_quote_of_the_day_is_sequence_1():
    seq = quote_numbering.next_sequence_for_today(date(2026, 8, 16))
    assert seq == 1


def test_sequence_increments_within_the_same_day():
    day = date(2026, 8, 16)
    assert quote_numbering.next_sequence_for_today(day) == 1
    assert quote_numbering.next_sequence_for_today(day) == 2
    assert quote_numbering.next_sequence_for_today(day) == 3


def test_sequence_resets_on_a_new_day():
    quote_numbering.next_sequence_for_today(date(2026, 8, 16))
    quote_numbering.next_sequence_for_today(date(2026, 8, 16))
    assert quote_numbering.next_sequence_for_today(date(2026, 8, 17)) == 1


def test_quote_number_format_matches_example():
    # Q-AB26081601 for initials "AB" on 2026-08-16, first quote of the day
    number = quote_numbering.next_quote_number("AB", today=date(2026, 8, 16))
    assert number == "Q-AB26081601"

    number2 = quote_numbering.next_quote_number("AB", today=date(2026, 8, 16))
    assert number2 == "Q-AB26081602"


def test_quote_number_defaults_placeholder_initials_when_unset():
    number = quote_numbering.next_quote_number("", today=date(2026, 8, 16))
    assert number == "Q-XX26081601"


def test_quote_number_normalizes_initials_to_uppercase():
    number = quote_numbering.next_quote_number("ab", today=date(2026, 8, 16))
    assert number.startswith("Q-AB")
