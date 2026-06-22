from __future__ import annotations

from typing import Iterable

from core.calculations.engine import (
    correcao_bowditch_x,
    correcao_bowditch_y,
    erro_fechamento_linear_x,
    erro_fechamento_linear_y,
    projecao_compensada_x,
    projecao_compensada_y,
    projecao_x_assinada as delta_x,
    projecao_y_assinada as delta_y,
    precisao_relativa,
)


def erro_fechamento(dxs: Iterable[float], dys: Iterable[float]) -> float:
    """Mantém a assinatura antiga de erro linear de fechamento."""
    dx_list = list(dxs)
    dy_list = list(dys)
    if len(dx_list) != len(dy_list):
        raise ValueError("Listas de ΔX e ΔY devem ter o mesmo comprimento")
    return (erro_fechamento_linear_x(dx_list) ** 2 + erro_fechamento_linear_y(dy_list) ** 2) ** 0.5


def precisao(erro: float, perimetro: float) -> float:
    """Mantém a assinatura antiga de precisão."""
    if erro < 0:
        raise ValueError("Erro de fechamento não pode ser negativo")
    return precisao_relativa(perimetro, erro)
