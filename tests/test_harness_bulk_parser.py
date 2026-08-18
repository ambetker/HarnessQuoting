from app.harness_bulk_parser import parse_harness_bulk_text


def test_groups_components_by_harness_name_and_part_number():
    text = (
        "Main engine harness, WH-4412-A, 25, DT04-12PA-L012, 1\n"
        "Main engine harness, WH-4412-A, 25, DT06-6S-E004, 2\n"
        "Sensor jumper, WH-4413-A, 60, DT06-4S-CE06, 1"
    )
    result = parse_harness_bulk_text(text)

    assert len(result.groups) == 2
    main, sensor = result.groups

    assert main.name == "Main engine harness"
    assert main.part_no == "WH-4412-A"
    assert main.qty == 25
    assert [(l.part_number, l.qty) for l in main.lines] == [
        ("DT04-12PA-L012", 1.0),
        ("DT06-6S-E004", 2.0),
    ]

    assert sensor.name == "Sensor jumper"
    assert sensor.qty == 60
    assert len(sensor.lines) == 1
    assert result.skipped == []


def test_preserves_harness_order_of_first_appearance():
    text = (
        "B harness, PN-B, 10, X, 1\n"
        "A harness, PN-A, 5, Y, 2\n"
        "B harness, PN-B, 10, Z, 3"
    )
    result = parse_harness_bulk_text(text)
    assert [g.name for g in result.groups] == ["B harness", "A harness"]
    assert len(result.groups[0].lines) == 2  # both B harness rows grouped together


def test_skips_a_non_parsing_header_row_silently():
    text = "Harness, P/N, Qty, Component, Qty\nMain, PN-1, 25, C-1, 1"
    result = parse_harness_bulk_text(text)
    assert len(result.groups) == 1
    assert result.skipped == []


def test_flags_unparseable_lines_after_the_first():
    text = "Main, PN-1, 25, C-1, 1\nthis is garbage\nMain, PN-1, 25, C-2, 2"
    result = parse_harness_bulk_text(text)
    assert len(result.groups) == 1
    assert len(result.groups[0].lines) == 2
    assert result.skipped == ["this is garbage"]


def test_ignores_extra_trailing_columns():
    result = parse_harness_bulk_text("Main, PN-1, 25, C-1, 1, extra, columns, here")
    assert len(result.groups) == 1
    assert result.groups[0].lines[0].part_number == "C-1"


def test_tolerates_tab_separated_as_fallback():
    result = parse_harness_bulk_text("Main\tPN-1\t25\tC-1\t1")
    assert len(result.groups) == 1
    assert result.groups[0].qty == 25
    assert result.groups[0].lines[0].part_number == "C-1"


def test_empty_input_produces_no_groups():
    result = parse_harness_bulk_text("   \n\n  ")
    assert result.groups == []
    assert result.skipped == []


def test_missing_harness_qty_is_flagged_when_not_the_first_line():
    bad_line = "Main, PN-1, not-a-number, C-1, 1"
    text = f"Sensor, PN-2, 10, C-2, 1\n{bad_line}"
    result = parse_harness_bulk_text(text)
    assert len(result.groups) == 1
    assert result.skipped == [bad_line]
