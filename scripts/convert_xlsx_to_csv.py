#!/usr/bin/env python3
"""Convert a Google-Sheets .xlsx export into one CSV per tab, stdlib only.

The study analysers consume the Sheet's CSV export. Downloading the workbook as
.xlsx is the path of least resistance in the Sheets UI, so this bridges the two
without adding openpyxl/pandas to the pinned environment.

Usage:
  python3 scripts/convert_xlsx_to_csv.py "Human Eval (5).xlsx" --outdir /tmp/heval
  python3 scripts/convert_xlsx_to_csv.py book.xlsx --tab responses_criteria
"""

from __future__ import annotations

import argparse
import csv
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def _text(node) -> str:
    """Concatenate the text runs of a shared-string or inline-string node."""
    if node is None:
        return ""
    return "".join(t.text or "" for t in node.iter(f"{{{NS['m']}}}t"))


def _shared_strings(z: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    return [_text(si) for si in root.findall("m:si", NS)]


def _sheet_paths(z: zipfile.ZipFile) -> list[tuple[str, str]]:
    """[(tab name, zip path)] in workbook order, resolved via the rels file."""
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target = {
        rel.get("Id"): rel.get("Target")
        for rel in rels.iter("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship")
    }
    book = ET.fromstring(z.read("xl/workbook.xml"))
    out = []
    for sheet in book.findall("m:sheets/m:sheet", NS):
        rid = sheet.get(f"{{{NS['r']}}}id")
        path = target.get(rid, "")
        if path.startswith("/"):
            path = path[1:]
        elif not path.startswith("xl/"):
            path = "xl/" + path
        out.append((sheet.get("name", rid), path))
    return out


def _col_index(ref: str) -> int:
    """'BC12' -> zero-based column 54."""
    letters = re.match(r"([A-Z]+)", ref or "A").group(1)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def read_tab(z: zipfile.ZipFile, path: str, shared: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    root = ET.fromstring(z.read(path))
    for row in root.findall("m:sheetData/m:row", NS):
        cells: list[str] = []
        for c in row.findall("m:c", NS):
            idx = _col_index(c.get("r", ""))
            # Sheets omits empty cells entirely; pad so columns stay aligned
            # with the header, which is how the analysers address fields.
            while len(cells) < idx:
                cells.append("")
            ctype = c.get("t")
            if ctype == "s":
                v = c.find("m:v", NS)
                i = int(v.text) if v is not None and v.text else -1
                cells.append(shared[i] if 0 <= i < len(shared) else "")
            elif ctype == "inlineStr":
                cells.append(_text(c.find("m:is", NS)))
            else:
                v = c.find("m:v", NS)
                cells.append(v.text if v is not None and v.text is not None else "")
        rows.append(cells)
    width = max((len(r) for r in rows), default=0)
    for r in rows:
        while len(r) < width:
            r.append("")
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx")
    ap.add_argument("--outdir", default=None,
                    help="default: alongside the workbook, <stem>_csv/")
    ap.add_argument("--tab", action="append", default=None,
                    help="only these tabs (repeatable)")
    args = ap.parse_args()

    src = Path(args.xlsx).expanduser()
    outdir = Path(args.outdir).expanduser() if args.outdir else src.with_name(src.stem + "_csv")
    outdir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(src) as z:
        shared = _shared_strings(z)
        for name, path in _sheet_paths(z):
            if args.tab and name not in args.tab:
                continue
            rows = read_tab(z, path, shared)
            dest = outdir / (re.sub(r"[^\w.-]+", "_", name) + ".csv")
            with dest.open("w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerows(rows)
            print(f"{name}: {len(rows)} rows x {len(rows[0]) if rows else 0} cols -> {dest}")


if __name__ == "__main__":
    main()
