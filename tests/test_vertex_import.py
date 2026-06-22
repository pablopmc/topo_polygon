from __future__ import annotations

from pathlib import Path

import pandas as pd

from controllers import ProjectController
from core.imports.vertex_import import read_vertices_from_file


def _sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Ponto": "P1", "G": 91, "M": 0, "S": 0.0, "Distância": 100.0, "Observação": "A"},
            {"Ponto": "P2", "G": 89, "M": 30, "S": 0.0, "Distância": 120.5, "Observação": "B"},
            {"Ponto": "P3", "G": 92, "M": 15, "S": 30.0, "Distância": 90.25, "Observação": "C"},
        ]
    )


def test_read_vertices_from_csv_and_excel(tmp_path: Path) -> None:
    dataframe = _sample_dataframe()

    csv_path = tmp_path / "vertices.csv"
    csv_semi_path = tmp_path / "vertices_semi.csv"
    xlsx_path = tmp_path / "vertices.xlsx"
    
    dataframe.to_csv(csv_path, index=False)
    dataframe.to_csv(csv_semi_path, index=False, sep=";")
    dataframe.to_excel(xlsx_path, index=False, sheet_name="Leituras")

    csv_vertices = read_vertices_from_file(csv_path)
    csv_semi_vertices = read_vertices_from_file(csv_semi_path)
    xlsx_vertices = read_vertices_from_file(xlsx_path)

    assert [v.point_name for v in csv_vertices] == ["P1", "P2", "P3"]
    assert [v.distancia for v in csv_vertices] == [100.0, 120.5, 90.25]
    
    assert [v.point_name for v in csv_semi_vertices] == ["P1", "P2", "P3"]
    assert [v.distancia for v in csv_semi_vertices] == [100.0, 120.5, 90.25]
    
    assert [v.point_name for v in xlsx_vertices] == ["P1", "P2", "P3"]
    assert xlsx_vertices[1].minutos == 30


def test_controller_importar_vertices_substitui_os_pontos(tmp_path: Path) -> None:
    dataframe = _sample_dataframe()
    csv_path = tmp_path / "vertices.csv"
    dataframe.to_csv(csv_path, index=False)

    controller = ProjectController()
    controller.novo_projeto(tmp_path / "projeto.topo", name="Projeto de teste")

    vertices = controller.importar_vertices(csv_path, substituir=True)

    assert len(vertices) == 3
    assert [v.sequence for v in vertices] == [1, 2, 3]
    assert [v.point_name for v in controller.current_vertices] == ["P1", "P2", "P3"]
    assert controller.current_db is not None
    assert len(controller.current_db.list_points(controller.current_project.id or 0)) == 3
