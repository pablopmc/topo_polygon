from __future__ import annotations
import pytest
import math
from core.calculations.engine import VertexData
from core.validation.validation_result import ValidationLevel
from core.validation.validator import ProjectValidator
from core.validation.angle_checks import check_angles
from core.validation.distance_checks import check_distances
from core.validation.coordinate_checks import check_coordinates
from core.validation.geometry_checks import check_geometry, segments_intersect

def test_angle_validation() -> None:
    # 1. Invalid angles individually
    vertices = [
        VertexData(sequence=1, point_name="V1", graus=-10, minutos=0, segundos=0.0, distancia=10.0),
        VertexData(sequence=2, point_name="V2", graus=370, minutos=75, segundos=0.0, distancia=10.0),
        VertexData(sequence=3, point_name="V3", graus=90, minutos=0, segundos=-5.0, distancia=10.0),
    ]
    
    msgs = check_angles(vertices)
    errs = [m for m in msgs if m.level == ValidationLevel.ERROR]
    assert len(errs) >= 3
    # Check that fields are correctly flagged
    assert any(m.field == "graus" for m in errs)
    assert any(m.field == "minutos" for m in errs)
    assert any(m.field == "segundos" for m in errs)

def test_distance_validation() -> None:
    vertices = [
        VertexData(sequence=1, point_name="V1", graus=90, minutos=0, segundos=0.0, distancia=-5.0),
        VertexData(sequence=2, point_name="V2", graus=90, minutos=0, segundos=0.0, distancia=0.05), # suspicious min
        VertexData(sequence=3, point_name="V3", graus=90, minutos=0, segundos=0.0, distancia=20000.0), # suspicious max
    ]
    
    msgs = check_distances(vertices, min_dist=0.1, max_dist=10000.0)
    
    errs = [m for m in msgs if m.level == ValidationLevel.ERROR]
    assert len(errs) == 1
    assert errs[0].vertex_index == 0
    assert errs[0].field == "distancia"
    
    warns = [m for m in msgs if m.level == ValidationLevel.WARNING]
    assert len(warns) == 2
    assert any(m.vertex_index == 1 for m in warns)
    assert any(m.vertex_index == 2 for m in warns)

def test_coordinate_validation() -> None:
    # 1. NaN coordinate
    coords = [(100.0, float("nan")), (200.0, 300.0)]
    names = ["V1", "V2"]
    msgs = check_coordinates(coords, names, coordinate_system=None)
    errs = [m for m in msgs if m.level == ValidationLevel.ERROR]
    assert len(errs) == 1
    assert errs[0].vertex_index == 0
    
    # 2. UTM boundaries check
    coords_utm = [(50000.0, 5000000.0), (500000.0, 12000000.0)]
    msgs_utm = check_coordinates(coords_utm, names, coordinate_system="UTM SIRGAS2000")
    warns = [m for m in msgs_utm if m.level == ValidationLevel.WARNING]
    assert len(warns) == 2
    assert any(m.vertex_index == 0 and "Easting" in m.message for m in warns)
    assert any(m.vertex_index == 1 and "Northing" in m.message for m in warns)

def test_segments_intersect() -> None:
    # Segments crossing
    # AB: (0, 0) -> (2, 2)
    # CD: (0, 2) -> (2, 0)
    assert segments_intersect((0, 0), (2, 2), (0, 2), (2, 0)) == True
    
    # Adjacent sharing endpoint - normal corner
    # AB: (0, 0) -> (0, 2)
    # BC: (0, 2) -> (2, 2)
    assert segments_intersect((0, 0), (0, 2), (0, 2), (2, 2)) == False
    
    # Adjacent segments colinear overlapping
    # AB: (0, 0) -> (0, 2)
    # BC: (0, 2) -> (0, 1) (overlaps)
    assert segments_intersect((0, 0), (0, 2), (0, 2), (0, 1)) == True

def test_geometry_duplicate_and_self_intersection() -> None:
    vertices = [
        VertexData(sequence=1, point_name="V1", graus=90, minutos=0, segundos=0.0, distancia=10.0),
        VertexData(sequence=2, point_name="v1", graus=90, minutos=0, segundos=0.0, distancia=10.0), # duplicate name
        VertexData(sequence=3, point_name="V3", graus=90, minutos=0, segundos=0.0, distancia=10.0),
    ]
    
    # Self-intersecting coordinates (hourglass shape)
    # V1=(0,0), V2=(10,0), V3=(0,10), V4=(10,10) - segments cross
    coords = [(0.0, 0.0), (10.0, 0.0), (0.0, 10.0), (10.0, 10.0)]
    vertices_hourglass = [
        VertexData(sequence=1, point_name="V1", graus=90, minutos=0, segundos=0.0, distancia=10.0),
        VertexData(sequence=2, point_name="V2", graus=90, minutos=0, segundos=0.0, distancia=10.0),
        VertexData(sequence=3, point_name="V3", graus=90, minutos=0, segundos=0.0, distancia=10.0),
        VertexData(sequence=4, point_name="V4", graus=90, minutos=0, segundos=0.0, distancia=10.0),
    ]
    
    msgs = check_geometry(
        vertices=vertices_hourglass,
        coordinates=coords,
        area=100.0,
        perimeter=40.0,
        precision=5000.0,
        erro_linear=0.01
    )
    
    # Hourglass coordinates must trigger self-intersection error
    errs = [m for m in msgs if m.level == ValidationLevel.ERROR]
    assert len(errs) == 1
    assert "auto-intersecta" in errs[0].message

def test_validator_orchestrator() -> None:
    # 1. Healthy project
    vertices = [
        VertexData(sequence=1, point_name="V1", graus=90, minutos=0, segundos=0.0, distancia=100.0),
        VertexData(sequence=2, point_name="V2", graus=90, minutos=0, segundos=0.0, distancia=100.0),
        VertexData(sequence=3, point_name="V3", graus=90, minutos=0, segundos=0.0, distancia=100.0),
        VertexData(sequence=4, point_name="V4", graus=90, minutos=0, segundos=0.0, distancia=100.0),
    ]
    
    result = ProjectValidator.validate(vertices, azimute_inicial=0.0)
    assert result.has_errors == False
    
    # 2. Project with errors
    vertices_bad = [
        VertexData(sequence=1, point_name="V1", graus=90, minutos=0, segundos=0.0, distancia=-100.0), # error
        VertexData(sequence=2, point_name="V2", graus=90, minutos=0, segundos=0.0, distancia=100.0),
        VertexData(sequence=3, point_name="V3", graus=90, minutos=0, segundos=0.0, distancia=100.0),
    ]
    
    result_bad = ProjectValidator.validate(vertices_bad, azimute_inicial=0.0)
    assert result_bad.has_errors == True
    assert any(m.level == ValidationLevel.ERROR for m in result_bad.messages)
