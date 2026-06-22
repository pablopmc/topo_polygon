from __future__ import annotations

import json
from pathlib import Path
import pytest
import shapefile

from core.calculations.engine import CalculationEngine, VertexData
from core.reports.exporter_registry import ExporterRegistry
import core.reports.csv_export
import core.reports.geojson_export
import core.reports.kml_export
import core.reports.shp_export


@pytest.fixture
def sample_data() -> tuple[dict, list, list, float, float]:
    project = {
        "name": "Projeto Teste",
        "surveyor": "Eng. Civil Pablo Medina",
        "institution": "FURG",
        "survey_date": "2026-06-21",
        "description": "Levantamento de teste para validacao de GIS",
    }
    
    engine = CalculationEngine(azimute_inicial=45.0, coordenada_inicial=(100.0, 200.0))
    vertices = [
        VertexData(sequence=1, point_name="V1", graus=90, minutos=0, segundos=0.0, distancia=50.0),
        VertexData(sequence=2, point_name="V2", graus=90, minutos=0, segundos=0.0, distancia=60.0),
        VertexData(sequence=3, point_name="V3", graus=90, minutos=0, segundos=0.0, distancia=50.0),
        VertexData(sequence=4, point_name="V4", graus=90, minutos=0, segundos=0.0, distancia=60.0),
    ]
    
    resultado = engine.calcular(vertices)
    tabela_final = resultado.tabela_final.to_dict(orient="records")
    sketch_points = resultado.coordenadas_corrigidas
    
    return project, tabela_final, sketch_points, resultado.area, resultado.perimetro


def test_exporter_registry_lists_alphabetically() -> None:
    formats = [f["display_name"] for f in ExporterRegistry.list_formats()]
    assert "CSV" in formats
    assert "DXF" in formats
    assert "Excel" in formats
    assert "GeoJSON" in formats
    assert "KML" in formats
    assert "PDF" in formats
    assert "SHP" in formats
    
    # Check alphabetical ordering
    assert formats == sorted(formats, key=lambda x: x.upper())


def test_geojson_export(tmp_path: Path, sample_data) -> None:
    project, rows, pts, area, perim = sample_data
    file_path = tmp_path / "test.geojson"
    
    exporter = ExporterRegistry.get_exporter("GEOJSON")
    exporter.export(
        filename=file_path,
        project=project,
        calculation_rows=rows,
        coordinates_rows=rows,
        sketch_points=pts,
        area=area,
        perimeter=perim,
        precision=1000.0,
    )
    
    assert file_path.exists()
    
    with open(file_path, mode="r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 5 # 1 Polygon + 4 Points
    
    # Verify polygon feature
    polygon_feat = data["features"][0]
    assert polygon_feat["geometry"]["type"] == "Polygon"
    assert polygon_feat["properties"]["tipo"] == "Poligonal"
    assert polygon_feat["properties"]["area_m2"] == area
    
    # Verify first point feature
    point_feat = data["features"][1]
    assert point_feat["geometry"]["type"] == "Point"
    assert point_feat["properties"]["nome"] == "V1"
    assert point_feat["geometry"]["coordinates"] == [pts[0][0], pts[0][1]]


def test_kml_export(tmp_path: Path, sample_data) -> None:
    project, rows, pts, area, perim = sample_data
    file_path = tmp_path / "test.kml"
    
    exporter = ExporterRegistry.get_exporter("KML")
    exporter.export(
        filename=file_path,
        project=project,
        calculation_rows=rows,
        coordinates_rows=rows,
        sketch_points=pts,
        area=area,
        perimeter=perim,
        precision=1000.0,
    )
    
    assert file_path.exists()
    content = file_path.read_text(encoding="utf-8")
    
    assert "<kml" in content
    assert "<Document>" in content
    assert "<Style id=\"vertexStyle\">" in content
    assert "<Style id=\"polygonStyle\">" in content
    assert "Projeto Teste" in content
    assert "V1" in content
    assert "V2" in content
    assert "<Polygon>" in content


def test_shp_export(tmp_path: Path, sample_data) -> None:
    project, rows, pts, area, perim = sample_data
    file_path = tmp_path / "test.shp"
    
    exporter = ExporterRegistry.get_exporter("SHP")
    exporter.export(
        filename=file_path,
        project=project,
        calculation_rows=rows,
        coordinates_rows=rows,
        sketch_points=pts,
        area=area,
        perimeter=perim,
        precision=1000.0,
    )
    
    vertices_shp = tmp_path / "test_vertices.shp"
    vertices_dbf = tmp_path / "test_vertices.dbf"
    vertices_shx = tmp_path / "test_vertices.shx"
    vertices_prj = tmp_path / "test_vertices.prj"
    
    poly_shp = tmp_path / "test_poligonal.shp"
    poly_dbf = tmp_path / "test_poligonal.dbf"
    poly_shx = tmp_path / "test_poligonal.shx"
    poly_prj = tmp_path / "test_poligonal.prj"
    
    # Check point files exist
    assert vertices_shp.exists()
    assert vertices_dbf.exists()
    assert vertices_shx.exists()
    assert vertices_prj.exists()
    
    # Check polygon files exist
    assert poly_shp.exists()
    assert poly_dbf.exists()
    assert poly_shx.exists()
    assert poly_prj.exists()
    
    # Read point shapefile with pyshp
    sf_pts = shapefile.Reader(str(vertices_shp))
    assert sf_pts.shapeType == shapefile.POINT
    assert len(sf_pts.shapes()) == 4
    
    # Read polygon shapefile with pyshp
    sf_poly = shapefile.Reader(str(poly_shp))
    assert sf_poly.shapeType == shapefile.POLYGON
    assert len(sf_poly.shapes()) == 1


def test_csv_export(tmp_path: Path, sample_data) -> None:
    project, rows, pts, area, perim = sample_data
    
    # 1. Test comma separator
    file_path_comma = tmp_path / "test_comma.csv"
    exporter = ExporterRegistry.get_exporter("CSV")
    exporter.export(
        filename=file_path_comma,
        project=project,
        calculation_rows=rows,
        coordinates_rows=rows,
        sketch_points=pts,
        area=area,
        perimeter=perim,
        precision=1000.0,
        separator=",",
    )
    
    assert file_path_comma.exists()
    lines_comma = file_path_comma.read_text(encoding="utf-8-sig").splitlines()
    assert lines_comma[0] == "Ordem,Nome,X,Y,Distância,Ângulo,Azimute,Rumo"
    assert "," in lines_comma[1]
    
    # 2. Test semicolon separator
    file_path_semi = tmp_path / "test_semi.csv"
    exporter.export(
        filename=file_path_semi,
        project=project,
        calculation_rows=rows,
        coordinates_rows=rows,
        sketch_points=pts,
        area=area,
        perimeter=perim,
        precision=1000.0,
        separator=";",
    )
    
    assert file_path_semi.exists()
    lines_semi = file_path_semi.read_text(encoding="utf-8-sig").splitlines()
    assert lines_semi[0] == "Ordem;Nome;X;Y;Distância;Ângulo;Azimute;Rumo"
    assert ";" in lines_semi[1]
