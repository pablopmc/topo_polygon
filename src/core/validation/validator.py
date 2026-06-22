from __future__ import annotations
from typing import Optional, Sequence
from core.calculations.engine import CalculationEngine, VertexData
from core.validation.validation_result import ValidationResult, ValidationMessage, ValidationLevel
from core.validation.angle_checks import check_angles
from core.validation.distance_checks import check_distances
from core.validation.coordinate_checks import check_coordinates
from core.validation.geometry_checks import check_geometry

class ProjectValidator:
    """Validador principal de integridade do projeto topográfico."""
    
    @staticmethod
    def validate(
        vertices: Sequence[VertexData],
        azimute_inicial: float = 0.0,
        coordenada_inicial: tuple[float, float] = (0.0, 0.0),
        coordinate_system: Optional[str] = None,
        min_dist: float = 0.1,
        max_dist: float = 10000.0,
        tolerance: float = 0.01
    ) -> ValidationResult:
        messages: list[ValidationMessage] = []
        
        # 1. Base validation for length
        n = len(vertices)
        if n == 0:
            messages.append(ValidationMessage(
                level=ValidationLevel.ERROR,
                message="O projeto não contém nenhum vértice.",
                vertex_index=None,
                field=None
            ))
            return ValidationResult(messages)
            
        if n < 3:
            messages.append(ValidationMessage(
                level=ValidationLevel.WARNING,
                message=f"Poligonal incompleta: apenas {n} vértice(s) cadastrado(s). É necessário no mínimo 3 para fechar a poligonal.",
                vertex_index=None,
                field=None
            ))
            
        # 2. Angle checks (graus, minutos, segundos, soma teórica)
        messages.extend(check_angles(vertices))
        
        # 3. Distance checks (dist < 0, suspicious values)
        messages.extend(check_distances(vertices, min_dist, max_dist))
        
        # 4. Perform dry-run calculation to extract coordinates, area, and perimeter
        if n >= 3:
            try:
                engine = CalculationEngine(azimute_inicial, coordenada_inicial)
                # Run calculation to obtain computed values
                res = engine.calcular(vertices, aplicar_compensacao=True)
                
                # Check computed coordinates
                messages.extend(check_coordinates(res.coordenadas, [v.point_name for v in vertices], coordinate_system))
                
                # Check geometry (self-intersection, area, perimeter, linear error classification)
                messages.extend(check_geometry(
                    vertices=vertices,
                    coordinates=res.coordenadas,
                    area=res.area,
                    perimeter=res.perimetro,
                    precision=res.precisao,
                    erro_linear=res.erro_linear,
                    tolerance=tolerance
                ))
            except Exception as e:
                messages.append(ValidationMessage(
                    level=ValidationLevel.ERROR,
                    message=f"Erro interno de cálculo durante a validação: {str(e)}",
                    vertex_index=None,
                    field=None
                ))
        else:
            # For less than 3 vertices, check initial coordinate
            messages.extend(check_coordinates([coordenada_inicial], ["Inicial"], coordinate_system))
            
        return ValidationResult(messages)
