from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import math
import re

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
    LongTable,
    PageBreak,
    PageTemplate,
    Paragraph,
    NextPageTemplate,
    Spacer,
    Table,
    TableStyle,
)

from core.calculations.engine import decimal_para_dms, precisao_relativa
from core.reports.pdf_templates.pdf_template_base import PDFTemplate
from core.reports.pdf_report import (
    _register_fonts,
    _font_name,
    _style,
    _escape,
    _p,
    _as_dict,
    _normalize_key,
    _row_value,
    _parse_date,
    _clean_zero,
    _format_number,
    _format_text,
    _format_dms,
    _parse_dms_to_decimal,
    _format_precision,
    _project_meta,
    _header_matrix,
    _fit_widths,
    _build_header,
    _format_cell,
    _build_table_style,
    PAGE_SIZE,
    PAGE_WIDTH,
    PAGE_HEIGHT,
    LEFT_MARGIN,
    RIGHT_MARGIN,
    TOP_MARGIN,
    BOTTOM_MARGIN,
    CONTENT_GAP,
    PAGE3_BOTTOM_BAND_H,
    PAGE3_GRAPH_H,
    PAGE_TITLE,
    REPORT_METHOD,
    REPORT_REVISION,
    DEFAULT_PROJECT_NAME,
    TABLE_SPECS,
    SketchFlowable,
    _draw_table,
)


class A3LandscapeTemplate(PDFTemplate):
    """Template A3 Paisagem - Preserva integralmente o relatório original de 3 páginas"""

    def generate(
        self,
        filename: str | Path,
        project_meta: Mapping[str, Any],
        calculation_rows: Sequence[Mapping[str, Any]],
        coordinates_rows: Sequence[Mapping[str, Any]],
        sketch_points: Sequence[tuple[float, float]],
        area: float,
        perimeter: float,
        precision: float | None,
        selected_fields: dict[str, bool],
        generated_at: datetime | None = None,
    ) -> None:
        _register_fonts()

        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        project_map = _as_dict(project_meta)
        proj_meta = _project_meta(project_map)
        generated_at = generated_at or datetime.now()
        
        # Normalizar pontos
        from core.reports.pdf_report import _normalize_points
        normalized_points = _normalize_points(sketch_points)

        frame = Frame(
            LEFT_MARGIN,
            BOTTOM_MARGIN + 5 * mm,
            PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN,
            PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN - 10 * mm,
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
            id="main",
        )

        sketch_frame = Frame(
            LEFT_MARGIN,
            BOTTOM_MARGIN + PAGE3_BOTTOM_BAND_H + 2 * mm,
            PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN,
            PAGE_HEIGHT - TOP_MARGIN - (BOTTOM_MARGIN + PAGE3_BOTTOM_BAND_H + 2 * mm),
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
            id="sketch",
        )

        def decorate(canvas, doc) -> None:
            self.build_footer(canvas, doc, proj_meta, generated_at)
            if canvas.getPageNumber() == 3:
                self._draw_page3_panels(canvas, proj_meta, area, perimeter, precision, coordinates_rows, selected_fields)

        doc = BaseDocTemplate(
            str(output_path),
            pagesize=PAGE_SIZE,
            leftMargin=LEFT_MARGIN,
            rightMargin=RIGHT_MARGIN,
            topMargin=TOP_MARGIN,
            bottomMargin=BOTTOM_MARGIN,
            title=PAGE_TITLE,
            author=proj_meta["surveyor"] or "TopoPABLO",
            subject=proj_meta["name"],
        )
        doc.addPageTemplates(
            [
                PageTemplate(id="report", frames=[frame], onPage=decorate),
                PageTemplate(id="sketch", frames=[sketch_frame], onPage=decorate),
            ]
        )

        # Construir a story com os dados filtrados
        story = []
        self.build_cover(story, proj_meta, selected_fields)
        self.build_tables(story, calculation_rows, coordinates_rows, selected_fields, frame._width)
        self.build_summary(story, calculation_rows, area, perimeter, precision, selected_fields, frame._width)

        doc.build(story)

    def build_cover(self, story: list[Any], project_meta: Mapping[str, Any], selected_fields: dict[str, bool] = None) -> None:
        title_style = _style(18, bold=True, align=TA_CENTER, leading=20)
        story.append(Paragraph(PAGE_TITLE, title_style))
        story.append(Spacer(1, 5 * mm))
        
        # Tabela de metadados do projeto
        if selected_fields is None or selected_fields.get("Dados do projeto", True):
            story.append(self._metadata_table(project_meta))
        else:
            # Renderiza tabela de metadados vazia para preservar layout
            empty_meta = {k: "" for k in project_meta}
            empty_meta["name"] = "PROJETO (IDENTIFICAÇÃO OCULTADA)"
            story.append(self._metadata_table(empty_meta))
            
        story.append(Spacer(1, 5 * mm))

    def build_tables(
        self,
        story: list[Any],
        calculation_rows: Sequence[Mapping[str, Any]],
        coordinates_rows: Sequence[Mapping[str, Any]],
        selected_fields: dict[str, bool],
        doc_width: float,
    ) -> None:
        section_style = _style(11.5, bold=True, align=TA_LEFT, leading=13)
        note_style = _style(7.2, align=TA_LEFT, leading=9)

        # 1. Tabela Principal de Cálculos (Página 1)
        story.append(Paragraph(TABLE_SPECS["tabela_calculos"]["title"], section_style))
        story.append(Spacer(1, 2 * mm))
        story.append(self._build_filtered_table(TABLE_SPECS["tabela_calculos"], calculation_rows, selected_fields, doc_width))
        story.append(Spacer(1, 4 * mm))

    def build_summary(
        self,
        story: list[Any],
        calculation_rows: Sequence[Mapping[str, Any]],
        area: float,
        perimeter: float,
        precision: float | None,
        selected_fields: dict[str, bool],
        doc_width: float,
    ) -> None:
        section_style = _style(11.5, bold=True, align=TA_LEFT, leading=13)
        note_style = _style(7.2, align=TA_LEFT, leading=9)
        title_style = _style(18, bold=True, align=TA_CENTER, leading=20)

        # Painel de verificações (Página 1)
        story.append(Paragraph("PAINEL DE VERIFICAÇÕES DE FECHAMENTO", section_style))
        story.append(Spacer(1, 2 * mm))
        story.append(self._verifications_table_filtered(calculation_rows, selected_fields, doc_width))

        # Ir para a página 2 (sketch)
        story.append(NextPageTemplate("sketch"))
        story.append(PageBreak())

        # 2. Tabela de Coordenadas e Duplas Áreas (Página 2)
        story.append(Paragraph(TABLE_SPECS["tabela_areas"]["title"], section_style))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph("Coordenadas corrigidas e consolidação das duplas áreas", note_style))
        story.append(Spacer(1, 2 * mm))
        story.append(self._build_filtered_table(TABLE_SPECS["tabela_areas"], calculation_rows, selected_fields, doc_width))

        # Ir para a página 3 (desenho gráfico)
        story.append(PageBreak())
        story.append(Paragraph("PRANCHA GRÁFICA DA POLIGONAL", title_style))
        story.append(Spacer(1, 4 * mm))
        
        # Prancha gráfica da poligonal
        sketch_points = []
        if selected_fields.get("Gráfico da Poligonal", True):
            for row in calculation_rows:
                x_val = _row_value(row, ["Coordenada X", "x_corrigido", "x"])
                y_val = _row_value(row, ["Coordenada Y", "y_corrigido", "y"])
                try:
                    sketch_points.append((float(x_val), float(y_val)))
                except (ValueError, TypeError):
                    pass
        story.append(SketchFlowable(sketch_points, width=doc_width, height=PAGE3_GRAPH_H))

    def build_footer(self, canvas: Any, doc: Any, project_meta: Mapping[str, Any], generated_at: datetime) -> None:
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#4d4d4d"))
        canvas.setLineWidth(0.55)
        canvas.rect(LEFT_MARGIN / 2, BOTTOM_MARGIN / 2, PAGE_WIDTH - LEFT_MARGIN, PAGE_HEIGHT - TOP_MARGIN, stroke=1, fill=0)

        name_display = project_meta['name']
        footer_text = f"Página {canvas.getPageNumber()} | {generated_at.strftime('%d/%m/%Y %H:%M')} | {name_display}"
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

    # Métodos privados auxiliares para A3

    def _metadata_table(self, project: Mapping[str, str]) -> Table:
        data = [
            [_p("PROJETO", 6.6, bold=True), _p(project["name"], 7.4, bold=True)],
            [_p("CONTRATANTE", 6.6, bold=True), _p(project.get("client") or "-", 6.6)],
            [_p("LOCALIDADE", 6.6, bold=True), _p(project.get("location") or "-", 6.6)],
            [_p("INSTITUIÇÃO", 6.6, bold=True), _p(project["institution"] or "-", 6.6)],
            [_p("RESPONSÁVEL", 6.6, bold=True), _p(project["surveyor"] or "-", 6.6)],
            [_p("DATA", 6.6, bold=True), _p(project["survey_date"] or "-", 6.6)],
            [_p("SISTEMA COORD.", 6.6, bold=True), _p(project.get("coordinate_system") or "-", 6.6)],
            [_p("DATUM/REF.", 6.6, bold=True), _p(project.get("reference_point") or "-", 6.6)],
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
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        return table

    def _build_filtered_table(self, spec: Mapping[str, Any], rows: Sequence[Mapping[str, Any]], selected_fields: dict[str, bool], max_width: float) -> LongTable:
        header = _build_header(spec)
        body: list[list[Paragraph]] = []
        
        for index, row in enumerate(rows, start=1):
            rendered_row: list[Paragraph] = []
            for column in spec["columns"]:
                label = column["label"]
                kind = column["kind"]
                keys = column["keys"]
                
                # Checa se o campo está habilitado
                show = True
                if label == "Estações" and not selected_fields.get("Vértices", True):
                    show = False
                elif label == "Estações Visadas" and not selected_fields.get("Vértices", True):
                    show = False
                elif "Distâncias" in label and not selected_fields.get("Distâncias", True):
                    show = False
                elif "Ângulos Internos Lidos" in label and not selected_fields.get("Ângulos", True):
                    show = False
                elif "Ângulos Internos Compensados" in label and not selected_fields.get("Ângulos", True):
                    show = False
                elif "Azimutes" in label and not selected_fields.get("Azimutes", True):
                    show = False
                elif "Rumos" in label and not selected_fields.get("Rumos", True):
                    show = False
                elif ("Senos" in label or "Cosenos" in label) and not selected_fields.get("Projeções", True):
                    show = False
                elif ("E (+)" in label or "O (-)" in label or "N (+)" in label or "S (-)" in label) and not selected_fields.get("Projeções", True):
                    show = False
                elif ("Cx" in label or "Cy" in label) and not selected_fields.get("Ajuste Bowditch", True):
                    show = False
                elif (label in ("x", "y", "X", "Y", "ΣX", "ΣY")) and not selected_fields.get("Coordenadas", True):
                    show = False
                elif "Duplas" in label and not selected_fields.get("Área", True):
                    show = False

                raw_value = _row_value(row, keys, default="")
                if label == "Estações" and raw_value in ("", None):
                    raw_value = index
                
                val_formatted = _format_cell(raw_value, kind) if show else ""
                rendered_row.append(_p(val_formatted, 6.2, align=TA_CENTER))
            body.append(rendered_row)

        sum_row = self._calculate_sum_row_filtered(spec, rows, selected_fields)
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

    def _calculate_sum_row_filtered(self, spec: Mapping[str, Any], rows: Sequence[Mapping[str, Any]], selected_fields: dict[str, bool]) -> list[Paragraph]:
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
            
            # Checa se o campo correspondente está habilitado para mostrar a soma
            show_sum = True
            if "Distâncias" in label and not selected_fields.get("Distâncias", True):
                show_sum = False
            elif "Ângulos" in label and not selected_fields.get("Ângulos", True):
                show_sum = False
            elif ("E (+)" in label or "O (-)" in label or "N (+)" in label or "S (-)" in label) and not selected_fields.get("Projeções", True):
                show_sum = False
            elif ("Cx" in label or "Cy" in label) and not selected_fields.get("Ajuste Bowditch", True):
                show_sum = False
            elif (label in ("x", "y")) and not selected_fields.get("Coordenadas", True):
                show_sum = False
            elif "Duplas" in label and not selected_fields.get("Área", True):
                show_sum = False

            should_sum = False
            if kind == "dms" and ("Ângulo" in label or "Angulo" in label):
                should_sum = True
            elif label in ("Distâncias Medidas", "E (+)", "O (-)", "N (+)", "S (-)", "Cx", "Cy", "x", "y", "A Somar", "A Subtrair"):
                should_sum = True
            
            if should_sum and show_sum:
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

    def _verifications_table_filtered(self, calculation_rows: Sequence[Mapping[str, Any]], selected_fields: dict[str, bool], max_width: float) -> Table:
        n = len(calculation_rows)
        
        # 1. Verificação angular
        sum_obs = 0.0
        sum_comp = 0.0
        for row in calculation_rows:
            sum_obs += _parse_dms_to_decimal(_row_value(row, ["Ângulo Interno Lido", "Angulo Interno Lido"]))
            sum_comp += _parse_dms_to_decimal(_row_value(row, ["Ângulo Interno Compensado", "Angulo Interno Compensado"]))
        
        val_teorico = (n - 2) * 180.0
        erro_ang = sum_obs - val_teorico
        
        show_ang = selected_fields.get("Fechamento Angular", True)
        ang_rows = [
            ("Soma dos Ângulos Lidos", _format_dms(sum_obs) if show_ang else ""),
            ("Fechamento Teórico (N-2)*180°", _format_dms(val_teorico) if show_ang else ""),
            ("Erro de Fechamento Angular", _format_dms(erro_ang) if show_ang else ""),
            ("Soma dos Ângulos Compensados", _format_dms(sum_comp) if show_ang else ""),
        ]
        
        # 2. Verificação de projeções lineares
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
        
        show_linear = selected_fields.get("Fechamento Linear", True)
        show_bowditch = selected_fields.get("Ajuste Bowditch", True)
        proj_rows = [
            ("Soma Projeções Leste (E+)", _format_number(sum_e, 3) if show_linear else ""),
            ("Soma Projeções Oeste (O-)", _format_number(sum_o, 3) if show_linear else ""),
            ("Erro de Fechamento em X (Dx)", _format_number(dx, 3) if show_linear else ""),
            ("Soma das Correções Cx", _format_number(sum_cx, 3) if show_bowditch else ""),
            ("Soma Projeções Norte (N+)", _format_number(sum_n, 3) if show_linear else ""),
            ("Soma Projeções Sul (S-)", _format_number(sum_s, 3) if show_linear else ""),
            ("Erro de Fechamento em Y (Dy)", _format_number(dy, 3) if show_linear else ""),
            ("Soma das Correções Cy", _format_number(sum_cy, 3) if show_bowditch else ""),
        ]
        
        # 3. Erros e precisão
        erro_lin = math.sqrt(dx**2 + dy**2)
        prec = precisao_relativa(perimeter, erro_lin) if perimeter > 0 else float("inf")
        
        show_prec = selected_fields.get("Fechamento Linear", True)
        err_rows = [
            ("Número de Estações", str(n)),
            ("Perímetro Total (m)", _format_number(perimeter, 3) if selected_fields.get("Perímetro", True) else ""),
            ("Erro de Fechamento Linear (m)", _format_number(erro_lin, 3) if show_prec else ""),
            ("Precisão Relativa Obtida", _format_precision(prec) if show_prec else ""),
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

    def _draw_page3_panels(
        self,
        canvas: Any,
        project_meta: Mapping[str, str],
        area: Any,
        perimeter: Any,
        precision: Any,
        coordinates_rows: Sequence[Mapping[str, Any]],
        selected_fields: dict[str, bool],
    ) -> None:
        left_x = LEFT_MARGIN
        right_margin = RIGHT_MARGIN
        bottom_y = BOTTOM_MARGIN + 2 * mm
        band_top = bottom_y + PAGE3_BOTTOM_BAND_H - 1 * mm
        left_width = 225 * mm
        right_width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN - left_width - 4 * mm
        right_width = max(78 * mm, right_width)
        left_width = min(left_width, PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN - right_width - 4 * mm)

        # Dados do projeto e resumo do painel
        show_area = selected_fields.get("Área", True)
        show_peri = selected_fields.get("Perímetro", True)
        show_meta = selected_fields.get("Dados do projeto", True)
        
        # Tabelas auxiliares
        area_val = area if show_area else 0.0
        peri_val = perimeter if show_peri else 0.0
        prec_val = precision if selected_fields.get("Fechamento Linear", True) else None
        
        summary = self._summary_table_filtered(area_val, peri_val, prec_val, project_meta["method"], selected_fields)
        points = self._points_table_filtered(coordinates_rows, selected_fields)
        legend = _legend_table()
        
        meta_to_stamp = project_meta if show_meta else {k: "" for k in project_meta}
        if not show_meta:
            meta_to_stamp["name"] = "PROJETO OCULTADO"
        stamp = self._stamp_table_filtered(meta_to_stamp, area_val, selected_fields)

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

    def _summary_table_filtered(self, area: Any, perimeter: Any, precision: Any, method: str, selected_fields: dict[str, bool]) -> Table:
        try:
            area_val = float(area)
        except (ValueError, TypeError):
            area_val = 0.0
            
        show_area = selected_fields.get("Área", True)
        show_peri = selected_fields.get("Perímetro", True)
        show_prec = selected_fields.get("Fechamento Linear", True)
        
        data = [
            [_p("ÁREA FINAL", 6.6, bold=True), _p(f"{_format_number(area, 3)} m²" if show_area else "", 6.9)],
            [_p("ÁREA EM HECTARES", 6.6, bold=True), _p(f"{_format_number(area_val / 10000.0, 4)} ha" if show_area else "", 6.9)],
            [_p("PERÍMETRO", 6.6, bold=True), _p(f"{_format_number(perimeter, 3)} m" if show_peri else "", 6.9)],
            [_p("PRECISÃO RELATIVA", 6.6, bold=True), _p(_format_precision(precision) if show_prec else "", 6.9)],
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

    def _points_table_filtered(self, rows: Sequence[Mapping[str, Any]], selected_fields: dict[str, bool]) -> Table:
        data = [[
            _p("PONTO", 6.2, bold=True),
            _p("Coordenadas em X", 6.2, bold=True),
            _p("Coordenadas em Y", 6.2, bold=True),
        ]]
        show_coords = selected_fields.get("Coordenadas", True)
        
        for row in rows:
            p_name = _format_text(_row_value(row, ["Ponto", "point_name", "point"])) or "-"
            x_val = _format_number(_row_value(row, ["Coordenada X"]), 3) if show_coords else ""
            y_val = _format_number(_row_value(row, ["Coordenada Y"]), 3) if show_coords else ""
            
            data.append([
                _p(p_name, 6.1),
                _p(x_val, 6.1),
                _p(y_val, 6.1),
            ])

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

    def _stamp_table_filtered(self, project: Mapping[str, str], area: Any, selected_fields: dict[str, bool]) -> Table:
        try:
            area_val = float(area)
        except (ValueError, TypeError):
            area_val = 0.0
            
        show_area = selected_fields.get("Área", True)
        
        rows = [
            ["PROJETO", project["name"]],
            ["CONTRATANTE", project.get("client") or "-"],
            ["LOCALIDADE", project.get("location") or "-"],
            ["RESPONSÁVEL", project["surveyor"] or "-"],
            ["DATA", project["survey_date"] or "-"],
            ["SISTEMA COORD.", project.get("coordinate_system") or "-"],
            ["DATUM/REF.", project.get("reference_point") or "-"],
            ["REVISÃO", project["revision"]],
            ["MÉTODO", project["method"]],
            ["ÁREA FINAL", f"{_format_number(area, 3)} m²" if show_area else ""],
            ["ÁREA EM HECTARES", f"{_format_number(area_val / 10000.0, 4)} ha" if show_area else ""],
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
                    ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                ]
            )
        )
        return table


# Helper local para tabelas de verificações (mesmo de pdf_report.py)
from core.reports.pdf_report import _make_sub_table, _legend_table
