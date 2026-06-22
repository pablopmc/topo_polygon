from __future__ import annotations
import re
from typing import Sequence
from core.calculations.engine import normalizar_azimute, _coagir_angulo, AngleInput

def parse_azimute_input(texto: str) -> float:
    """Valida e converte uma string de azimute (decimal ou GMS) para graus decimais."""
    texto_limpo = texto.strip().upper()
    if not texto_limpo:
        raise ValueError("O azimute inicial é obrigatório e não foi informado.")
    
    # Tenta converter como decimal diretamente
    try:
        # Suporta vírgula e ponto
        val = float(texto_limpo.replace(",", "."))
        if not (0.0 <= val <= 360.0):
            raise ValueError("O azimute deve estar no intervalo entre 0° e 360°.")
        return val
    except ValueError:
        pass

    # Tenta converter como DMS
    try:
        # Encontra todos os números no texto
        numeros = re.findall(r"-?\d+(?:[.,]\d+)?", texto_limpo)
        if len(numeros) < 3:
            raise ValueError("Formato inválido. Use graus decimais (ex: 123.45) ou GMS (ex: 123 27 00)")
        
        sinal = -1 if "-" in texto_limpo else 1
        graus = float(numeros[0].replace(",", "."))
        minutos = float(numeros[1].replace(",", "."))
        segundos = float(numeros[2].replace(",", "."))
        
        if minutos < 0 or minutos >= 60:
            raise ValueError("Minutos devem estar entre 0 e 59.")
        if segundos < 0 or segundos >= 60:
            raise ValueError("Segundos devem estar entre 0 e 59.999...")
        
        val = sinal * (abs(graus) + minutos / 60.0 + segundos / 3600.0)
        # normaliza para 0-360
        val = normalizar_azimute(val)
        return val
    except ValueError as e:
        raise ValueError(f"Azimute inicial inválido: {str(e)}") from e


class TopographicOrientation:
    """Classe responsável por gerenciar a orientação e consistência direcional do polígono."""
    
    def __init__(self, azimute_inicial: float) -> None:
        if azimute_inicial is None:
            raise ValueError("O azimute inicial é obrigatório.")
        self.azimute_inicial = normalizar_azimute(azimute_inicial)

    def calcular_azimutes_sucessivos(self, angulos_compensados: Sequence[AngleInput]) -> list[float]:
        """Calcula a sequência de azimutes a partir do azimute inicial e ângulos internos.
        Normaliza os azimutes resultantes e garante a consistência angular global.
        """
        atual = self.azimute_inicial
        sequencia = [atual]
        for angulo in angulos_compensados:
            angulo_decimal = _coagir_angulo(angulo)
            atual = normalizar_azimute(atual + 180.0 - angulo_decimal)
            sequencia.append(atual)
        return sequencia
