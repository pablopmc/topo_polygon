from __future__ import annotations

from pathlib import Path
from typing import Optional

from core.calculations.engine import CalculationEngine, VertexData, ResultadoCalculo
from core.imports.vertex_import import read_vertices_from_file
from core.persistence.persistence_manager import PersistenceManager
from data.database import Database
from models import Point, Project


class ProjectController:
    """Controller para gerenciar projetos e cálculos"""

    def __init__(self) -> None:
        self.persistence = PersistenceManager()
        self.engine: Optional[CalculationEngine] = None
        self.current_project: Optional[Project] = None
        self.current_db: Optional[Database] = None
        self.current_vertices: list[VertexData] = []
        self.last_calculation: Optional[ResultadoCalculo] = None

    def novo_projeto(
        self,
        file_path: str | Path,
        name: str,
        description: str = "",
        author: str = "",
        coordinate_system: str = "",
        reference_point: str = "",
        azimute_inicial: float = 0.0,
        coordenada_inicial: tuple[float, float] = (0.0, 0.0),
    ) -> int:
        """Cria um novo projeto"""
        project_id = self.persistence.new_project(
            file_path,
            name,
            description,
            author,
            coordinate_system,
            reference_point,
            azimute_inicial,
        )
        self.current_db = self.persistence.db
        if self.current_db is not None:
            self.current_project = self.current_db.get_project(project_id)
        self.engine = CalculationEngine(azimute_inicial, coordenada_inicial)
        self.current_vertices = []
        return project_id

    def abrir_projeto(self, file_path: str | Path) -> Project:
        """Abre um projeto existente"""
        self.current_db = self.persistence.open(file_path)
        if self.current_db is None:
            raise RuntimeError("Falha ao abrir banco de dados")
        
        # Carregar primeiro projeto (assumindo um por arquivo)
        projetos = self.current_db.list_projects()
        if not projetos:
            raise ValueError("Nenhum projeto encontrado no arquivo")
        
        self.current_project = projetos[0]
        azimute_inicial = self.current_project.azimute_inicial
        if azimute_inicial == 0.0 and self.current_project.id is not None:
            configuracao = self.current_db.get_configuration(self.current_project.id, "azimute_inicial")
            if configuracao and configuracao.value:
                try:
                    azimute_inicial = float(configuracao.value)
                    self.current_project.azimute_inicial = azimute_inicial
                    self.current_db.update_project(self.current_project)
                except ValueError:
                    pass
        self.engine = CalculationEngine(azimute_inicial)
        
        # Carregar vértices
        pontos = self.current_db.list_points(self.current_project.id or 0)
        self.current_vertices = [
            VertexData(
                sequence=p.sequence,
                point_name=p.point_name or "",
                graus=p.angle_deg or 0,
                minutos=p.angle_min or 0,
                segundos=p.angle_sec or 0.0,
                distancia=p.distance or 0.0,
                observacao=p.notes or "",
            )
            for p in pontos
        ]
        
        return self.current_project

    def salvar_projeto(self) -> None:
        """Salva o projeto atual"""
        if self.current_project is None or self.current_db is None:
            raise RuntimeError("Nenhum projeto aberto")
        self.persistence.save_project(self.current_project)

    def salvar_como(self, file_path: str | Path) -> None:
        """Salva o projeto em um novo local"""
        if self.current_db is None:
            raise RuntimeError("Nenhum projeto aberto")
        self.persistence.save_as(file_path)

    def fechar_projeto(self) -> None:
        """Fecha o projeto atual"""
        self.persistence.close()
        self.current_project = None
        self.current_db = None
        self.engine = None
        self.current_vertices = []
        self.last_calculation = None

    def importar_vertices(self, file_path: str | Path, substituir: bool = True) -> list[VertexData]:
        """Importa vértices de um arquivo CSV/Excel e opcionalmente substitui os existentes."""
        if self.current_db is None or self.current_project is None or self.current_project.id is None:
            raise RuntimeError("Abra ou crie um projeto antes de importar dados.")

        vertices = read_vertices_from_file(file_path)
        if substituir:
            self.current_db.clear_points(self.current_project.id)
            self.current_vertices = []
            next_sequence = 1
        else:
            next_sequence = len(self.current_vertices) + 1

        for index, vertex in enumerate(vertices, start=next_sequence):
            vertex.sequence = index
            self.current_vertices.append(vertex)
            self._salvar_vertice(vertex)

        self.last_calculation = None
        return list(self.current_vertices)

    def adicionar_vertice(
        self,
        ponto: str,
        graus: int,
        minutos: int,
        segundos: float,
        distancia: float,
        observacao: str = "",
    ) -> None:
        """Adiciona um vértice ao projeto"""
        if not self.engine:
            raise RuntimeError("Nenhum projeto aberto")
        
        vertex = VertexData(
            sequence=len(self.current_vertices) + 1,
            point_name=ponto,
            graus=graus,
            minutos=minutos,
            segundos=segundos,
            distancia=distancia,
            observacao=observacao,
        )
        self.current_vertices.append(vertex)
        self._salvar_vertice(vertex)

    def atualizar_vertice(
        self,
        index: int,
        ponto: str,
        graus: int,
        minutos: int,
        segundos: float,
        distancia: float,
        observacao: str = "",
    ) -> None:
        """Atualiza um vértice existente"""
        if index < 0 or index >= len(self.current_vertices):
            raise IndexError("Índice de vértice inválido")
        
        vertex = VertexData(
            sequence=index + 1,
            point_name=ponto,
            graus=graus,
            minutos=minutos,
            segundos=segundos,
            distancia=distancia,
            observacao=observacao,
        )
        self.current_vertices[index] = vertex
        self._salvar_vertice(vertex)

    def excluir_vertice(self, index: int) -> None:
        """Remove um vértice do projeto"""
        if index < 0 or index >= len(self.current_vertices):
            raise IndexError("Índice de vértice inválido")
        
        self.current_vertices.pop(index)
        
        # Renumerar sequências
        for i, v in enumerate(self.current_vertices):
            v.sequence = i + 1

    def calcular(self, azimute_inicial: float, aplicar_compensacao: bool = True) -> ResultadoCalculo:
        """Executa os cálculos topográficos"""
        if not self.engine or not self.current_vertices:
            raise RuntimeError("Dados insuficientes para cálculos")

        if self.current_project is not None:
            self.current_project.azimute_inicial = azimute_inicial
            if self.current_db is not None:
                self.current_db.update_project(self.current_project)
        
        self.engine.azimute_inicial = azimute_inicial
        resultado = self.engine.calcular(self.current_vertices, aplicar_compensacao)
        self.last_calculation = resultado
        return resultado

    def _salvar_vertice(self, vertex: VertexData) -> None:
        """Salva um vértice no banco de dados"""
        if self.current_db is None or self.current_project is None or self.current_project.id is None:
            return
        
        point = Point(
            project_id=self.current_project.id,
            sequence=vertex.sequence,
            point_name=vertex.point_name,
            angle_deg=vertex.graus,
            angle_min=vertex.minutos,
            angle_sec=vertex.segundos,
            distance=vertex.distancia,
            notes=vertex.observacao,
        )
        
        # Check if point exists
        existing = self.current_db.list_points(self.current_project.id)
        existing_at_seq = [p for p in existing if p.sequence == vertex.sequence]
        
        if existing_at_seq:
            point.id = existing_at_seq[0].id
            self.current_db.update_point(point)
        else:
            self.current_db.add_point(point)
