import zipfile
import os
from pathlib import Path
import xml.etree.ElementTree as ET


# Always resolve paths relative to THIS script location
BASE_DIR = Path(__file__).resolve().parent

# New workbook
XLSX = BASE_DIR / "The rest.xlsx"

# Make the output folder depend on the workbook name automatically
OUT_DIR = BASE_DIR / f"exported_images_{XLSX.stem}"


def normpath(p: str) -> str:
    parts = []
    for seg in p.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if parts:
                parts.pop()
        else:
            parts.append(seg)
    return "/".join(parts)


def parse_workbook_sheets(zf: zipfile.ZipFile):
    """
    Returns list of (sheet_name, sheet_target) where sheet_target is like
    'worksheets/sheet1.xml' in workbook order.
    """
    wbxml = ET.fromstring(zf.read("xl/workbook.xml"))
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rns = {"rel": "http://schemas.openxmlformats.org/package/2006/relationships"}
    rid_to_target = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels.findall("rel:Relationship", rns)
    }

    out = []
    for sh in wbxml.find("m:sheets", ns):
        name = sh.attrib["name"]
        rid = sh.attrib.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        )
        target = rid_to_target[rid]
        out.append((name, target))
    return out


def drawing_path_for_sheet(zf: zipfile.ZipFile, sheet_target: str):
    """
    For a sheet xml target 'worksheets/sheetN.xml', find its drawing xml path
    'xl/drawings/drawingX.xml'.
    """
    sheet_xml = ET.fromstring(zf.read("xl/" + sheet_target))
    ns = {
        "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }
    drawing = sheet_xml.find("m:drawing", ns)
    if drawing is None:
        return None

    rid = drawing.attrib.get(
        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    )
    rel_path = "xl/worksheets/_rels/" + os.path.basename(sheet_target) + ".rels"
    rels_xml = ET.fromstring(zf.read(rel_path))
    rns = {"rel": "http://schemas.openxmlformats.org/package/2006/relationships"}

    for rel in rels_xml.findall("rel:Relationship", rns):
        if rel.attrib["Id"] == rid:
            return "xl/" + normpath(rel.attrib["Target"])
    return None


def images_for_drawing(zf: zipfile.ZipFile, drawing_path: str):
    """
    Returns list of (row, col, media_path) sorted by anchor position.
    media_path returned as 'xl/media/imageNN.png'.
    """
    dp = drawing_path[3:] if drawing_path.startswith("xl/") else drawing_path
    dp = normpath(dp)

    drawing_xml = ET.fromstring(zf.read("xl/" + dp))
    ns = {
        "xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }

    rel_path = "xl/drawings/_rels/" + os.path.basename(dp) + ".rels"
    rels_xml = ET.fromstring(zf.read(rel_path))
    rns = {"rel": "http://schemas.openxmlformats.org/package/2006/relationships"}

    rid_to_media = {}
    for rel in rels_xml.findall("rel:Relationship", rns):
        tgt = rel.attrib.get("Target", "")
        if "media/" in tgt:
            rid_to_media[rel.attrib["Id"]] = "xl/" + normpath(tgt)

    out = []
    for anchor in drawing_xml.findall("xdr:twoCellAnchor", ns):
        frm = anchor.find("xdr:from", ns)
        if frm is None:
            continue

        row = int(frm.find("xdr:row", ns).text)
        col = int(frm.find("xdr:col", ns).text)

        pic = anchor.find("xdr:pic", ns)
        if pic is None:
            continue

        blip = pic.find(".//a:blip", ns)
        if blip is None:
            continue

        rid = blip.attrib.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
        )
        media = rid_to_media.get(rid)
        if media:
            out.append((row, col, media))

    out.sort(key=lambda t: (t[0], t[1]))
    return out


def safe_folder_name(name: str) -> str:
    return "".join(
        ch if ch.isalnum() or ch in ("-", "_", " ") else "_"
        for ch in name
    ).strip()


def main():
    if not XLSX.exists():
        raise FileNotFoundError(f"Workbook not found: {XLSX}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    total = 0
    with zipfile.ZipFile(XLSX, "r") as zf:
        sheets = parse_workbook_sheets(zf)

        print(f"Workbook: {XLSX.name}")
        print("Sheets found:")
        for sheet_name, _ in sheets:
            print(f"  - {sheet_name}")
        print()

        for sheet_name, sheet_target in sheets:
            drawing_path = drawing_path_for_sheet(zf, sheet_target)
            if drawing_path is None:
                print(f"{sheet_name}: no drawing found")
                continue

            anchors = images_for_drawing(zf, drawing_path)
            if not anchors:
                print(f"{sheet_name}: drawing found, but no images anchored")
                continue

            sheet_dir = OUT_DIR / safe_folder_name(sheet_name)
            sheet_dir.mkdir(parents=True, exist_ok=True)

            for i, (_r, _c, media_path) in enumerate(anchors, start=1):
                img_bytes = zf.read(media_path)
                base = Path(media_path).name
                out_name = f"{i:04d}_{base}"
                (sheet_dir / out_name).write_bytes(img_bytes)
                total += 1

            print(f"{sheet_name}: wrote {len(anchors)} images -> {sheet_dir}")

    print(f"\nExtracted {total} images total")
    print(f"Wrote to: {OUT_DIR}")


if __name__ == "__main__":
    main()
