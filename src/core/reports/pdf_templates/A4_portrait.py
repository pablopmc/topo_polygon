from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence
import math

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    SimpleDocTemplate,
    Flowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from core.calculations.engine import precisao_relativa
from core.reports.pdf_templates.pdf_template_base import PDFTemplate
from core.reports.pdf_report import (
    _register_fonts,
    _font_name,
    _style,
    _p,
    _as_dict,
    _project_meta,
    _parse_dms_to_decimal,
    _format_number,
    _format_text,
    _format_dms,
    _format_precision,
    _clean_zero,
    SketchFlowable,
    _row_value,
    _fit_widths,
)

PAGE_SIZE = A4
PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE

LEFT_MARGIN = 12 * mm
RIGHT_MARGIN = 12 * mm
TOP_MARGIN = 15 * mm
BOTTOM_MARGIN = 18 * mm
PRINTABLE_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN


class A4PortraitTemplate(PDFTemplate):
    """Template A4 Retrato - Reorganiza e desmembra tabelas para ajuste vertical ideal"""

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

        proj_map = _as_dict(project_meta)
        proj_meta = _project_meta(proj_map)
        generated_at = generated_at or datetime.now()

        # Configura o documento SimpleDocTemplate com paginação automática do ReportLab
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=PAGE_SIZE,
            leftMargin=LEFT_MARGIN,
            rightMargin=RIGHT_MARGIN,
            topMargin=TOP_MARGIN,
            bottomMargin=BOTTOM_MARGIN,
            title="Relatório Topográfico - Retrato A4",
            author=proj_meta["surveyor"] or "TopoPABLO",
        )

        story = []

        # 1. Capa / Cabeçalho
        self.build_cover(story, proj_meta, selected_fields)

        # 2. Tabelas Desmembradas
        self.build_tables(story, calculation_rows, coordinates_rows, selected_fields, PRINTABLE_WIDTH)

        # 3. Resumo de Fechamento e Prancha Gráfica
        self.build_summary(story, calculation_rows, area, perimeter, precision, selected_fields, PRINTABLE_WIDTH)

        # Constrói o documento chamando a decoração de página (build_footer) via canvas maker
        def on_page_cb(canvas, doc_obj):
            self.build_footer(canvas, doc_obj, proj_meta, generated_at)

        doc.build(story, onFirstPage=on_page_cb, onLaterPages=on_page_cb)

    def build_cover(self, story: list[Any], project_meta: Mapping[str, Any], selected_fields: dict[str, bool] = None) -> None:
        title_style = _style(14, bold=True, align=TA_CENTER, leading=16)
        story.append(Paragraph("RELATÓRIO TÉCNICO TOPOGRÁFICO", title_style))
        story.append(Spacer(1, 4 * mm))

        # Tabela de Identificação do Projeto
        if selected_fields is None or selected_fields.get("Dados do projeto", True):
            story.append(Paragraph("IDENTIFICAÇÃO DO PROJETO", _style(9, bold=True, align=TA_LEFT)))
            story.append(Spacer(1, 1.5 * mm))
            
            data = [
                [_p("Nome do Projeto", 8, bold=True, align=TA_LEFT), _p(project_meta["name"], 8, align=TA_LEFT)],
                [_p("Contratante/Cliente", 8, bold=True, align=TA_LEFT), _p(project_meta.get("client") or "-", 8, align=TA_LEFT)],
                [_p("Localidade/Endereço", 8, bold=True, align=TA_LEFT), _p(project_meta.get("location") or "-", 8, align=TA_LEFT)],
                [_p("Instituição", 8, bold=True, align=TA_LEFT), _p(project_meta["institution"] or "-", 8, align=TA_LEFT)],
                [_p("Responsável", 8, bold=True, align=TA_LEFT), _p(project_meta["surveyor"] or "-", 8, align=TA_LEFT)],
                [_p("Data do Levantamento", 8, bold=True, align=TA_LEFT), _p(project_meta["survey_date"] or "-", 8, align=TA_LEFT)],
                [_p("Sistema de Coordenadas", 8, bold=True, align=TA_LEFT), _p(project_meta.get("coordinate_system") or "-", 8, align=TA_LEFT)],
                [_p("Ponto de Referência", 8, bold=True, align=TA_LEFT), _p(project_meta.get("reference_point") or "-", 8, align=TA_LEFT)],
                [_p("Método de Ajuste", 8, bold=True, align=TA_LEFT), _p(project_meta["method"], 8, align=TA_LEFT)],
                [_p("Revisão", 8, bold=True, align=TA_LEFT), _p(project_meta["revision"], 8, align=TA_LEFT)],
            ]
            if project_meta.get("description"):
                data.append([_p("Descrição", 8, bold=True, align=TA_LEFT), _p(project_meta["description"], 8, align=TA_LEFT)])
                
            table = Table(data, colWidths=[45 * mm, PRINTABLE_WIDTH - 45 * mm], hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#444444")),
                        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#666666")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(table)
            story.append(Spacer(1, 5 * mm))

    def build_tables(
        self,
        story: list[Any],
        calculation_rows: Sequence[Mapping[str, Any]],
        coordinates_rows: Sequence[Mapping[str, Any]],
        selected_fields: dict[str, bool],
        doc_width: float,
    ) -> None:
        title_style = _style(9, bold=True, align=TA_LEFT, leading=11)

        # TABELA 1: ÂNGULOS E AZIMUTES (Seq, Ponto, Ângulo Lido, Ângulo Compensado, Azimute, Rumo)
        # Determinar colunas ativas
        cols_ang = []
        cols_ang.append(("Estação", "Estação", 15 * mm, "text"))
        cols_ang.append(("Ponto", "Ponto", 25 * mm, "text"))
        
        if selected_fields.get("Ângulos", True):
            cols_ang.append(("Ângulo Lido", "Ângulo Interno Lido", 38 * mm, "dms"))
            cols_ang.append(("Ângulo Comp.", "Ângulo Interno Compensado", 38 * mm, "dms"))
        if selected_fields.get("Azimutes", True):
            cols_ang.append(("Azimute", "Azimute", 35 * mm, "dms"))
        if selected_fields.get("Rumos", True):
            cols_ang.append(("Rumo", "Rumo", 35 * mm, "text"))

        if len(cols_ang) > 2:
            story.append(Paragraph("1. ÂNGULOS INTERNOS E ORIENTAÇÕES", title_style))
            story.append(Spacer(1, 1.5 * mm))
            story.append(self._generate_a4_table(cols_ang, calculation_rows, doc_width))
            story.append(Spacer(1, 5 * mm))

        # TABELA 2: PROJEÇÕES E AJUSTE (Seq, Ponto, Distância, Projeções E/O/N/S, Cx, Cy)
        cols_proj = []
        cols_proj.append(("Estação", "Estação", 15 * mm, "text"))
        cols_proj.append(("Ponto", "Ponto", 25 * mm, "text"))
        
        if selected_fields.get("Distâncias", True):
            cols_proj.append(("Distância (m)", "Distância (m)", 28 * mm, "float3"))
        if selected_fields.get("Projeções", True):
            cols_proj.append(("Proj. E (+)", "Projeção E (+)", 23 * mm, "float3"))
            cols_proj.append(("Proj. O (-)", "Projeção O (-)", 23 * mm, "float3"))
            cols_proj.append(("Proj. N (+)", "Projeção N (+)", 23 * mm, "float3"))
            cols_proj.append(("Proj. S (-)", "Projeção S (-)", 23 * mm, "float3"))
        if selected_fields.get("Ajuste Bowditch", True):
            cols_proj.append(("Cx", "Correção em X (Cx)", 20 * mm, "float3"))
            cols_proj.append(("Cy", "Correção em Y (Cy)", 20 * mm, "float3"))

        if len(cols_proj) > 2:
            story.append(Paragraph("2. DISTÂNCIAS, PROJEÇÕES E CORREÇÕES", title_style))
            story.append(Spacer(1, 1.5 * mm))
            story.append(self._generate_a4_table(cols_proj, calculation_rows, doc_width))
            story.append(Spacer(1, 5 * mm))

        # TABELA 3: COORDENADAS CORRIGIDAS (Seq, Ponto, Proj. X Comp, Proj. Y Comp, Coordenada X, Coordenada Y)
        if selected_fields.get("Coordenadas", True):
            cols_coord = [
                ("Estação", "Estação", 15 * mm, "text"),
                ("Ponto", "Ponto", 25 * mm, "text"),
                ("Proj. X Comp.", "Projeção Compensada X (Leste/Oeste)", 36 * mm, "float3"),
                ("Proj. Y Comp.", "Projeção Compensada Y (Norte/Sul)", 36 * mm, "float3"),
                ("Coordenada X (E)", "Coordenada X", 37 * mm, "float3"),
                ("Coordenada Y (N)", "Coordenada Y", 37 * mm, "float3"),
            ]
            story.append(Paragraph("3. COORDENADAS RETANGULARES AJUSTADAS", title_style))
            story.append(Spacer(1, 1.5 * mm))
            story.append(self._generate_a4_table(cols_coord, calculation_rows, doc_width))
            story.append(Spacer(1, 5 * mm))

        # TABELA 4: DUPLAS ÁREAS (Seq, Ponto, Soma X, Dupla X+, Dupla X-, Soma Y, Dupla Y+, Dupla Y-)
        if selected_fields.get("Área", True):
            cols_area = [
                ("Estação", "Estação", 12 * mm, "text"),
                ("Ponto", "Ponto", 20 * mm, "text"),
                ("Soma X (ΣX)", "Soma X", 26 * mm, "float3"),
                ("Dupla X (+)", "Duplas Áreas X (+)", 26 * mm, "float3_empty_zero"),
                ("Dupla X (-)", "Duplas Áreas X (-)", 26 * mm, "float3_empty_zero"),
                ("Soma Y (ΣY)", "Soma Y", 26 * mm, "float3"),
                ("Dupla Y (+)", "Duplas Áreas Y (+)", 26 * mm, "float3_empty_zero"),
                ("Dupla Y (-)", "Duplas Áreas Y (-)", 26 * mm, "float3_empty_zero"),
            ]
            story.append(Paragraph("4. DUPLAS ÁREAS DE FECHAMENTO (MÉTODO DE GAUSS)", title_style))
            story.append(Spacer(1, 1.5 * mm))
            story.append(self._generate_a4_table(cols_area, calculation_rows, doc_width))
            story.append(Spacer(1, 5 * mm))

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
        title_style = _style(9, bold=True, align=TA_LEFT, leading=11)
        n = len(calculation_rows)

        # 1. Painel de Fechamentos (Angular, Linear, Bowditch)
        story.append(Paragraph("5. VERIFICAÇÃO DOS ERROS DE FECHAMENTO", title_style))
        story.append(Spacer(1, 1.5 * mm))

        verification_data = []

        # Angular
        if selected_fields.get("Fechamento Angular", True):
            sum_obs = 0.0
            for row in calculation_rows:
                sum_obs += _parse_dms_to_decimal(_row_value(row, ["Ângulo Interno Lido", "Angulo Interno Lido"]))
            val_teorico = (n - 2) * 180.0
            erro_ang = sum_obs - val_teorico

            verification_data.extend([
                [_p("Soma dos Ângulos Lido", 7.5, bold=True, align=TA_LEFT), _p(_format_dms(sum_obs), 7.5, align=TA_CENTER)],
                [_p("Soma Teórica (N-2)x180°", 7.5, bold=True, align=TA_LEFT), _p(_format_dms(val_teorico), 7.5, align=TA_CENTER)],
                [_p("Erro de Fechamento Angular", 7.5, bold=True, align=TA_LEFT), _p(_format_dms(erro_ang), 7.5, align=TA_CENTER)],
            ])

        # Linear
        sum_e = sum_o = sum_n = sum_s = perimeter_val = 0.0
        for row in calculation_rows:
            sum_e += float(_row_value(row, ["Projeção E (+)"], 0.0))
            sum_o += float(_row_value(row, ["Projeção O (-)"], 0.0))
            sum_n += float(_row_value(row, ["Projeção N (+)"], 0.0))
            sum_s += float(_row_value(row, ["Projeção S (-)"], 0.0))
            perimeter_val += float(_row_value(row, ["Distância (m)", "distancia"], 0.0))
        dx = sum_e - sum_o
        dy = sum_n - sum_s
        erro_lin = math.sqrt(dx**2 + dy**2)
        prec = precisao_relativa(perimeter_val, erro_lin) if perimeter_val > 0 else float("inf")

        if selected_fields.get("Fechamento Linear", True):
            verification_data.extend([
                [_p("Erro Linear em X (Dx)", 7.5, bold=True, align=TA_LEFT), _p(f"{dx:.4f} m", 7.5, align=TA_CENTER)],
                [_p("Erro Linear em Y (Dy)", 7.5, bold=True, align=TA_LEFT), _p(f"{dy:.4f} m", 7.5, align=TA_CENTER)],
                [_p("Erro de Fechamento Linear", 7.5, bold=True, align=TA_LEFT), _p(f"{erro_lin:.4f} m", 7.5, align=TA_CENTER)],
                [_p("Precisão Relativa Obtida", 7.5, bold=True, align=TA_LEFT), _p(_format_precision(prec), 7.5, align=TA_CENTER)],
            ])

        if selected_fields.get("Perímetro", True):
            verification_data.append([_p("Perímetro Total", 7.5, bold=True, align=TA_LEFT), _p(f"{perimeter_val:.4f} m", 7.5, align=TA_CENTER)])

        if selected_fields.get("Área", True):
            verification_data.extend([
                [_p("Área Planimétrica Final", 7.5, bold=True, align=TA_LEFT), _p(f"{area:.4f} m²", 7.5, align=TA_CENTER)],
                [_p("Área Final em Hectares", 7.5, bold=True, align=TA_LEFT), _p(f"{area/10000.0:.6f} ha", 7.5, align=TA_CENTER)],
            ])

        if verification_data:
            table_ver = Table(verification_data, colWidths=[doc_width * 0.65, doc_width * 0.35], hAlign="LEFT")
            table_ver.setStyle(
                TableStyle(
                    [
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#333333")),
                        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#666666")),
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8f8f8")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )
            story.append(table_ver)
            story.append(Spacer(1, 6 * mm))

        # 2. Prancha Gráfica (Forçar quebra de página se houver prancha)
        if selected_fields.get("Gráfico da Poligonal", True) and len(calculation_rows) >= 3:
            story.append(PageBreak())
            story.append(Paragraph("PRANCHA GRÁFICA DA POLIGONAL", _style(11, bold=True, align=TA_CENTER)))
            story.append(Spacer(1, 3 * mm))
            
            sketch_points = []
            for row in calculation_rows:
                x_val = _row_value(row, ["Coordenada X", "x_corrigido", "x"])
                y_val = _row_value(row, ["Coordenada Y", "y_corrigido", "y"])
                try:
                    sketch_points.append((float(x_val), float(y_val)))
                except (ValueError, TypeError):
                    pass
            
            # Reduz a altura para encaixar no espaço vertical do A4 Retrato
            story.append(SketchFlowable(sketch_points, width=doc_width, height=130 * mm))

    def build_footer(self, canvas: Any, doc: Any, project_meta: Mapping[str, str], generated_at: datetime) -> None:
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#6d6d6d"))
        canvas.setLineWidth(0.5)
        # Borda externa do A4
        canvas.rect(LEFT_MARGIN - 2 * mm, BOTTOM_MARGIN - 2 * mm, PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN + 4 * mm, PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN + 4 * mm)

        footer_text = f"Página {canvas.getPageNumber()} | {generated_at.strftime('%d/%m/%Y %H:%M')} | {project_meta['name']}"
        canvas.setFont(_font_name(False), 7.5)
        canvas.setFillColor(colors.HexColor("#333333"))
        
        # Desenha rodapé
        canvas.drawString(LEFT_MARGIN, BOTTOM_MARGIN - 7 * mm, footer_text)
        canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, BOTTOM_MARGIN - 7 * mm, "TopoCalc - Relatório Técnico")
        
        canvas.restoreState()

    # Métodos privados auxiliares para A4

    def _generate_a4_table(self, col_specs: list[tuple[str, str, float, str]], rows: Sequence[Mapping[str, Any]], total_width: float) -> Table:
        # Construir headers
        header_row = [_p(spec[0], 7.0, bold=True, align=TA_CENTER) for spec in col_specs]
        
        table_data = [header_row]
        for index, row in enumerate(rows):
            rendered_row = []
            for spec in col_specs:
                label, key, _, kind = spec
                val = _row_value(row, [key])
                if label == "Estação" and val in ("", None):
                    val = index + 1
                
                # Formatar o dado
                val_str = self._format_cell_local(val, kind)
                rendered_row.append(_p(val_str, 6.8, align=TA_CENTER))
            table_data.append(rendered_row)

        # Calcular largura proporcional das colunas para preencher exatamente total_width
        original_widths = [spec[2] for spec in col_specs]
        widths = _fit_widths(original_widths, total_width)

        table = Table(table_data, colWidths=widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), _font_name(False)),
                    ("FONTSIZE", (0, 0), (-1, -1), 6.5),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#555555")),
                    ("BOX", (0, 0), (-1, -1), 0.55, colors.HexColor("#222222")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaeaea")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return table

    def _format_cell_local(self, value: Any, kind: str) -> str:
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
        return _format_text(value)
