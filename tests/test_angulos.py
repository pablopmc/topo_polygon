import pytest

from core.calculations.angulos import (
    compensacao_angular,
    decimal_para_dms,
    dms_para_decimal,
    soma_angular,
)


def test_dms_para_decimal_positivo():
    assert dms_para_decimal(30, 20, 10) == pytest.approx(30.33611111111111, rel=1e-9)


def test_dms_para_decimal_negativo():
    assert dms_para_decimal(-10, 15, 30) == pytest.approx(-10.258333333333333, rel=1e-9)


def test_decimal_para_dms_positivo():
    graus, minutos, segundos = decimal_para_dms(30.33611111111111)
    assert graus == 30
    assert minutos == 20
    assert segundos == pytest.approx(10.0, abs=1e-6)


def test_decimal_para_dms_negativo():
    graus, minutos, segundos = decimal_para_dms(-10.258333333333333)
    assert graus == -10
    assert minutos == 15
    assert segundos == pytest.approx(30.0, abs=1e-6)


def test_soma_angular():
    angulos = [(10, 0, 0.0), (20, 30, 0.0)]
    resultado = soma_angular(angulos)
    assert resultado == (30, 30, 0.0)


def test_compensacao_angular_sem_erro():
    angulos = [(60, 0, 0.0), (60, 0, 0.0), (60, 0, 0.0)]
    ajustados, correcao = compensacao_angular(angulos)
    assert ajustados == [(60, 0, 0.0), (60, 0, 0.0), (60, 0, 0.0)]
    assert correcao == [(0, 0, 0.0), (0, 0, 0.0), (0, 0, 0.0)]


def test_compensacao_angular_com_erro_uniforme():
    angulos = [(59, 0, 0.0), (59, 0, 0.0), (59, 0, 0.0)]
    ajustados, correcao = compensacao_angular(angulos)
    assert ajustados == [(60, 0, 0.0), (60, 0, 0.0), (60, 0, 0.0)]
    assert correcao == [(1, 0, 0.0), (1, 0, 0.0), (1, 0, 0.0)]


def test_compensacao_angular_esperado_personalizado():
    angulos = [(45, 0, 0.0), (45, 0, 0.0), (45, 0, 0.0), (45, 0, 0.0)]
    ajustados, correcao = compensacao_angular(angulos, esperado=360.0)
    assert ajustados == [(90, 0, 0.0), (90, 0, 0.0), (90, 0, 0.0), (90, 0, 0.0)]
    assert correcao == [(45, 0, 0.0), (45, 0, 0.0), (45, 0, 0.0), (45, 0, 0.0)]


def test_compensacao_angular_lista_vazia():
    with pytest.raises(ValueError):
        compensacao_angular([], esperado=180.0)
