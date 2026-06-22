from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from core.reports.exporter_registry import BaseExporter, ExporterRegistry
from core.reports.pdf_report import _row_value


class GeoJSONExporter(BaseExporter):
    """Exportador para formato GeoJSON de poligonal topográfica e seus vértices"""

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

        data_geracao = datetime.now().isoformat()
        nome_projeto = project.get("name") or project.get("project_name") or "PROJETO"

        features = []

        # 1. Feature Polígono (poligonal)
        if len(sketch_points) >= 3:
            # Fechar o polígono se necessário
            coords = list(sketch_points)
            if coords[0] != coords[-1]:
                coords.append(coords[0])

            polygon_feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[list(pt) for pt in coords]]
                },
                "properties": {
                    "tipo": "Poligonal",
                    "projeto": nome_projeto,
                    "area_m2": area,
                    "perimetro_m": perimeter,
                    "data_geracao": data_geracao,
                }
            }
            features.append(polygon_feature)

        # 2. Features Pontos (vértices)
        for index, row in enumerate(calculation_rows):
            name = _row_value(row, ["Ponto", "point_name", "point"])
            x_val = _row_value(row, ["Coordenada X", "x_corrigido", "x"])
            y_val = _row_value(row, ["Coordenada Y", "y_corrigido", "y"])

            try:
                x = float(x_val)
                y = float(y_val)
            except (ValueError, TypeError):
                continue

            point_feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [x, y]
                },
                "properties": {
                    "tipo": "Vértice",
                    "nome": name,
                    "x": x,
                    "y": y,
                    "sequencia": index + 1,
                    "data_geracao": data_geracao,
                }
            }
            features.append(point_feature)

        geojson_data = {
            "type": "FeatureCollection",
            "crs": {
                "type": "name",
                "properties": {
                    "name": "urn:ogc:def:crs:OGC:1.3:CRS84" # padrão
                }
            },
            "features": features
        }

        with open(output_path, mode="w", encoding="utf-8") as f:
            json.dump(geojson_data, f, indent=2, ensure_ascii=False)


# Registrar exportador no registry global
ExporterRegistry.register(
    format_id="GEOJSON",
    display_name="GeoJSON",
    file_filter="Arquivos GeoJSON (*.geojson)",
    default_ext="geojson",
    default_name="poligonal.geojson",
    icon_name="SP_DriveHDIcon",
    exporter_class=GeoJSONExporter,
)
