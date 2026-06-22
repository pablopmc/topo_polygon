from __future__ import annotations

from dataclasses import dataclass, field
from math import cos, isfinite, radians, sin, sqrt
import re
from typing import Iterable, Mapping, Sequence, Tuple

import pandas as pd


Point2D = Tuple[float, float]
DMS = Tuple[int, int, float]
AngleInput = float | int | str | DMS


def _ensure_finite(value: float, name: str) -> None:
    if not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise ValueError(f"{name} deve ser um número finito")


def _normalize_360(value: float) -> float:
    _ensure_finite(value, "Valor")
    result = float(value) % 360.0
    return result if result >= 0.0 else result + 360.0


def dms_para_graus(graus: int, minutos: int, segundos: float) -> float:
    """Converte GMS para graus decimais."""
    if not isinstance(graus, int):
        raise ValueError("Graus deve ser inteiro")
    if not isinstance(minutos, int) or not 0 <= minutos < 60:
        raise ValueError("Minutos deve estar entre 0 e 59")
    if not isinstance(segundos, (int, float)) or not 0 <= float(segundos) < 60:
        raise ValueError("Segundos deve estar entre 0 e 59,999...")

    sinal = -1 if graus < 0 else 1
    graus_abs = abs(graus)
    return sinal * (graus_abs + minutos / 60.0 + float(segundos) / 3600.0)


def texto_dms_para_graus(texto: str) -> float:
    """Converte um texto DMS para graus decimais."""
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("Texto de ângulo inválido")

    texto_limpo = texto.strip().upper()
    sinal = -1 if any(token in texto_limpo for token in ("S", "W", "O", "-")) else 1
    numeros = re.findall(r"-?\d+(?:[.,]\d+)?", texto_limpo)
    if len(numeros) < 3:
        raise ValueError("Texto DMS deve conter graus, minutos e segundos")

    graus = float(numeros[0].replace(",", "."))
    minutos = float(numeros[1].replace(",", "."))
    segundos = float(numeros[2].replace(",", "."))
    return sinal * (abs(graus) + minutos / 60.0 + segundos / 3600.0)


def decimal_para_dms(valor: float) -> DMS:
    """Converte graus decimais para GMS."""
    _ensure_finite(valor, "Valor")
    sinal = -1 if valor < 0 else 1
    total = abs(float(valor))
    graus = int(total)
    minutos = int((total - graus) * 60.0)
    segundos = round((total - graus - minutos / 60.0) * 3600.0, 8)

    if segundos >= 60.0:
        segundos -= 60.0
        minutos += 1
    if minutos >= 60:
        minutos -= 60
        graus += 1

    return graus * sinal, minutos, segundos


def _formatar_dms(valor: float) -> str:
    graus, minutos, segundos = decimal_para_dms(valor)
    sinal = "-" if graus < 0 else ""
    return f"{sinal}{abs(graus)}° {minutos:02d}' {segundos:06.3f}\""


def _coagir_angulo(valor: AngleInput) -> float:
    if isinstance(valor, tuple) and len(valor) == 3:
        return dms_para_graus(int(valor[0]), int(valor[1]), float(valor[2]))
    if isinstance(valor, str):
        return texto_dms_para_graus(valor)
    if isinstance(valor, (int, float)):
        _ensure_finite(float(valor), "Ângulo")
        return float(valor)
    raise ValueError("Ângulo inválido")


def soma_angular(angulos: Iterable[DMS]) -> DMS:
    """Soma ângulos em GMS."""
    total_decimal = sum(dms_para_graus(g, m, s) for g, m, s in angulos)
    return decimal_para_dms(total_decimal)


def compensar_angulos_iguais(lista_angulos: Sequence[AngleInput]) -> list[float]:
    """Compensa os ângulos distribuindo igualmente o erro angular."""
    angulos = [_coagir_angulo(valor) for valor in lista_angulos]
    if len(angulos) < 3:
        raise ValueError("A poligonal deve ter ao menos três vértices")

    soma_teorica = (len(angulos) - 2) * 180.0
    soma_observada = sum(angulos)
    correcao = -(soma_observada - soma_teorica) / len(angulos)
    return [angulo + correcao for angulo in angulos]


def compensacao_angular(angulos: Sequence[DMS], esperado: float | None = None) -> tuple[list[DMS], list[DMS]]:
    """Compatibilidade com a API antiga de compensação angular."""
    angulos_decimais = [dms_para_graus(g, m, s) for g, m, s in angulos]
    if esperado is None:
        esperado = (len(angulos_decimais) - 2) * 180.0
    compensados = compensar_angulos_iguais(angulos_decimais)
    correcoes = [comp - obs for comp, obs in zip(compensados, angulos_decimais)]
    return [decimal_para_dms(valor) for valor in compensados], [decimal_para_dms(valor) for valor in correcoes]


def normalizar_azimute(azimute: float) -> float:
    """Normaliza um azimute para o intervalo [0, 360)."""
    return _normalize_360(azimute)


def azimutes_por_angulos_internos(azimute_inicial: float, angulos_compensados: Sequence[AngleInput]) -> list[float]:
    """Calcula a sequência de azimutes a partir dos ângulos internos compensados."""
    from core.calculations.orientation import TopographicOrientation
    orientation = TopographicOrientation(azimute_inicial)
    return orientation.calcular_azimutes_sucessivos(angulos_compensados)


def validar_azimute(azimute: float) -> bool:
    """Verifica se o azimute está no intervalo válido."""
    return isinstance(azimute, (int, float)) and isfinite(float(azimute)) and 0.0 <= float(azimute) < 360.0


def validar_resultados(azimutes: Iterable[float]) -> list[int]:
    """Retorna os índices de azimutes inválidos."""
    return [indice for indice, valor in enumerate(azimutes) if not validar_azimute(valor)]


def rumo_graus_quadrante(azimute: float) -> tuple[float, str]:
    """Retorna o ângulo reduzido do rumo e seu quadrante."""
    az = normalizar_azimute(azimute)
    if 0.0 <= az < 90.0:
        return az, "NE"
    if 90.0 <= az < 180.0:
        return 180.0 - az, "SE"
    if 180.0 <= az < 270.0:
        return az - 180.0, "SW"
    return 360.0 - az, "NW"


def rumo_texto(azimute: float) -> str:
    """Converte azimute para texto de rumo."""
    angulo, quadrante = rumo_graus_quadrante(azimute)
    graus, minutos, segundos = decimal_para_dms(angulo)
    norte_sul = "N" if quadrante in ("NE", "NW") else "S"
    leste_oeste = "L" if quadrante in ("NE", "SE") else "O"
    return f"{norte_sul} {abs(graus)}° {minutos:02d}' {segundos:06.3f}\" {leste_oeste}"


def seno_do_rumo(azimute: float) -> float:
    """Calcula o seno do rumo do azimute."""
    angulo, _ = rumo_graus_quadrante(azimute)
    return sin(radians(angulo))


def cosseno_do_rumo(azimute: float) -> float:
    """Calcula o cosseno do rumo do azimute."""
    angulo, _ = rumo_graus_quadrante(azimute)
    return cos(radians(angulo))


@dataclass(frozen=True)
class ProjectionResult:
    """Resultado detalhado de uma projeção por lado."""

    rumo_angulo: float
    quadrante: str
    rumo: str
    seno: float
    cosseno: float
    proj_e: float
    proj_o: float
    proj_n: float
    proj_s: float
    proj_x: float
    proj_y: float


def projecao_x_assinada(distancia: float, azimute: float) -> float:
    """Calcula a projeção assinada em X."""
    _ensure_finite(distancia, "Distância")
    if distancia < 0:
        raise ValueError("Distância deve ser não negativa")
    return float(distancia) * sin(radians(normalizar_azimute(azimute)))


def projecao_y_assinada(distancia: float, azimute: float) -> float:
    """Calcula a projeção assinada em Y."""
    _ensure_finite(distancia, "Distância")
    if distancia < 0:
        raise ValueError("Distância deve ser não negativa")
    return float(distancia) * cos(radians(normalizar_azimute(azimute)))


def projecoes(distancia: float, azimute: float) -> ProjectionResult:
    """Calcula projeções quadranteadas e assinadas."""
    proj_x = projecao_x_assinada(distancia, azimute)
    proj_y = projecao_y_assinada(distancia, azimute)
    rumo_angulo, quadrante = rumo_graus_quadrante(azimute)
    return ProjectionResult(
        rumo_angulo=rumo_angulo,
        quadrante=quadrante,
        rumo=rumo_texto(azimute),
        seno=seno_do_rumo(azimute),
        cosseno=cosseno_do_rumo(azimute),
        proj_e=max(proj_x, 0.0),
        proj_o=max(-proj_x, 0.0),
        proj_n=max(proj_y, 0.0),
        proj_s=max(-proj_y, 0.0),
        proj_x=proj_x,
        proj_y=proj_y,
    )


def erro_fechamento_linear_x(lista_proj_x: Iterable[float]) -> float:
    """Soma as projeções em X."""
    return sum(float(valor) for valor in lista_proj_x)


def erro_fechamento_linear_y(lista_proj_y: Iterable[float]) -> float:
    """Soma as projeções em Y."""
    return sum(float(valor) for valor in lista_proj_y)


def correcao_bowditch_x(delta_x: float, distancia: float, perimetro: float) -> float:
    """Calcula a correção de Bowditch em X."""
    _ensure_finite(delta_x, "delta_x")
    _ensure_finite(distancia, "distância")
    _ensure_finite(perimetro, "perímetro")
    if perimetro <= 0:
        raise ValueError("Perímetro deve ser maior que zero")
    return -(float(delta_x) * float(distancia) / float(perimetro))


def correcao_bowditch_y(delta_y: float, distancia: float, perimetro: float) -> float:
    """Calcula a correção de Bowditch em Y."""
    _ensure_finite(delta_y, "delta_y")
    _ensure_finite(distancia, "distância")
    _ensure_finite(perimetro, "perímetro")
    if perimetro <= 0:
        raise ValueError("Perímetro deve ser maior que zero")
    return -(float(delta_y) * float(distancia) / float(perimetro))


def projecao_compensada_x(proj_x: float, cx: float) -> float:
    """Aplica a correção em X."""
    return float(proj_x) + float(cx)


def projecao_compensada_y(proj_y: float, cy: float) -> float:
    """Aplica a correção em Y."""
    return float(proj_y) + float(cy)


def coordenadas_acumuladas(
    proj_x_comp: Sequence[float],
    proj_y_comp: Sequence[float],
    x0: float = 0.0,
    y0: float = 0.0,
) -> list[Point2D]:
    """Calcula coordenadas acumuladas a partir de projeções compensadas."""
    if len(proj_x_comp) != len(proj_y_comp):
        raise ValueError("As listas de projeções devem ter o mesmo tamanho")
    _ensure_finite(x0, "x0")
    _ensure_finite(y0, "y0")

    coordenadas: list[Point2D] = []
    x_atual = float(x0)
    y_atual = float(y0)
    for dx, dy in zip(proj_x_comp, proj_y_comp):
        x_atual += float(dx)
        y_atual += float(dy)
        coordenadas.append((x_atual, y_atual))
    return coordenadas


def soma_x_duplas_areas(x_anterior: float, x_atual: float) -> float:
    """Soma as coordenadas X de uma faixa da área."""
    return float(x_anterior) + float(x_atual)


def soma_y_duplas_areas(y_anterior: float, y_atual: float) -> float:
    """Soma as coordenadas Y de uma faixa da área."""
    return float(y_anterior) + float(y_atual)


def dupla_area_por_faixa_x(soma_x: float, proj_y_comp: float) -> float:
    """Calcula a dupla área usando a componente Y."""
    return float(soma_x) * float(proj_y_comp)


def dupla_area_por_faixa_y(soma_y: float, proj_x_comp: float) -> float:
    """Calcula a dupla área usando a componente X."""
    return float(soma_y) * float(proj_x_comp)


def area_gauss(coords: Iterable[Point2D]) -> float:
    """Calcula a área pelo método de Gauss."""
    pontos: list[Point2D] = []
    for ponto in coords:
        if isinstance(ponto, tuple) and len(ponto) == 2:
            pontos.append((float(ponto[0]), float(ponto[1])))
            continue
        try:
            pontos.append((float(ponto.x), float(ponto.y)))
        except AttributeError as exc:
            raise ValueError("Cada ponto deve ser uma tupla (x, y) ou objeto com atributos x e y") from exc
    if len(pontos) < 3:
        raise ValueError("É necessário pelo menos três pontos para calcular a área")
    if len(pontos) > 1 and pontos[0] == pontos[-1]:
        pontos = pontos[:-1]

    area = 0.0
    for indice, (x1, y1) in enumerate(pontos):
        x2, y2 = pontos[(indice + 1) % len(pontos)]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def erro_fechamento_linear(coords: Iterable[Point2D]) -> float:
    """Calcula o erro linear de fechamento a partir de coordenadas."""
    pontos = [(float(x), float(y)) for x, y in coords]
    if len(pontos) < 2:
        return 0.0
    x0, y0 = pontos[0]
    xn, yn = pontos[-1]
    return sqrt((xn - x0) ** 2 + (yn - y0) ** 2)


def precisao_relativa(perimetro: float, erro_linear: float) -> float:
    """Calcula a precisão relativa como perímetro dividido pelo erro."""
    _ensure_finite(perimetro, "Perímetro")
    _ensure_finite(erro_linear, "Erro linear")
    if perimetro <= 0:
        raise ValueError("Perímetro deve ser maior que zero")
    if erro_linear == 0:
        return float("inf")
    return float(perimetro) / float(erro_linear)


@dataclass
class VertexData:
    """Dados de entrada de um vértice."""

    sequence: int
    point_name: str
    graus: int
    minutos: int
    segundos: float
    distancia: float
    observacao: str = ""

    @property
    def angulo_decimal(self) -> float:
        return dms_para_graus(self.graus, self.minutos, self.segundos)


@dataclass
class ResultadoCalculo:
    """Resultado completo do fechamento poligonal."""

    angulos_observados_dms: list[DMS] = field(default_factory=list)
    angulos_observados_decimais: list[float] = field(default_factory=list)
    angulos_compensados_dms: list[DMS] = field(default_factory=list)
    angulos_compensados_decimais: list[float] = field(default_factory=list)
    correcao_angular_dms: list[DMS] = field(default_factory=list)
    correcao_angular_decimal: list[float] = field(default_factory=list)
    soma_observada: float = 0.0
    soma_teorica: float = 0.0
    erro_angular: float = 0.0
    azimute_inicial: float = 0.0
    azimutes: list[float] = field(default_factory=list)
    azimutes_dms: list[DMS] = field(default_factory=list)
    azimute_fechamento: float = 0.0
    rumos: list[str] = field(default_factory=list)
    quadrantes: list[str] = field(default_factory=list)
    senos: list[float] = field(default_factory=list)
    cossenos: list[float] = field(default_factory=list)
    deltas_x: list[float] = field(default_factory=list)
    deltas_y: list[float] = field(default_factory=list)
    proj_e: list[float] = field(default_factory=list)
    proj_w: list[float] = field(default_factory=list)
    proj_n: list[float] = field(default_factory=list)
    proj_s: list[float] = field(default_factory=list)
    cx: list[float] = field(default_factory=list)
    cy: list[float] = field(default_factory=list)
    cx_calculo: list[float] = field(default_factory=list)
    cy_calculo: list[float] = field(default_factory=list)
    proj_x_corrigida: list[float] = field(default_factory=list)
    proj_y_corrigida: list[float] = field(default_factory=list)
    coordenadas: list[Point2D] = field(default_factory=list)
    coordenadas_corrigidas: list[Point2D] = field(default_factory=list)
    soma_x: list[float] = field(default_factory=list)
    soma_y: list[float] = field(default_factory=list)
    dupla_area_plus: list[float] = field(default_factory=list)
    dupla_area_minus: list[float] = field(default_factory=list)
    dupla_x_y_plus: list[float] = field(default_factory=list)
    dupla_x_y_minus: list[float] = field(default_factory=list)
    dupla_y_x_plus: list[float] = field(default_factory=list)
    dupla_y_x_minus: list[float] = field(default_factory=list)
    area: float = 0.0
    perimetro: float = 0.0
    delta_x_total: float = 0.0
    delta_y_total: float = 0.0
    erro_linear: float = 0.0
    precisao: float | None = None
    tabela_final: pd.DataFrame = field(default_factory=lambda: pd.DataFrame())


def _extrair_vertices(vertices: Sequence[VertexData | Mapping[str, object]]) -> list[VertexData]:
    saida: list[VertexData] = []
    for indice, vertice in enumerate(vertices, start=1):
        if isinstance(vertice, VertexData):
            saida.append(vertice)
            continue
        if isinstance(vertice, Mapping):
            saida.append(
                VertexData(
                    sequence=int(vertice.get("sequence", indice)),
                    point_name=str(vertice.get("point_name", vertice.get("ponto", ""))),
                    graus=int(vertice.get("graus", 0)),
                    minutos=int(vertice.get("minutos", 0)),
                    segundos=float(vertice.get("segundos", 0.0)),
                    distancia=float(vertice.get("distancia", 0.0)),
                    observacao=str(vertice.get("observacao", "")),
                )
            )
            continue

        attrs = {nome: getattr(vertice, nome, None) for nome in ("sequence", "point_name", "graus", "minutos", "segundos", "distancia", "observacao")}
        if attrs["point_name"] is None:
            raise ValueError("Formato de vértice inválido")
        saida.append(
            VertexData(
                sequence=int(attrs["sequence"] or indice),
                point_name=str(attrs["point_name"]),
                graus=int(attrs["graus"] or 0),
                minutos=int(attrs["minutos"] or 0),
                segundos=float(attrs["segundos"] or 0.0),
                distancia=float(attrs["distancia"] or 0.0),
                observacao=str(attrs["observacao"] or ""),
            )
        )
    return saida


class FechamentoPoligonal:
    """Motor completo de fechamento poligonal planimétrico."""

    def __init__(self, azimute_inicial: float | None = None, coordenada_inicial: Point2D = (0.0, 0.0)) -> None:
        if azimute_inicial is None:
            raise ValueError("O azimute inicial é obrigatório para orientar o polígono.")
        self.azimute_inicial = normalizar_azimute(azimute_inicial)
        self.coordenada_inicial = (float(coordenada_inicial[0]), float(coordenada_inicial[1]))

    def calcular(
        self,
        vertices: Sequence[VertexData | Mapping[str, object]],
        aplicar_compensacao: bool = True,
    ) -> ResultadoCalculo:
        """Executa o fechamento angular, linear, compensação e área."""
        dados = _extrair_vertices(vertices)
        if len(dados) < 3:
            raise ValueError("A poligonal deve ter ao menos três vértices")

        resultado = ResultadoCalculo()
        resultado.azimute_inicial = self.azimute_inicial
        resultado.angulos_observados_dms = [(v.graus, v.minutos, v.segundos) for v in dados]
        resultado.angulos_observados_decimais = [v.angulo_decimal for v in dados]
        resultado.soma_observada = sum(resultado.angulos_observados_decimais)
        resultado.soma_teorica = (len(dados) - 2) * 180.0
        resultado.erro_angular = resultado.soma_observada - resultado.soma_teorica

        resultado.angulos_compensados_decimais = compensar_angulos_iguais(resultado.angulos_observados_decimais)
        resultado.angulos_compensados_dms = [decimal_para_dms(valor) for valor in resultado.angulos_compensados_decimais]
        resultado.correcao_angular_decimal = [comp - obs for comp, obs in zip(resultado.angulos_compensados_decimais, resultado.angulos_observados_decimais)]
        resultado.correcao_angular_dms = [decimal_para_dms(valor) for valor in resultado.correcao_angular_decimal]

        # Rotaciona os ângulos compensados para alinhar com os vértices na propagação dos azimutes
        angulos_propagacao = resultado.angulos_compensados_decimais[1:] + [resultado.angulos_compensados_decimais[0]]
        azimutes_seq = azimutes_por_angulos_internos(self.azimute_inicial, angulos_propagacao)
        resultado.azimutes = azimutes_seq[:-1]
        resultado.azimute_fechamento = azimutes_seq[-1]
        resultado.azimutes_dms = [decimal_para_dms(valor) for valor in resultado.azimutes]

        projeções = [projecoes(v.distancia, az) for v, az in zip(dados, resultado.azimutes)]
        resultado.rumos = [item.rumo for item in projeções]
        resultado.quadrantes = [item.quadrante for item in projeções]
        resultado.senos = [item.seno for item in projeções]
        resultado.cossenos = [item.cosseno for item in projeções]
        resultado.deltas_x = [item.proj_x for item in projeções]
        resultado.deltas_y = [item.proj_y for item in projeções]
        resultado.proj_e = [item.proj_e for item in projeções]
        resultado.proj_w = [item.proj_o for item in projeções]
        resultado.proj_n = [item.proj_n for item in projeções]
        resultado.proj_s = [item.proj_s for item in projeções]

        resultado.delta_x_total = erro_fechamento_linear_x(resultado.deltas_x)
        resultado.delta_y_total = erro_fechamento_linear_y(resultado.deltas_y)
        resultado.erro_linear = sqrt(resultado.delta_x_total**2 + resultado.delta_y_total**2)
        resultado.perimetro = sum(v.distancia for v in dados)

        if aplicar_compensacao and resultado.perimetro > 0:
            resultado.cx = [correcao_bowditch_x(resultado.delta_x_total, v.distancia, resultado.perimetro) for v in dados]
            resultado.cy = [correcao_bowditch_y(resultado.delta_y_total, v.distancia, resultado.perimetro) for v in dados]
        else:
            resultado.cx = [0.0] * len(dados)
            resultado.cy = [0.0] * len(dados)

        resultado.cx_calculo = list(resultado.cx)
        resultado.cy_calculo = list(resultado.cy)
        resultado.proj_x_corrigida = [projecao_compensada_x(dx, cx) for dx, cx in zip(resultado.deltas_x, resultado.cx)]
        resultado.proj_y_corrigida = [projecao_compensada_y(dy, cy) for dy, cy in zip(resultado.deltas_y, resultado.cy)]

        resultado.coordenadas = coordenadas_acumuladas(
            resultado.proj_x_corrigida,
            resultado.proj_y_corrigida,
            x0=self.coordenada_inicial[0],
            y0=self.coordenada_inicial[1],
        )

        # fecha a poligonal para área e verificação final
        coordenadas_fechadas = [self.coordenada_inicial, *resultado.coordenadas, self.coordenada_inicial]
        resultado.coordenadas_corrigidas = list(resultado.coordenadas)

        resultado.soma_x = []
        resultado.soma_y = []
        resultado.dupla_area_plus = []
        resultado.dupla_area_minus = []
        resultado.dupla_x_y_plus = []
        resultado.dupla_x_y_minus = []
        resultado.dupla_y_x_plus = []
        resultado.dupla_y_x_minus = []
        for indice, (x_atual, y_atual) in enumerate(resultado.coordenadas_corrigidas):
            x_prev, y_prev = coordenadas_fechadas[indice]
            resultado.soma_x.append(soma_x_duplas_areas(x_prev, x_atual))
            resultado.soma_y.append(soma_y_duplas_areas(y_prev, y_atual))
            
            # X.y calculations (Duplas Areas X)
            val_x_y = dupla_area_por_faixa_x(resultado.soma_x[-1], resultado.proj_y_corrigida[indice])
            resultado.dupla_area_plus.append(val_x_y)
            resultado.dupla_x_y_plus.append(val_x_y if val_x_y >= 0.0 else 0.0)
            resultado.dupla_x_y_minus.append(val_x_y if val_x_y < 0.0 else 0.0)
            
            # Y.x calculations (Duplas Areas Y)
            val_y_x = dupla_area_por_faixa_y(resultado.soma_y[-1], resultado.proj_x_corrigida[indice])
            resultado.dupla_area_minus.append(val_y_x)
            resultado.dupla_y_x_plus.append(val_y_x if val_y_x >= 0.0 else 0.0)
            resultado.dupla_y_x_minus.append(val_y_x if val_y_x < 0.0 else 0.0)

        resultado.area = area_gauss(coordenadas_fechadas)
        resultado.precisao = precisao_relativa(resultado.perimetro, resultado.erro_linear)
        resultado.tabela_final = self._montar_tabela_final(dados, resultado)
        return resultado

    def _montar_tabela_final(self, vertices: Sequence[VertexData], resultado: ResultadoCalculo) -> pd.DataFrame:
        linhas: list[dict[str, object]] = []
        for indice, vertice in enumerate(vertices):
            x, y = resultado.coordenadas[indice]
            linha = {
                "Ponto": vertice.point_name,
                "Ângulo Interno Lido": _formatar_dms(resultado.angulos_observados_decimais[indice]),
                "Ângulo Interno Decimal(°) Lido": resultado.angulos_observados_decimais[indice],
                "Ângulo Interno Compensado": _formatar_dms(resultado.angulos_compensados_decimais[indice]),
                "Azimute": resultado.azimutes[indice],
                "Rumo": resultado.rumos[indice],
                "Quadrante": resultado.quadrantes[indice],
                "Seno do Rumo": resultado.senos[indice],
                "Cosseno do Rumo": resultado.cossenos[indice],
                "Distância (m)": vertice.distancia,
                "Estação": vertice.sequence,
                "Projeção E (+)": resultado.proj_e[indice],
                "Projeção O (-)": resultado.proj_w[indice],
                "Projeção N (+)": resultado.proj_n[indice],
                "Projeção S (-)": resultado.proj_s[indice],
                "Correção em X (Cx)": resultado.cx[indice],
                "Correção em Y (Cy)": resultado.cy[indice],
                "Cálculo Cx": resultado.cx_calculo[indice],
                "Cálculo Cy": resultado.cy_calculo[indice],
                "Projeção Compensada X (Leste/Oeste)": resultado.proj_x_corrigida[indice],
                "Projeção Compensada Y (Norte/Sul)": resultado.proj_y_corrigida[indice],
                "Coordenada X": x,
                "Coordenada Y": y,
                "Soma X": resultado.soma_x[indice],
                "Soma Y": resultado.soma_y[indice],
                "Duplas Áreas X (+)": resultado.dupla_x_y_plus[indice],
                "Duplas Áreas X (-)": resultado.dupla_x_y_minus[indice],
                "Duplas Áreas Y (+)": resultado.dupla_y_x_plus[indice],
                "Duplas Áreas Y (-)": resultado.dupla_y_x_minus[indice],
                "Duplas Áreas (+)": resultado.dupla_area_plus[indice],
                "Duplas Áreas (-)": resultado.dupla_area_minus[indice],
                "Área final": resultado.area,
            }
            linhas.append(linha)
        return pd.DataFrame(linhas)


class CalculationEngine(FechamentoPoligonal):
    """Compatibilidade com o nome antigo da engine."""
