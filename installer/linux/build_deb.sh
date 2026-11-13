#!/usr/bin/env bash
# Builds dist/riot-office_<version>_all.deb for Ubuntu 24.04 / 26.04 (and Debian 12+).
#
#   bash installer/linux/build_deb.sh
#
# The package contains only Riot Office's own files. LibreOffice, the Italian language pack,
# the fonts and the dictionaries come from the distribution's repositories as dependencies,
# so they keep receiving the distribution's security updates.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VERSION="$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$ROOT/riot_office/__init__.py")"
PKG="$ROOT/build/linux/riot-office_${VERSION}_all"
OUT="$ROOT/dist/riot-office_${VERSION}_all.deb"

rm -rf "$PKG"
install -d "$PKG/DEBIAN" "$PKG/usr/lib/riot-office/riot_office" "$PKG/usr/lib/riot-office/config" \
    "$PKG/usr/lib/riot-office/assets" "$PKG/usr/lib/riot-office/docs" "$PKG/usr/lib/riot-office/addins" "$PKG/usr/bin" \
    "$PKG/etc/libreoffice/registry" "$PKG/usr/share/applications" \
    "$PKG/usr/share/icons/hicolor/256x256/apps" "$PKG/usr/share/doc/riot-office"

install -m 644 "$ROOT"/riot_office/*.py "$PKG/usr/lib/riot-office/riot_office/"
install -m 644 "$ROOT"/config/riot-office*.xcd "$PKG/usr/lib/riot-office/config/"
# The configuration layers LibreOffice reads (conffiles: local edits survive upgrades).
install -m 644 "$ROOT"/config/riot-office*.xcd "$PKG/etc/libreoffice/registry/"
# The Excel functions for Calc: an extension that postinst registers with LibreOffice for every user.
python3 "$ROOT/addins/calc/build_oxt.py" --out "$PKG/usr/lib/riot-office/addins" >/dev/null
chmod 644 "$PKG"/usr/lib/riot-office/addins/*.oxt
install -m 644 "$ROOT/assets/icon.png" "$PKG/usr/lib/riot-office/assets/"
install -m 644 "$ROOT/assets/icon.png" "$PKG/usr/share/icons/hicolor/256x256/apps/riot-office.png"
install -m 644 "$ROOT/docs/Guide.html" "$PKG/usr/lib/riot-office/docs/"
install -m 644 "$ROOT/LICENSE.txt" "$PKG/usr/share/doc/riot-office/copyright"
install -m 644 "$ROOT/installer/THIRD-PARTY-NOTICES.txt" "$PKG/usr/share/doc/riot-office/"
install -m 644 "$ROOT/CHANGELOG.md" "$PKG/usr/share/doc/riot-office/"

# Isolated mode (-I): the user's own Python packages and PYTHONPATH never leak in.
cat > "$PKG/usr/bin/riot-office" <<'EOF'
#!/bin/sh
exec /usr/bin/python3 -I -c 'import sys; sys.path.insert(0, "/usr/lib/riot-office"); from riot_office.cli import main; sys.exit(main())' "$@"
EOF
chmod 755 "$PKG/usr/bin/riot-office"

desktop() {  # file name, Name, Name[it], Comment, Comment[it], arguments
    cat > "$PKG/usr/share/applications/$1.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=$2
Name[it]=$3
Comment=$4
Comment[it]=$5
Exec=riot-office $6
Icon=riot-office
Terminal=false
Categories=Office;
StartupWMClass=riot-office
EOF
}
desktop riot-office "Riot Office" "Riot Office" "Local office suite built on LibreOffice" \
    "Suite per ufficio locale basata su LibreOffice" ""
desktop riot-writer "Riot Writer" "Riot Writer" "Documents (.docx, .odt)" "Documenti (.docx, .odt)" "open writer"
desktop riot-calc "Riot Calc" "Riot Calc" "Spreadsheets (.xlsx, .ods)" "Fogli di calcolo (.xlsx, .ods)" "open calc"
desktop riot-impress "Riot Impress" "Riot Impress" "Presentations (.pptx, .odp)" "Presentazioni (.pptx, .odp)" "open impress"

(cd "$PKG" && find etc -type f | sed 's#^#/#' | sort) > "$PKG/DEBIAN/conffiles"
SIZE="$(du -sk "$PKG" | cut -f1)"
cat > "$PKG/DEBIAN/control" <<EOF
Package: riot-office
Version: $VERSION
Section: editors
Priority: optional
Architecture: all
Installed-Size: $SIZE
Maintainer: Orso Peruzzi <battles5@users.noreply.github.com>
Homepage: https://github.com/battles5/riot-office
Depends: python3 (>= 3.10), python3-tk, python3-pypdf (>= 4.0), python3-uno,
 libreoffice-writer, libreoffice-calc, libreoffice-impress, libreoffice-l10n-it,
 fonts-crosextra-carlito, fonts-crosextra-caladea, fonts-liberation2 | fonts-liberation,
 hunspell-it, hunspell-en-us
Recommends: libreoffice-help-it, libreoffice-help-en-us, hyphen-it, mythes-it,
 libreoffice-gtk3 | libreoffice-gnome, ocrmypdf, tesseract-ocr-ita, tesseract-ocr-eng
Description: RIOT OFFICE - loud colours, local files
 A local desktop office suite built on LibreOffice: Writer, Calc and Impress
 configured to save as .docx/.xlsx/.pptx by default, with the tabbed interface,
 metric-compatible fonts, English and Italian. Adds Excel functions Calc lacks
 (GROUPBY, PIVOTBY, PERCENTOF, REGEXTEST/EXTRACT/REPLACE), a synthwave launcher
 with PDF tools (merge, split, rotate, convert, OCR), a compatibility inventory
 and a fidelity check against Microsoft Office.
EOF

# Register the Excel functions with LibreOffice for every user. unopkg wants a profile folder of
# its own: use a throw-away one, so nothing is left behind in root's home.
cat > "$PKG/DEBIAN/postinst" <<'POSTINST'
#!/bin/sh
set -e
if [ "$1" = configure ] && command -v unopkg >/dev/null 2>&1; then
    profile=file:///var/tmp/riot-office-unopkg
    for oxt in /usr/lib/riot-office/addins/RiotOffice-ExcelFunctions-*.oxt; do
        unopkg add --shared --suppress-license "-env:UserInstallation=$profile" "$oxt" \
            || echo "riot-office: could not register the Excel functions; run: sudo riot-office addin install" >&2
    done
    rm -rf /var/tmp/riot-office-unopkg
fi
exit 0
POSTINST
cat > "$PKG/DEBIAN/prerm" <<'PRERM'
#!/bin/sh
set -e
if [ "$1" = remove ] && command -v unopkg >/dev/null 2>&1; then
    unopkg remove --shared "-env:UserInstallation=file:///var/tmp/riot-office-unopkg" org.riotoffice.excel-functions >/dev/null 2>&1 || true
    rm -rf /var/tmp/riot-office-unopkg
fi
exit 0
PRERM
chmod 755 "$PKG/DEBIAN/postinst" "$PKG/DEBIAN/prerm"

mkdir -p "$ROOT/dist"
dpkg-deb --root-owner-group --build "$PKG" "$OUT"
echo "ready: $OUT"
