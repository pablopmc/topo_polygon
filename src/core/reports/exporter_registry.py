from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


class BaseExporter(ABC):
    """Classe base abstrata para todos os exportadores do TopoCalc"""

    @abstractmethod
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
        """Executa a exportação para o formato específico"""
        pass


class ExporterRegistry:
    """Registro global e dinâmico de todos os exportadores cadastrados (Factory Pattern)"""

    _exporters: dict[str, dict[str, Any]] = {}

    @classmethod
    def register(
        cls,
        format_id: str,
        display_name: str,
        file_filter: str,
        default_ext: str,
        default_name: str,
        icon_name: str,  # Nome amigável para associar a ícones do QStyle
        exporter_class: type[BaseExporter] | Callable[[], BaseExporter],
    ) -> None:
        """Cadastra um novo formato de exportação no registro"""
        cls._exporters[format_id.upper()] = {
            "format_id": format_id.upper(),
            "display_name": display_name,
            "file_filter": file_filter,
            "default_ext": default_ext,
            "default_name": default_name,
            "icon_name": icon_name,
            "exporter_class": exporter_class,
        }

    @classmethod
    def get_exporter(cls, format_id: str) -> BaseExporter:
        """Retorna uma instância do exportador correspondente ao format_id"""
        info = cls._exporters.get(format_id.upper())
        if not info:
            raise ValueError(f"Exportador para o formato '{format_id}' não está registrado.")
        return info["exporter_class"]()

    @classmethod
    def get_format_info(cls, format_id: str) -> dict[str, Any]:
        """Retorna as informações do formato registrado"""
        info = cls._exporters.get(format_id.upper())
        if not info:
            raise ValueError(f"Formato '{format_id}' não registrado.")
        return info

    @classmethod
    def list_formats(cls) -> list[dict[str, Any]]:
        """Retorna a lista de todos os formatos registrados ordenados alfabeticamente pelo nome de exibição"""
        return sorted(cls._exporters.values(), key=lambda x: x["display_name"].upper())
