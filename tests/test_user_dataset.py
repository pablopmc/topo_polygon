import pytest
from core.calculations.engine import FechamentoPoligonal

def test_user_dataset_calculations():
    # User's dataset from the Excel/PDF comparison
    vertices = [
        {"sequence": 1, "point_name": "P1", "graus": 69, "minutos": 3, "segundos": 49.0, "distancia": 265.0},
        {"sequence": 2, "point_name": "P2", "graus": 110, "minutos": 35, "segundos": 28.0, "distancia": 123.45},
        {"sequence": 3, "point_name": "P3", "graus": 256, "minutos": 9, "segundos": 30.0, "distancia": 234.76},
        {"sequence": 4, "point_name": "P4", "graus": 94, "minutos": 56, "segundos": 59.0, "distancia": 128.19},
        {"sequence": 5, "point_name": "P5", "graus": 106, "minutos": 5, "segundos": 27.0, "distancia": 326.21},
        {"sequence": 6, "point_name": "P6", "graus": 128, "minutos": 23, "segundos": 37.0, "distancia": 183.19},
        {"sequence": 7, "point_name": "P7", "graus": 134, "minutos": 45, "segundos": 10.0, "distancia": 312.0},
    ]

    # Azimuth V1->V2 is 104° 01' 37"
    # in decimal degrees: 104.02694444444444
    az_inicial = 104.02694444444444
    engine = FechamentoPoligonal(azimute_inicial=az_inicial)
    resultado = engine.calcular(vertices)

    # Verify propagated azimuths match Excel values
    # Excel azimuths:
    # P1: 104° 01' 37" (104.02694)
    # P2: 173° 26' 09" (173.43583)
    # P3: 97° 16' 39" (97.27750)
    # P4: 182° 19' 40" (182.32778)
    # P5: 256° 14' 13" (256.23694)
    # P6: 307° 50' 36" (307.84333)
    # P7: 353° 05' 26" (353.09056)
    expected_azimuths = [
        104.02694444444444, # P1
        173.43583333333333, # P2
        97.2775,            # P3
        182.32777777777778, # P4
        256.2369444444444,  # P5
        307.8433333333333,  # P6
        353.09055555555555, # P7
    ]

    # Note: Excel calculated azimuths using observed angles instead of compensated ones.
    # If the engine correctly distributes the angular error (compensates angles),
    # the azimuths will differ slightly (by less than 0.001 degrees/seconds).
    for i, az in enumerate(resultado.azimutes):
        assert az == pytest.approx(expected_azimuths[i], abs=1e-3)

    # Verify perimeter is 1572.8 m
    assert resultado.perimetro == pytest.approx(1572.8)

    # Verify calculated area matches the theoretically correct area using compensated azimuths (~124666.14 m²)
    # which is close to user's Excel area (124665.7958 m²) calculated with rounding errors and uncompensated angles.
    assert resultado.area == pytest.approx(124666.145, abs=1e-1)
