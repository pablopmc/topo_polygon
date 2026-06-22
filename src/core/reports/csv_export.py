from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Mapping, Sequence

from core.reports.exporter_registry import BaseExporter, ExporterRegistry
from core.reports.pdf_report import _row_value, _format_dms


class CSVExporter(BaseExporter):
    """Exportador para formato CSV de poligonal topográfica"""

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
        # Define o separador: padrão é vírgula, permitindo customizar via kwargs
        sep = kwargs.get("separator", ",")
        if sep not in (",", ";"):
            sep = ","

        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        headers = ["Ordem", "Nome", "X", "Y", "Distância", "Ângulo", "Azimute", "Rumo"]

        with open(output_path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=sep)
            writer.writerow(headers)

            for index, row in enumerate(calculation_rows):
                seq = index + 1
                name = _row_value(row, ["Ponto", "point_name", "point"])
                
                # Coordenadas X e Y da tabela de coordenadas ou cálculo
                x_val = _row_value(row, ["Coordenada X", "x_corrigido", "x"])
                y_val = _row_value(row, ["Coordenada Y", "y_corrigido", "y"])
                
                try:
                    x = f"{float(x_val):.4f}"
                except (ValueError, TypeError):
                    x = ""
                    
                try:
                    y = f"{float(y_val):.4f}"
                except (ValueError, TypeError):
                    y = ""

                dist_val = _row_value(row, ["Distância (m)", "distancia"])
                try:
                    dist = f"{float(dist_val):.4f}"
                except (ValueError, TypeError):
                    dist = ""

                ang_val = _row_value(row, ["Ângulo Interno Compensado", "angulo_compensado"])
                ang = _format_dms(ang_val)

                az_val = _row_value(row, ["Azimute", "azimute"])
                try:
                    az = _format_dms(float(az_val))
                except (ValueError, TypeError):
                    az = _format_dms(az_val)

                rumo = _row_value(row, ["Rumo", "rumo"])

                writer.writerow([seq, name, x, y, dist, ang, az, rumo])


# Registrar exportador no registry global
ExporterRegistry.register(
    format_id="CSV",
    display_name="CSV",
    file_filter="Arquivos CSV (*.csv)",
    default_ext="csv",
    default_name="relatorio.csv",
    icon_name="SP_FileIcon",
    exporter_class=CSVExporter,
)
