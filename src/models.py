from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Project:
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    coordinate_system: Optional[str] = None
    reference_point: Optional[str] = None
    azimute_inicial: float = 0.0



@dataclass
class Point:
    id: Optional[int] = None
    project_id: Optional[int] = None
    sequence: int = 0
    point_code: Optional[str] = None
    point_name: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    distance: Optional[float] = None
    azimuth: Optional[float] = None
    rumbo: Optional[str] = None
    quadrant: Optional[str] = None
    angle_deg: Optional[int] = None
    angle_min: Optional[int] = None
    angle_sec: Optional[float] = None
    delta_x: Optional[float] = None
    delta_y: Optional[float] = None
    corrected_x: Optional[float] = None
    corrected_y: Optional[float] = None
    notes: Optional[str] = None


@dataclass
class Configuration:
    id: Optional[int] = None
    project_id: Optional[int] = None
    key: str = ""
    value: Optional[str] = None


@dataclass
class Report:
    id: Optional[int] = None
    project_id: Optional[int] = None
    report_type: str = ""
    generated_at: Optional[str] = None
    file_name: Optional[str] = None
    file_content: Optional[bytes] = None
    summary: Optional[str] = None