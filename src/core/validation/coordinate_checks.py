from __future__ import annotations
from typing import Optional, Sequence
import math
from core.calculations.engine import Point2D
from core.validation.validation_result import ValidationMessage, ValidationLevel

def check_coordinates(
    coordinates: Sequence[Point2D],
    point_names: Sequence[str],
    coordinate_system: Optional[str] = None
) -> list[ValidationMessage]:
    messages = []
    
    # 1. Check coordinates for NaN/infinity/empty
    for idx, (x, y) in enumerate(coordinates):
        name = point_names[idx] if idx < len(point_names) else f"#{idx+1}"
        
        if x is None or math.isnan(x) or not math.isfinite(x):
            messages.append(ValidationMessage(
                level=ValidationLevel.ERROR,
                message=f"Vértice '{name}': Coordenada X calculada inválida (NaN/Infinito)",
                vertex_index=idx,
                field="coordenada"
            ))
        if y is None or math.isnan(y) or not math.isfinite(y):
            messages.append(ValidationMessage(
                level=ValidationLevel.ERROR,
                message=f"Vértice '{name}': Coordenada Y calculada inválida (NaN/Infinito)",
                vertex_index=idx,
                field="coordenada"
            ))
            
        # 2. UTM checks if coordinate system contains "utm"
        if coordinate_system and "utm" in coordinate_system.lower():
            # Easting check
            if not (100000.0 <= x <= 900000.0):
                messages.append(ValidationMessage(
                    level=ValidationLevel.WARNING,
                    message=f"Vértice '{name}': Coordenada UTM X (Easting) fora dos limites normais de 100km a 900km ({x:.3f} m)",
                    vertex_index=idx,
                    field="coordenada"
                ))
            # Northing check
            if not (0.0 <= y <= 10000000.0):
                messages.append(ValidationMessage(
                    level=ValidationLevel.WARNING,
                    message=f"Vértice '{name}': Coordenada UTM Y (Northing) fora dos limites normais de 0m a 10.000.000m ({y:.3f} m)",
                    vertex_index=idx,
                    field="coordenada"
                ))
                
    return messages
