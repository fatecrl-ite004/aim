"""Generate the editable physical ER diagram directly from migration 001.

This only reads the migration and writes documentation; it never connects to a DB.
Run from any directory: python scripts/diagrams/generate_mer_v1.py
"""

from __future__ import annotations

import html
import re
import textwrap
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "system/backend/aim/migrations/001_init.sql"
OUTPUT = ROOT / "docs/monografia/mer-v1.drawio"
ROW = 24
WIDTH = 390
HEADER = 30


def split_items(body: str) -> list[str]:
    depth = 0
    quote = False
    start = 0
    result = []
    for i, char in enumerate(body):
        if char == "'":
            quote = not quote
        elif not quote:
            depth += (char == "(") - (char == ")")
            if char == "," and depth == 0:
                result.append(body[start:i].strip())
                start = i + 1
    result.append(body[start:].strip())
    return result


def names(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(","))


def parse_schema() -> dict:
    tables = {}
    for match in re.finditer(r"CREATE TABLE (\w+)\s*\((.*?)\n\);", SOURCE.read_text(encoding="utf-8"), re.S):
        table_name, body = match.groups()
        table = {"name": table_name, "columns": [], "pk": (), "fk": [], "uq": []}
        for item in split_items(body):
            compact = " ".join(item.split())
            if compact.startswith("FOREIGN KEY"):
                fk = re.fullmatch(r"FOREIGN KEY \(([^)]+)\) REFERENCES (\w+)\(([^)]+)\)(?: ON DELETE (CASCADE|RESTRICT))?", compact)
                assert fk, compact
                table["fk"].append((names(fk[1]), fk[2], names(fk[3]), fk[4] or "NO ACTION"))
            elif compact.startswith("PRIMARY KEY"):
                table["pk"] = names(re.search(r"\(([^)]+)\)", compact)[1])
            elif compact.startswith("UNIQUE"):
                table["uq"].append(names(re.search(r"\(([^)]+)\)", compact)[1]))
            elif not compact.startswith("CHECK"):
                column = re.match(r"(\w+) (.*)", compact)
                name, declaration = column.groups()
                datatype = re.split(r"\s+(?:PRIMARY|NOT|REFERENCES|DEFAULT|CHECK|UNIQUE)\b", declaration, maxsplit=1)[0]
                primary = "PRIMARY KEY" in declaration
                table["columns"].append((name, datatype, primary or "NOT NULL" in declaration))
                if primary:
                    table["pk"] = (name,)
                inline = re.search(r"REFERENCES (\w+)\(([^)]+)\)(?: ON DELETE (CASCADE|RESTRICT))?", declaration)
                if inline:
                    table["fk"].append(((name,), inline[1], names(inline[2]), inline[3] or "NO ACTION"))
        tables[table_name] = table
    assert len(tables) == 14, "Review page assignments if the migration changes"
    return tables


# Every table has one complete view. Repeated tables show only the key projection.
# Compact columns follow the relationship direction and keep cards on a regular grid.
PAGES = [
    ("1 · Replay e identidade", "Contexto, serviços, instâncias e eventos de referência", [
        ("replay_run", 520, 160, False),
        ("service_entity", 60, 160, False),
        ("service_instance", 60, 570, False),
        ("ingest_batch", 980, 160, False),
        ("ground_truth_event", 520, 790, False),
    ], ["service_entity", "service_instance", "ingest_batch", "ground_truth_event"]),
    ("2 · Telemetria bruta", "Catálogo de origem, identidade da série e pontos recebidos", [
        ("source_metric_definition", 60, 160, False),
        ("service_instance", 520, 160, True),
        ("metric_series", 520, 570, False),
        ("raw_metric_point", 980, 570, False),
        ("replay_run", 60, 790, True),
        ("ingest_batch", 980, 160, True),
    ], ["metric_series", "raw_metric_point"]),
    ("3 · Transformação e janelas", "Execução versionada e janela de observação por instância", [
        ("replay_run", 60, 160, True),
        ("service_instance", 980, 160, True),
        ("transform_run", 520, 160, False),
        ("observation_window", 520, 570, False),
    ], ["transform_run", "observation_window"]),
    ("4 · Métricas derivadas", "Cobertura e valor são registros distintos para a mesma janela e definição", [
        ("observation_window", 60, 160, True),
        ("metric_coverage", 520, 160, False),
        ("derived_metric_point", 520, 570, False),
        ("derived_metric_definition", 980, 350, False),
    ], ["metric_coverage", "derived_metric_point"]),
    ("5 · Proveniência", "A associação N:M preserva os pontos brutos usados em cada valor derivado", [
        ("raw_metric_point", 60, 160, True),
        ("derived_point_source", 520, 160, False),
        ("derived_metric_point", 980, 160, True),
    ], ["derived_point_source"]),
]


def cell(graph_root, cell_id: str, value: str, style: str, x: int, y: int, w: int, h: int, **extra):
    item = ET.SubElement(graph_root, "mxCell", id=cell_id, value=value, style=style, vertex="1", **extra)
    ET.SubElement(item, "mxGeometry", x=str(x), y=str(y), width=str(w), height=str(h), **{"as": "geometry"})
    return item


def generate() -> None:
    tables = parse_schema()
    owners = {name: index for index, (_, _, nodes, _) in enumerate(PAGES, 1) for name, _, _, ref in nodes if not ref}
    assert set(owners) == set(tables)
    file = ET.Element("mxfile", host="app.diagrams.net", agent="AIM", version="24.7.17", type="device")
    represented = set()
    counts = []
    for page_number, (page_title, subtitle, nodes, children) in enumerate(PAGES, 1):
        diagram = ET.SubElement(file, "diagram", id=f"aim-mer-v1-{page_number}", name=page_title)
        model = ET.SubElement(diagram, "mxGraphModel", adaptiveColors="auto", dx="1450", dy="1100", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="1450", pageHeight="1100", math="0", shadow="0")
        root = ET.SubElement(model, "root")
        ET.SubElement(root, "mxCell", id="0")
        ET.SubElement(root, "mxCell", id="1", parent="0")
        text_style = "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=top;fontFamily=Arial;fontColor=#1F2937;"
        cell(root, "title", f"AIM · MER físico da V1 | {page_title}", text_style + "fontSize=22;fontStyle=1;", 50, 20, 1320, 34, parent="1")
        cell(root, "subtitle", subtitle, text_style + "fontSize=15;", 50, 58, 1320, 26, parent="1")
        cell(root, "legend", "PK chave primária  ·  FK chave estrangeira  ·  UQ unicidade  ·  ? aceita NULL  ·  1 para 0..N", text_style + "fontSize=13;", 50, 91, 1320, 24, parent="1")
        present = {name for name, *_ in nodes}
        # Reference views only expose the key columns used in this page's links.
        relevant = defaultdict(set)
        grouped = defaultdict(list)
        for child in children:
            for number, fk in enumerate(tables[child]["fk"], 1):
                fields, parent, parent_fields, _ = fk
                assert parent in present, (page_number, child, parent)
                grouped[(parent, child)].append((number, fk))
                relevant[child].update(fields)
                relevant[parent].update(parent_fields)
                represented.add((child, number))
        for name, x, y, reference in nodes:
            table = tables[name]
            columns = table["columns"]
            if reference:
                exposed = relevant[name] | set(table["pk"])
                columns = [col for col in columns if col[0] in exposed]
            rows = []
            for column_name, datatype, required in columns:
                tags = []
                if column_name in table["pk"]:
                    tags.append("PK")
                if any(column_name in fk[0] for fk in table["fk"]):
                    tags.append("FK")
                marker = "/".join(tags)
                label = (marker, column_name, datatype + ("" if required else " ?"))
                rows.append((column_name, label, 28, bool(tags)))
            if reference:
                rows.append(("reference", f"Tabela completa na aba {owners[name]}", 24, False))
            else:
                for number, uq in enumerate(table["uq"], 1):
                    # Wrap composite UQs after each column rather than shrinking the text.
                    value = f"UQ{number} ({', '.join(uq)})"
                    lines = textwrap.wrap(value, width=48, break_long_words=False, break_on_hyphens=False)
                    wrapped = "<br>".join(html.escape(line) for line in lines)
                    rows.append((f"uq{number}", wrapped, 21 * len(lines), False))
            total_height = HEADER + sum(row[2] for row in rows)
            color = "#FFF8D8" if reference else "#FFF2B2"
            style = f"swimlane;html=1;startSize={HEADER};horizontal=1;childLayout=stackLayout;horizontalStack=0;resizeParent=1;resizeParentMax=0;collapsible=0;rounded=0;whiteSpace=wrap;fontFamily=Arial;fontSize=15;fontStyle=1;fontColor=#263238;fillColor={color};swimlaneFillColor=#FFFDF2;strokeColor=#65604A;strokeWidth=1.2;align=left;spacingLeft=10;"
            cell(root, name, name, style, x, y, WIDTH, total_height, parent="1")
            row_y = HEADER
            for column_name, label, height, key in rows:
                base = "text;html=1;strokeColor=none;align=left;verticalAlign=middle;spacingLeft=8;spacingRight=8;fontFamily=Arial;fontColor=#263238;fontSize=12;fontStyle=0;"
                base += f"fillColor={'#FFF8D8' if key else '#FFFDF2'};"
                if column_name.startswith("uq") or column_name == "reference":
                    base += "fontColor=#64748B;fontSize=13;"
                row_id = f"{name}.{column_name}"
                if isinstance(label, tuple):
                    cell(root, row_id, "", f"rounded=0;html=1;strokeColor=none;fillColor={'#FFF8D8' if key else '#FFFDF2'};", 0, row_y, WIDTH, height, parent=name)
                    marker, column_label, type_label = label
                    column_style = "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=6;fontFamily=Arial;fontSize=12;"
                    cell(root, f"{row_id}.marker", marker, column_style + "fontColor=#7A5B00;fontStyle=1;", 0, 0, 48, height, parent=row_id, connectable="0")
                    cell(root, f"{row_id}.name", column_label, column_style + "fontColor=#263238;", 48, 0, 220, height, parent=row_id, connectable="0")
                    cell(root, f"{row_id}.type", type_label, column_style + "align=right;spacingRight=6;fontColor=#626B73;", 268, 0, 122, height, parent=row_id, connectable="0")
                else:
                    cell(root, row_id, label, base, 0, row_y, WIDTH, height, parent=name)
                row_y += height
        for (parent, child), fks in grouped.items():
            # One visual association for each table pair; every actual SQL FK is
            # retained in the tooltip and footer, including redundant constraints.
            _, representative = max(fks, key=lambda entry: len(entry[1][0]))
            child_fields, _, parent_fields, _ = representative
            tooltip = "\n".join(f"FK{number} ({', '.join(fk[0])}) → {fk[1]} ({', '.join(fk[2])}); ON DELETE {fk[3]}" for number, fk in fks)
            edge = ET.SubElement(root, "mxCell", id=f"rel.{parent}.{child}", value="", edge="1", parent="1", source=f"{parent}.{parent_fields[0]}", target=f"{child}.{child_fields[0]}", tooltip=tooltip, style="edgeStyle=entityRelationEdgeStyle;html=1;rounded=0;dashed=1;dashPattern=6 4;startArrow=ERmandOne;startFill=0;endArrow=ERzeroToMany;endFill=0;startSize=12;endSize=16;strokeColor=#6B6655;strokeWidth=1.2;fontSize=12;defaultLabelBackgroundColor=page;")
            if page_number == 1 and (parent, child) == ("service_entity", "service_instance"):
                edge.set("style", edge.get("style") + "sourcePortConstraint=west;targetPortConstraint=west;")
            ET.SubElement(edge, "mxGeometry", relative="1", **{"as": "geometry"})
        note = "Cada linha tracejada representa uma associação; detalhes de chaves compostas, CHECKs e ON DELETE estão na migration 001_init.sql."
        if page_number == 4:
            note += " Cobertura e valor derivado são entidades separadas."
        if page_number == 5:
            note += " derived_point_source resolve uma associação N:M."
        bottom = max(y + int(root.find(f"mxCell[@id='{name}']/mxGeometry").get("height")) for name, _, y, _ in nodes)
        note_y = bottom + 25
        cell(root, "note", note, text_style + "fontSize=12;whiteSpace=wrap;", 50, note_y, 1320, 32, parent="1")
        model.set("pageHeight", str(max(1100, note_y + 70)))
        # Global IDs also satisfy the MCP validator across multiple diagram tabs.
        for item in root.findall("mxCell"):
            for attribute in ("id", "parent", "source", "target"):
                if attribute in item.attrib:
                    if item.get(attribute) not in ("0", "1"):
                        item.set(attribute, f"p{page_number}__{item.get(attribute)}")
        counts.append((page_title, len(nodes), len(grouped), sum(len(tables[c]["fk"]) for c in children)))
    expected = {(name, number) for name, table in tables.items() for number, _ in enumerate(table["fk"], 1)}
    assert represented == expected, f"Foreign key coverage mismatch: {expected ^ represented}"
    ET.indent(file, space="  ")
    ET.ElementTree(file).write(OUTPUT, encoding="utf-8", xml_declaration=True)
    # Parse again after serialization: unique cells, valid edge endpoints/geometry.
    parsed = ET.parse(OUTPUT)
    for diagram in parsed.findall("diagram"):
        all_cells = diagram.findall(".//mxCell")
        ids = [item.get("id") for item in all_cells]
        assert len(ids) == len(set(ids)), diagram.get("name")
        id_set = set(ids)
        for item in all_cells:
            if item.get("parent"):
                assert item.get("parent") in id_set, (diagram.get("name"), item.get("id"), item.get("parent"))
            if item.get("edge") == "1":
                assert item.get("source") in id_set and item.get("target") in id_set
                assert item.find("mxGeometry").get("relative") == "1"
    print(f"Validated: {len(tables)} tables, {sum(len(t['columns']) for t in tables.values())} columns, {len(expected)} SQL foreign keys, {len(PAGES)} pages")
    for title, nodes, links, fks in counts:
        print(f"  {title}: {nodes} views, {links} associations, {fks} SQL foreign keys")


if __name__ == "__main__":
    generate()
