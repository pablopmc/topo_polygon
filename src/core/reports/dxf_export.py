from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence, Tuple

import ezdxf

Point2D = Tuple[float, float]


def _ensure_closed_polyline(points: Sequence[Point2D]) -> Sequence[Point2D]:
    if len(points) < 2:
        raise ValueError("São necessários pelo menos dois pontos para exportar DXF.")
    if points[0] != points[-1]:
        return tuple(points) + (points[0],)
    return tuple(points)


def _create_layers(doc: ezdxf.DXFDocument) -> None:
    doc.layers.new("POLIGONO", dxfattribs={"color": 5})
    doc.layers.new("PONTOS", dxfattribs={"color": 3})
    doc.layers.new("TEXTOS", dxfattribs={"color": 1})


def _build_point_labels(points: Sequence[Point2D], labels: Sequence[str] | None = None) -> Sequence[Tuple[float, float, str]]:
    if labels is None:
        labels = [str(i + 1) for i in range(len(points))]
    if len(labels) != len(points):
        raise ValueError("O número de rótulos deve ser igual ao número de pontos.")
    return [(x, y, label) for (x, y), label in zip(points, labels)]


def generate_dxf_report(
    filename: str | Path,
    points: Sequence[Point2D],
    area: float,
    perimeter: float,
    labels: Sequence[str] | None = None,
    text_height: float = 2.5,
) -> None:
    """
    Gera um arquivo DXF contendo polilinha, vértices, textos de identificação,
    e anotações de área e perímetro.
    """
    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = ezdxf.new(dxfversion="R2013")
    _create_layers(doc)
    msp = doc.modelspace()

    closed_points = _ensure_closed_polyline(points)

    # Polilinha principal
    msp.add_lwpolyline(
        closed_points,
        dxfattribs={"layer": "POLIGONO", "color": 5, "closed": True},
    )

    # Pontos e textos de identificação
    for x, y, label in _build_point_labels(points, labels):
        msp.add_point((x, y), dxfattribs={"layer": "PONTOS", "color": 3})
        text_entity = msp.add_text(
            label,
            dxfattribs={"layer": "TEXTOS", "height": text_height, "color": 1},
        )
        text_entity.dxf.insert = (x + text_height * 0.5, y + text_height * 0.5, 0.0)

    # Área e perímetro como textos de anotação
    min_x = min(x for x, _ in points)
    min_y = min(y for _, y in points)
    annotation_x = min_x
    annotation_y = min_y - text_height * 4

    area_text = msp.add_text(
        f"AREA = {area:.3f} m2",
        dxfattribs={"layer": "TEXTOS", "height": text_height, "color": 1},
    )
    area_text.dxf.insert = (annotation_x, annotation_y, 0.0)

    perimeter_text = msp.add_text(
        f"PERIMETRO = {perimeter:.3f} m",
        dxfattribs={"layer": "TEXTOS", "height": text_height, "color": 1},
    )
    perimeter_text.dxf.insert = (annotation_x, annotation_y - text_height * 1.5, 0.0)

    doc.saveas(str(output_path))


from core.reports.exporter_registry import BaseExporter, ExporterRegistry
from typing import Any, Mapping


class DXFExporter(BaseExporter):
    """Adaptador de exportação para formato DXF"""

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
        labels = [str(r.get("Ponto") or r.get("point_name") or "") for r in calculation_rows]
        generate_dxf_report(
            filename=filename,
            points=sketch_points,
            area=area,
            perimeter=perimeter,
            labels=labels,
        )


# Registrar exportador no registry global
ExporterRegistry.register(
    format_id="DXF",
    display_name="DXF",
    file_filter="Arquivos DXF (*.dxf)",
    default_ext="dxf",
    default_name="planta.dxf",
    icon_name="SP_FileDialogContentsView",
    exporter_class=DXFExporter,
)

