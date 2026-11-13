"""Excel 365 functions that Calc does not have, as plain Python: GROUPBY, PIVOTBY, PERCENTOF and
the REGEX family.

This module knows nothing about LibreOffice. Tables are lists of rows (lists or tuples), exactly
as Calc hands cell ranges to an add-in; cells are floats, strings, or ``None``/``""`` for blanks.
Results are lists of rows. The Calc add-in in ``addins/calc`` is a thin layer on top of it.

Differences from Excel, deliberately small and documented in docs/EXCEL-FUNCTIONS.md:

- Calc has no LAMBDA yet, so the aggregation is named by text ("SUM", "AVERAGE", "SOMMA", ...),
  or by several names separated by commas ("SUM,AVERAGE") to get one column per name.
- Subtotals (total depth 2 / -2) and the ``field_relationship`` argument are not implemented.
- Errors are raised as ``ValueError`` and shown by Calc as an error value; there is no ``#N/A``.
"""

from __future__ import annotations

import math
import re
import statistics
from typing import Callable, Iterable, Sequence

LABELS = {
    "total": {"en": "Total", "it": "Totale"},
    "value": {"en": "Value", "it": "Valore"},
    "field": {"en": "Field {n}", "it": "Campo {n}"},
}
FUNCTION_LABELS = {  # how a value column is titled: "<label> of <header>"
    "en": {"SUM": "Sum", "AVERAGE": "Average", "COUNT": "Count", "COUNTA": "Count", "MIN": "Min", "MAX": "Max",
           "MEDIAN": "Median", "PRODUCT": "Product", "STDEV": "StDev", "STDEVP": "StDevP", "VAR": "Var",
           "VARP": "VarP", "PERCENTOF": "Percent", "MODE": "Mode"},
    "it": {"SUM": "Somma", "AVERAGE": "Media", "COUNT": "Conteggio", "COUNTA": "Conteggio", "MIN": "Min",
           "MAX": "Max", "MEDIAN": "Mediana", "PRODUCT": "Prodotto", "STDEV": "Dev.st.", "STDEVP": "Dev.st.pop.",
           "VAR": "Var.", "VARP": "Var.pop.", "PERCENTOF": "Percentuale", "MODE": "Moda"},
}
OF = {"en": "{label} of {header}", "it": "{label} di {header}"}

# Aggregation names, English and Italian, by canonical name.
ALIASES = {
    "SUM": ("SUM", "SOMMA"), "AVERAGE": ("AVERAGE", "MEDIA"), "COUNT": ("COUNT", "CONTA.NUMERI"),
    "COUNTA": ("COUNTA", "CONTA.VALORI"), "MIN": ("MIN",), "MAX": ("MAX",), "MEDIAN": ("MEDIAN", "MEDIANA"),
    "PRODUCT": ("PRODUCT", "PRODOTTO"), "STDEV": ("STDEV", "STDEV.S", "DEV.ST", "DEV.ST.C"),
    "STDEVP": ("STDEVP", "STDEV.P", "DEV.ST.POP", "DEV.ST.P"), "VAR": ("VAR", "VAR.S", "VAR.C"),
    "VARP": ("VARP", "VAR.P", "VAR.POP"), "PERCENTOF": ("PERCENTOF", "PERCENTUALEDI"), "MODE": ("MODE", "MODA"),
}
CANONICAL = {alias: name for name, aliases in ALIASES.items() for alias in aliases}


# ----- values --------------------------------------------------------------------------------
def is_blank(value: object) -> bool:
    return value is None or value == ""


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def numbers(values: Iterable[object]) -> list[float]:
    return [float(v) for v in values if is_number(v)]


def as_table(data: object) -> list[list[object]]:
    """A cell range or a single value as a list of rows."""
    if isinstance(data, (list, tuple)):
        if data and not isinstance(data[0], (list, tuple)):
            return [list(data)]
        return [list(row) for row in data]
    return [[data]]


def flatten(data: object) -> list[object]:
    return [cell for row in as_table(data) for cell in row]


def text_of(value: object) -> str:
    """A cell as text: whole numbers without the ".0", blanks as an empty string."""
    if is_blank(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def sort_key(value: object) -> tuple:
    """Numbers first, then text without regard to case, blanks last."""
    if is_blank(value):
        return (2, 0, "")
    if is_number(value):
        return (0, float(value), "")
    return (1, 0, str(value).casefold())


def group_key(value: object) -> object:
    """Cells that differ only by case, or by 1 and 1.0, belong to the same group."""
    if is_blank(value):
        return ""
    if is_number(value):
        return float(value)
    return str(value).casefold()


def label(kind: str, lang: str, **fields) -> str:
    return LABELS[kind].get(lang, LABELS[kind]["en"]).format(**fields)


# ----- aggregation ---------------------------------------------------------------------------
def _need(values: list[float], minimum: int = 1) -> list[float]:
    if len(values) < minimum:
        raise ValueError("not enough numbers to aggregate")
    return values


AGGREGATES: dict[str, Callable[[list[object]], float]] = {
    "SUM": lambda v: math.fsum(numbers(v)),
    "AVERAGE": lambda v: math.fsum(_need(numbers(v))) / len(numbers(v)),
    "COUNT": lambda v: float(len(numbers(v))),
    "COUNTA": lambda v: float(sum(not is_blank(x) for x in v)),
    "MIN": lambda v: min(_need(numbers(v))),
    "MAX": lambda v: max(_need(numbers(v))),
    "MEDIAN": lambda v: statistics.median(_need(numbers(v))),
    "PRODUCT": lambda v: math.prod(_need(numbers(v))),
    "STDEV": lambda v: statistics.stdev(_need(numbers(v), 2)),
    "STDEVP": lambda v: statistics.pstdev(_need(numbers(v))),
    "VAR": lambda v: statistics.variance(_need(numbers(v), 2)),
    "VARP": lambda v: statistics.pvariance(_need(numbers(v))),
    "MODE": lambda v: statistics.multimode(_need(numbers(v)))[0],
}


def function_names(function: object) -> list[str]:
    """Canonical aggregation names from "SUM", "SUM,AVERAGE", "SOMMA" or a range of names."""
    names = []
    for cell in flatten(function):
        for part in str(cell).replace(";", ",").split(","):
            part = part.strip().upper()
            if part:
                if part not in CANONICAL:
                    raise ValueError(f"unknown aggregation function: {part}")
                names.append(CANONICAL[part])
    if not names:
        raise ValueError("no aggregation function given")
    return names


def aggregate(name: str, values: list[object], all_values: list[object]) -> float:
    if name == "PERCENTOF":
        total = math.fsum(numbers(all_values))
        if total == 0:
            raise ValueError("division by zero in PERCENTOF")
        return math.fsum(numbers(values)) / total
    return AGGREGATES[name](values)


def percentof(subset: object, everything: object) -> float:
    """PERCENTOF(data_subset, data_all): the sum of the subset as a fraction of the sum of all data."""
    total = math.fsum(numbers(flatten(everything)))
    if total == 0:
        raise ValueError("the sum of all data is zero")
    return math.fsum(numbers(flatten(subset))) / total


# ----- argument handling ---------------------------------------------------------------------
def _int_or_none(value: object, name: str) -> int | None:
    if is_blank(value):
        return None
    if not is_number(value) or float(value) != int(value):
        raise ValueError(f"{name} must be a whole number")
    return int(value)


def _headers_flag(flag: int | None, values: list[list[object]]) -> tuple[bool, bool]:
    """(the data starts with a header row, show headers) for a field_headers code.

    0: no headers in data, none shown. 1: none in data, generated ones shown. 2: in data, not shown.
    3: in data, shown. Missing: detected, the data has headers when the first row of ``values`` is
    all text and there is a number further down.
    """
    if flag is None:
        first = values[0] if values else []
        has = bool(first) and all(isinstance(v, str) and v != "" for v in first) and any(
            is_number(v) for row in values[1:] for v in row)
        return has, has
    if flag not in (0, 1, 2, 3):
        raise ValueError("field_headers must be 0, 1, 2 or 3")
    return flag in (2, 3), flag in (1, 3)


def _check_depth(depth: int | None, name: str) -> int:
    if depth is None:
        return 1
    if depth in (2, -2):
        raise ValueError(f"{name} {depth} (subtotals) is not implemented; use 0, 1 or -1")
    if depth not in (0, 1, -1):
        raise ValueError(f"{name} must be 0, 1 or -1")
    return depth


def _sort_spec(order: object, width: int, default: Sequence[int]) -> list[int]:
    cells = [c for c in flatten(order) if not is_blank(c)] if order is not None else []
    spec = [int(c) for c in cells] if cells else list(default)
    for column in spec:
        if column == 0 or abs(column) > width:
            raise ValueError(f"sort column {column} is outside 1-{width}")
    return spec


def _filter_rows(rows: int, filter_array: object, has_header: bool) -> list[bool]:
    """One keep/drop flag per data row. The filter has one entry per row of ``row_fields``, header
    row included when there is one."""
    if filter_array is None or all(is_blank(c) for c in flatten(filter_array)):
        return [True] * rows
    flags = [bool(c) and c != 0 for c in flatten(filter_array)]
    if len(flags) != rows + has_header:
        raise ValueError("filter_array must have one row per row of row_fields")
    return flags[has_header:]


def _split_headers(table: list[list[object]], has_header: bool) -> tuple[list[object] | None, list[list[object]]]:
    return (table[0], table[1:]) if has_header else (None, table)


def _value_columns(names: list[str], ncols: int) -> list[tuple[str, int]]:
    """(aggregation, values column index) for each result column."""
    if len(names) == 1:
        return [(names[0], c) for c in range(ncols)]
    if ncols == 1:
        return [(n, 0) for n in names]
    if len(names) == ncols:
        return [(n, c) for c, n in enumerate(names)]
    raise ValueError("give one aggregation, or as many as there are value columns")


def _value_title(name: str, header: object, lang: str) -> str:
    base = text_of(header) or label("value", lang)
    words = FUNCTION_LABELS.get(lang, FUNCTION_LABELS["en"])[name]
    return OF.get(lang, OF["en"]).format(label=words, header=base)


def _sorted_rows(rows: list[list[object]], spec: list[int]) -> list[list[object]]:
    for column in reversed(spec):
        rows.sort(key=lambda r, c=abs(column) - 1: sort_key(r[c]), reverse=column < 0)
    return rows


# ----- GROUPBY -------------------------------------------------------------------------------
def groupby(row_fields: object, values: object, function: object, field_headers: object = None,
            total_depth: object = None, sort_order: object = None, filter_array: object = None,
            lang: str = "en") -> list[list[object]]:
    """GROUPBY(row_fields, values, function, [field_headers], [total_depth], [sort_order], [filter_array]).

    Groups the rows by the combination of the ``row_fields`` columns and aggregates each ``values``
    column with ``function`` (a name such as "SUM", or "SUM,AVERAGE"). ``sort_order`` lists result
    columns (1 = first), negative for descending; the default is ascending by every row field in turn.
    """
    keys, data = as_table(row_fields), as_table(values)
    if len(keys) != len(data):
        raise ValueError("row_fields and values must have the same number of rows")
    has_header, show = _headers_flag(_int_or_none(field_headers, "field_headers"), data)
    key_head, key_rows = _split_headers(keys, has_header)
    val_head, val_rows = _split_headers(data, has_header)
    depth = _check_depth(_int_or_none(total_depth, "total_depth"), "total_depth")
    nkeys, nvals = len(keys[0]), len(data[0])
    columns = _value_columns(function_names(function), nvals)
    spec = _sort_spec(sort_order, nkeys + len(columns), range(1, nkeys + 1))
    keep = _filter_rows(len(key_rows), filter_array, has_header)

    groups: dict[tuple, tuple[list[object], list[int]]] = {}
    for i, key_row in enumerate(key_rows):
        if keep[i]:
            groups.setdefault(tuple(group_key(k) for k in key_row), (list(key_row), []))[1].append(i)

    def line(display: list[object], members: list[int]) -> list[object]:
        every = [r for r, k in zip(val_rows, keep) if k]
        return display + [aggregate(name, [val_rows[i][c] for i in members], [r[c] for r in every])
                          for name, c in columns]

    body = _sorted_rows([line(display, members) for display, members in groups.values()], spec)
    out: list[list[object]] = []
    if show:
        left = ([text_of(h) for h in key_head] if key_head else [label("field", lang, n=n + 1) for n in range(nkeys)])
        right = [_value_title(name, (val_head[c] if val_head else None), lang) for name, c in columns]
        out.append(left + right)
    if depth and body:
        everyone = [i for i, k in enumerate(keep) if k]
        total = line([label("total", lang)] + [""] * (nkeys - 1), everyone)
        out += [total] + body if depth < 0 else body + [total]
    else:
        out += body
    return out


# ----- PIVOTBY -------------------------------------------------------------------------------
def pivotby(row_fields: object, col_fields: object, values: object, function: object,
            field_headers: object = None, row_total_depth: object = None, row_sort_order: object = None,
            col_total_depth: object = None, col_sort_order: object = None, filter_array: object = None,
            lang: str = "en") -> list[list[object]]:
    """PIVOTBY(row_fields, col_fields, values, function, [field_headers], [row_total_depth],
    [row_sort_order], [col_total_depth], [col_sort_order], [filter_array]).

    A cross table: one row per combination of ``row_fields``, one column per combination of
    ``col_fields``, each cell the aggregate of the single ``values`` column. Several column fields
    give stacked header rows. ``row_sort_order`` lists row-field columns (1 = first) or result
    columns after them; ``col_sort_order`` lists column-field levels. Negative sorts descending.
    """
    rows_t, cols_t, data = as_table(row_fields), as_table(col_fields), as_table(values)
    if not (len(rows_t) == len(cols_t) == len(data)):
        raise ValueError("row_fields, col_fields and values must have the same number of rows")
    if len(data[0]) != 1:
        raise ValueError("PIVOTBY aggregates a single values column")
    has_header, show = _headers_flag(_int_or_none(field_headers, "field_headers"), data)
    row_head, row_keys = _split_headers(rows_t, has_header)
    _, col_keys = _split_headers(cols_t, has_header)
    _, val_rows = _split_headers(data, has_header)
    name = function_names(function)
    if len(name) != 1:
        raise ValueError("PIVOTBY takes a single aggregation")
    name = name[0]
    row_depth = _check_depth(_int_or_none(row_total_depth, "row_total_depth"), "row_total_depth")
    col_depth = _check_depth(_int_or_none(col_total_depth, "col_total_depth"), "col_total_depth")
    nrow, ncol = len(rows_t[0]), len(cols_t[0])
    keep = _filter_rows(len(row_keys), filter_array, has_header)
    row_spec = _sort_spec(row_sort_order, nrow, range(1, nrow + 1))
    col_spec = _sort_spec(col_sort_order, ncol, range(1, ncol + 1))
    used = [i for i, k in enumerate(keep) if k]
    everything = [val_rows[i][0] for i in used]

    row_groups: dict[tuple, tuple[list[object], list[int]]] = {}
    col_groups: dict[tuple, list[object]] = {}
    for i in used:
        row_groups.setdefault(tuple(group_key(k) for k in row_keys[i]), (list(row_keys[i]), []))[1].append(i)
        col_groups.setdefault(tuple(group_key(k) for k in col_keys[i]), list(col_keys[i]))

    col_list = _sorted_rows([list(display) for display in col_groups.values()], col_spec)
    col_ids = [tuple(group_key(k) for k in display) for display in col_list]

    def cell(members: list[int], col_id: tuple | None) -> object:
        chosen = [val_rows[i][0] for i in members if col_id is None or tuple(group_key(k) for k in col_keys[i]) == col_id]
        if not chosen:
            return ""
        return aggregate(name, chosen, everything)

    body = []
    for display, members in row_groups.values():
        body.append(display + [cell(members, cid) for cid in col_ids] + ([cell(members, None)] if col_depth else []))
    body = _sorted_rows(body, row_spec)
    if row_depth and body:
        grand = [label("total", lang)] + [""] * (nrow - 1) + [cell(used, cid) for cid in col_ids]
        grand += [cell(used, None)] if col_depth else []
        body = [grand] + body if row_depth < 0 else body + [grand]

    def with_total_column(row: list[object]) -> list[object]:
        """Move the total column to the left when the column total depth is negative."""
        if col_depth >= 0 or not row:
            return row
        return row[:nrow] + [row[-1]] + row[nrow:-1]

    body = [with_total_column(r) for r in body] if col_depth < 0 else body
    total_header = [label("total", lang)] if col_depth else []
    levels = []
    for level in range(ncol):
        cells = [display[level] for display in col_list]
        cells = total_header + cells if col_depth < 0 else cells + total_header
        levels.append([""] * nrow + [text_of(c) for c in cells])
    if show:
        row_titles = [text_of(h) for h in row_head] if row_head else [label("field", lang, n=n + 1) for n in range(nrow)]
        levels[-1][:nrow] = row_titles
    return levels + body


# ----- REGEX family --------------------------------------------------------------------------
def _compile(pattern: object, case_sensitivity: object) -> re.Pattern:
    flag = _int_or_none(case_sensitivity, "case_sensitivity") or 0
    if flag not in (0, 1):
        raise ValueError("case_sensitivity must be 0 (case sensitive) or 1 (ignore case)")
    try:
        return re.compile(text_of(pattern), re.IGNORECASE if flag else 0)
    except re.error as exc:
        raise ValueError(f"invalid regular expression: {exc}") from exc


def _map_text(text: object, one: Callable[[str], object]) -> object:
    """Apply ``one`` to a text, or to every cell of a range."""
    if isinstance(text, (list, tuple)):
        return [[one(text_of(c)) for c in row] for row in as_table(text)]
    return one(text_of(text))


def regextest(text: object, pattern: object, case_sensitivity: object = None) -> object:
    """REGEXTEST(text, pattern, [case_sensitivity]): 1 when the text matches anywhere, otherwise 0."""
    rx = _compile(pattern, case_sensitivity)
    return _map_text(text, lambda s: 1.0 if rx.search(s) else 0.0)


def regexextract(text: object, pattern: object, return_mode: object = None, case_sensitivity: object = None) -> object:
    """REGEXEXTRACT(text, pattern, [return_mode], [case_sensitivity]).

    return_mode 0: the first match (default). 1: all matches, in a row. 2: the capture groups of
    the first match, in a row. An error when nothing matches; wrap in IFERROR for a default.
    """
    mode = _int_or_none(return_mode, "return_mode") or 0
    if mode not in (0, 1, 2):
        raise ValueError("return_mode must be 0, 1 or 2")
    rx = _compile(pattern, case_sensitivity)

    def one(s: str) -> object:
        if mode == 1:
            found = [m.group(0) for m in rx.finditer(s)]
            if not found:
                raise ValueError("no match")
            return found
        m = rx.search(s)
        if m is None:
            raise ValueError("no match")
        if mode == 2:
            if not rx.groups:
                raise ValueError("the pattern has no capture groups")
            return [g or "" for g in m.groups()]
        return m.group(0)

    if isinstance(text, (list, tuple)) or mode == 0:
        return _map_text(text, one)
    return [one(text_of(text))]


def regexreplace(text: object, pattern: object, replacement: object, occurrence: object = None,
                 case_sensitivity: object = None) -> object:
    """REGEXREPLACE(text, pattern, replacement, [occurrence], [case_sensitivity]).

    ``occurrence`` 0 replaces every match (default), n the nth match, a negative n the nth from the
    end. ``replacement`` may use $1..$9 for capture groups.
    """
    n = _int_or_none(occurrence, "occurrence") or 0
    rx = _compile(pattern, case_sensitivity)
    template = re.sub(r"\$(\d)", r"\\\1", text_of(replacement))

    def one(s: str) -> str:
        if n == 0:
            return rx.sub(template, s)
        matches = list(rx.finditer(s))
        index = n - 1 if n > 0 else len(matches) + n
        if not matches or not 0 <= index < len(matches):
            return s
        m = matches[index]
        return s[:m.start()] + m.expand(template) + s[m.end():]

    return _map_text(text, one)
