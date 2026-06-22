from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QHeaderView,
)
from ui.widgets.validation_panel import ValidationPanel


class ResultsPanel(QWidget):
    add_vertex_requested = Signal()
    edit_vertex_requested = Signal(int)
    delete_vertex_requested = Signal(int)
    add_azimuth_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._create_tables()
        self._create_summary()
        self._assemble_layout()
        self._connect_buttons()

    def _create_tables(self) -> None:
        self.tabs = QTabWidget(self)

        # 1. New Vértices tab
        self.vertices_tab = QWidget(self)
        vertices_layout = QVBoxLayout(self.vertices_tab)
        vertices_layout.setContentsMargins(4, 4, 4, 4)

        self.vertices_table = QTableWidget(0, 6, self)
        self.vertices_table.setHorizontalHeaderLabels(
            ["Ponto", "G", "M", "S", "Distância", "Observação"]
        )
        self._configure_table(self.vertices_table)
        vertices_layout.addWidget(self.vertices_table)

        # Re-introduced button layouts directly below the vertices table
        buttons_layout = QHBoxLayout()
        self.btn_add_vertex = QPushButton("Adicionar Vértice", self)
        self.btn_edit_vertex = QPushButton("Editar Vértice", self)
        self.btn_delete_vertex = QPushButton("Excluir Vértice", self)
        self.btn_azimuth = QPushButton("Adicionar Azimute Inicial", self)

        self.btn_edit_vertex.setEnabled(False)
        self.btn_delete_vertex.setEnabled(False)

        buttons_layout.addWidget(self.btn_add_vertex)
        buttons_layout.addWidget(self.btn_edit_vertex)
        buttons_layout.addWidget(self.btn_delete_vertex)
        buttons_layout.addWidget(self.btn_azimuth)
        vertices_layout.addLayout(buttons_layout)

        # 2. Existing calculation tables
        self.angulos_table = QTableWidget(0, 5, self)
        self.angulos_table.setHorizontalHeaderLabels(
            ["Seq", "Ponto", "Grau", "Min", "Seg"]
        )
        self._configure_table(self.angulos_table)

        self.azimutes_table = QTableWidget(0, 3, self)
        self.azimutes_table.setHorizontalHeaderLabels(["Seq", "Ponto", "Azimute"])
        self._configure_table(self.azimutes_table)

        self.rumos_table = QTableWidget(0, 4, self)
        self.rumos_table.setHorizontalHeaderLabels(
            ["Seq", "Ponto", "Rumo", "Quadrante"]
        )
        self._configure_table(self.rumos_table)

        self.projecoes_table = QTableWidget(0, 5, self)
        self.projecoes_table.setHorizontalHeaderLabels(
            ["Seq", "Ponto", "ΔX", "ΔY", "Distância"]
        )
        self._configure_table(self.projecoes_table)

        self.coordenadas_table = QTableWidget(0, 6, self)
        self.coordenadas_table.setHorizontalHeaderLabels(
            ["Seq", "Ponto", "X", "Y", "X Corrigido", "Y Corrigido"]
        )
        self._configure_table(self.coordenadas_table)

        # Add tabs, placing Vértices as the first one ("Antes de Ângulos")
        self.tabs.addTab(self.vertices_tab, "Vértices")
        self.tabs.addTab(self.angulos_table, "Ângulos")
        self.tabs.addTab(self.azimutes_table, "Azimutes")
        self.tabs.addTab(self.rumos_table, "Rumos")
        self.tabs.addTab(self.projecoes_table, "Projeções")
        self.tabs.addTab(self.coordenadas_table, "Coordenadas")
        
        self.validation_tab = ValidationPanel(self)
        self.tabs.addTab(self.validation_tab, "Validação")

    def _create_summary(self) -> None:
        summary_group = QGroupBox("Resumo")
        summary_layout = QVBoxLayout(summary_group)
        summary_layout.setContentsMargins(4, 4, 4, 4)

        self.summary_table = QTableWidget(8, 2, self)
        self.summary_table.setHorizontalHeaderLabels(["Métrica", "Valor"])
        self.summary_table.verticalHeader().setVisible(False)
        self.summary_table.horizontalHeader().setStretchLastSection(True)
        self.summary_table.setAlternatingRowColors(True)
        self.summary_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.summary_table.setSelectionBehavior(QTableWidget.SelectRows)

        self.summary_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.summary_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        metrics = [
            "Área (m²)",
            "Área (ha)",
            "Perímetro (m)",
            "Precisão",
            "Número de Estações",
            "Erro de Fechamento Linear (m)",
            "Soma dos Ângulos Lidos",
            "Erro de Fechamento Angular"
        ]
        for row, metric in enumerate(metrics):
            item = QTableWidgetItem(metric)
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.summary_table.setItem(row, 0, item)
            
            val_item = QTableWidgetItem("N/A" if row in (3, 7) else "0.00")
            val_item.setTextAlignment(Qt.AlignCenter)
            self.summary_table.setItem(row, 1, val_item)

        summary_layout.addWidget(self.summary_table)
        self.summary_group = summary_group

    def _assemble_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs, 2)
        layout.addWidget(self.summary_group, 1)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)

    def _connect_buttons(self) -> None:
        self.btn_add_vertex.clicked.connect(self.add_vertex_requested.emit)
        self.btn_edit_vertex.clicked.connect(self._on_edit_clicked)
        self.btn_delete_vertex.clicked.connect(self._on_delete_clicked)
        self.btn_azimuth.clicked.connect(self.add_azimuth_requested.emit)
        self.vertices_table.itemSelectionChanged.connect(self._on_vertices_selection_changed)

    def _on_edit_clicked(self) -> None:
        selected = self.vertices_table.selectedItems()
        if selected:
            row = selected[0].row()
            self.edit_vertex_requested.emit(row)

    def _on_delete_clicked(self) -> None:
        selected = self.vertices_table.selectedItems()
        if selected:
            row = selected[0].row()
            self.delete_vertex_requested.emit(row)

    def _on_vertices_selection_changed(self) -> None:
        selected = self.vertices_table.selectedItems()
        has_selection = bool(selected)
        self.btn_edit_vertex.setEnabled(has_selection)
        self.btn_delete_vertex.setEnabled(has_selection)

    @staticmethod
    def _configure_table(table: QTableWidget) -> None:
        table.horizontalHeader().setStretchLastSection(True)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)

    def update_summary(
        self,
        area_m2: str,
        area_ha: str,
        perimetro: str,
        precisao: str,
        num_estacoes: str,
        erro_linear: str,
        soma_angulos: str,
        erro_angular: str,
    ) -> None:
        values = [
            area_m2,
            area_ha,
            perimetro,
            precisao,
            num_estacoes,
            erro_linear,
            soma_angulos,
            erro_angular,
        ]
        for row, val in enumerate(values):
            item = self.summary_table.item(row, 1)
            if item:
                item.setText(str(val))

    def clear_tables(self) -> None:
        self.angulos_table.setRowCount(0)
        self.azimutes_table.setRowCount(0)
        self.rumos_table.setRowCount(0)
        self.projecoes_table.setRowCount(0)
        self.coordenadas_table.setRowCount(0)
        for row in range(8):
            item = self.summary_table.item(row, 1)
            if item:
                item.setText("N/A" if row in (3, 7) else "0.00")

    def clear_vertices_table(self) -> None:
        self.vertices_table.setRowCount(0)
        self.btn_edit_vertex.setEnabled(False)
        self.btn_delete_vertex.setEnabled(False)

    def add_vertex_row(self, ponto: str, g: int | str, m: int | str, s: float | str, dist: float | str, obs: str) -> None:
        row = self.vertices_table.rowCount()
        self.vertices_table.insertRow(row)
        self.vertices_table.setItem(row, 0, QTableWidgetItem(str(ponto)))
        self.vertices_table.setItem(row, 1, QTableWidgetItem(str(g)))
        self.vertices_table.setItem(row, 2, QTableWidgetItem(str(m)))
        
        try:
            seg_val = float(s)
            seg_str = f"{seg_val:.2f}"
        except ValueError:
            seg_str = str(s)
        self.vertices_table.setItem(row, 3, QTableWidgetItem(seg_str))
        
        try:
            dist_val = float(dist)
            dist_str = f"{dist_val:.4f}"
        except ValueError:
            dist_str = str(dist)
        self.vertices_table.setItem(row, 4, QTableWidgetItem(dist_str))
        self.vertices_table.setItem(row, 5, QTableWidgetItem(str(obs)))
        for col in range(6):
            item = self.vertices_table.item(row, col)
            if item:
                item.setTextAlignment(Qt.AlignCenter)

    def add_angulo_row(self, seq: int, ponto: str, graus: str, minutos: str, segundos: str) -> None:
        self._add_row(self.angulos_table, [str(seq), ponto, graus, minutos, segundos])

    def add_azimute_row(self, seq: int, ponto: str, azimute: str) -> None:
        self._add_row(self.azimutes_table, [str(seq), ponto, azimute])

    def add_rumo_row(self, seq: int, ponto: str, rumo: str, quadrante: str) -> None:
        self._add_row(self.rumos_table, [str(seq), ponto, rumo, quadrante])

    def add_projecao_row(
        self,
        seq: int,
        ponto: str,
        dx: str,
        dy: str,
        distancia: str,
    ) -> None:
        self._add_row(self.projecoes_table, [str(seq), ponto, dx, dy, distancia])

    def add_coordenada_row(
        self,
        seq: int,
        ponto: str,
        x: str,
        y: str,
        x_corrigido: str,
        y_corrigido: str,
    ) -> None:
        self._add_row(
            self.coordenadas_table,
            [str(seq), ponto, x, y, x_corrigido, y_corrigido],
        )

    @staticmethod
    def _add_row(table: QTableWidget, values: list[str]) -> None:
        row = table.rowCount()
        table.insertRow(row)
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, column, item)
