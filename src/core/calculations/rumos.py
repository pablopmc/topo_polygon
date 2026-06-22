from __future__ import annotations

from core.calculations.engine import cosseno_do_rumo as cosseno_azimute
from core.calculations.engine import normalizar_azimute, rumo_graus_quadrante, rumo_texto, seno_do_rumo as seno_azimute


def determinar_quadrante(azimute: float) -> str:
    """Retorna o quadrante do azimute."""
    return rumo_graus_quadrante(azimute)[1]


def azimute_para_rumo(azimute: float) -> str:
    """Retorna o rumo textual no formato legado."""
    return rumo_texto(azimute).replace("L", "E").replace("O", "W")