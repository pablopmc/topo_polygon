import math
import pytest

from core.calculations.rumos import (
    azimute_para_rumo,
    cosseno_azimute,
    determinar_quadrante,
    seno_azimute,
)


def test_determinar_quadrante_corretamente():
    assert determinar_quadrante(45.0) == "NE"
    assert determinar_quadrante(135.0) == "SE"
    assert determinar_quadrante(225.0) == "SW"
    assert determinar_quadrante(315.0) == "NW"
    assert determinar_quadrante(-45.0) == "NW"


def test_azimute_para_rumo_primeiro_quadrante():
    assert azimute_para_rumo(45.0) == 'N 45° 00\' 00.000" E'


def test_azimute_para_rumo_segundo_quadrante():
    assert azimute_para_rumo(135.0) == 'S 45° 00\' 00.000" E'


def test_azimute_para_rumo_terceiro_quadrante():
    assert azimute_para_rumo(225.0) == 'S 45° 00\' 00.000" W'


def test_azimute_para_rumo_quarto_quadrante():
    assert azimute_para_rumo(315.0) == 'N 45° 00\' 00.000" W'


def test_seno_e_cosseno_azimute():
    assert seno_azimute(0.0) == pytest.approx(0.0, abs=1e-12)
    assert cosseno_azimute(0.0) == pytest.approx(1.0, abs=1e-12)
    assert seno_azimute(90.0) == pytest.approx(1.0, abs=1e-12)
    assert cosseno_azimute(90.0) == pytest.approx(0.0, abs=1e-12)


def test_azimute_invalido_levanta_erro():
    with pytest.raises(ValueError):
        azimute_para_rumo(None)
    with pytest.raises(ValueError):
        determinar_quadrante("90")
    with pytest.raises(ValueError):
        seno_azimute(float("nan"))
    with pytest.raises(ValueError):
        cosseno_azimute(float("nan"))