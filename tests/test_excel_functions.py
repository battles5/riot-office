"""Tests of the GROUPBY / PIVOTBY / PERCENTOF / REGEX functions (pure Python, no LibreOffice)."""

import pytest

from riot_office import excel_functions as xf

REGION = [["Region"], ["North"], ["South"], ["north"], ["West"], ["South"]]
PRODUCT = [["Product"], ["A"], ["B"], ["B"], ["A"], ["A"]]
SALES = [["Sales"], [10.0], [20.0], [5.0], [7.0], [1.0]]


def test_groupby_sum_with_headers_total_and_default_sort():
    out = xf.groupby(REGION, SALES, "SUM")
    assert out == [
        ["Region", "Sum of Sales"],
        ["North", 15.0],   # "North" and "north" are one group; the first spelling is kept
        ["South", 21.0],
        ["West", 7.0],
        ["Total", 43.0],
    ]


def test_groupby_headers_total_on_top_and_descending_sort():
    out = xf.groupby(REGION, SALES, "SUM", None, -1, -2)
    assert [r[0] for r in out] == ["Region", "Total", "South", "North", "West"]


def test_groupby_without_headers_and_without_total():
    out = xf.groupby(REGION[1:], SALES[1:], "SUM", 0, 0)
    assert out == [["North", 15.0], ["South", 21.0], ["West", 7.0]]


def test_groupby_generated_headers_in_italian():
    out = xf.groupby(REGION[1:], SALES[1:], "SOMMA", 1, 0, lang="it")
    assert out[0] == ["Campo 1", "Somma di Valore"]


def test_groupby_several_aggregations_and_columns():
    out = xf.groupby(REGION, SALES, "SUM,COUNT", None, 0)
    assert out[0] == ["Region", "Sum of Sales", "Count of Sales"]
    assert out[2] == ["South", 21.0, 2.0]
    two = xf.groupby(REGION, [["Sales", "Units"], [1, 2], [3, 4], [5, 6], [7, 8], [9, 10]], "SUM", None, 0)
    assert two[0] == ["Region", "Sum of Sales", "Sum of Units"]
    assert two[2] == ["South", 12.0, 14.0]


def test_groupby_percentof_and_filter():
    out = xf.groupby(REGION, SALES, "PERCENTOF", None, 1)
    assert out[1][1] == pytest.approx(15 / 43)
    assert out[-1] == ["Total", pytest.approx(1.0)]
    filtered = xf.groupby(REGION, SALES, "SUM", None, 0, None, [[1], [1], [0], [1], [1], [1]])
    assert [r[0] for r in filtered] == ["Region", "North", "South", "West"]
    assert filtered[2][1] == 1.0  # South: the 20 was filtered out, only the 1 is left


def test_groupby_several_row_fields():
    out = xf.groupby([[r[0], p[0]] for r, p in zip(REGION, PRODUCT)], SALES, "SUM", None, 0)
    assert out[0] == ["Region", "Product", "Sum of Sales"]
    assert out[1:] == [["North", "A", 10.0], ["north", "B", 5.0], ["South", "A", 1.0], ["South", "B", 20.0],
                       ["West", "A", 7.0]]


def test_groupby_errors():
    with pytest.raises(ValueError, match="subtotals"):
        xf.groupby(REGION, SALES, "SUM", None, 2)
    with pytest.raises(ValueError, match="unknown aggregation"):
        xf.groupby(REGION, SALES, "NOPE")
    with pytest.raises(ValueError, match="same number of rows"):
        xf.groupby(REGION[1:], SALES, "SUM")
    with pytest.raises(ValueError, match="sort column"):
        xf.groupby(REGION, SALES, "SUM", None, None, 9)


def test_pivotby_cross_table_with_totals():
    out = xf.pivotby(REGION, PRODUCT, SALES, "SUM")
    assert out == [
        ["Region", "A", "B", "Total"],
        ["North", 10.0, 5.0, 15.0],
        ["South", 1.0, 20.0, 21.0],
        ["West", 7.0, "", 7.0],
        ["Total", 18.0, 25.0, 43.0],
    ]


def test_pivotby_no_totals_and_totals_first():
    out = xf.pivotby(REGION[1:], PRODUCT[1:], SALES[1:], "SUM", 0, 0, None, 0)
    assert out == [["", "A", "B"], ["North", 10.0, 5.0], ["South", 1.0, 20.0], ["West", 7.0, ""]]
    first = xf.pivotby(REGION, PRODUCT, SALES, "SUM", None, -1, None, -1)
    assert first[0] == ["Region", "Total", "A", "B"]
    assert first[1] == ["Total", 43.0, 18.0, 25.0]


def test_pivotby_stacked_column_fields():
    cols = [["Product", "Year"], ["A", 2024.0], ["B", 2024.0], ["B", 2025.0], ["A", 2025.0], ["A", 2025.0]]
    out = xf.pivotby(REGION, cols, SALES, "SUM", None, 0, None, 0)
    assert out[0] == ["", "A", "A", "B", "B"]
    assert out[1] == ["Region", "2024", "2025", "2024", "2025"]
    assert out[2][0] == "North"


def test_pivotby_rejects_several_values_columns():
    with pytest.raises(ValueError, match="single values column"):
        xf.pivotby(REGION, PRODUCT, [["a", "b"]] * 6, "SUM")


def test_percentof():
    assert xf.percentof([[1.0], [2.0]], [[1.0], [2.0], [7.0]]) == pytest.approx(0.3)
    with pytest.raises(ValueError):
        xf.percentof([[1.0]], [[0.0]])


@pytest.mark.parametrize("name,expected", [("SUM", 6.0), ("AVERAGE", 2.0), ("COUNT", 3.0), ("MIN", 1.0),
                                          ("MAX", 3.0), ("MEDIAN", 2.0), ("PRODUCT", 6.0), ("MEDIA", 2.0),
                                          ("CONTA.NUMERI", 3.0), ("STDEV", 1.0), ("VARP", pytest.approx(2 / 3))])
def test_aggregations(name, expected):
    canon = xf.function_names(name)[0]
    assert xf.aggregate(canon, [1.0, 2.0, 3.0, "text", None], []) == expected


def test_regextest():
    assert xf.regextest("Riot Office", r"off") == 0.0
    assert xf.regextest("Riot Office", r"off", 1) == 1.0
    assert xf.regextest([["a1", "b"]], r"\d") == [[1.0, 0.0]]
    assert xf.regextest(42.0, r"^\d+$") == 1.0  # numbers are matched as text, without the ".0"
    with pytest.raises(ValueError, match="invalid regular expression"):
        xf.regextest("x", "(")


def test_regexextract_modes():
    assert xf.regexextract("tel 055 1234 and 02 999", r"\d{2,3}") == "055"
    assert xf.regexextract("tel 055 1234 and 02 999", r"\d{2,3}", 1) == [["055", "123", "02", "999"]] or \
        xf.regexextract("tel 055 1234 and 02 999", r"\d{2,3}", 1) == ["055", "123", "02", "999"]
    assert xf.regexextract("name: Ada Lovelace", r"(\w+) (\w+)", 2) == [["Ada", "Lovelace"]] or \
        xf.regexextract("name: Ada Lovelace", r"(\w+) (\w+)", 2) == ["Ada", "Lovelace"]
    with pytest.raises(ValueError, match="no match"):
        xf.regexextract("abc", r"\d")
    with pytest.raises(ValueError, match="capture groups"):
        xf.regexextract("abc", r"b", 2)


def test_regexreplace():
    assert xf.regexreplace("a-b-c", "-", "+") == "a+b+c"
    assert xf.regexreplace("a-b-c", "-", "+", 2) == "a-b+c"
    assert xf.regexreplace("a-b-c", "-", "+", -1) == "a-b+c"
    assert xf.regexreplace("a-b-c", "-", "+", 5) == "a-b-c"
    assert xf.regexreplace("Ada Lovelace", r"(\w+) (\w+)", "$2, $1") == "Lovelace, Ada"
    assert xf.regexreplace([["x1", "y2"]], r"\d", "#") == [["x#", "y#"]]
