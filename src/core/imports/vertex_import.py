from __future__ import annotations

from pathlib import Path
import re
import unicodedata
from typing import Any

import pandas as pd

from core.calculations.engine import VertexData, decimal_para_dms


def _normalize_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _clean_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none"}:
        return ""
    return text


def _to_int(value: Any, field: str) -> int:
    text = _clean_value(value)
    if not text:
        raise ValueError(f"Campo obrigatório ausente: {field}")
    try:
        return int(float(text.replace(",", ".")))
    except ValueError as exc:
        raise ValueError(f"Valor inválido em {field}: {text}") from exc


def _to_float(value: Any, field: str) -> float:
    text = _clean_value(value)
    if not text:
        raise ValueError(f"Campo obrigatório ausente: {field}")
    try:
        return float(text.replace(",", "."))
    except ValueError as exc:
        raise ValueError(f"Valor inválido em {field}: {text}") from exc


def _optional_text(value: Any) -> str:
    return _clean_value(value)


def _find_column(columns: dict[str, str], aliases: tuple[str, ...]) -> str | None:
    for alias in aliases:
        key = _normalize_text(alias)
        if key in columns:
            return columns[key]
    return None


def _read_dataframe(file_path: Path) -> pd.DataFrame:
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        # Tentativa de detectar delimitador e codificação de forma robusta
        encodings = ["utf-8-sig", "latin1", "cp1252"]
        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding, errors="ignore") as f:
                    first_line = f.readline()
                
                delimiter = ";"
                if first_line:
                    counts = {
                        ";": first_line.count(";"),
                        ",": first_line.count(","),
                        "\t": first_line.count("\t"),
                    }
                    best_sep = max(counts, key=counts.get)
                    if counts[best_sep] > 0:
                        delimiter = best_sep
                    else:
                        delimiter = ","
                
                df = pd.read_csv(file_path, sep=delimiter, encoding=encoding)
                if len(df.columns) > 1:
                    return df
            except Exception:
                continue
        # Fallback para o comportamento padrão anterior
        return pd.read_csv(file_path, sep=None, engine="python", encoding="utf-8-sig")
    if suffix in {".xlsx", ".xlsm"}:
        xls = pd.ExcelFile(file_path)
        sheet_name = "Leituras" if "Leituras" in xls.sheet_names else xls.sheet_names[0]
        return pd.read_excel(file_path, sheet_name=sheet_name)
    raise ValueError("Formato não suportado. Use CSV, XLSX ou XLSM.")


def read_vertices_from_file(file_path: str | Path) -> list[VertexData]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    dataframe = _read_dataframe(path)
    if dataframe.empty:
        raise ValueError("O arquivo não contém linhas de dados.")

    columns = {_normalize_text(column): column for column in dataframe.columns}

    point_column = _find_column(columns, ("ponto", "point", "point name", "nome do ponto", "vertex", "vertice", "estacao", "estação", "est", "station"))
    distance_column = _find_column(columns, ("distancia", "distance", "distância", "comprimento", "dist", "len", "length"))
    obs_column = _find_column(columns, ("observacao", "observação", "notes", "nota", "comentario", "comentário", "obs", "observacoes"))
    graus_column = _find_column(columns, ("graus", "g", "grau", "angulo grau", "angulo g", "graus_g", "deg", "degrees"))
    minutos_column = _find_column(columns, ("minutos", "m", "min", "angulo minuto", "angulo m", "minutos_m", "minutes"))
    segundos_column = _find_column(columns, ("segundos", "s", "sec", "angulo segundo", "angulo s", "segundos_s", "seconds"))
    angle_decimal_column = _find_column(columns, ("angulo decimal", "angulo", "angulos", "angulo interno decimal", "angulo interno", "angulo_decimal", "angle_decimal"))

    if point_column is None:
        raise ValueError("Não foi encontrada uma coluna de ponto.")
    if distance_column is None:
        raise ValueError("Não foi encontrada uma coluna de distância.")

    vertices: list[VertexData] = []
    for index, row in dataframe.iterrows():
        point_name = _optional_text(row.get(point_column))
        if not point_name:
            continue

        if graus_column and minutos_column and segundos_column:
            graus = _to_int(row.get(graus_column), "graus")
            minutos = _to_int(row.get(minutos_column), "minutos")
            segundos = float(_clean_value(row.get(segundos_column)).replace(",", ".") or "0")
        elif angle_decimal_column:
            angle_decimal = _to_float(row.get(angle_decimal_column), "ângulo")
            graus, minutos, segundos = decimal_para_dms(angle_decimal)
        else:
            raise ValueError("O arquivo precisa ter colunas de ângulo em G/M/S ou em graus decimais.")

        distancia = _to_float(row.get(distance_column), "distância")
        observacao = _optional_text(row.get(obs_column)) if obs_column else ""

        vertices.append(
            VertexData(
                sequence=len(vertices) + 1,
                point_name=point_name,
                graus=graus,
                minutos=minutos,
                segundos=segundos,
                distancia=distancia,
                observacao=observacao,
            )
        )

    if not vertices:
        raise ValueError("Nenhum vértice válido foi encontrado no arquivo.")

    return vertices
