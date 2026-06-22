import math

import pytest

from core.calculations.projections import delta_x, delta_y, erro_fechamento, precisao


def test_delta_x_calcula_corretamente():
    assert delta_x(100.0, 0.0) == pytest.approx(0.0, abs=1e-12)
    assert delta_x(100.0, 90.0) == pytest.approx(100.0, abs=1e-12)
    assert delta_x(100.0, 180.0) == pytest.approx(0.0, abs=1e-12)


def test_delta_y_calcula_corretamente():
    assert delta_y(100.0, 0.0) == pytest.approx(100.0, abs=1e-12)
    assert delta_y(100.0, 90.0) == pytest.approx(0.0, abs=1e-12)
    assert delta_y(100.0, 180.0) == pytest.approx(-100.0, abs=1e-12)


def test_delta_x_e_delta_y_com_entrada_invalida():
    with pytest.raises(ValueError):
        delta_x(-10.0, 45.0)
    with pytest.raises(ValueError):
        delta_y(-10.0, 45.0)
    with pytest.raises(ValueError):
        delta_x(10.0, "90")


def test_erro_fechamento_calcula_corretamente():
    dxs = [10.0, -10.0, 5.0, -5.0]
    dys = [0.0, 0.0, 2.0, -2.0]
    assert erro_fechamento(dxs, dys) == pytest.approx(0.0, abs=1e-12)

    dxs = [10.0, 5.0]
    dys = [5.0, -5.0]
    assert erro_fechamento(dxs, dys) == pytest.approx(math.sqrt(15.0**2 + 0.0**2), abs=1e-12)


def test_erro_fechamento_listas_diferentes_levanta_erro():
    with pytest.raises(ValueError):
        erro_fechamento([10.0], [5.0, -5.0])


def test_precisao_calcula_corretamente():
    assert precisao(0.5, 100.0) == pytest.approx(200.0, abs=1e-12)
    assert precisao(0.0, 100.0) == float("inf")


def test_precisao_entradas_invalidas():
    with pytest.raises(ValueError):
        precisao(-1.0, 100.0)
    with pytest.raises(ValueError):
        precisao(0.5, 0.0)