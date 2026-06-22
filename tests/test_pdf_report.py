from __future__ import annotations

from pathlib import Path

from PySide6.QtPdf import QPdfDocument

from core.calculations.engine import CalculationEngine, VertexData
from core.reports.pdf_report import generate_pdf_report


def test_generate_pdf_report_creates_three_pages(tmp_path: Path) -> None:
    engine = CalculationEngine(azimute_inicial=0.0, coordenada_inicial=(0.0, 0.0))
    vertices = [
        VertexData(sequence=1, point_name="P1", graus=91, minutos=0, segundos=0.0, distancia=100.0),
        VertexData(sequence=2, point_name="P2", graus=89, minutos=0, segundos=0.0, distancia=120.0),
        VertexData(sequence=3, point_name="P3", graus=92, minutos=30, segundos=0.0, distancia=90.0),
        VertexData(sequence=4, point_name="P4", graus=88, minutos=30, segundos=0.0, distancia=110.0),
    ]

    resultado = engine.calcular(vertices)
    rows = resultado.tabela_final.to_dict(orient="records")
    output = tmp_path / "relatorio.pdf"

    generate_pdf_report(
        output,
        project={
            "name": "Projeto Amostra",
            "institution": "TopoPABLO",
            "surveyor": "Pablo Medina Camacho",
            "survey_date": "2026-06-21",
            "created_at": "2026-06-21",
            "survey_description": "Exportação técnica de teste",
            "client": "Cliente Amostra S/A",
            "location": "Rio Grande - RS",
            "coordinate_system": "UTM SIRGAS2000",
            "reference_point": "M-01",
        },
        calculation_rows=rows,
        coordinates_rows=rows,
        sketch_points=resultado.coordenadas_corrigidas,
        area=resultado.area,
        perimeter=resultado.perimetro,
    )

    document = QPdfDocument()
    document.load(str(output))

    assert output.exists()
    assert document.pageCount() == 3


def test_generate_pdf_report_creates_a4_portrait(tmp_path: Path) -> None:
    engine = CalculationEngine(azimute_inicial=0.0, coordenada_inicial=(0.0, 0.0))
    vertices = [
        VertexData(sequence=1, point_name="P1", graus=91, minutos=0, segundos=0.0, distancia=100.0),
        VertexData(sequence=2, point_name="P2", graus=89, minutos=0, segundos=0.0, distancia=120.0),
        VertexData(sequence=3, point_name="P3", graus=92, minutos=30, segundos=0.0, distancia=90.0),
        VertexData(sequence=4, point_name="P4", graus=88, minutos=30, segundos=0.0, distancia=110.0),
    ]

    resultado = engine.calcular(vertices)
    rows = resultado.tabela_final.to_dict(orient="records")
    output = tmp_path / "relatorio_a4.pdf"

    generate_pdf_report(
        output,
        project={
            "name": "Projeto Amostra A4",
            "institution": "TopoPABLO",
            "surveyor": "Pablo Medina Camacho",
            "survey_date": "2026-06-21",
            "created_at": "2026-06-21",
            "survey_description": "Exportação técnica de teste A4",
            "client": "Cliente Amostra A4 S/A",
            "location": "Porto Alegre - RS",
            "coordinate_system": "UTM WGS84",
            "reference_point": "M-02",
        },
        calculation_rows=rows,
        coordinates_rows=rows,
        sketch_points=resultado.coordenadas_corrigidas,
        area=resultado.area,
        perimeter=resultado.perimetro,
        template_id="A4_PORTRAIT",
    )

    document = QPdfDocument()
    document.load(str(output))

    assert output.exists()
    assert document.pageCount() > 0


def test_parse_dms_to_decimal() -> None:
    from core.reports.pdf_report import _parse_dms_to_decimal
    
    # Test numeric values
    assert _parse_dms_to_decimal(12.5) == 12.5
    assert _parse_dms_to_decimal(0) == 0.0
    
    # Test tuple values
    assert _parse_dms_to_decimal((90, 30, 0.0)) == 90.5
    assert _parse_dms_to_decimal((-45, 15, 0.0)) == -45.25
    
    # Test formatted strings
    assert abs(_parse_dms_to_decimal("90° 30' 00.000\"") - 90.5) < 1e-7
    assert abs(_parse_dms_to_decimal("-45° 15' 00.000\"") - (-45.25)) < 1e-7
    assert _parse_dms_to_decimal("") == 0.0
    assert _parse_dms_to_decimal(None) == 0.0

