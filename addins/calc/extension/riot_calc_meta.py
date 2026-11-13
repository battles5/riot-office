"""Names and descriptions of the Riot add-in functions, in English and Italian.

One source for two consumers: the add-in itself (``riot_calc_functions.py``, which answers
Calc's questions about function names) and ``build_oxt.py``, which generates CalcAddIns.xcu from
it. Keep this module free of any LibreOffice import so that the build script can load it.

``programmatic`` names are the IDL method names; ``display`` is what the user types in a cell.
Argument names are the IDL parameter names (camelCase); ``snake`` turns them into what the user
sees. The last argument of every function is the variable list of optional arguments (``options``):
Calc offers it as one repeating argument, the description names them in order.
"""

CATEGORY = "Add-In"


def snake(name: str) -> str:
    """The IDL parameter name as shown in the formula: ``rowFields`` -> ``row_fields``."""
    return "".join("_" + c.lower() if c.isupper() else c for c in name)


FUNCTIONS = {
    "groupby": {
        "display": "GROUPBY",
        "description": {
            "en": "Groups rows by one or more fields and aggregates the values (Excel's GROUPBY, with the "
                  "aggregation given by name).",
            "it": "Raggruppa le righe per uno o più campi e aggrega i valori (GROUPBY di Excel, con "
                  "l'aggregazione indicata per nome)."},
        "args": [
            ("rowFields", {"en": "Columns to group by (include the header row if there is one)",
                            "it": "Colonne per cui raggruppare (con la riga di intestazione, se c'è)"}),
            ("values", {"en": "Columns to aggregate", "it": "Colonne da aggregare"}),
            ("function", {"en": 'Aggregation by name: "SUM", "AVERAGE", "COUNT", "MIN", "MAX", "MEDIAN", ... '
                                'or several separated by commas',
                          "it": 'Aggregazione per nome: "SOMMA", "MEDIA", "CONTA.NUMERI", "MIN", "MAX", '
                                '"MEDIANA", ... o più nomi separati da virgole'}),
            ("options", {"en": "In order, all optional: field_headers (0-3), total_depth (0, 1 or -1), "
                               "sort_order (columns, negative = descending), filter_array",
                         "it": "In ordine, tutti facoltativi: field_headers (0-3), total_depth (0, 1 o -1), "
                               "sort_order (colonne, negativo = decrescente), filter_array"}),
        ],
    },
    "pivotby": {
        "display": "PIVOTBY",
        "description": {
            "en": "Cross table: rows by one set of fields, columns by another, aggregating the values "
                  "(Excel's PIVOTBY, with the aggregation given by name).",
            "it": "Tabella a doppia entrata: righe per un gruppo di campi, colonne per un altro, con i valori "
                  "aggregati (PIVOTBY di Excel, con l'aggregazione indicata per nome)."},
        "args": [
            ("rowFields", {"en": "Columns that make the rows", "it": "Colonne che formano le righe"}),
            ("colFields", {"en": "Columns that make the columns", "it": "Colonne che formano le colonne"}),
            ("values", {"en": "The column to aggregate (a single one)", "it": "La colonna da aggregare (una sola)"}),
            ("function", {"en": 'Aggregation by name: "SUM", "AVERAGE", "COUNT", ...',
                          "it": 'Aggregazione per nome: "SOMMA", "MEDIA", "CONTA.NUMERI", ...'}),
            ("options", {"en": "In order, all optional: field_headers (0-3), row_total_depth (0, 1 or -1), "
                               "row_sort_order, col_total_depth (0, 1 or -1), col_sort_order, filter_array",
                         "it": "In ordine, tutti facoltativi: field_headers (0-3), row_total_depth (0, 1 o -1), "
                               "row_sort_order, col_total_depth (0, 1 o -1), col_sort_order, filter_array"}),
        ],
    },
    "percentof": {
        "display": "PERCENTOF",
        "description": {
            "en": "The sum of a subset as a fraction of the sum of all the data.",
            "it": "La somma di un sottoinsieme come frazione della somma di tutti i dati."},
        "args": [
            ("dataSubset", {"en": "The values of the subset", "it": "I valori del sottoinsieme"}),
            ("dataAll", {"en": "All the values", "it": "Tutti i valori"}),
        ],
    },
    "regextest": {
        "display": "REGEXTEST",
        "description": {
            "en": "1 if the text matches the regular expression, otherwise 0.",
            "it": "1 se il testo corrisponde all'espressione regolare, altrimenti 0."},
        "args": [
            ("text", {"en": "The text, or a range of texts", "it": "Il testo, o un intervallo di testi"}),
            ("pattern", {"en": "The regular expression", "it": "L'espressione regolare"}),
            ("options", {"en": "Optional: case_sensitivity (0 = case sensitive, 1 = ignore case)",
                         "it": "Facoltativo: case_sensitivity (0 = maiuscole/minuscole distinte, 1 = ignorale)"}),
        ],
    },
    "regexextract": {
        "display": "REGEXEXTRACT",
        "description": {
            "en": "Extracts text that matches a regular expression: the first match, all matches, or the "
                  "capture groups of the first match.",
            "it": "Estrae il testo che corrisponde a un'espressione regolare: la prima corrispondenza, tutte, "
                  "o i gruppi di cattura della prima."},
        "args": [
            ("text", {"en": "The text, or a range of texts", "it": "Il testo, o un intervallo di testi"}),
            ("pattern", {"en": "The regular expression", "it": "L'espressione regolare"}),
            ("options", {"en": "In order, optional: return_mode (0 = first match, 1 = all matches in a row, "
                               "2 = capture groups in a row), case_sensitivity (0 or 1)",
                         "it": "In ordine, facoltativi: return_mode (0 = prima corrispondenza, 1 = tutte in una "
                               "riga, 2 = gruppi di cattura in una riga), case_sensitivity (0 o 1)"}),
        ],
    },
    "regexreplace": {
        "display": "REGEXREPLACE",
        "description": {
            "en": "Replaces text that matches a regular expression; $1..$9 in the replacement stand for "
                  "capture groups.",
            "it": "Sostituisce il testo che corrisponde a un'espressione regolare; $1..$9 nella sostituzione "
                  "indicano i gruppi di cattura."},
        "args": [
            ("text", {"en": "The text, or a range of texts", "it": "Il testo, o un intervallo di testi"}),
            ("pattern", {"en": "The regular expression", "it": "L'espressione regolare"}),
            ("replacement", {"en": "The replacement text", "it": "Il testo sostitutivo"}),
            ("options", {"en": "In order, optional: occurrence (0 = all, n = nth, negative = nth from the end), "
                               "case_sensitivity (0 or 1)",
                         "it": "In ordine, facoltativi: occurrence (0 = tutte, n = l'ennesima, negativo = "
                               "dalla fine), case_sensitivity (0 o 1)"}),
        ],
    },
}
