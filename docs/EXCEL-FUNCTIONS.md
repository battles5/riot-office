# Excel functions for Calc

Riot Office adds the Excel 365 functions that LibreOffice Calc 26.8 does not have. They come as a
Calc extension, `RiotOffice-ExcelFunctions-<version>.oxt`, installed by the setup and by the
Ubuntu package. Check with `riot-office doctor`; install by hand with `riot-office addin install`
(administrator / root), or `riot-office addin install --user`.

| Function | What it does | Status |
|---|---|---|
| `GROUPBY` | Group rows by one or more fields and aggregate the values | ✅ subset, see below |
| `PIVOTBY` | Cross table: rows by some fields, columns by others | ✅ subset, see below |
| `PERCENTOF` | A subset's sum as a fraction of the sum of all the data | ✅ |
| `REGEXTEST` | 1 if the text matches a regular expression, otherwise 0 | ✅ |
| `REGEXEXTRACT` | First match, all matches, or the capture groups | ✅ |
| `REGEXREPLACE` | Replace matches; `$1`..`$9` stand for capture groups | ✅ |

Not provided: `LAMBDA` and friends (LibreOffice 27.2 brings them), `IMAGE`, `STOCKHISTORY`,
`TRANSLATE`, `COPILOT`, `PY`, `TRIMRANGE`; slicers, Power Query and Power Pivot are a different
kind of feature, see [COMPATIBILITY](COMPATIBILITY.md).

## Read this first: where the functions work

- ✅ **Typed in Calc.** Enter `=GROUPBY(...)` in a cell like any other function. It is listed in the
  function wizard under *Add-In*, with descriptions in English and Italian.
- ✅ **Saved in `.ods`.** The formulas are stored and recalculated when the file is opened.

> **What has been checked, and what has not.** CI installs the extension in a real LibreOffice
> 26.8 and checks the numbers of every function in a spreadsheet that calls them (arrays, totals,
> sorting, several aggregations, Italian names, regular expressions on ranges). LibreOffice also
> asks the add-in for its function names, which is how the short names get registered. What has
> *not* been exercised is the typing itself, and the function wizard, in the graphical interface:
> they use the same registration, but no automated test drives the window. If `=GROUPBY(...)` does
> not turn into a result in your Calc, tell us.
- ⚠️ **In `.xlsx` they do not survive.** LibreOffice writes the formula under the add-in's internal
  name (`ORG.RIOTOFFICE.CALC.RIOTFUNCTIONS.GROUPBY`), which Excel does not know, and it does not
  read such a name back from `.xlsx` either: it shows `#NAME?` when the file is reopened. The
  values calculated before saving stay in the file. Keep workbooks that use these functions as
  `.ods`, or paste the results as values before sending an `.xlsx`.
- ⚠️ **An `.xlsx` written by Excel that already contains `GROUPBY`, `PIVOTBY` or `REGEX*`** opens
  with `#NAME?` in those cells (LibreOffice recognises add-in functions in `.xlsx` only from a fixed
  internal list). Re-enter the formulas in Calc. `riot-office inventory` finds these files for you.

This is a limit of LibreOffice's import and export filters, not of the add-in; it would need a change
in LibreOffice itself, see the [roadmap](ROADMAP.md).

## Differences from Excel

Calc has no `LAMBDA`, so the aggregation is **named by text** instead of passed as a function:

```
=GROUPBY(A1:A100; C1:C100; "SUM")
=GROUPBY(A1:A100; C1:C100; "SUM,AVERAGE")       one result column per name
=GROUPBY(A1:A100; C1:C100; "SOMMA")             Italian names work too
```

Names (English and Italian): `SUM`/`SOMMA`, `AVERAGE`/`MEDIA`, `COUNT`/`CONTA.NUMERI`,
`COUNTA`/`CONTA.VALORI`, `MIN`, `MAX`, `MEDIAN`/`MEDIANA`, `PRODUCT`/`PRODOTTO`,
`STDEV`/`DEV.ST`, `STDEVP`/`DEV.ST.POP`, `VAR`, `VARP`, `MODE`/`MODA` and `PERCENTOF`.

Also different:

- **Subtotals** (total depth `2` and `-2`) and the `field_relationship` argument are not implemented;
  asking for them gives an error instead of a wrong result.
- **Header texts** of the result are generated as "Sum of Sales" ("Somma di Vendite" with an Italian
  Calc); the corner and stacked column headers of `PIVOTBY` are laid out slightly differently from
  Excel's.
- **Errors** appear as a Calc error value, not `#N/A`: `REGEXEXTRACT` with no match, for example,
  gives an error; wrap it in `IFERROR`.
- **`REGEXTEST`** returns 1 or 0 rather than TRUE or FALSE (`IF(REGEXTEST(...); ...)` works).
- **Regular expressions** use Python's `re` flavour, close to PCRE; some Excel (PCRE2) extensions
  differ.
- **Arrays.** `GROUPBY`, `PIVOTBY` and the REGEX functions on ranges return several cells. Enter
  them as array formulas: select the output range, type the formula and press **Ctrl+Shift+Enter**.
  Whether Calc 26.8 spills an add-in result automatically has not been checked.

## GROUPBY

```
GROUPBY(row_fields; values; function; [field_headers]; [total_depth]; [sort_order]; [filter_array])
```

| Argument | Meaning |
|---|---|
| `row_fields` | The column(s) to group by. Include the header row if the data has one |
| `values` | The column(s) to aggregate, same number of rows |
| `function` | Aggregation by name (see above), or several separated by commas |
| `field_headers` | `0` no headers in the data; `1` none in the data, show generated ones; `2` in the data, don't show; `3` in the data, show. Omitted: detected |
| `total_depth` | `1` grand total at the bottom (default); `-1` on top; `0` none |
| `sort_order` | Result columns to sort by, `1` = first, negative = descending. Default: every row field, ascending |
| `filter_array` | One 1/0 per row of `row_fields` (header row included): rows with 0 are left out |

Example: sales by region, largest first, with a grand total at the bottom. The two empty
arguments keep the defaults for `field_headers` and `total_depth`.

```
Region   Sales            =GROUPBY(A1:A6; C1:C6; "SUM"; ; ; -2)
North    10
South    20               Region   Sum of Sales
north    5                South    21
West     7                North    15     ("North" and "north" are one group)
South    1                West     7
                          Total    43
```

## PIVOTBY

```
PIVOTBY(row_fields; col_fields; values; function; [field_headers]; [row_total_depth];
        [row_sort_order]; [col_total_depth]; [col_sort_order]; [filter_array])
```

One aggregated cell for every combination of a row key and a column key; `values` is a single
column and `function` a single name. With several `col_fields` the column headers are stacked.
`row_total_depth` adds the grand total row, `col_total_depth` the grand total column (`1`, `-1`
or `0`).

```
=PIVOTBY(A1:A6; B1:B6; C1:C6; "SUM")

Region   A     B     Total
North    10    5     15
South    1     20    21
West     7           7
Total    18    25    43
```

## PERCENTOF

`=PERCENTOF(C2:C3; C2:C6)` is the sum of the first range divided by the sum of the second. Inside
`GROUPBY` and `PIVOTBY`, `"PERCENTOF"` gives every group's share of the grand total.

## REGEXTEST, REGEXEXTRACT, REGEXREPLACE

```
REGEXTEST(text; pattern; [case_sensitivity])
REGEXEXTRACT(text; pattern; [return_mode]; [case_sensitivity])
REGEXREPLACE(text; pattern; replacement; [occurrence]; [case_sensitivity])
```

- `case_sensitivity`: `0` distinguishes upper and lower case (default), `1` ignores it.
- `return_mode`: `0` first match (default), `1` all matches in a row, `2` the capture groups of
  the first match in a row.
- `occurrence`: `0` replaces every match (default), `n` the nth, a negative `n` the nth from the end.
- `text` may be a range: the function is applied to every cell.

```
=REGEXREPLACE("Ada Lovelace"; "(\w+) (\w+)"; "$2, $1")      Lovelace, Ada
=REGEXEXTRACT("tel 055 1234"; "\d{3}")                      055
=REGEXTEST("Riot Office"; "off"; 1)                         1
```

(Calc also has its own `REGEX()` function; these three follow Excel's argument order and options.)

## How it is built

The logic is plain Python, `riot_office/excel_functions.py`, covered by unit tests. The extension
in `addins/calc/` is a thin layer: an IDL interface (compiled to `types/RiotFunctions.rdb`), a
Python component that receives the cell ranges from Calc, and the names and descriptions in
English and Italian (`extension/riot_calc_meta.py`, from which `CalcAddIns.xcu` is generated).
`python addins/calc/build_oxt.py` packages it; CI installs it in a real LibreOffice and checks the
numbers it produces (`ci/check_excel_functions.py`).
