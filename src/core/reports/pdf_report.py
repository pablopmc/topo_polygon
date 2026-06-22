from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    LongTable,
    PageBreak,
    PageTemplate,
    Paragraph,
    NextPageTemplate,
    Spacer,
    Table,
    TableStyle,
)
import math
import re

from core.calculations.engine import decimal_para_dms, precisao_relativa

PAGE_SIZE = landscape(A3)
PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE

LEFT_MARGIN = 10 * mm
RIGHT_MARGIN = 10 * mm
TOP_MARGIN = 14 * mm
BOTTOM_MARGIN = 18 * mm
CONTENT_GAP = 4 * mm
PAGE3_BOTTOM_BAND_H = 74 * mm
PAGE3_GRAPH_H = 150 * mm

FONT_REGULAR = "TopoSans"
FONT_BOLD = "TopoSans-Bold"

PAGE_TITLE = "Relatório Técnico Topográfico"
REPORT_METHOD = "Bowditch / Gauss"
REPORT_REVISION = "1"
DEFAULT_PROJECT_NAME = "PROJETO"

TABLE_SPECS = {
    "tabela_calculos": {
        "title": "TABELA PRINCIPAL DE CÁLCULOS",
        "header_rows": [
            [
                {"label": "Estações", "rowspan": 3},
                {"label": "Estações Visadas", "rowspan": 3},
                {"label": "Elementos Angulares", "colspan": 2},
                {"label": "Rumos Calculados", "colspan": 1},
                {"label": "Linhas Trigonométricas", "colspan": 2},
                {"label": "Distâncias Medidas", "rowspan": 3},
                {"label": "Projeções Calculadas", "colspan": 4},
                {"label": "Correções", "colspan": 2},
            ],
            [
                {"label": "Ângulos Internos", "colspan": 2},
                {"label": "Azimutes Calculados", "rowspan": 2},
                {"label": "Senos", "rowspan": 2},
                {"label": "Cosenos", "rowspan": 2},
                {"label": "Sobre o eixo dos X (Dxsen)", "colspan": 2},
                {"label": "Sobre o eixo dos Y (Dxcos)", "colspan": 2},
                {"label": "Cx", "rowspan": 2},
                {"label": "Cy", "rowspan": 2},
            ],
            [
                {"label": "Lidos"},
                {"label": "Compensados"},
                {"label": "E (+)"},
                {"label": "O (-)"},
                {"label": "N (+)"},
                {"label": "S (-)"},
            ],
        ],
        "columns": [
            {"label": "Estações", "keys": ["Estação", "Estacao", "sequence"], "kind": "text", "width_mm": 18},
            {"label": "Estações Visadas", "keys": ["Ponto", "Point", "point_name"], "kind": "text", "width_mm": 24},
            {"label": "Ângulos Internos Lidos", "keys": ["Ângulo Interno Lido", "Angulo Interno Lido"], "kind": "dms", "width_mm": 24},
            {"label": "Ângulos Internos Compensados", "keys": ["Ângulo Interno Compensado", "Angulo Interno Compensado"], "kind": "dms", "width_mm": 24},
            {"label": "Azimutes Calculados", "keys": ["Azimute"], "kind": "dms", "width_mm": 22},
            {"label": "Senos", "keys": ["Seno do Rumo"], "kind": "float6", "width_mm": 18},
            {"label": "Cosenos", "keys": ["Cosseno do Rumo"], "kind": "float6", "width_mm": 18},
            {"label": "Distâncias Medidas", "keys": ["Distância (m)", "Distancia (m)"], "kind": "float3", "width_mm": 18},
            {"label": "E (+)", "keys": ["Projeção E (+)"], "kind": "float3", "width_mm": 18},
            {"label": "O (-)", "keys": ["Projeção O (-)"], "kind": "float3", "width_mm": 18},
            {"label": "N (+)", "keys": ["Projeção N (+)"], "kind": "float3", "width_mm": 18},
            {"label": "S (-)", "keys": ["Projeção S (-)"], "kind": "float3", "width_mm": 18},
            {"label": "Cx", "keys": ["Correção em X (Cx)"], "kind": "float3", "width_mm": 16},
            {"label": "Cy", "keys": ["Correção em Y (Cy)"], "kind": "float3", "width_mm": 16},
        ],
    },
    "tabela_areas": {
        "title": "TABELA DE COORDENADAS, PROJEÇÕES COMPENSADAS E DUPLAS ÁREAS",
        "header_rows": [
            [
                {"label": "Estações", "rowspan": 2},
                {"label": "Estações Visadas", "rowspan": 2},
                {"label": "Projeções Compensadas", "colspan": 2},
                {"label": "Coordenadas", "colspan": 2},
                {"label": "ΣX", "rowspan": 2},
                {"label": "Duplas áreas (ΣX.y)", "colspan": 2},
                {"label": "ΣY", "rowspan": 2},
                {"label": "Duplas áreas (ΣY.x)", "colspan": 2},
            ],
            [
                {"label": "Sobre o eixo dos x (x)"},
                {"label": "Sobre o eixo dos y (y)"},
                {"label": "Abcissas X"},
                {"label": "Ordenadas Y"},
                {"label": "A Somar"},
                {"label": "A Subtrair"},
                {"label": "A Somar"},
                {"label": "A Subtrair"},
            ],
        ],
        "columns": [
            {"label": "Estações", "keys": ["Estação", "Estacao", "sequence"], "kind": "text", "width_mm": 18},
            {"label": "Estações Visadas", "keys": ["Ponto", "Point", "point_name"], "kind": "text", "width_mm": 24},
            {"label": "x", "keys": ["Projeção Compensada X (Leste/Oeste)"], "kind": "float3", "width_mm": 22},
            {"label": "y", "keys": ["Projeção Compensada Y (Norte/Sul)"], "kind": "float3", "width_mm": 22},
            {"label": "X", "keys": ["Coordenada X"], "kind": "float3", "width_mm": 20},
            {"label": "Y", "keys": ["Coordenada Y"], "kind": "float3", "width_mm": 20},
            {"label": "ΣX", "keys": ["Soma X"], "kind": "float3", "width_mm": 18},
            {"label": "A Somar", "keys": ["Duplas Áreas X (+)", "dupla_x_y_plus"], "kind": "float3_empty_zero", "width_mm": 18},
            {"label": "A Subtrair", "keys": ["Duplas Áreas X (-)", "dupla_x_y_minus"], "kind": "float3_empty_zero", "width_mm": 18},
            {"label": "ΣY", "keys": ["Soma Y"], "kind": "float3", "width_mm": 18},
            {"label": "A Somar", "keys": ["Duplas Áreas Y (+)", "dupla_y_x_plus"], "kind": "float3_empty_zero", "width_mm": 18},
            {"label": "A Subtrair", "keys": ["Duplas Áreas Y (-)", "dupla_y_x_minus"], "kind": "float3_empty_zero", "width_mm": 18},
        ],
    },
}


def _register_fonts() -> None:
    candidates = [
        (FONT_REGULAR, r"C:\Windows\Fonts\arial.ttf"),
        (FONT_BOLD, r"C:\Windows\Fonts\arialbd.ttf"),
    ]
    for font_name, font_path in candidates:
        path = Path(font_path)
        if path.exists() and font_name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(font_name, str(path)))


def _font_name(bold: bool = False) -> str:
    if bold and FONT_BOLD in pdfmetrics.getRegisteredFontNames():
        return FONT_BOLD
    if FONT_REGULAR in pdfmetrics.getRegisteredFontNames():
        return FONT_REGULAR
    return "Helvetica-Bold" if bold else "Helvetica"


def _style(size: float, *, bold: bool = False, align: int = TA_LEFT, leading: float | None = None, color: colors.Color | None = None) -> ParagraphStyle:
    return ParagraphStyle(
        name=f"style_{size}_{'b' if bold else 'r'}_{align}",
        parent=getSampleStyleSheet()["BodyText"],
        fontName=_font_name(bold),
        fontSize=size,
        leading=leading or (size + 1.4),
        alignment=align,
        textColor=color or colors.HexColor("#1b1b1b"),
    )


def _escape(text: Any) -> str:
    value = "" if text is None else str(text)
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


def _p(text: Any, size: float = 6.4, *, bold: bool = False, align: int = TA_CENTER) -> Paragraph:
    return Paragraph(_escape(text), _style(size, bold=bold, align=align))


def _as_dict(value: object) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


def _normalize_key(value: Any) -> str:
    text = "" if value is None else str(value)
    return "".join(ch for ch in text.casefold().strip() if ch.isalnum())


def _row_value(row: Mapping[str, Any], keys: Sequence[str], default: Any = "") -> Any:
    normalized = {_normalize_key(k): v for k, v in row.items()}
    for key in keys:
        normalized_key = _normalize_key(key)
        if normalized_key in normalized:
            value = normalized[normalized_key]
            if value not in (None, ""):
                return value
    return default


def _parse_date(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    text = str(value).strip()
    candidates = (
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
    )
    for fmt in candidates:
        try:
            return datetime.strptime(text[:19], fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text).strftime("%d/%m/%Y")
    except ValueError:
        return text


def _clean_zero(value: Any, decimals: int) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    threshold = 0.5 * 10 ** (-decimals)
    if abs(number) < threshold:
        return 0.0
    return number


def _format_number(value: Any, decimals: int) -> str:
    try:
        return f"{_clean_zero(value, decimals):.{decimals}f}"
    except Exception:
        return ""


def _format_text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip().upper()


def _format_dms(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, (tuple, list)) and len(value) == 3:
        graus, minutos, segundos = int(value[0]), int(value[1]), float(value[2])
        sinal = "-" if graus < 0 or minutos < 0 or segundos < 0 else ""
    elif isinstance(value, (int, float)):
        val_float = float(value)
        sinal = "-" if val_float < 0 else ""
        graus, minutos, segundos = decimal_para_dms(val_float)
    else:
        return str(value)
    return f"{sinal}{abs(graus)}° {abs(minutos):02d}' {abs(segundos):06.3f}\""


def _parse_dms_to_decimal(val: Any) -> float:
    if val in (None, ""):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, (tuple, list)) and len(val) == 3:
        from core.calculations.engine import dms_para_graus
        try:
            return dms_para_graus(int(val[0]), int(val[1]), float(val[2]))
        except Exception:
            return 0.0
    
    try:
        clean = str(val).strip()
        sinal = -1.0 if "-" in clean else 1.0
        # extract all numeric values (including decimals)
        nums = re.findall(r"\d+(?:\.\d+)?", clean)
        if len(nums) == 3:
            g, m, s = float(nums[0]), float(nums[1]), float(nums[2])
            return sinal * (g + m / 60.0 + s / 3600.0)
        elif len(nums) == 1:
            return sinal * float(nums[0])
    except Exception:
        pass
    return 0.0


def _format_precision(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if number == float("inf"):
        return "1:∞"
    if number <= 0:
        return ""
    return f"1:{int(round(number)):,}".replace(",", ".")


def _project_meta(project: Mapping[str, Any]) -> dict[str, str]:
    return {
        "name": _format_text(
            project.get("name")
            or project.get("project_name")
            or project.get("Nome do Projeto")
            or DEFAULT_PROJECT_NAME
        ),
        "institution": _format_text(project.get("institution") or project.get("Instituição")),
        "surveyor": _format_text(project.get("surveyor") or project.get("author") or project.get("Responsável")),
        "survey_date": _parse_date(project.get("survey_date") or project.get("Data do Levantamento") or project.get("created_at")),
        "revision": str(project.get("revision") or project.get("revisao") or REPORT_REVISION).strip() or REPORT_REVISION,
        "method": str(project.get("method") or REPORT_METHOD).strip() or REPORT_METHOD,
        "description": str(project.get("survey_description") or project.get("description") or project.get("Descrição") or "").strip(),
        "client": _format_text(project.get("client") or project.get("client_name") or project.get("Contratante/Cliente")),
        "location": _format_text(project.get("location") or project.get("project_location") or project.get("Localidade/Endereço")),
        "coordinate_system": _format_text(project.get("coordinate_system") or project.get("Sistema de Coordenadas")),
        "reference_point": _format_text(project.get("reference_point") or project.get("Ponto de Referência")),
    }


def _header_matrix(header_rows: Sequence[Sequence[Mapping[str, Any]]], col_count: int) -> tuple[list[list[str]], list[tuple[tuple[int, int], tuple[int, int]]]]:
    matrix = [["" for _ in range(col_count)] for _ in range(len(header_rows))]
    spans: list[tuple[tuple[int, int], tuple[int, int]]] = []
    occupied = [[False for _ in range(col_count)] for _ in range(len(header_rows))]
    for row_index, row in enumerate(header_rows):
        col_index = 0
        for cell in row:
            while col_index < col_count and occupied[row_index][col_index]:
                col_index += 1
            label = str(cell.get("label", ""))
            colspan = int(cell.get("colspan", 1))
            rowspan = int(cell.get("rowspan", 1))
            matrix[row_index][col_index] = label
            if colspan > 1 or rowspan > 1:
                spans.append(((col_index, row_index), (col_index + colspan - 1, row_index + rowspan - 1)))
            for rr in range(row_index, min(len(header_rows), row_index + rowspan)):
                for cc in range(col_index, min(col_count, col_index + colspan)):
                    occupied[rr][cc] = True
            col_index += colspan
    return matrix, spans


def _fit_widths(widths_mm: Sequence[float], available: float) -> list[float]:
    widths = [width * mm for width in widths_mm]
    total = sum(widths)
    if total == 0:
        return [available / max(1, len(widths_mm)) for _ in widths_mm]
    if total < available:
        extra = available - total
        weights = [max(1.0, value) for value in widths]
        weight_sum = sum(weights)
        return [value + extra * (weights[index] / weight_sum) for index, value in enumerate(widths)]
    scale = available / total
    return [value * scale for value in widths]


def _format_cell(value: Any, kind: str) -> str:
    if kind == "dms":
        return _format_dms(value)
    if kind == "float3":
        return _format_number(value, 3)
    if kind == "float3_empty_zero":
        try:
            val_float = float(value)
            if abs(val_float) < 1e-5:
                return ""
            return _format_number(val_float, 3)
        except (ValueError, TypeError):
            return ""
    if kind == "float2":
        return _format_number(value, 2)
    if kind == "float6":
        return _format_number(value, 6)
    return _format_text(value)


def _build_header(spec: Mapping[str, Any]) -> list[list[Paragraph]]:
    header_rows = spec["header_rows"]
    col_count = len(spec["columns"])
    matrix, _ = _header_matrix(header_rows, col_count)
    return [[_p(cell, 6.6, bold=True, align=TA_CENTER) for cell in row] for row in matrix]


def _build_table_style(spec: Mapping[str, Any], header_rows: int) -> TableStyle:
    style = TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, -1), _font_name(False)),
            ("FONTSIZE", (0, 0), (-1, -1), 6.2),
            ("LEADING", (0, 0), (-1, -1), 7.0),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#555555")),
            ("BOX", (0, 0), (-1, -1), 0.55, colors.HexColor("#2a2a2a")),
            ("BACKGROUND", (0, 0), (-1, header_rows - 1), colors.HexColor("#efefef")),
            ("TEXTCOLOR", (0, 0), (-1, header_rows - 1), colors.HexColor("#111111")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]
    )
    matrix, spans = _header_matrix(spec["header_rows"], len(spec["columns"]))
    for start, end in spans:
        style.add("SPAN", start, end)
    for row_index, row in enumerate(matrix):
        for col_index, label in enumerate(row):
            if label:
                style.add("ALIGN", (col_index, row_index), (col_index, row_index), "CENTER")
    return style


def _calculate_sum_row(spec: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> list[Paragraph]:
    sum_row: list[Paragraph] = []
    for column in spec["columns"]:
        label = column["label"]
        kind = column["kind"]
        keys = column["keys"]
        
        if label == "Estações":
            sum_row.append(_p("SOMA", 6.2, bold=True, align=TA_CENTER))
            continue
        
        if label == "Estações Visadas":
            sum_row.append(_p("", 6.2, align=TA_CENTER))
            continue
        
        # Check if we should sum
        should_sum = False
        if kind == "dms" and ("Ângulo" in label or "Angulo" in label):
            should_sum = True
        elif label in ("Distâncias Medidas", "E (+)", "O (-)", "N (+)", "S (-)", "Cx", "Cy", "x", "y", "A Somar", "A Subtrair"):
            should_sum = True
        
        if should_sum:
            total = 0.0
            for row in rows:
                raw_value = _row_value(row, keys, default=0.0)
                if kind == "dms":
                    val_float = _parse_dms_to_decimal(raw_value)
                else:
                    try:
                        val_float = float(raw_value)
                    except (ValueError, TypeError):
                        val_float = 0.0
                total += val_float
            
            if kind == "dms":
                formatted = _format_dms(total)
            elif kind == "float3_empty_zero":
                formatted = _format_number(total, 3)
            else:
                formatted = _format_cell(total, kind)
            
            sum_row.append(_p(formatted, 6.2, bold=True, align=TA_CENTER))
        else:
            sum_row.append(_p("", 6.2, align=TA_CENTER))
    return sum_row


def _build_long_table(spec: Mapping[str, Any], rows: Sequence[Mapping[str, Any]], max_width: float) -> LongTable:
    header = _build_header(spec)
    body: list[list[Paragraph]] = []
    for index, row in enumerate(rows, start=1):
        rendered_row: list[Paragraph] = []
        for column in spec["columns"]:
            raw_value = _row_value(row, column["keys"], default="")
            if column["label"] == "Estações" and raw_value in ("", None):
                raw_value = index
            rendered_row.append(_p(_format_cell(raw_value, column["kind"]), 6.2, align=TA_CENTER))
        body.append(rendered_row)

    sum_row = _calculate_sum_row(spec, rows)
    body.append(sum_row)

    table_data: list[list[Paragraph]] = header + body
    col_widths = _fit_widths([column["width_mm"] for column in spec["columns"]], max_width)
    table = LongTable(table_data, colWidths=col_widths, repeatRows=len(spec["header_rows"]), splitByRow=1)
    
    style = _build_table_style(spec, len(spec["header_rows"]))
    style.add("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#efefef"))
    style.add("LINEABOVE", (0, -1), (-1, -1), 1.0, colors.HexColor("#2a2a2a"))
    style.add("LINEBELOW", (0, -1), (-1, -1), 1.2, colors.HexColor("#2a2a2a"))
    table.setStyle(style)
    return table



def _metadata_table(project: Mapping[str, str]) -> Table:
    data = [
        [_p("PROJETO", 6.6, bold=True), _p(project["name"], 7.4, bold=True)],
        [_p("INSTITUIÇÃO", 6.6, bold=True), _p(project["institution"] or "-", 6.6)],
        [_p("RESPONSÁVEL", 6.6, bold=True), _p(project["surveyor"] or "-", 6.6)],
        [_p("DATA", 6.6, bold=True), _p(project["survey_date"] or "-", 6.6)],
        [_p("REVISÃO", 6.6, bold=True), _p(project["revision"], 6.6)],
        [_p("MÉTODO", 6.6, bold=True), _p(project["method"], 6.6)],
    ]
    table = Table(data, colWidths=[38 * mm, 120 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f3f3")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#444444")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#666666")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _summary_table(area: Any, perimeter: Any, precision: Any, method: str) -> Table:
    try:
        area_val = float(area)
    except (ValueError, TypeError):
        area_val = 0.0
    data = [
        [_p("ÁREA FINAL", 6.6, bold=True), _p(f"{_format_number(area, 3)} m²", 6.9)],
        [_p("ÁREA EM HECTARES", 6.6, bold=True), _p(f"{_format_number(area_val / 10000.0, 4)} ha", 6.9)],
        [_p("PERÍMETRO", 6.6, bold=True), _p(f"{_format_number(perimeter, 3)} m", 6.9)],
        [_p("PRECISÃO RELATIVA", 6.6, bold=True), _p(_format_precision(precision), 6.9)],
        [_p("MÉTODO", 6.6, bold=True), _p(method, 6.9)],
    ]
    table = Table(data, colWidths=[42 * mm, 58 * mm], hAlign="RIGHT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f1f1")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#2d2d2d")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#666666")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _stamp_table(project: Mapping[str, str], area: Any) -> Table:
    try:
        area_val = float(area)
    except (ValueError, TypeError):
        area_val = 0.0
    rows = [
        ["PROJETO", project["name"]],
        ["RESPONSÁVEL", project["surveyor"] or "-"],
        ["DATA", project["survey_date"] or "-"],
        ["REVISÃO", project["revision"]],
        ["MÉTODO", project["method"]],
        ["ÁREA FINAL", f"{_format_number(area, 3)} m²"],
        ["ÁREA EM HECTARES", f"{_format_number(area_val / 10000.0, 4)} ha"],
    ]
    table = Table([[_p(left, 6.4, bold=True), _p(right, 6.4)] for left, right in rows], colWidths=[33 * mm, 66 * mm], hAlign="RIGHT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f4f4f4")),
                ("BOX", (0, 0), (-1, -1), 0.55, colors.HexColor("#363636")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#696969")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _legend_table() -> Table:
    data = [
        [_p("LEGENDA TÉCNICA", 6.6, bold=True), _p("VÉRTICE NUMERADO", 6.2)],
        [_p("Linhas da poligonal", 6.2), _p("Sequência de pontos do fechamento", 6.2)],
        [_p("Escala gráfica", 6.2), _p("Ajustada ao espaço disponível", 6.2)],
    ]
    table = Table(data, colWidths=[38 * mm, 72 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#efefef")),
                ("BOX", (0, 0), (-1, -1), 0.55, colors.HexColor("#363636")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#696969")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _points_table(rows: Sequence[Mapping[str, Any]]) -> Table:
    data = [[
        _p("PONTO", 6.2, bold=True),
        _p("Coordenadas em X", 6.2, bold=True),
        _p("Coordenadas em Y", 6.2, bold=True),
    ]]
    for row in rows:
        data.append(
            [
                _p(_format_text(_row_value(row, ["Ponto", "point_name", "point"])) or "-", 6.1),
                _p(_format_number(_row_value(row, ["Coordenada X"]), 3), 6.1),
                _p(_format_number(_row_value(row, ["Coordenada Y"]), 3), 6.1),
            ]
        )

    table = Table(data, colWidths=[40 * mm, 55 * mm, 55 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#efefef")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#3d3d3d")),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#6a6a6a")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return table


def _make_sub_table(title: str, rows: list[tuple[str, str]], col_widths: list[float]) -> Table:
    data = [[_p(title, 6.6, bold=True, align=TA_CENTER), ""]]
    for desc, val in rows:
        data.append([
            _p(desc, 6.2, align=TA_LEFT),
            _p(val, 6.2, bold=True, align=TA_CENTER)
        ])
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), _font_name(False)),
        ("FONTSIZE", (0, 0), (-1, -1), 6.2),
        ("LEADING", (0, 0), (-1, -1), 7.0),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#555555")),
        ("BOX", (0, 0), (-1, -1), 0.55, colors.HexColor("#2a2a2a")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#efefef")),
        ("SPAN", (0, 0), (1, 0)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("ALIGN", (1, 1), (1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _verifications_table(calculation_rows: Sequence[Mapping[str, Any]], max_width: float) -> Table:
    n = len(calculation_rows)
    
    # 1. Angular verification
    sum_obs = 0.0
    sum_comp = 0.0
    for row in calculation_rows:
        sum_obs += _parse_dms_to_decimal(_row_value(row, ["Ângulo Interno Lido", "Angulo Interno Lido"]))
        sum_comp += _parse_dms_to_decimal(_row_value(row, ["Ângulo Interno Compensado", "Angulo Interno Compensado"]))
    
    val_teorico = (n - 2) * 180.0
    erro_ang = sum_obs - val_teorico
    
    ang_rows = [
        ("Soma dos Ângulos Lidos", _format_dms(sum_obs)),
        ("Fechamento Teórico (N-2)*180°", _format_dms(val_teorico)),
        ("Erro de Fechamento Angular", _format_dms(erro_ang)),
        ("Soma dos Ângulos Compensados", _format_dms(sum_comp)),
    ]
    
    # 2. Linear projection verification
    sum_e = 0.0
    sum_o = 0.0
    sum_n = 0.0
    sum_s = 0.0
    sum_cx = 0.0
    sum_cy = 0.0
    perimeter = 0.0
    
    for row in calculation_rows:
        sum_e += float(_row_value(row, ["Projeção E (+)"], 0.0))
        sum_o += float(_row_value(row, ["Projeção O (-)"], 0.0))
        sum_n += float(_row_value(row, ["Projeção N (+)"], 0.0))
        sum_s += float(_row_value(row, ["Projeção S (-)"], 0.0))
        sum_cx += float(_row_value(row, ["Correção em X (Cx)"], 0.0))
        sum_cy += float(_row_value(row, ["Correção em Y (Cy)"], 0.0))
        perimeter += float(_row_value(row, ["Distância (m)", "Distancia (m)"], 0.0))
        
    dx = sum_e - sum_o
    dy = sum_n - sum_s
    
    proj_rows = [
        ("Soma Projeções Leste (E+)", _format_number(sum_e, 3)),
        ("Soma Projeções Oeste (O-)", _format_number(sum_o, 3)),
        ("Erro de Fechamento em X (Dx)", _format_number(dx, 3)),
        ("Soma das Correções Cx", _format_number(sum_cx, 3)),
        ("Soma Projeções Norte (N+)", _format_number(sum_n, 3)),
        ("Soma Projeções Sul (S-)", _format_number(sum_s, 3)),
        ("Erro de Fechamento em Y (Dy)", _format_number(dy, 3)),
        ("Soma das Correções Cy", _format_number(sum_cy, 3)),
    ]
    
    # 3. Errors and precision
    erro_lin = math.sqrt(dx**2 + dy**2)
    prec = precisao_relativa(perimeter, erro_lin) if perimeter > 0 else float("inf")
    
    err_rows = [
        ("Número de Estações", str(n)),
        ("Perímetro Total (m)", _format_number(perimeter, 3)),
        ("Erro de Fechamento Linear (m)", _format_number(erro_lin, 3)),
        ("Precisão Relativa Obtida", _format_precision(prec)),
    ]
    
    spacer_w = 12 * mm
    avail_tables = max_width - 2 * spacer_w
    w1 = avail_tables * 0.32
    w2 = avail_tables * 0.36
    w3 = avail_tables * 0.32
    
    t1 = _make_sub_table("VERIFICAÇÃO ANGULAR", ang_rows, [w1 * 0.6, w1 * 0.4])
    t2 = _make_sub_table("FECHAMENTO LINEAR (PROJEÇÕES)", proj_rows, [w2 * 0.65, w2 * 0.35])
    t3 = _make_sub_table("METADADOS E PRECISÃO", err_rows, [w3 * 0.6, w3 * 0.4])
    
    parent_data = [[t1, "", t2, "", t3]]
    parent_table = Table(parent_data, colWidths=[w1, spacer_w, w2, spacer_w, w3])
    parent_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return parent_table


class SketchFlowable(Flowable):

    def __init__(self, points: Sequence[tuple[float, float]], width: float, height: float, labels: Sequence[str] | None = None) -> None:
        super().__init__()
        self.points = [(float(x), float(y)) for x, y in points]
        self._width = width
        self._height = height
        self.labels = list(labels) if labels else [str(index + 1) for index in range(len(self.points))]

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        self.width = min(self._width, availWidth)
        self.height = min(self._height, availHeight)
        return self.width, self.height

    def draw(self) -> None:
        canvas = self.canv
        width = self.width
        height = self.height
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#303030"))
        canvas.setLineWidth(0.8)
        canvas.rect(0, 0, width, height, stroke=1, fill=0)

        if len(self.points) < 2:
            canvas.setFont(_font_name(False), 9)
            canvas.drawCentredString(width / 2, height / 2, "Sem pontos suficientes para a prancha gráfica")
            canvas.restoreState()
            return

        pad_x = 18 * mm
        pad_y = 16 * mm
        plot_left = pad_x
        plot_bottom = pad_y
        plot_width = max(10.0, width - 2 * pad_x)
        plot_height = max(10.0, height - 2 * pad_y)

        xs = [point[0] for point in self.points]
        ys = [point[1] for point in self.points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span_x = max(max_x - min_x, 1e-9)
        span_y = max(max_y - min_y, 1e-9)
        
        # S_min is the minimum scale denominator to fit the A3 viewport.
        # 1 meter on paper is 1000 mm = 2834.64567 points.
        scale_raw = min(plot_width / span_x, plot_height / span_y)
        s_min = 2834.64567 / scale_raw

        # Round up to the next standard engineering/topography scale denominator
        allowed_scales = [
            1, 2, 5, 10, 20, 25, 50, 75, 100, 125, 150, 200, 250, 300, 400, 500, 750, 
            1000, 1250, 1500, 2000, 2500, 3000, 4000, 5000, 7500, 10000, 12500, 15000, 
            20000, 25000, 50000, 75000, 100000
        ]
        s_allowed = 100
        for s in allowed_scales:
            if s >= s_min:
                s_allowed = s
                break
        else:
            s_allowed = int(s_min)

        scale = 2834.64567 / s_allowed

        center_plot_x = plot_left + plot_width / 2
        center_plot_y = plot_bottom + plot_height / 2
        center_poly_x = (min_x + max_x) / 2
        center_poly_y = (min_y + max_y) / 2

        def tx(x: float) -> float:
            return center_plot_x + (x - center_poly_x) * scale

        def ty(y: float) -> float:
            return center_plot_y + (y - center_poly_y) * scale

        transformed = [(tx(x), ty(y)) for x, y in self.points]

        canvas.setStrokeColor(colors.HexColor("#7b7b7b"))
        canvas.setLineWidth(0.35)
        canvas.line(plot_left, plot_bottom, plot_left + plot_width, plot_bottom)
        canvas.line(plot_left, plot_bottom, plot_left, plot_bottom + plot_height)

        canvas.setStrokeColor(colors.HexColor("#184a7d"))
        canvas.setLineWidth(1.4)
        canvas.lines([(transformed[i][0], transformed[i][1], transformed[(i + 1) % len(transformed)][0], transformed[(i + 1) % len(transformed)][1]) for i in range(len(transformed))])

        canvas.setFillColor(colors.HexColor("#184a7d"))
        canvas.setStrokeColor(colors.HexColor("#184a7d"))
        for index, (x_pos, y_pos) in enumerate(transformed):
            canvas.circle(x_pos, y_pos, 1.8 * mm, stroke=1, fill=1)
            label = self.labels[index] if index < len(self.labels) else str(index + 1)
            canvas.setFillColor(colors.white)
            canvas.setFont(_font_name(True), 7.5)
            text_width = stringWidth(label, _font_name(True), 7.5)
            canvas.drawString(x_pos - text_width / 2, y_pos - 2.2, label)
            canvas.setFillColor(colors.HexColor("#184a7d"))

        canvas.setFont(_font_name(True), 8.2)
        canvas.setFillColor(colors.HexColor("#1b1b1b"))
        canvas.drawString(plot_left, height - 10, "PRANCHA GRÁFICA DA POLIGONAL")

        # Choose a nice distance for the scale bar (1, 2, 5, 10, 20, 50, etc. meters)
        nice_distances = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
        best_dist = 10
        best_diff = float('inf')
        for dist in nice_distances:
            w_mm = (dist * 1000.0) / s_allowed
            if 20 <= w_mm <= 80:
                diff = abs(w_mm - 40)
                if diff < best_diff:
                    best_diff = diff
                    best_dist = dist

        bar_w = (best_dist * 1000.0 / s_allowed) * (72.0 / 25.4)
        bar_x = width - bar_w - 18 * mm
        bar_y = 12 * mm

        canvas.setStrokeColor(colors.HexColor("#1b1b1b"))
        canvas.setLineWidth(0.7)
        canvas.line(bar_x, bar_y, bar_x + bar_w, bar_y)
        canvas.line(bar_x, bar_y - 1.8 * mm, bar_x, bar_y + 1.8 * mm)
        canvas.line(bar_x + bar_w / 2, bar_y - 1.4 * mm, bar_x + bar_w / 2, bar_y + 1.4 * mm)
        canvas.line(bar_x + bar_w, bar_y - 1.8 * mm, bar_x + bar_w, bar_y + 1.8 * mm)
        
        canvas.setFont(_font_name(False), 6.5)
        canvas.drawCentredString(bar_x, bar_y - 4.5 * mm, "0")
        canvas.drawCentredString(bar_x + bar_w / 2, bar_y - 4.5 * mm, str(best_dist // 2 if best_dist % 2 == 0 else best_dist / 2))
        canvas.drawCentredString(bar_x + bar_w, bar_y - 4.5 * mm, f"{best_dist} m")

        scale_text = f"ESCALA 1:{s_allowed}"
        canvas.setFont(_font_name(True), 7.5)
        canvas.drawString(bar_x, bar_y + 4.5 * mm, scale_text)
        canvas.restoreState()


def _draw_table(canvas, table: Table, x: float, y: float, max_width: float | None = None) -> tuple[float, float]:
    width, height = table.wrapOn(canvas, max_width or 10_000, 10_000)
    table.drawOn(canvas, x, y)
    return width, height


def _draw_page3_panels(
    canvas,
    project_meta: Mapping[str, str],
    area: Any,
    perimeter: Any,
    precision: Any,
    coordinates_rows: Sequence[Mapping[str, Any]],
) -> None:
    left_x = LEFT_MARGIN
    right_margin = RIGHT_MARGIN
    bottom_y = BOTTOM_MARGIN + 2 * mm
    band_top = bottom_y + PAGE3_BOTTOM_BAND_H - 1 * mm
    left_width = 225 * mm
    right_width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN - left_width - 4 * mm
    right_width = max(78 * mm, right_width)
    left_width = min(left_width, PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN - right_width - 4 * mm)

    summary = _summary_table(area, perimeter, precision, project_meta["method"])
    points = _points_table(coordinates_rows)
    legend = _legend_table()
    stamp = _stamp_table(project_meta, area)

    summary_w, summary_h = summary.wrapOn(canvas, left_width, 1000)
    points_w, points_h = points.wrapOn(canvas, left_width, 1000)
    legend_w, legend_h = legend.wrapOn(canvas, left_width, 1000)
    stamp_w, stamp_h = stamp.wrapOn(canvas, right_width, 1000)

    left_stack_height = summary_h + points_h + legend_h + 4 * mm
    stack_top = band_top
    current_y = stack_top - summary_h
    summary.drawOn(canvas, left_x, current_y)

    current_y -= 1.5 * mm + points_h
    points.drawOn(canvas, left_x, current_y)

    current_y -= 1.5 * mm + legend_h
    legend.drawOn(canvas, left_x, current_y)

    stamp_x = PAGE_WIDTH - RIGHT_MARGIN - stamp_w
    stamp_y = bottom_y
    stamp.drawOn(canvas, stamp_x, stamp_y)


def _page_decorations(canvas, doc, project_meta: Mapping[str, str], generated_at: datetime) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#4d4d4d"))
    canvas.setLineWidth(0.55)
    canvas.rect(LEFT_MARGIN / 2, BOTTOM_MARGIN / 2, PAGE_WIDTH - LEFT_MARGIN, PAGE_HEIGHT - TOP_MARGIN, stroke=1, fill=0)

    footer_text = f"Página {canvas.getPageNumber()} | {generated_at.strftime('%d/%m/%Y %H:%M')} | {project_meta['name']}"
    text_width = stringWidth(footer_text, _font_name(False), 8.0)
    center_x = PAGE_WIDTH / 2
    footer_y = BOTTOM_MARGIN / 2 + 3 * mm

    canvas.setStrokeColor(colors.HexColor("#6d6d6d"))
    canvas.setLineWidth(0.45)
    canvas.line(LEFT_MARGIN / 2, footer_y + 2.2 * mm, PAGE_WIDTH - LEFT_MARGIN / 2, footer_y + 2.2 * mm)
    canvas.line(LEFT_MARGIN / 2, footer_y - 2.2 * mm, PAGE_WIDTH - LEFT_MARGIN / 2, footer_y - 2.2 * mm)

    canvas.setFillColor(colors.white)
    canvas.rect(center_x - text_width / 2 - 2 * mm, footer_y - 2.6 * mm, text_width + 4 * mm, 5.2 * mm, stroke=0, fill=1)

    canvas.setFillColor(colors.HexColor("#1b1b1b"))
    canvas.setFont(_font_name(False), 8.0)
    canvas.drawCentredString(center_x, footer_y - 0.25 * mm, footer_text)
    canvas.restoreState()


def _build_story(
    project_meta: Mapping[str, str],
    calculation_rows: Sequence[Mapping[str, Any]],
    coordinates_rows: Sequence[Mapping[str, Any]],
    sketch_points: Sequence[tuple[float, float]],
    area: Any,
    perimeter: Any,
    precision: Any,
    generated_at: datetime,
    doc_width: float,
) -> list[Any]:
    title_style = _style(18, bold=True, align=TA_CENTER, leading=20)
    subtitle_style = _style(9.5, bold=False, align=TA_CENTER, leading=12)
    section_style = _style(11.5, bold=True, align=TA_LEFT, leading=13)
    note_style = _style(7.2, align=TA_LEFT, leading=9)

    story: list[Any] = []

    story.append(Paragraph(PAGE_TITLE, title_style))
    story.append(Spacer(1, 5 * mm))
    story.append(_metadata_table(project_meta))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph(TABLE_SPECS["tabela_calculos"]["title"], section_style))
    story.append(Spacer(1, 2 * mm))
    story.append(_build_long_table(TABLE_SPECS["tabela_calculos"], calculation_rows, doc_width))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("PAINEL DE VERIFICAÇÕES DE FECHAMENTO", section_style))
    story.append(Spacer(1, 2 * mm))
    story.append(_verifications_table(calculation_rows, doc_width))

    story.append(NextPageTemplate("sketch"))
    story.append(PageBreak())


    story.append(Paragraph(TABLE_SPECS["tabela_areas"]["title"], section_style))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("Coordenadas corrigidas e consolidação das duplas áreas", note_style))
    story.append(Spacer(1, 2 * mm))
    story.append(_build_long_table(TABLE_SPECS["tabela_areas"], coordinates_rows, doc_width))

    story.append(PageBreak())
    story.append(Paragraph("PRANCHA GRÁFICA DA POLIGONAL", title_style))
    story.append(Spacer(1, 4 * mm))
    story.append(SketchFlowable(sketch_points, width=doc_width, height=PAGE3_GRAPH_H))

    return story


def _normalize_points(points: Sequence[Any]) -> list[tuple[float, float]]:
    normalized: list[tuple[float, float]] = []
    for point in points:
        if isinstance(point, Mapping):
            x = point.get("x", point.get("X", point.get("coord_x", 0.0)))
            y = point.get("y", point.get("Y", point.get("coord_y", 0.0)))
            normalized.append((float(x), float(y)))
        elif isinstance(point, (tuple, list)) and len(point) >= 2:
            normalized.append((float(point[0]), float(point[1])))
    return normalized


def generate_pdf_report(
    filename: str | Path,
    project: Mapping[str, Any] | object,
    calculation_rows: Sequence[Mapping[str, Any]],
    coordinates_rows: Sequence[Mapping[str, Any]],
    sketch_points: Sequence[Any],
    area: float,
    perimeter: float,
    precision: Any = None,
    sketch_image: str | Path | Any | None = None,
    generated_at: datetime | None = None,
    template_id: str = "A3_LANDSCAPE",
    selected_fields: dict[str, bool] | None = None,
) -> None:
    if selected_fields is None:
        selected_fields = {
            "Dados do projeto": True,
            "Vértices": True,
            "Distâncias": True,
            "Ângulos": True,
            "Azimutes": True,
            "Rumos": True,
            "Projeções": True,
            "Coordenadas": True,
            "Fechamento Angular": True,
            "Fechamento Linear": True,
            "Ajuste Bowditch": True,
            "Área": True,
            "Perímetro": True,
            "Gráfico da Poligonal": True,
        }

    from core.reports.pdf_templates.template_factory import PDFTemplateFactory
    template = PDFTemplateFactory.get_template(template_id)
    
    # Normalizar os pontos passados
    normalized_points = _normalize_points(sketch_points)
    
    template.generate(
        filename=filename,
        project_meta=project,
        calculation_rows=calculation_rows,
        coordinates_rows=coordinates_rows,
        sketch_points=normalized_points,
        area=area,
        perimeter=perimeter,
        precision=precision,
        selected_fields=selected_fields,
        generated_at=generated_at,
    )


from core.reports.exporter_registry import BaseExporter, ExporterRegistry


class PDFExporter(BaseExporter):
    """Adaptador de exportação para formato PDF unificado"""

    def export(
        self,
        filename: str | Path,
        project: Mapping[str, Any],
        calculation_rows: Sequence[Mapping[str, Any]],
        coordinates_rows: Sequence[Mapping[str, Any]],
        sketch_points: Sequence[tuple[float, float]],
        area: float,
        perimeter: float,
        precision: float | None,
        **kwargs: Any,
    ) -> None:
        template_id = kwargs.get("template_id", "A3_LANDSCAPE")
        selected_fields = kwargs.get("selected_fields")
        
        generate_pdf_report(
            filename=filename,
            project=project,
            calculation_rows=calculation_rows,
            coordinates_rows=coordinates_rows,
            sketch_points=sketch_points,
            area=area,
            perimeter=perimeter,
            precision=precision,
            template_id=template_id,
            selected_fields=selected_fields,
        )


# Registrar no registro global
ExporterRegistry.register(
    format_id="PDF",
    display_name="PDF",
    file_filter="Arquivos PDF (*.pdf)",
    default_ext="pdf",
    default_name="relatorio.pdf",
    icon_name="SP_FileDialogListView",
    exporter_class=PDFExporter,
)

