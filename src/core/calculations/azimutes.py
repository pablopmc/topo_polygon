from __future__ import annotations

from typing import Iterable, List

from core.calculations.engine import azimutes_por_angulos_internos, normalizar_azimute, validar_azimute, validar_resultados


def calcular_azimutes_sucessivos(
    azimute_inicial: float,
    angulos: Iterable[float],
    tipo: str = "interno",
) -> List[float]:
    """Mantém a API antiga e mapeia para a nova rotina de azimutes."""
    if tipo not in {"interno", "deflexao"}:
        raise ValueError("Tipo deve ser 'interno' ou 'deflexao'")
    if tipo == "deflexao":
        resultado = []
        atual = normalizar_azimute(azimute_inicial)
        for angulo in angulos:
            atual = normalizar_azimute(atual + float(angulo))
            resultado.append(atual)
        return resultado
    return azimutes_por_angulos_internos(azimute_inicial, list(angulos))[1:]