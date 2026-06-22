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