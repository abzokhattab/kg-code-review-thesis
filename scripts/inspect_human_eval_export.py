#!/usr/bin/env python3
"""Read a Human Eval spreadsheet export without adding a dependency.

An .xlsx is a zip of XML, so the pinned environment does not need openpyxl for
a one-off inspection of a pilot export. Used to check that a full end-to-end
run through the study UI lands every field the instrument claims to record.

Usage:
    python3 scripts/inspect_human_eval_export.py "/path/to/Human Eval.xlsx"
"""

import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def _col_index(ref):
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def read_workbook(path):
    """Return {sheet_name: [row, ...]} where each row is a list of strings."""
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall(f"{NS}si"):
                shared.append("".join(t.text or "" for t in si.iter(f"{NS}t")))

        rels = {}
        rel_root = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        for rel in rel_root:
            rels[rel.get("Id")] = rel.get("Target")

        sheets = {}
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        for sh in wb.find(f"{NS}sheets"):
            target = rels[sh.get(f"{REL_NS}id")].lstrip("/")
            if not target.startswith("xl/"):
                target = "xl/" + target
            sheets[sh.get("name")] = read_sheet(z, target, shared)
        return sheets


def read_sheet(z, target, shared):
    root = ET.fromstring(z.read(target))
    rows = []
    for row in root.iter(f"{NS}row"):
        cells = {}
        for c in row.findall(f"{NS}c"):
            idx = _col_index(c.get("r"))
            if c.get("t") == "s":
                v = c.find(f"{NS}v")
                cells[idx] = shared[int(v.text)] if v is not None else ""
            elif c.get("t") == "inlineStr":
                cells[idx] = "".join(t.text or "" for t in c.iter(f"{NS}t"))
            else:
                v = c.find(f"{NS}v")
                cells[idx] = v.text if v is not None else ""
        if cells:
            width = max(cells) + 1
            rows.append([cells.get(i, "") for i in range(width)])
    return rows


def main():
    path = sys.argv[1]
    for name, rows in read_workbook(path).items():
        print(f"\n{'=' * 70}\nSHEET: {name}   ({len(rows)} rows incl. header)\n{'=' * 70}")
        if not rows:
            print("  (empty)")
            continue
        header = rows[0]
        print("columns:", header)
        for r in rows[1:]:
            print("-" * 60)
            for i, col in enumerate(header):
                val = r[i] if i < len(r) else ""
                flag = "" if str(val).strip() else "   <-- EMPTY"
                shown = str(val)
                if len(shown) > 160:
                    shown = shown[:160] + f"... [{len(str(val))} chars]"
                print(f"  {col:<22} {shown}{flag}")


if __name__ == "__main__":
    main()
