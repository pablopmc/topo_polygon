from __future__ import annotations

from typing import Iterable, Sequence, Tuple

from core.calculations.engine import area_gauss


Point2D = Tuple[float, float]


def gauss_area(points: Iterable[Point2D]) -> float:
    """Mantém a API antiga e delega o cálculo para a nova engine."""
    return area_gauss(points)