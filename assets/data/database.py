from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, List, Optional

from models import Configuration, Point, Project, Report


class Database:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.connection: Optional[sqlite3.Connection] = None
        self._connect()

    def _connect(self) -> None:
        self.connection = sqlite3.connect(str(self.path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON;")
        self._run_migrations()
        self.connection.commit()

    def _run_migrations(self) -> None:
        try:
            cursor = self.connection.execute("PRAGMA table_info(projects);")
            columns = [row["name"] for row in cursor.fetchall()]
            if "azimute_inicial" not in columns:
                self.connection.execute("ALTER TABLE projects ADD COLUMN azimute_inicial REAL NOT NULL DEFAULT 0.0;")
                self.connection.commit()
        except Exception:
            pass

    @contextmanager
    def transaction(self):
        if self.connection is None:
            self._connect()
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def initialize(self, schema_path: Optional[str | Path] = None) -> None:
        if schema_path is None:
            raise ValueError("schema_path is required to initialize the database")
        schema_file = Path(schema_path)
        with schema_file.open("r", encoding="utf-8") as handle:
            schema = handle.read()
        with self.transaction() as cursor:
            cursor.executescript(schema)

    def create_project(self, project: Project) -> int:
        with self.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO projects
                    (name, description, author, created_at, updated_at, coordinate_system, reference_point, azimute_inicial)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project.name,
                    project.description,
                    project.author,
                    project.created_at,
                    project.updated_at,
                    project.coordinate_system,
                    project.reference_point,
                    project.azimute_inicial,
                ),
            )
            return cursor.lastrowid

    def update_project(self, project: Project) -> None:
        if project.id is None:
            raise ValueError("Project ID is required for update.")
        with self.transaction() as cursor:
            cursor.execute(
                """
                UPDATE projects
                SET name = ?, description = ?, author = ?, updated_at = ?, coordinate_system = ?, reference_point = ?, azimute_inicial = ?
                WHERE id = ?
                """,
                (
                    project.name,
                    project.description,
                    project.author,
                    project.updated_at,
                    project.coordinate_system,
                    project.reference_point,
                    project.azimute_inicial,
                    project.id,
                ),
            )

    def get_project(self, project_id: int) -> Optional[Project]:
        cursor = self.connection.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,),
        )
        row = cursor.fetchone()
        return self._row_to_project(row) if row else None

    def list_projects(self) -> List[Project]:
        cursor = self.connection.execute(
            "SELECT * FROM projects ORDER BY created_at DESC"
        )
        return [self._row_to_project(row) for row in cursor.fetchall()]

    def delete_project(self, project_id: int) -> None:
        with self.transaction() as cursor:
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))

    def add_point(self, point: Point) -> int:
        with self.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO points
                    (project_id, sequence, point_code, point_name, x, y, distance, azimuth, rumbo, quadrant,
                     angle_deg, angle_min, angle_sec, delta_x, delta_y, corrected_x, corrected_y, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    point.project_id,
                    point.sequence,
                    point.point_code,
                    point.point_name,
                    point.x,
                    point.y,
                    point.distance,
                    point.azimuth,
                    point.rumbo,
                    point.quadrant,
                    point.angle_deg,
                    point.angle_min,
                    point.angle_sec,
                    point.delta_x,
                    point.delta_y,
                    point.corrected_x,
                    point.corrected_y,
                    point.notes,
                ),
            )
            return cursor.lastrowid

    def update_point(self, point: Point) -> None:
        if point.id is None:
            raise ValueError("Point ID is required for update.")
        with self.transaction() as cursor:
            cursor.execute(
                """
                UPDATE points
                SET sequence = ?, point_code = ?, point_name = ?, x = ?, y = ?, distance = ?, azimuth = ?, rumbo = ?,
                    quadrant = ?, angle_deg = ?, angle_min = ?, angle_sec = ?, delta_x = ?, delta_y = ?,
                    corrected_x = ?, corrected_y = ?, notes = ?
                WHERE id = ?
                """,
                (
                    point.sequence,
                    point.point_code,
                    point.point_name,
                    point.x,
                    point.y,
                    point.distance,
                    point.azimuth,
                    point.rumbo,
                    point.quadrant,
                    point.angle_deg,
                    point.angle_min,
                    point.angle_sec,
                    point.delta_x,
                    point.delta_y,
                    point.corrected_x,
                    point.corrected_y,
                    point.notes,
                    point.id,
                ),
            )

    def list_points(self, project_id: int) -> List[Point]:
        cursor = self.connection.execute(
            "SELECT * FROM points WHERE project_id = ? ORDER BY sequence ASC",
            (project_id,),
        )
        return [self._row_to_point(row) for row in cursor.fetchall()]

    def delete_point(self, point_id: int) -> None:
        with self.transaction() as cursor:
            cursor.execute("DELETE FROM points WHERE id = ?", (point_id,))

    def clear_points(self, project_id: int) -> None:
        with self.transaction() as cursor:
            cursor.execute("DELETE FROM points WHERE project_id = ?", (project_id,))

    def set_configuration(self, config: Configuration) -> int:
        with self.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO configurations(project_id, key, value)
                VALUES (?, ?, ?)
                ON CONFLICT(project_id, key) DO UPDATE SET value = excluded.value
                """,
                (config.project_id, config.key, config.value),
            )
            if config.id:
                return config.id
            return cursor.lastrowid

    def get_configuration(self, project_id: int, key: str) -> Optional[Configuration]:
        cursor = self.connection.execute(
            "SELECT * FROM configurations WHERE project_id = ? AND key = ?",
            (project_id, key),
        )
        row = cursor.fetchone()
        return self._row_to_configuration(row) if row else None

    def list_configurations(self, project_id: int) -> List[Configuration]:
        cursor = self.connection.execute(
            "SELECT * FROM configurations WHERE project_id = ? ORDER BY key ASC",
            (project_id,),
        )
        return [self._row_to_configuration(row) for row in cursor.fetchall()]

    def save_report(self, report: Report) -> int:
        with self.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO reports(project_id, report_type, generated_at, file_name, file_content, summary)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    report.project_id,
                    report.report_type,
                    report.generated_at,
                    report.file_name,
                    report.file_content,
                    report.summary,
                ),
            )
            return cursor.lastrowid

    def list_reports(self, project_id: int) -> List[Report]:
        cursor = self.connection.execute(
            "SELECT * FROM reports WHERE project_id = ? ORDER BY generated_at DESC",
            (project_id,),
        )
        return [self._row_to_report(row) for row in cursor.fetchall()]

    def get_report(self, report_id: int) -> Optional[Report]:
        cursor = self.connection.execute(
            "SELECT * FROM reports WHERE id = ?",
            (report_id,),
        )
        row = cursor.fetchone()
        return self._row_to_report(row) if row else None

    def _row_to_project(self, row: sqlite3.Row) -> Project:
        return Project(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            author=row["author"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            coordinate_system=row["coordinate_system"],
            reference_point=row["reference_point"],
            azimute_inicial=row["azimute_inicial"] if "azimute_inicial" in row.keys() else 0.0,
        )

    def _row_to_point(self, row: sqlite3.Row) -> Point:
        return Point(
            id=row["id"],
            project_id=row["project_id"],
            sequence=row["sequence"],
            point_code=row["point_code"],
            point_name=row["point_name"],
            x=row["x"],
            y=row["y"],
            distance=row["distance"],
            azimuth=row["azimuth"],
            rumbo=row["rumbo"],
            quadrant=row["quadrant"],
            angle_deg=row["angle_deg"],
            angle_min=row["angle_min"],
            angle_sec=row["angle_sec"],
            delta_x=row["delta_x"],
            delta_y=row["delta_y"],
            corrected_x=row["corrected_x"],
            corrected_y=row["corrected_y"],
            notes=row["notes"],
        )

    def _row_to_configuration(self, row: sqlite3.Row) -> Configuration:
        return Configuration(
            id=row["id"],
            project_id=row["project_id"],
            key=row["key"],
            value=row["value"],
        )

    def _row_to_report(self, row: sqlite3.Row) -> Report:
        return Report(
            id=row["id"],
            project_id=row["project_id"],
            report_type=row["report_type"],
            generated_at=row["generated_at"],
            file_name=row["file_name"],
            file_content=row["file_content"],
            summary=row["summary"],
        )
