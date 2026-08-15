import json

from app import persistence, seed_data
from app.models import Harness, LaborAssumptions, PartLine, Process, Quote


def test_roundtrip_preserves_default_quote(tmp_path):
    quote = seed_data.make_default_quote()
    path = tmp_path / "quote.json"

    persistence.save_quote(quote, path)
    loaded = persistence.load_quote(path)

    assert loaded.customer == quote.customer
    assert loaded.labor == quote.labor
    assert len(loaded.harnesses) == len(quote.harnesses)
    for original, restored in zip(quote.harnesses, loaded.harnesses):
        assert restored == original


def test_roundtrip_preserves_manual_override_and_resolved_state(tmp_path):
    line = PartLine(
        part_number="CLT50N-C630", qty=6.5, category="Loom / braid",
        resolved=True, catalog_price=96.965, catalog_category="Wire",
        description="SLIT WRAP 0.512\" X 100' BLACK", source="Mfr",
        price_tier_label="10 ft tier", lookup_attempted=True,
        manual_override=True, manual_cost=0.28,
    )
    harness = Harness(
        name="Test harness", part_no="TH-1", order_qty=10, setup=100, freight=1.5,
        lines=[line], processes=[Process(id="cut", name="Cut and strip", on=True, count=2)],
    )
    quote = Quote(
        customer="Acme",
        labor=LaborAssumptions(
            labor_rate=62, efficiency=1, scrap_pct=2.5, margin_pct=32,
            times={"cut": 25}, round_price_to=0.0,
        ),
        harnesses=[harness],
    )
    path = tmp_path / "quote.json"

    persistence.save_quote(quote, path)
    loaded = persistence.load_quote(path)

    restored_line = loaded.harnesses[0].lines[0]
    assert restored_line.manual_override is True
    assert restored_line.manual_cost == 0.28
    assert restored_line.catalog_price == 96.965
    assert restored_line.resolved is True


def test_load_tolerates_missing_fields(tmp_path):
    # Simulates an older save file missing a field added later
    # (manual_override), which shouldn't raise.
    path = tmp_path / "old_quote.json"
    path.write_text(json.dumps({
        "customer": "Old Co",
        "labor": {"labor_rate": 50, "times": {"cut": 20}},
        "harnesses": [{
            "name": "H1", "lines": [{"part_number": "X", "qty": 1, "category": "Other"}],
            "processes": [],
        }],
    }))

    loaded = persistence.load_quote(path)

    assert loaded.customer == "Old Co"
    assert loaded.harnesses[0].lines[0].manual_override is False
    assert loaded.harnesses[0].order_qty == 1  # default fallback
