"""The Riot Office add-in for Calc: GROUPBY, PIVOTBY, PERCENTOF and the REGEX functions.

A thin UNO layer: it receives cell ranges from Calc, hands them to ``excel_functions`` (plain
Python, tested on its own) and returns the result. Errors in the arguments become
IllegalArgumentException, which Calc shows as an error value in the cell.
"""

import os
import sys

import uno
import unohelper
from com.sun.star.lang import IllegalArgumentException, Locale, XServiceInfo, XServiceName
from com.sun.star.sheet import XAddIn
from org.riotoffice.calc import XRiotFunctions

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # excel_functions and riot_calc_meta sit beside us

import excel_functions as xf  # noqa: E402
import riot_calc_meta as meta  # noqa: E402

IMPLEMENTATION = "org.riotoffice.calc.RiotFunctions"
SERVICES = ("com.sun.star.sheet.AddIn", IMPLEMENTATION)


def _optional(options, index):
    """The ``index``-th optional argument of a formula, None when it was left out or empty."""
    if options is None or index >= len(options):
        return None
    value = options[index]
    return None if value == "" else value


def _rows(result):
    """A function result in the form Calc wants: arrays typed as sequence< sequence< any > >, scalars as they are.

    The methods return ``any``, and pyuno would turn a plain tuple into sequence< any >, which Calc
    shows as #VALUE!: the type has to be named.
    """
    if isinstance(result, (list, tuple)):
        rows = result if result and isinstance(result[0], (list, tuple)) else [result]
        return uno.Any("[][]any", tuple(tuple(row) for row in rows))
    return result


class RiotFunctions(unohelper.Base, XRiotFunctions, XAddIn, XServiceName, XServiceInfo):
    def __init__(self, ctx):
        self.ctx = ctx
        self.locale = Locale("en", "US", "")

    def _call(self, fn, *args, **kwargs):
        try:
            return _rows(fn(*args, **kwargs))
        except ValueError as exc:
            raise IllegalArgumentException(str(exc), self, 0)

    @property
    def _lang(self):
        return self.locale.Language if self.locale.Language in ("en", "it") else "en"

    # ----- XRiotFunctions ---------------------------------------------------------------------
    def groupby(self, row_fields, values, function, options):
        return self._call(xf.groupby, row_fields, values, function, _optional(options, 0), _optional(options, 1),
                          _optional(options, 2), _optional(options, 3), lang=self._lang)

    def pivotby(self, row_fields, col_fields, values, function, options):
        return self._call(xf.pivotby, row_fields, col_fields, values, function, *[_optional(options, i) for i in range(6)],
                          lang=self._lang)

    def percentof(self, data_subset, data_all):
        return self._call(xf.percentof, data_subset, data_all)

    def regextest(self, text, pattern, options):
        return self._call(xf.regextest, text, pattern, _optional(options, 0))

    def regexextract(self, text, pattern, options):
        return self._call(xf.regexextract, text, pattern, _optional(options, 0), _optional(options, 1))

    def regexreplace(self, text, pattern, replacement, options):
        return self._call(xf.regexreplace, text, pattern, replacement, _optional(options, 0), _optional(options, 1))

    # ----- XLocalizable (through XAddIn) --------------------------------------------------------
    def setLocale(self, locale):
        self.locale = locale

    def getLocale(self):
        return self.locale

    # ----- XAddIn: names and descriptions, from riot_calc_meta ----------------------------------
    def getProgrammaticFuntionName(self, display_name):  # the misspelling is the real UNO method name
        for programmatic, data in meta.FUNCTIONS.items():
            if data["display"] == display_name.upper():
                return programmatic
        return ""

    def getDisplayFunctionName(self, programmatic_name):
        return meta.FUNCTIONS[programmatic_name]["display"]

    def getFunctionDescription(self, programmatic_name):
        return meta.FUNCTIONS[programmatic_name]["description"].get(self._lang, "")

    def getDisplayArgumentName(self, programmatic_name, argument):
        return meta.snake(meta.FUNCTIONS[programmatic_name]["args"][argument][0])

    def getArgumentDescription(self, programmatic_name, argument):
        return meta.FUNCTIONS[programmatic_name]["args"][argument][1].get(self._lang, "")

    def getProgrammaticCategoryName(self, programmatic_name):
        return meta.CATEGORY

    def getDisplayCategoryName(self, programmatic_name):
        return meta.CATEGORY

    # ----- XServiceName: Calc ignores an add-in that lacks it; the name is the key of its CalcAddIns.xcu --
    def getServiceName(self):
        return IMPLEMENTATION

    # ----- XServiceInfo ---------------------------------------------------------------------
    def getImplementationName(self):
        return IMPLEMENTATION

    def supportsService(self, name):
        return name in SERVICES

    def getSupportedServiceNames(self):
        return SERVICES


g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation(RiotFunctions, IMPLEMENTATION, SERVICES)
