import pytest

from core.calculations.bowditch import (
    correcoes_bowditch,
    cx,
    cy,
    projecoes_compensadas,
)


def test_cx_cy_calcula_fechamento():
    assert cx([1.0, -1.0, 0.5, -0.5]) == pytest.approx(0.0)
    assert cy([2.0, -1.0, -1.0]) == pytest.approx(0.0)


def test_correcoes_bowditch():
    dxs = [10.0, -5.0, -5.0]
    dys = [0.0, 5.0, -5.0]
    distancias = [100.0, 100.0, 100.0]

    correcoes_x, correcoes_y = correcoes_bowditch(dxs, dys, distancias)

    assert len(correcoes_x) == 3
    assert len(correcoes_y) == 3
    assert correcoes_x == pytest.approx([0.0, 0.0, 0.0])
    assert correcoes_y == pytest.approx([0.0, 0.0, 0.0])


def test_projecoes_compensadas_aplica_correcao():
    dxs = [10.0, -9.0, -1.0]
    dys = [0.0, 4.0, -4.0]
    distancias = [50.0, 50.0, 50.0]

    dxs_comp, dys_comp = projecoes_compensadas(dxs, dys, distancias)

    assert dxs_comp == pytest.approx([10.0, -9.0, -1.0])
    assert dys_comp == pytest.approx([0.0, 4.0, -4.0])


def test_correcoes_bowditch_invalido_tamanhos():
    with pytest.raises(ValueError):
        correcoes_bowditch([10.0, -5.0], [0.0], [100.0, 50.0])

    with pytest.raises(ValueError):
        projecoes_compensadas([10.0], [5.0], [0.0])


def test_correcoes_bowditch_valores_invalidos():
    with pytest.raises(ValueError):
        correcoes_bowditch([10.0, float("nan")], [0.0, 0.0], [10.0, 10.0])
