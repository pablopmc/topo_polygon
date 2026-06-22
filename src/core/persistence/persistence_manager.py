from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from data.database import Database
from models import Project

PROJECT_FILE_EXTENSION = ".topo"

SCHEMA_SQL = """
BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    author TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    coordinate_system TEXT,
    reference_point TEXT,
    azimute_inicial REAL NOT NULL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL,
    point_code TEXT,
    point_name TEXT,
    x REAL,
    y REAL,
    distance REAL,
    azimuth REAL,
    rumbo TEXT,
    quadrant TEXT,
    angle_deg INTEGER,
    angle_min INTEGER,
    angle_sec REAL,
    delta_x REAL,
    delta_y REAL,
    corrected_x REAL,
    corrected_y REAL,
    notes TEXT,
    UNIQUE(project_id, sequence)
);

CREATE INDEX IF NOT EXISTS idx_points_project_id ON points(project_id);

CREATE TABLE IF NOT EXISTS configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value TEXT,
    UNIQUE(project_id, key)
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    report_type TEXT NOT NULL,
    generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    file_name TEXT,
    file_content BLOB,
    summary TEXT
);

COMMIT;
"""


class PersistenceManager:
    def __init__(self) -> None:
        self.db: Optional[Database] = None
        self.file_path: Optional[Path] = None

    def _ensure_extension(self, file_path: Path) -> Path:
        if file_path.suffix.lower() != PROJECT_FILE_EXTENSION:
            file_path = file_path.with_suffix(PROJECT_FILE_EXTENSION)
        return file_path

    def _initialize_database(self, path: Path) -> Database:
        db = Database(path)
        with db.transaction() as cursor:
            cursor.executescript(SCHEMA_SQL)
        return db

    def new_project(
        self,
        file_path: str | Path,
        name: str,
        description: str = "",
        author: str = "",
        coordinate_system: str = "",
        reference_point: str = "",
        azimute_inicial: float = 0.0,
    ) -> int:
        path = self._ensure_extension(Path(file_path))
        if path.exists():
            raise FileExistsError(f"O arquivo '{path}' já existe.")
        db = self._initialize_database(path)
        project = Project(
            name=name,
            description=description,
            author=author,
            created_at=datetime.now().isoformat(timespec="seconds"),
            updated_at=datetime.now().isoformat(timespec="seconds"),
            coordinate_system=coordinate_system,
            reference_point=reference_point,
            azimute_inicial=azimute_inicial,
        )
        project_id = db.create_project(project)
        self.db = db
        self.file_path = path
        return project_id

    def open(self, file_path: str | Path) -> Database:
        path = self._ensure_extension(Path(file_path))
        if not path.exists():
            raise FileNotFoundError(f"Arquivo de projeto não encontrado: {path}")
        db = Database(path)
        self.db = db
        self.file_path = path
        return db

    def save_project(self, project: Project) -> None:
        if self.db is None:
            raise RuntimeError("Nenhum projeto aberto para salvar.")
        project.updated_at = datetime.now().isoformat(timespec="seconds")
        if project.id is None:
            self.db.create_project(project)
        else:
            self.db.update_project(project)

    def save_as(self, target_path: str | Path) -> None:
        if self.db is None or self.db.connection is None:
            raise RuntimeError("Nenhum projeto aberto para salvar.")
        target = self._ensure_extension(Path(target_path))
        if self.file_path is not None and target.resolve() == self.file_path.resolve():
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        dest_conn = sqlite3.connect(str(target))
        try:
            self.db.connection.backup(dest_conn)
        finally:
            dest_conn.close()
        self.file_path = target

    def close(self) -> None:
        if self.db is not None and self.db.connection is not None:
            self.db.connection.close()
        self.db = None
        self.file_path = None