"""Unit tests that need neither LibreOffice nor a display."""

import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from riot_office import config, i18n, inventory, libreoffice, pdftools
from riot_office.paths import CONFIG_DIR


# ----- i18n -------------------------------------------------------------------------------
def test_every_text_has_english_and_italian():
    for key, texts in i18n.T.items():
        assert set(texts) == set(i18n.LANGUAGES), key
        assert all(value.strip() for value in texts.values()), key


def test_texts_stay_within_latin1_except_windows_dots():
    # Linux Tk may only draw Latin-1; the ellipsis is substituted per platform through {dots}.
    for key, texts in i18n.T.items():
        for value in texts.values():
            value.encode("latin-1")


def test_every_language_has_a_libreoffice_locale():
    assert set(i18n.LIBREOFFICE_LOCALES) == set(i18n.LANGUAGES)


def test_language_is_saved(tmp_path, monkeypatch):
    monkeypatch.setattr(i18n, "SETTINGS", tmp_path / "settings.json")
    monkeypatch.setattr(i18n, "_settings_cache", None)
    i18n.set_language("it")
    monkeypatch.setattr(i18n, "_settings_cache", None)
    assert i18n.get_language() == "it"
    assert i18n.t("done") == "Fatto"
    with pytest.raises(ValueError):
        i18n.set_language("xx")


def test_system_language_from_environment(monkeypatch):
    monkeypatch.setattr(i18n.sys, "platform", "linux")  # the Windows branch asks the OS instead
    monkeypatch.setenv("LC_ALL", "it_IT.UTF-8")
    assert i18n.system_language() == "it"
    monkeypatch.setenv("LC_ALL", "fr_FR.UTF-8")
    monkeypatch.setenv("LANG", "de_DE.UTF-8")
    assert i18n.system_language() == "en"


# ----- configuration ------------------------------------------------------------------------
def _xcd_values() -> dict[str, str]:
    values = {}
    for xcd in config.shipped_files():
        for prop in ET.parse(xcd).getroot().iter("prop"):
            values[prop.get("{http://openoffice.org/2001/registry}name")] = prop.findtext("value")
    return values


def test_xcd_files_are_well_formed_and_set_ooxml_defaults():
    names = [f.name for f in config.shipped_files()]
    assert names == ["riot-office-calc.xcd", "riot-office-impress.xcd", "riot-office-writer.xcd", "riot-office.xcd"]
    text = "".join(f.read_text(encoding="utf-8") for f in config.shipped_files())
    for filter_name in ("MS Word 2007 XML", "Calc MS Excel 2007 XML", "Impress MS PowerPoint 2007 XML"):
        assert f"<value>{filter_name}</value>" in text
    assert _xcd_values()["WarnAlienFormat"] == "false"


def test_module_files_depend_on_their_module():
    # LibreOffice loads the registry files in no fixed order; only <dependency> orders them.
    for module in ("writer", "calc", "impress"):
        text = (CONFIG_DIR / f"riot-office-{module}.xcd").read_text(encoding="utf-8")
        assert f'<dependency file="{module}"/>' in text


def _fake_installation(tmp_path):
    program = tmp_path / "LibreOffice" / "program"
    program.mkdir(parents=True)
    (program / "soffice").write_text("")
    return libreoffice.Installation(program / "soffice")


def test_install_and_uninstall(tmp_path):
    inst = _fake_installation(tmp_path)
    assert not config.is_installed(inst)
    written = config.install(inst)
    assert len(written) == 4
    assert written[0].parent == tmp_path / "LibreOffice" / "share" / "registry"
    assert config.is_installed(inst)
    (inst.registry_dir / "riot-office-old.xcd").write_text("<oor:data/>")  # left by an older version
    config.install(inst)
    assert not (inst.registry_dir / "riot-office-old.xcd").exists()
    (inst.registry_dir / "riot-office-calc.xcd").write_text("changed")
    assert not config.is_installed(inst)
    assert config.uninstall(inst)
    assert not config.uninstall(inst)


def test_install_refuses_broken_xcd(tmp_path):
    program = tmp_path / "program"
    program.mkdir()
    bad = tmp_path / "riot-office-bad.xcd"
    bad.write_text("<oor:data")
    with pytest.raises(ET.ParseError):
        config.install(libreoffice.Installation(program / "soffice"), bad)


def test_ui_locale_new_profile(tmp_path):
    path = config.set_ui_locale("it", tmp_path)
    assert path.name == "registrymodifications.xcu"
    assert config.get_ui_locale(tmp_path) == "it"


def test_ui_locale_keeps_other_settings(tmp_path):
    existing = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
        '<item oor:path="/org.openoffice.Office.Common/Misc"><prop oor:name="FirstRun" oor:op="fuse"><value>false</value></prop></item>\n'
        '<item oor:path="/org.openoffice.Office.Linguistic/General"><prop oor:name="UILocale" oor:op="fuse"><value>en-US</value></prop></item>\n'
        "</oor:items>\n")
    (tmp_path / "registrymodifications.xcu").write_text(existing, encoding="utf-8")
    config.set_ui_locale("it", tmp_path)
    text = (tmp_path / "registrymodifications.xcu").read_text(encoding="utf-8")
    assert "FirstRun" in text
    assert text.count("UILocale") == 1
    assert config.get_ui_locale(tmp_path) == "it"


# ----- LibreOffice helpers --------------------------------------------------------------------
def test_module_for_extensions():
    assert libreoffice.module_for(Path("a.DOCX")) == "writer"
    assert libreoffice.module_for(Path("a.xlsm")) == "calc"
    assert libreoffice.module_for(Path("a.pptx")) == "impress"
    assert libreoffice.module_for(Path("a.unknown")) == "writer"


def test_convert_names_filters_explicitly(tmp_path, monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        out = Path(args[args.index("--outdir") + 1])
        (out / (Path(args[-1]).stem + "." + args[args.index("--convert-to") + 1].split(":")[0])).write_text("x")

        class Done:
            returncode, stdout, stderr = 0, "", ""
        return Done()

    monkeypatch.setattr(libreoffice.subprocess, "run", fake_run)
    monkeypatch.setattr(libreoffice, "CONVERT_PROFILE", tmp_path / "profile")
    inst = libreoffice.Installation(tmp_path / "soffice")
    html = tmp_path / "a.html"
    html.write_text("<p>x</p>")
    libreoffice.convert(inst, [html], tmp_path / "out", "docx")
    args = calls[-1]
    assert "--infilter=HTML (StarWriter)" in args
    assert args[args.index("--convert-to") + 1] == "docx:MS Word 2007 XML"
    sheet = tmp_path / "b.csv"
    sheet.write_text("1,2")
    libreoffice.convert(inst, [sheet], tmp_path / "out", "pdf", pdfa=True)
    spec = calls[-1][calls[-1].index("--convert-to") + 1]
    assert spec.startswith("pdf:calc_pdf_Export:") and "SelectPdfVersion" in spec


def test_version_from_ini(tmp_path):
    program = tmp_path / "program"
    program.mkdir()
    (program / "version.ini").write_text("[Version]\nMsiProductVersion=26.8.3.2\nbuildid=abc\n")
    assert libreoffice.Installation(program / "soffice").version() == "26.8.3.2"


def test_find_uses_environment(tmp_path, monkeypatch):
    program = tmp_path / "program"
    program.mkdir()
    soffice = program / "soffice"
    soffice.write_text("")
    monkeypatch.setenv("RIOT_SOFFICE", str(soffice))
    assert libreoffice.find().soffice == soffice


# ----- PDF tools ------------------------------------------------------------------------------
def make_pdf(path: Path, pages: int, width: int = 200) -> Path:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=width, height=300)
    with open(path, "wb") as f:
        writer.write(f)
    return path


def test_parse_pages():
    assert pdftools.parse_pages("", 3) == [0, 1, 2]
    assert pdftools.parse_pages("1, 3-4", 5) == [0, 2, 3]
    with pytest.raises(ValueError):
        pdftools.parse_pages("2-9", 5)
    assert pdftools.parse_ranges("", 2) == [(1, 1), (2, 2)]
    assert pdftools.parse_ranges("1-2,3", 3) == [(1, 2), (3, 3)]


def test_merge_split_rotate(tmp_path):
    a = make_pdf(tmp_path / "a.pdf", 2, width=200)
    b = make_pdf(tmp_path / "b.pdf", 3, width=250)
    merged = pdftools.merge([a, b], tmp_path / "out" / "merged.pdf")
    reader = PdfReader(merged)
    assert len(reader.pages) == 5
    assert float(reader.pages[2].mediabox.width) == 250
    assert [o.title for o in reader.outline] == ["a", "b"]

    parts = pdftools.split(merged, tmp_path / "parts", "1-2,3-5")
    assert [p.name for p in parts] == ["merged_p1-2.pdf", "merged_p3-5.pdf"]
    assert [len(PdfReader(p).pages) for p in parts] == [2, 3]
    assert len(pdftools.split(a, tmp_path / "single")) == 2

    rotated = pdftools.rotate(merged, tmp_path / "rotated.pdf", 90, "2")
    pages = PdfReader(rotated).pages
    assert [p.rotation for p in pages] == [0, 90, 0, 0, 0]
    with pytest.raises(ValueError):
        pdftools.rotate(merged, tmp_path / "x.pdf", 45)


# ----- inventory ------------------------------------------------------------------------------
def make_zip(path: Path, files: dict[str, str | bytes]) -> Path:
    with zipfile.ZipFile(path, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return path


def test_inventory_finds_excel_features(tmp_path):
    sheet = ('<worksheet><sheetData><row><c><f>_xlfn.LAMBDA(x,x+1)(2)</f></c>'
             '<c><f>_xlfn._xlws.GROUPBY(A1:A3,B1:B3,SUM)</f></c><c><f>_xlfn.IMAGE("x")</f></c><c><f>_xlfn.XLOOKUP(1,A:A,B:B)</f></c></row></sheetData></worksheet>')
    make_zip(tmp_path / "model.xlsm", {
        "[Content_Types].xml": "<Types/>",
        "xl/workbook.xml": "<workbook/>",
        "xl/worksheets/sheet1.xml": sheet,
        "xl/vbaProject.bin": b"\x00",
        "xl/connections.xml": '<connections><connection name="Query - Sales" connectionString="Provider=Microsoft.Mashup.OleDb.1"/></connections>',
        "xl/model/item.data": b"\x00",
        "xl/slicers/slicer1.xml": "<slicers/>",
        "xl/pivotTables/pivotTable1.xml": "<pivotTableDefinition/>",
        "xl/theme/theme1.xml": '<a:theme><a:latin typeface="Aptos"/></a:theme>',
    })
    make_zip(tmp_path / "clean.docx", {"word/document.xml": "<w:document/>"})
    (tmp_path / "~$lock.docx").write_bytes(b"")
    (tmp_path / "plan.mpp").write_bytes(b"x")

    reports = {r.path.name: r for r in inventory.scan(tmp_path)}
    assert set(reports) == {"model.xlsm", "clean.docx", "plan.mpp"}
    model = reports["model.xlsm"]
    assert {"macros", "power_query", "data_model", "slicers", "pivot_tables", "functions_later", "functions_riot",
            "functions_missing", "aptos_font"} <= model.findings
    assert model.functions == {"LAMBDA", "GROUPBY", "IMAGE"}  # XLOOKUP is supported
    assert reports["clean.docx"].ok
    assert reports["plan.mpp"].findings == {"not_supported_format"}

    report = inventory.markdown(list(reports.values()), tmp_path)
    assert "**3 files scanned**" in report
    assert "| GROUPBY | 1 | Riot add-in |" in report and "| IMAGE | 1 | missing |" in report
    inventory.write_csv(list(reports.values()), tmp_path / "inv.csv", tmp_path)
    assert "model.xlsm" in (tmp_path / "inv.csv").read_text(encoding="utf-8")


def test_inventory_legacy_and_encrypted(tmp_path):
    ole = inventory.OLE_MAGIC + b"\x00" * 64
    (tmp_path / "macro.xls").write_bytes(ole + "_VBA_PROJECT".encode("utf-16-le"))
    (tmp_path / "locked.docx").write_bytes(ole + "EncryptionInfo".encode("utf-16-le"))
    (tmp_path / "broken.doc").write_bytes(b"not an office file")
    reports = {r.path.name: r for r in inventory.scan(tmp_path)}
    assert "macros" in reports["macro.xls"].findings
    assert reports["locked.docx"].findings == {"encrypted"}
    assert reports["broken.doc"].findings == {"unreadable"}
