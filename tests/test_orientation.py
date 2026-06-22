import pytest
from core.calculations.orientation import parse_azimute_input, TopographicOrientation
from core.calculations.engine import decimal_para_dms

def test_parse_azimute_decimal():
    assert parse_azimute_input("123.456") == pytest.approx(123.456)
    assert parse_azimute_input("123,456") == pytest.approx(123.456)
    assert parse_azimute_input(" 0 ") == pytest.approx(0.0)
    assert parse_azimute_input("360") == pytest.approx(360.0)

def test_parse_azimute_dms():
    # 123° 27' 36"
    assert parse_azimute_input("123 27 36") == pytest.approx(123.46)
    assert parse_azimute_input("123° 27' 36\"") == pytest.approx(123.46)
    assert parse_azimute_input(" 123d 27m 36s ") == pytest.approx(123.46)

def test_parse_azimute_invalid():
    with pytest.raises(ValueError):
        parse_azimute_input("")
    with pytest.raises(ValueError):
        parse_azimute_input("abc")
    with pytest.raises(ValueError):
        parse_azimute_input("-10")
    with pytest.raises(ValueError):
        parse_azimute_input("361")
    with pytest.raises(ValueError):
        # Invalid minutes
        parse_azimute_input("120 65 00")

def test_topographic_orientation_calculation():
    # Azimuth V1->V2 = 45°
    orientation = TopographicOrientation(45.0)
    assert orientation.azimute_inicial == 45.0

    # Compensated internal angles
    # For a triangle (sum = 180°), internal angles are 60°
    # V1 = 60°, V2 = 60°, V3 = 60°
    # Azimuth V1->V2 = 45°
    # Azimuth V2->V3 = Azimuth V1->V2 + 180° - V2 = 45° + 180° - 60° = 165°
    # Azimuth V3->V1 = 165° + 180° - 60° = 285°
    # Azimuth V1->V2 (rec) = 285° + 180° - 60° = 405° = 45°
    azimutes = orientation.calcular_azimutes_sucessivos([60.0, 60.0, 60.0])
    assert azimutes == pytest.approx([45.0, 165.0, 285.0, 45.0])
