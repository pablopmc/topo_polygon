from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence
import shapefile

from core.reports.exporter_registry import BaseExporter, ExporterRegistry
from core.reports.pdf_report import _row_value


class SHPExporter(BaseExporter):
    """Exportador para formato ESRI Shapefile de poligonal topográfica e seus vértices"""

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
        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Remove a extensão se fornecida para criar os arquivos de camada separados
        base_path = output_path.parent / output_path.stem

        prj_content = (
            'GEOGCS["GCS_WGS_1984",'
            'DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],'
            'PRIMEM["Greenwich",0.0],'
            'UNIT["Degree",0.0174532925199433]]'
        )

        nome_projeto = project.get("name") or project.get("project_name") or "PROJETO"

        # 1. Exportar os Vértices (Camada de Pontos)
        vertices_shp_path = f"{base_path}_vertices"
        w_points = shapefile.Writer(vertices_shp_path, shapeType=shapefile.POINT)
        w_points.field("ID", "N")
        w_points.field("Nome", "C", size=50)
        w_points.field("X", "F", decimal=4)
        w_points.field("Y", "F", decimal=4)

        for index, row in enumerate(calculation_rows):
            name = _row_value(row, ["Ponto", "point_name", "point"])
            x_val = _row_value(row, ["Coordenada X", "x_corrigido", "x"])
            y_val = _row_value(row, ["Coordenada Y", "y_corrigido", "y"])

            try:
                x = float(x_val)
                y = float(y_val)
            except (ValueError, TypeError):
                continue

            w_points.point(x, y)
            w_points.record(ID=index + 1, Nome=name, X=x, Y=y)

        w_points.close()

        # Escrever arquivo .prj dos pontos
        with open(f"{vertices_shp_path}.prj", mode="w", encoding="utf-8") as f:
            f.write(prj_content)

        # 2. Exportar a Poligonal (Camada de Polígono)
        if len(sketch_points) >= 3:
            poly_shp_path = f"{base_path}_poligonal"
            w_poly = shapefile.Writer(poly_shp_path, shapeType=shapefile.POLYGON)
            w_poly.field("ID", "N")
            w_poly.field("Nome", "C", size=50)
            w_poly.field("Area", "F", decimal=4)
            w_poly.field("Perimetro", "F", decimal=4)

            # Fechar o polígono para o pyshp
            coords = [list(pt) for pt in sketch_points]
            if coords[0] != coords[-1]:
                coords.append(coords[0])

            w_poly.poly([coords])
            w_poly.record(ID=1, Nome=nome_projeto, Area=area, Perimetro=perimeter)
            w_poly.close()

            # Escrever arquivo .prj do polígono
            with open(f"{poly_shp_path}.prj", mode="w", encoding="utf-8") as f:
                f.write(prj_content)


# Registrar exportador no registry global
ExporterRegistry.register(
    format_id="SHP",
    display_name="SHP",
    file_filter="Arquivos Shapefile (*.shp)",
    default_ext="shp",
    default_name="poligonal.shp",
    icon_name="SP_ArrowDown",
    exporter_class=SHPExporter,
)
