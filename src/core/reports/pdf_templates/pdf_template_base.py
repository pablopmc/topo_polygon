from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence


class PDFTemplate(ABC):
    """Classe base abstrata para todos os templates de relatório PDF (Strategy Pattern)"""

    @abstractmethod
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
        """Método principal para gerar o relatório PDF"""
        pass

    @abstractmethod
    def build_cover(self, story: list[Any], project_meta: Mapping[str, Any]) -> None:
        """Constrói a capa ou cabeçalho inicial do relatório"""
        pass

    @abstractmethod
    def build_tables(
        self,
        story: list[Any],
        calculation_rows: Sequence[Mapping[str, Any]],
        coordinates_rows: Sequence[Mapping[str, Any]],
        selected_fields: dict[str, bool],
        doc_width: float,
    ) -> None:
        """Constrói as tabelas de cálculos e coordenadas"""
        pass

    @abstractmethod
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
        """Constrói o resumo de fechamento e painel de verificações"""
        pass

    @abstractmethod
    def build_footer(self, canvas: Any, doc: Any, project_meta: Mapping[str, Any], generated_at: datetime) -> None:
        """Desenha o rodapé ou decorações da página no canvas"""
        pass
