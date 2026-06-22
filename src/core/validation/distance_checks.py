from __future__ import annotations
from typing import Sequence
import math
from core.calculations.engine import VertexData
from core.validation.validation_result import ValidationMessage, ValidationLevel

def check_distances(
    vertices: Sequence[VertexData],
    min_dist: float = 0.1,
    max_dist: float = 10000.0
) -> list[ValidationMessage]:
    messages = []
    
    for idx, v in enumerate(vertices):
        dist = v.distancia
        # 1. Invalid values
        if dist is None or math.isnan(dist) or not math.isfinite(dist):
            messages.append(ValidationMessage(
                level=ValidationLevel.ERROR,
                message=f"Vértice '{v.point_name}': Distância inválida ou nula",
                vertex_index=idx,
                field="distancia"
            ))
        elif dist <= 0:
            messages.append(ValidationMessage(
                level=ValidationLevel.ERROR,
                message=f"Vértice '{v.point_name}': Distância deve ser maior que zero ({dist:.4f} m)",
                vertex_index=idx,
                field="distancia"
            ))
        else:
            # 2. Suspicious values
            if dist < min_dist:
                messages.append(ValidationMessage(
                    level=ValidationLevel.WARNING,
                    message=f"Vértice '{v.point_name}': Distância suspeitosamente pequena ({dist:.4f} m)",
                    vertex_index=idx,
                    field="distancia"
                ))
            elif dist > max_dist:
                messages.append(ValidationMessage(
                    level=ValidationLevel.WARNING,
                    message=f"Vértice '{v.point_name}': Distância suspeitosamente grande ({dist:.4f} m)",
                    vertex_index=idx,
                    field="distancia"
                ))
                
    return messages
