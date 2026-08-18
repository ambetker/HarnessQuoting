from app.bom_parser import ParsedBomLine, parse_bom_text


def test_parses_simple_comma_separated_lines():
    text = "DT04-12PA-L012, 1\nDT06-6S-E004, 2\n0462-201-16141, 18"
    result = parse_bom_text(text)

    assert [(l.part_number, l.qty) for l in result.lines] == [
        ("DT04-12PA-L012", 1.0),
        ("DT06-6S-E004", 2.0),
        ("0462-201-16141", 18.0),
    ]
    assert result.skipped == []


def test_ignores_extra_trailing_columns():
    result = parse_bom_text("CLT50N-C, 6.5, Loom / braid, Split loom tubing 1/2 in")
    assert result.lines == [ParsedBomLine("CLT50N-C", 6.5)]


def test_skips_a_non_parsing_header_row_silently():
    text = "Part Number, Qty\nDT04-12PA-L012, 1"
    result = parse_bom_text(text)

    assert len(result.lines) == 1
    assert result.lines[0].part_number == "DT04-12PA-L012"
    assert result.skipped == []  # header isn't reported as an error


def test_flags_unparseable_lines_after_the_first():
    text = "DT04-12PA-L012, 1\nthis line is garbage\nDT06-6S-E004, 2"
    result = parse_bom_text(text)

    assert len(result.lines) == 2
    assert result.skipped == ["this line is garbage"]


def test_tolerates_tab_separated_as_fallback():
    result = parse_bom_text("DT04-12PA-L012\t1\nDT06-6S-E004\t2")
    assert [(l.part_number, l.qty) for l in result.lines] == [
        ("DT04-12PA-L012", 1.0),
        ("DT06-6S-E004", 2.0),
    ]


def test_supports_decimal_quantities():
    result = parse_bom_text("M22759/16-18-9, 14.5")
    assert result.lines[0].qty == 14.5


def test_empty_input_produces_no_lines():
    result = parse_bom_text("   \n\n  ")
    assert result.lines == []
    assert result.skipped == []


def test_blank_part_number_is_skipped():
    text = "DT04-12PA-L012, 1\n, 5"
    result = parse_bom_text(text)
    assert len(result.lines) == 1
    assert result.skipped == [", 5"]
