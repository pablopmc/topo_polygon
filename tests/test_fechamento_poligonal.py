import pytest

from core.calculations.engine import (
    FechamentoPoligonal,
    area_gauss,
    azimutes_por_angulos_internos,
    compensar_angulos_iguais,
    correcao_bowditch_x,
    dms_para_graus,
    projecao_x_assinada,
    projecao_y_assinada,
)


def test_dms_para_graus():
    assert dms_para_graus(30, 20, 10) == pytest.approx(30.33611111111111)


def test_compensar_angulos_iguais():
    angulos = [59.0, 59.0, 59.0]
    compensados = compensar_angulos_iguais(angulos)
    assert compensados == pytest.approx([60.0, 60.0, 60.0])


def test_azimutes_por_angulos_internos():
    azimutes = azimutes_por_angulos_internos(45.0, [60.0, 60.0, 60.0])
    assert azimutes[0] == pytest.approx(45.0)
    assert len(azimutes) == 4


def test_correcao_bowditch():
    assert correcao_bowditch_x(10.0, 50.0, 200.0) == pytest.approx(-2.5)


def test_area_gauss():
    assert area_gauss([(0.0, 0.0), (10.0, 0.0), (0.0, 5.0)]) == pytest.approx(25.0)


def test_fechamento_poligonal_completo():
    engine = FechamentoPoligonal(azimute_inicial=45.0)
    vertices = [
        {"sequence": 1, "point_name": "P1", "graus": 60, "minutos": 0, "segundos": 0.0, "distancia": 100.0},
        {"sequence": 2, "point_name": "P2", "graus": 60, "minutos": 0, "segundos": 0.0, "distancia": 100.0},
        {"sequence": 3, "point_name": "P3", "graus": 60, "minutos": 0, "segundos": 0.0, "distancia": 100.0},
    ]
    resultado = engine.calcular(vertices)
    assert len(resultado.azimutes) == 3
    assert len(resultado.coordenadas) == 3
    assert resultado.perimetro == pytest.approx(300.0)
    assert resultado.tabela_final.shape[0] == 3