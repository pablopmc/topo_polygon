from __future__ import annotations

from typing import Iterable, List, Tuple

from core.calculations.engine import correcao_bowditch_x, correcao_bowditch_y, erro_fechamento_linear_x, erro_fechamento_linear_y, projecao_compensada_x, projecao_compensada_y


def cx(deltas_x: Iterable[float]) -> float:
    """Retorna a soma das projeções em X."""
    return erro_fechamento_linear_x(deltas_x)


def cy(deltas_y: Iterable[float]) -> float:
    """Retorna a soma das projeções em Y."""
    return erro_fechamento_linear_y(deltas_y)


def aplicar_compensacao_bowditch(
    deltas_x: Iterable[float],
    deltas_y: Iterable[float],
    distancias: Iterable[float],
    perimetro: float,
) -> Tuple[List[float], List[float]]:
    """Aplica a compensação de Bowditch proporcional ao comprimento de cada lado."""
    deltas_x_list = list(deltas_x)
    deltas_y_list = list(deltas_y)
    distancias_list = list(distancias)
    if len(deltas_x_list) != len(deltas_y_list) or len(deltas_x_list) != len(distancias_list):
        raise ValueError("Listas deve ter o mesmo comprimento")

    soma_dx = erro_fechamento_linear_x(deltas_x_list)
    soma_dy = erro_fechamento_linear_y(deltas_y_list)
    return (
        [projecao_compensada_x(dx, correcao_bowditch_x(soma_dx, dist, perimetro)) for dx, dist in zip(deltas_x_list, distancias_list)],
        [projecao_compensada_y(dy, correcao_bowditch_y(soma_dy, dist, perimetro)) for dy, dist in zip(deltas_y_list, distancias_list)],
    )


def correcoes_bowditch(
    deltas_x: Iterable[float],
    deltas_y: Iterable[float],
    distancias: Iterable[float],
) -> Tuple[List[float], List[float]]:
    """Mantém a API antiga de correções de Bowditch."""
    dxs = list(deltas_x)
    dys = list(deltas_y)
    dist_list = list(distancias)
    if len(dxs) != len(dys) or len(dxs) != len(dist_list):
        raise ValueError("Listas deve ter o mesmo comprimento")
    perimetro = sum(dist_list)
    soma_dx = cx(dxs)
    soma_dy = cy(dys)
    return (
        [correcao_bowditch_x(soma_dx, dist, perimetro) for dist in dist_list],
        [correcao_bowditch_y(soma_dy, dist, perimetro) for dist in dist_list],
    )


def projecoes_compensadas(
    deltas_x: Iterable[float],
    deltas_y: Iterable[float],
    distancias: Iterable[float],
) -> Tuple[List[float], List[float]]:
    """Retorna as projeções compensadas por Bowditch."""
    dxs = list(deltas_x)
    dys = list(deltas_y)
    dist_list = list(distancias)
    if len(dxs) != len(dys) or len(dxs) != len(dist_list):
        raise ValueError("Listas deve ter o mesmo comprimento")
    perimetro = sum(dist_list)
    soma_dx = cx(dxs)
    soma_dy = cy(dys)
    return (
        [projecao_compensada_x(dx, correcao_bowditch_x(soma_dx, dist, perimetro)) for dx, dist in zip(dxs, dist_list)],
        [projecao_compensada_y(dy, correcao_bowditch_y(soma_dy, dist, perimetro)) for dy, dist in zip(dys, dist_list)],
    )


def calcular_erro_absoluto(deltas_x: Iterable[float], deltas_y: Iterable[float]) -> float:
    """Calcula o erro absoluto de fechamento linear."""
    soma_dx = erro_fechamento_linear_x(deltas_x)
    soma_dy = erro_fechamento_linear_y(deltas_y)
    return (soma_dx**2 + soma_dy**2) ** 0.5
