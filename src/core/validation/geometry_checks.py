from __future__ import annotations
from typing import Optional, Sequence
import math
from core.calculations.engine import Point2D, VertexData
from core.validation.validation_result import ValidationMessage, ValidationLevel

def orientation(p: Point2D, q: Point2D, r: Point2D) -> int:
    val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    if abs(val) < 1e-9:
        return 0
    return 1 if val > 0 else 2

def on_segment(p: Point2D, q: Point2D, r: Point2D) -> bool:
    if (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
        q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1])):
        return True
    return False

def segments_intersect(p1: Point2D, q1: Point2D, p2: Point2D, q2: Point2D) -> bool:
    shared = False
    if p1 == p2 or p1 == q2 or q1 == p2 or q1 == q2:
        shared = True
        
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    if not shared:
        if o1 != o2 and o3 != o4:
            return True
        if o1 == 0 and on_segment(p1, p2, q1):
            return True
        if o2 == 0 and on_segment(p1, q2, q1):
            return True
        if o3 == 0 and on_segment(p2, p1, q2):
            return True
        if o4 == 0 and on_segment(p2, q1, q2):
            return True
    else:
        # Colinear overlap check for adjacent segments sharing an endpoint
        if p1 == p2:
            n1, n2, s = q1, q2, p1
        elif p1 == q2:
            n1, n2, s = q1, p2, p1
        elif q1 == p2:
            n1, n2, s = p1, q2, q1
        else: # q1 == q2
            n1, n2, s = p1, p2, q1
            
        if orientation(n1, s, n2) == 0:
            v1 = (n1[0] - s[0], n1[1] - s[1])
            v2 = (n2[0] - s[0], n2[1] - s[1])
            dot = v1[0]*v2[0] + v1[1]*v2[1]
            if dot > 1e-9:
                return True
    return False

def check_geometry(
    vertices: Sequence[VertexData],
    coordinates: Sequence[Point2D],
    area: float,
    perimeter: float,
    precision: Optional[float],
    erro_linear: float,
    tolerance: float = 0.01
) -> list[ValidationMessage]:
    messages = []
    n = len(vertices)
    
    # 1. Duplicate vertices (names, coordinates identical or close)
    seen_names = {}
    for idx, v in enumerate(vertices):
        name_lower = v.point_name.lower().strip()
        if name_lower in seen_names:
            prev_idx = seen_names[name_lower]
            messages.append(ValidationMessage(
                level=ValidationLevel.WARNING,
                message=f"Nome de vértice duplicado: '{v.point_name}' (usado nos índices {prev_idx+1} e {idx+1})",
                vertex_index=idx,
                field="ponto"
            ))
        else:
            seen_names[name_lower] = idx
            
    # Check identical/close coordinates
    if len(coordinates) == n:
        for i in range(n):
            for j in range(i + 1, n):
                pi = coordinates[i]
                pj = coordinates[j]
                dx = pi[0] - pj[0]
                dy = pi[1] - pj[1]
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < tolerance:
                    messages.append(ValidationMessage(
                        level=ValidationLevel.WARNING,
                        message=f"Vértices '{vertices[i].point_name}' e '{vertices[j].point_name}' estão extremamente próximos ({dist:.4f} m)",
                        vertex_index=j,
                        field="coordenada"
                    ))

    # 2. Self-intersection check
    if len(coordinates) >= 3:
        poly_pts = list(coordinates)
        # Ensure it is closed
        if poly_pts[0] != poly_pts[-1]:
            poly_pts.append(poly_pts[0])
            
        segments = []
        for i in range(len(poly_pts) - 1):
            segments.append((poly_pts[i], poly_pts[i+1], i)) # i is the index of the start vertex
            
        num_segs = len(segments)
        intersection_found = False
        for i in range(num_segs):
            for j in range(i + 1, num_segs):
                p1, q1, idx1 = segments[i]
                p2, q2, idx2 = segments[j]
                if segments_intersect(p1, q1, p2, q2):
                    messages.append(ValidationMessage(
                        level=ValidationLevel.ERROR,
                        message=f"O polígono se auto-intersecta (cruzamento detectado entre os segmentos {vertices[idx1].point_name}-{vertices[(idx1+1)%n].point_name} e {vertices[idx2].point_name}-{vertices[(idx2+1)%n].point_name})",
                        vertex_index=idx1,
                        field=None
                    ))
                    intersection_found = True
                    break
            if intersection_found:
                break

    # 3. Area validation
    if n >= 3:
        if area <= 0:
            messages.append(ValidationMessage(
                level=ValidationLevel.ERROR,
                message=f"Área inválida (nula ou negativa): {area:.4f} m²",
                vertex_index=None,
                field=None
            ))
        elif area < 0.1:
            messages.append(ValidationMessage(
                level=ValidationLevel.WARNING,
                message=f"Área do polígono é muito pequena ({area:.4f} m²)",
                vertex_index=None,
                field=None
            ))

    # 4. Perimeter validation
    if n >= 1:
        if perimeter <= 0:
            messages.append(ValidationMessage(
                level=ValidationLevel.ERROR,
                message=f"Perímetro inválido (nulo ou negativo): {perimeter:.4f} m",
                vertex_index=None,
                field=None
            ))
            
    # 5. Open polygon / linear error quality classification
    if n >= 3:
        # Classify relative precision
        if precision is None or math.isnan(precision):
            qual = "Incalculável"
            level = ValidationLevel.WARNING
        elif precision == float("inf") or not math.isfinite(precision):
            qual = "Classe A - Perfeita (Erro Linear Nulo)"
            level = ValidationLevel.INFO
        else:
            if precision >= 10000.0:
                qual = "Classe A - Excelente (Alta Precisão)"
                level = ValidationLevel.INFO
            elif precision >= 5000.0:
                qual = "Classe B - Boa (Padrão Topográfico Urbano)"
                level = ValidationLevel.INFO
            elif precision >= 2000.0:
                qual = "Classe C - Regular (Cadastro Rural/Limites)"
                level = ValidationLevel.INFO
            else:
                qual = "Classe D - Ruim/Inaceitável (Necessita Revisão)"
                level = ValidationLevel.WARNING
                
        prec_str = "1:∞" if precision == float("inf") or precision is None or not math.isfinite(precision) else f"1:{int(round(precision))}"
        messages.append(ValidationMessage(
            level=level,
            message=f"Poligonal aberta: Erro Linear={erro_linear:.4f}m, Precisão={prec_str} -> Qualidade: {qual}",
            vertex_index=None,
            field=None
        ))
        
    return messages
