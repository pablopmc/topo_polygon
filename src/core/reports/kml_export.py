from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence
import xml.etree.ElementTree as ET

from core.reports.exporter_registry import BaseExporter, ExporterRegistry
from core.reports.pdf_report import _row_value


class KMLExporter(BaseExporter):
    """Exportador para formato KML de poligonal topográfica e seus vértices"""

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

        nome_projeto = project.get("name") or project.get("project_name") or "PROJETO"
        desc_projeto = project.get("survey_description") or project.get("description") or ""

        # KML Header e Styles
        kml_content = []
        kml_content.append('<?xml version="1.0" encoding="UTF-8"?>')
        kml_content.append('<kml xmlns="http://www.opengis.net/kml/2.2">')
        kml_content.append('  <Document>')
        kml_content.append(f'    <name>{self._escape_xml(nome_projeto)}</name>')
        kml_content.append(f'    <description>Projeto: {self._escape_xml(nome_projeto)}\nDescrição: {self._escape_xml(desc_projeto)}\nÁrea: {area:.4f} m²\nPerímetro: {perimeter:.4f} m</description>')
        
        # Styles
        # 1. Estilo do Vértice (Vermelho)
        kml_content.append('    <Style id="vertexStyle">')
        kml_content.append('      <IconStyle>')
        kml_content.append('        <color>ff0000ff</color>')  # Vermelho (AABBGGRR)
        kml_content.append('        <scale>1.0</scale>')
        kml_content.append('        <Icon>')
        kml_content.append('          <href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href>')
        kml_content.append('        </Icon>')
        kml_content.append('      </IconStyle>')
        kml_content.append('      <LabelStyle>')
        kml_content.append('        <scale>0.85</scale>')
        kml_content.append('      </LabelStyle>')
        kml_content.append('    </Style>')
        
        # 2. Estilo do Polígono (Preenchimento azul semi-transparente, borda azul)
        kml_content.append('    <Style id="polygonStyle">')
        kml_content.append('      <LineStyle>')
        kml_content.append('        <color>ffff9900</color>')  # Borda azul (AABBGGRR)
        kml_content.append('        <width>3</width>')
        kml_content.append('      </LineStyle>')
        kml_content.append('      <PolyStyle>')
        kml_content.append('        <color>4dff9900</color>')  # Preenchimento azul transparente
        kml_content.append('        <fill>1</fill>')
        kml_content.append('        <outline>1</outline>')
        kml_content.append('      </PolyStyle>')
        kml_content.append('    </Style>')

        # Pasta de Vértices
        kml_content.append('    <Folder>')
        kml_content.append('      <name>Vértices</name>')
        
        for index, row in enumerate(calculation_rows):
            name = _row_value(row, ["Ponto", "point_name", "point"])
            x_val = _row_value(row, ["Coordenada X", "x_corrigido", "x"])
            y_val = _row_value(row, ["Coordenada Y", "y_corrigido", "y"])
            dist_val = _row_value(row, ["Distância (m)", "distancia"])
            obs = _row_value(row, ["Observação", "observacao", "notes"])

            try:
                x = float(x_val)
                y = float(y_val)
            except (ValueError, TypeError):
                continue

            kml_content.append('      <Placemark>')
            kml_content.append(f'        <name>{self._escape_xml(name)}</name>')
            kml_content.append('        <styleUrl>#vertexStyle</styleUrl>')
            
            desc = f"Vértice: {name}\nSequência: {index+1}\nCoordenadas: ({x:.4f}, {y:.4f})"
            if dist_val:
                desc += f"\nDistância para o próximo: {dist_val} m"
            if obs:
                desc += f"\nObservação: {obs}"
                
            kml_content.append(f'        <description>{self._escape_xml(desc)}</description>')
            kml_content.append('        <Point>')
            kml_content.append(f'          <coordinates>{x},{y},0</coordinates>')
            kml_content.append('        </Point>')
            kml_content.append('      </Placemark>')
            
        kml_content.append('    </Folder>')

        # Pasta da Poligonal
        if len(sketch_points) >= 3:
            kml_content.append('    <Folder>')
            kml_content.append('      <name>Poligonal</name>')
            kml_content.append('      <Placemark>')
            kml_content.append('        <name>Polígono</name>')
            kml_content.append('        <styleUrl>#polygonStyle</styleUrl>')
            kml_content.append(f'        <description>Polígono da poligonal topográfica.\nÁrea: {area:.4f} m²\nPerímetro: {perimeter:.4f} m</description>')
            kml_content.append('        <Polygon>')
            kml_content.append('          <outerBoundaryIs>')
            kml_content.append('            <LinearRing>')
            kml_content.append('              <coordinates>')
            
            coords = list(sketch_points)
            if coords[0] != coords[-1]:
                coords.append(coords[0])
                
            for pt in coords:
                kml_content.append(f'                {pt[0]},{pt[1]},0')
                
            kml_content.append('              </coordinates>')
            kml_content.append('            </LinearRing>')
            kml_content.append('          </outerBoundaryIs>')
            kml_content.append('        </Polygon>')
            kml_content.append('      </Placemark>')
            kml_content.append('    </Folder>')

        kml_content.append('  </Document>')
        kml_content.append('</kml>')

        with open(output_path, mode="w", encoding="utf-8") as f:
            f.write("\n".join(kml_content))

    @staticmethod
    def _escape_xml(text: Any) -> str:
        if text is None:
            return ""
        val = str(text)
        return (
            val.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )


# Registrar exportador no registry global
ExporterRegistry.register(
    format_id="KML",
    display_name="KML",
    file_filter="Arquivos KML (*.kml)",
    default_ext="kml",
    default_name="poligonal.kml",
    icon_name="SP_DialogSaveButton",
    exporter_class=KMLExporter,
)
