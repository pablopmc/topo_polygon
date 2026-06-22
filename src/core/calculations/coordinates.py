from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

from core.calculations.engine import coordenadas_acumuladas, erro_fechamento_linear, precisao_relativa


Point2D = Tuple[float, float]


def calcular_coordenadas(
    coordinate_inicial: Point2D,
    deltas_x: Iterable[float],
    deltas_y: Iterable[float],
) -> List[Point2D]:
    """Mantém a API antiga e delega o acumulado para a nova engine."""
    return coordenadas_acumuladas(list(deltas_x), list(deltas_y), x0=coordinate_inicial[0], y0=coordinate_inicial[1])


def calcular_perimetro(pontos: Sequence[Point2D]) -> float:
    """Calcula o perímetro como soma dos segmentos sucessivos."""
    if len(pontos) < 2:
        raise ValueError("São necessários pelo menos dois pontos")
    perimetro = 0.0
    for indice in range(len(pontos) - 1):
        x1, y1 = pontos[indice]
        x2, y2 = pontos[indice + 1]
        perimetro += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    return perimetro


def calcular_distancia(ponto1: Point2D, ponto2: Point2D) -> float:
    """Calcula a distância entre dois pontos."""
    x1, y1 = ponto1
    x2, y2 = ponto2
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
