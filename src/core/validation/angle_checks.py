from __future__ import annotations
from typing import Sequence
from core.calculations.engine import VertexData
from core.validation.validation_result import ValidationMessage, ValidationLevel

def check_angles(vertices: Sequence[VertexData]) -> list[ValidationMessage]:
    messages = []
    
    # 1. Individual angle checks
    for idx, v in enumerate(vertices):
        # Negativos
        if v.graus < 0:
            messages.append(ValidationMessage(
                level=ValidationLevel.ERROR,
                message=f"Vértice '{v.point_name}': Graus não podem ser negativos ({v.graus}°)",
                vertex_index=idx,
                field="graus"
            ))
        elif v.graus > 360:
            messages.append(ValidationMessage(
                level=ValidationLevel.ERROR,
                message=f"Vértice '{v.point_name}': Graus não podem ser superiores a 360° ({v.graus}°)",
                vertex_index=idx,
                field="graus"
            ))
            
        if v.minutos < 0 or v.minutos >= 60:
            messages.append(ValidationMessage(
                level=ValidationLevel.ERROR,
                message=f"Vértice '{v.point_name}': Minutos devem estar entre 0 e 59 ({v.minutos}')",
                vertex_index=idx,
                field="minutos"
            ))
            
        if v.segundos < 0.0 or v.segundos >= 60.0:
            messages.append(ValidationMessage(
                level=ValidationLevel.ERROR,
                message=f"Vértice '{v.point_name}': Segundos devem estar entre 0 e 59.99 ({v.segundos}\")",
                vertex_index=idx,
                field="segundos"
            ))

    # 2. Theoretical sum check (only if n >= 3)
    n = len(vertices)
    if n >= 3:
        soma_teorica = (n - 2) * 180.0
        
        # Safe decimal sum
        soma_observada = 0.0
        for v in vertices:
            soma_observada += abs(v.graus) + v.minutos / 60.0 + v.segundos / 3600.0
            
        dif = abs(soma_observada - soma_teorica)
        
        # Format difference as GMS
        from core.calculations.engine import decimal_para_dms
        g, m, s = decimal_para_dms(dif)
        sinal = "-" if soma_observada < soma_teorica else "+"
        dif_str = f"{sinal}{g}° {m:02d}' {s:05.2f}\""
        
        obs_g, obs_m, obs_s = decimal_para_dms(soma_observada)
        obs_str = f"{obs_g}° {obs_m:02d}' {obs_s:05.2f}\""
        
        teor_g, teor_m, teor_s = decimal_para_dms(soma_teorica)
        teor_str = f"{teor_g}° {teor_m:02d}' {teor_s:05.2f}\""
        
        msg_text = f"Soma angular: teórica={teor_str}, observada={obs_str}, erro={dif_str}"
        
        if dif > 2.0: # Large difference generates warning
            messages.append(ValidationMessage(
                level=ValidationLevel.WARNING,
                message=f"Diferença angular excessiva! {msg_text}",
                vertex_index=None,
                field=None
            ))
        else:
            messages.append(ValidationMessage(
                level=ValidationLevel.INFO,
                message=msg_text,
                vertex_index=None,
                field=None
            ))
            
    return messages
