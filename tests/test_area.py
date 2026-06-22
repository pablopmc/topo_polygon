import pytest

from core.calculations.area import gauss_area


class Ponto:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def test_gauss_area_triangulo():
    pontos = [(0.0, 0.0), (10.0, 0.0), (0.0, 5.0)]
    assert gauss_area(pontos) == pytest.approx(25.0)


def test_gauss_area_retangulo():
    pontos = [(0.0, 0.0), (10.0, 0.0), (10.0, 5.0), (0.0, 5.0)]
    assert gauss_area(pontos) == pytest.approx(50.0)


def test_gauss_area_poligono_nao_fechado():
    pontos = [(0.0, 0.0), (10.0, 0.0), (5.0, 5.0)]
    assert gauss_area(pontos) == pytest.approx(25.0)


def test_gauss_area_com_objetos():
    pontos = [Ponto(0.0, 0.0), Ponto(4.0, 0.0), Ponto(4.0, 3.0)]
    assert gauss_area(pontos) == pytest.approx(6.0)


def test_gauss_area_com_menos_de_tres_pontos_levanta_erro():
    with pytest.raises(ValueError):
        gauss_area([(0.0, 0.0), (1.0, 1.0)])
