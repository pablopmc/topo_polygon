import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

from core.calculations.engine import FechamentoPoligonal

vertices = [
    {"sequence": 1, "point_name": "P1", "graus": 69, "minutos": 3, "segundos": 49.0, "distancia": 265.0},
    {"sequence": 2, "point_name": "P2", "graus": 110, "minutos": 35, "segundos": 28.0, "distancia": 123.45},
    {"sequence": 3, "point_name": "P3", "graus": 256, "minutos": 9, "segundos": 30.0, "distancia": 234.76},
    {"sequence": 4, "point_name": "P4", "graus": 94, "minutos": 56, "segundos": 59.0, "distancia": 128.19},
    {"sequence": 5, "point_name": "P5", "graus": 106, "minutos": 5, "segundos": 27.0, "distancia": 326.21},
    {"sequence": 6, "point_name": "P6", "graus": 128, "minutos": 23, "segundos": 37.0, "distancia": 183.19},
    {"sequence": 7, "point_name": "P7", "graus": 134, "minutos": 45, "segundos": 10.0, "distancia": 312.0},
]

engine = FechamentoPoligonal(azimute_inicial=104 + 1/60 + 37/3600) # 104° 01' 37"
resultado = engine.calcular(vertices)
print("Área Calculada:", resultado.area)
print("Soma X:", resultado.soma_x)
print("Soma Y:", resultado.soma_y)
print("Duplas Áreas (+):", resultado.dupla_area_plus)
print("Duplas Áreas (-):", resultado.dupla_area_minus)
print("\nTABELA FINAL:")
print(resultado.tabela_final)
