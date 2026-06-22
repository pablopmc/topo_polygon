import pytest

from core.calculations.azimutes import (
    calcular_azimutes_sucessivos,
    normalizar_azimute,
    validar_azimute,
    validar_resultados,
)


def test_normalizar_azimute_simples():
    assert normalizar_azimute(370.0) == pytest.approx(10.0)
    assert normalizar_azimute(-30.0) == pytest.approx(330.0)
    assert normalizar_azimute(0.0) == pytest.approx(0.0)


def test_normalizar_azimute_infinito_levanta_erro():
    with pytest.raises(ValueError):
        normalizar_azimute(float("inf"))


def test_calcular_azimutes_sucessivos_interno():
    azimutes = calcular_azimutes_sucessivos(45.0, [90.0, 90.0, 90.0])
    assert azimutes == [135.0, 225.0, 315.0]


def test_calcular_azimutes_sucessivos_deflexao():
    azimutes = calcular_azimutes_sucessivos(0.0, [45.0, -45.0, 90.0], tipo="deflexao")
    assert azimutes == [45.0, 0.0, 90.0]


def test_calcular_azimutes_sucessivos_tipo_invalido():
    with pytest.raises(ValueError):
        calcular_azimutes_sucessivos(0.0, [10.0], tipo="invalido")


def test_validar_azimute():
    assert validar_azimute(0.0)
    assert validar_azimute(359.9999)
    assert not validar_azimute(360.0)
    assert not validar_azimute(float("nan"))


def test_validar_resultados():
    indices_invalidos = validar_resultados([10.0, 360.0, -5.0, 180.0])
    assert indices_invalidos == [1, 2]