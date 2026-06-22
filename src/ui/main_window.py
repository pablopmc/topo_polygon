from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QAction, QPainter, QIcon, QColor, QFont, QPainterPath, QPen, QBrush
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QMainWindow,
    QMenuBar,
    QStatusBar,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QGraphicsScene,
    QGraphicsView,
    QLabel,
    QFileDialog,
    QMessageBox,
    QLineEdit,
    QTextEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QDateEdit,
    QStyle,
    QTextBrowser,
    QTabWidget,
    QRadioButton,
    QButtonGroup,
    QCheckBox,
    QGridLayout,
)

from dataclasses import asdict
from ui.widgets.results_panel import ResultsPanel
from core.reports.exporter_registry import ExporterRegistry
import core.reports.csv_export
import core.reports.dxf_export
import core.reports.excel_report
import core.reports.geojson_export
import core.reports.kml_export
import core.reports.pdf_report
import core.reports.shp_export
from controllers import ProjectController
from models import Configuration



class AzimuteInicialDialog(QDialog):
    """Diálogo modal para entrada e edição do Azimute Inicial (GMS)"""
    def __init__(self, current_g: int = 0, current_m: int = 0, current_s: float = 0.0, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Azimute Inicial")
        self.resize(300, 130)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.az_g_edit = QLineEdit(self)
        self.az_m_edit = QLineEdit(self)
        self.az_s_edit = QLineEdit(self)

        self.az_g_edit.setPlaceholderText("G")
        self.az_m_edit.setPlaceholderText("M")
        self.az_s_edit.setPlaceholderText("S")

        self.az_g_edit.setText(str(abs(current_g)))
        self.az_m_edit.setText(str(current_m))
        self.az_s_edit.setText(f"{current_s:.2f}")

        self.az_g_edit.setMaximumWidth(60)
        self.az_m_edit.setMaximumWidth(60)
        self.az_s_edit.setMaximumWidth(80)

        az_gms_layout = QHBoxLayout()
        az_gms_layout.addWidget(self.az_g_edit)
        az_gms_layout.addWidget(QLabel("°"))
        az_gms_layout.addWidget(self.az_m_edit)
        az_gms_layout.addWidget(QLabel("'"))
        az_gms_layout.addWidget(self.az_s_edit)
        az_gms_layout.addWidget(QLabel('"'))
        az_gms_layout.addStretch()

        form_layout.addRow("Azimute Inicial (V1 → V2):", az_gms_layout)
        layout.addLayout(form_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_values(self) -> tuple[int, int, float]:
        try:
            g = int(self.az_g_edit.text().strip() or 0)
            m = int(self.az_m_edit.text().strip() or 0)
            s = float(self.az_s_edit.text().strip().replace(",", ".") or 0.0)
            return g, m, s
        except ValueError as exc:
            raise ValueError("Os valores do azimute inicial devem ser numéricos.") from exc


class VertexDialog(QDialog):
    """Diálogo modal para adição e edição de vértices"""
    def __init__(
        self,
        title: str,
        parent=None,
        ponto: str = "",
        g: int = 0,
        m: int = 0,
        s: float = 0.0,
        dist: float = 0.0,
        obs: str = "",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(360, 220)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.point_edit = QLineEdit(self)
        self.point_edit.setText(ponto)

        self.g_edit = QLineEdit(self)
        self.m_edit = QLineEdit(self)
        self.s_edit = QLineEdit(self)

        self.g_edit.setPlaceholderText("G")
        self.m_edit.setPlaceholderText("M")
        self.s_edit.setPlaceholderText("S")

        self.g_edit.setText(str(abs(g)) if ponto else "")
        self.m_edit.setText(str(m) if ponto else "")
        self.s_edit.setText(f"{s:.2f}" if ponto else "")

        self.g_edit.setMaximumWidth(60)
        self.m_edit.setMaximumWidth(60)
        self.s_edit.setMaximumWidth(80)

        gms_layout = QHBoxLayout()
        gms_layout.addWidget(self.g_edit)
        gms_layout.addWidget(QLabel("°"))
        gms_layout.addWidget(self.m_edit)
        gms_layout.addWidget(QLabel("'"))
        gms_layout.addWidget(self.s_edit)
        gms_layout.addWidget(QLabel('"'))
        gms_layout.addStretch()

        self.distance_edit = QLineEdit(self)
        self.distance_edit.setText(f"{dist:.4f}" if ponto else "")

        self.note_edit = QLineEdit(self)
        self.note_edit.setText(obs)

        form_layout.addRow("Ponto:", self.point_edit)
        form_layout.addRow("Ângulo GMS:", gms_layout)
        form_layout.addRow("Distância (m):", self.distance_edit)
        form_layout.addRow("Observação:", self.note_edit)

        layout.addLayout(form_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_values(self) -> dict:
        ponto = self.point_edit.text().strip()
        g_text = self.g_edit.text().strip()
        m_text = self.m_edit.text().strip()
        s_text = self.s_edit.text().strip()
        dist_text = self.distance_edit.text().strip()
        obs = self.note_edit.text().strip()

        if not ponto:
            raise ValueError("O campo Ponto é obrigatório.")
        if not g_text or not m_text or not s_text:
            raise ValueError("O ângulo GMS deve ser totalmente informado.")
        if not dist_text:
            raise ValueError("O campo Distância é obrigatório.")

        try:
            g = int(g_text)
            m = int(m_text)
            s = float(s_text.replace(",", "."))
            dist = float(dist_text.replace(",", "."))
        except ValueError as exc:
            raise ValueError("Os campos de ângulo e distância devem ser numéricos.") from exc

        if m < 0 or m >= 60 or s < 0 or s >= 60:
            raise ValueError("Minutos e segundos devem estar entre 0 e 59.")
        if dist < 0:
            raise ValueError("A distância não pode ser negativa.")

        return {
            "ponto": ponto,
            "graus": g,
            "minutos": m,
            "segundos": s,
            "distancia": dist,
            "observacao": obs,
        }


class ProjectIdentificationDialog(QDialog):
    """Diálogo modal para identificação do projeto"""
    def __init__(self, parent=None, initial_values: dict | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Identificação do Projeto")
        self.resize(450, 420)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        initial = initial_values or {}

        self.name_edit = QLineEdit(self)
        self.name_edit.setText(initial.get("name") or "Novo Projeto")

        self.client_edit = QLineEdit(self)
        self.client_edit.setText(initial.get("client") or "")

        self.location_edit = QLineEdit(self)
        self.location_edit.setText(initial.get("location") or "")

        self.institution_edit = QLineEdit(self)
        self.institution_edit.setText(initial.get("institution") or "")

        self.surveyor_edit = QLineEdit(self)
        self.surveyor_edit.setText(initial.get("surveyor") or initial.get("author") or "")

        self.date_edit = QDateEdit(self)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        
        date_val = initial.get("survey_date") or initial.get("created_at")
        if date_val:
            try:
                qd = QDate.fromString(date_val[:10], "yyyy-MM-dd")
                if qd.isValid():
                    self.date_edit.setDate(qd)
                else:
                    self.date_edit.setDate(QDate.currentDate())
            except Exception:
                self.date_edit.setDate(QDate.currentDate())
        else:
            self.date_edit.setDate(QDate.currentDate())

        self.coord_system_edit = QLineEdit(self)
        self.coord_system_edit.setText(initial.get("coordinate_system") or "")

        self.ref_point_edit = QLineEdit(self)
        self.ref_point_edit.setText(initial.get("reference_point") or "")

        self.desc_edit = QTextEdit(self)
        self.desc_edit.setTabChangesFocus(True)
        desc_val = initial.get("survey_description") or initial.get("description") or ""
        self.desc_edit.setPlainText(desc_val)

        form.addRow("Nome do Projeto:", self.name_edit)
        form.addRow("Contratante/Cliente:", self.client_edit)
        form.addRow("Localidade/Endereço:", self.location_edit)
        form.addRow("Instituição:", self.institution_edit)
        form.addRow("Responsável:", self.surveyor_edit)
        form.addRow("Data:", self.date_edit)
        form.addRow("Sistema de Coordenadas:", self.coord_system_edit)
        form.addRow("Ponto de Referência (Datum):", self.ref_point_edit)
        form.addRow("Descrição/Observações:", self.desc_edit)

        layout.addLayout(form)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_values(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "client": self.client_edit.text().strip(),
            "location": self.location_edit.text().strip(),
            "institution": self.institution_edit.text().strip(),
            "surveyor": self.surveyor_edit.text().strip(),
            "survey_date": self.date_edit.date().toString("yyyy-MM-dd"),
            "coordinate_system": self.coord_system_edit.text().strip(),
            "reference_point": self.ref_point_edit.text().strip(),
            "survey_description": self.desc_edit.toPlainText().strip(),
        }


class PDFExportDialog(QDialog):
    """Diálogo modal para seleção de template PDF e campos personalizáveis"""
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Exportar Relatório PDF")
        self.resize(460, 430)

        layout = QVBoxLayout(self)

        # 1. Grupo de Modelos (Templates)
        group_template = QGroupBox("Modelo de Relatório", self)
        layout_temp = QVBoxLayout(group_template)
        
        self.radio_a3 = QRadioButton("Relatório A3 Paisagem (Preservar original)", self)
        self.radio_a4 = QRadioButton("Relatório A4 Retrato (Novo)", self)
        self.radio_a3.setChecked(True)
        
        self.btn_group = QButtonGroup(self)
        self.btn_group.addButton(self.radio_a3)
        self.btn_group.addButton(self.radio_a4)

        layout_temp.addWidget(self.radio_a3)
        layout_temp.addWidget(self.radio_a4)
        layout.addWidget(group_template)

        # 2. Grupo de Campos Personalizáveis
        group_fields = QGroupBox("Campos para Exportação", self)
        layout_fields = QGridLayout(group_fields)

        self.checkboxes = {}
        fields = [
            "Dados do projeto",
            "Vértices",
            "Distâncias",
            "Ângulos",
            "Azimutes",
            "Rumos",
            "Projeções",
            "Coordenadas",
            "Fechamento Angular",
            "Fechamento Linear",
            "Ajuste Bowditch",
            "Área",
            "Perímetro",
            "Gráfico da Poligonal",
        ]
        
        for index, field in enumerate(fields):
            cb = QCheckBox(field, self)
            cb.setChecked(True)
            row = index // 2
            col = index % 2
            layout_fields.addWidget(cb, row, col)
            self.checkboxes[field] = cb

        layout.addWidget(group_fields)

        # 3. Botões
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.button(QDialogButtonBox.Ok).setText("Exportar")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_values(self) -> tuple[str, dict[str, bool]]:
        template_id = "A3_LANDSCAPE" if self.radio_a3.isChecked() else "A4_PORTRAIT"
        selected_fields = {name: cb.isChecked() for name, cb in self.checkboxes.items()}
        return template_id, selected_fields


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("TopoCalc")
        self.resize(1400, 900)

        # Define window icon with fallback support (development and PyInstaller build)
        import sys
        if hasattr(sys, "_MEIPASS"):
            icon_path = Path(sys._MEIPASS) / "icone.ico"
        else:
            icon_path = Path(__file__).parent.parent / "icone.ico"
            
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.controller = ProjectController()
        self.current_file: Path | None = None
        self.highlighted_vertex_idx: int | None = None

        self._create_actions()
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_central_widget()
        self._create_status_bar()
        self._connect_actions()

    def _create_actions(self) -> None:
        self.action_new = QAction("Novo", self)
        self.action_open = QAction("Abrir", self)
        self.action_import_data = QAction("Importar CSV/Excel", self)
        self.action_save = QAction("Salvar", self)
        self.action_save_as = QAction("Salvar como", self)
        self.action_exit = QAction("Sair", self)

        self.action_edit_project = QAction("Editar Projeto", self)
        self.action_calculate = QAction("Calcular", self)

        self.action_undo = QAction("Desfazer", self)
        self.action_redo = QAction("Refazer", self)

        # Ações de exportação dinâmicas e ordenadas alfabeticamente
        self.export_actions = {}
        for fmt in ExporterRegistry.list_formats():
            action = QAction(f"{fmt['display_name']}", self)
            icon_attr = getattr(QStyle, fmt["icon_name"], None)
            if icon_attr is not None:
                action.setIcon(self.style().standardIcon(icon_attr))
            else:
                action.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
            
            # Vinculação tardia usando argumento padrão
            action.triggered.connect(
                lambda checked=False, f_id=fmt["format_id"]: self._on_export_format(f_id)
            )
            self.export_actions[fmt["format_id"]] = action

        self.action_how_to_use = QAction("Como Utilizar", self)
        self.action_about = QAction("Sobre", self)
        self.action_exit.triggered.connect(self.close)

        # Apply native standard QStyle icons for visual excellence
        self.action_new.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        self.action_open.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.action_import_data.setIcon(self.style().standardIcon(QStyle.SP_ArrowDown))
        self.action_save.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.action_save_as.setIcon(self.style().standardIcon(QStyle.SP_DriveHDIcon))
        self.action_calculate.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.action_how_to_use.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxQuestion))
        self.action_about.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))

    def _connect_actions(self) -> None:
        """Conecta as ações aos métodos correspondentes"""
        self.action_new.triggered.connect(self._on_new_project)
        self.action_open.triggered.connect(self._on_open_project)
        self.action_import_data.triggered.connect(self._on_import_data)
        self.action_save.triggered.connect(self._on_save_project)
        self.action_save_as.triggered.connect(self._on_save_as_project)
        self.action_edit_project.triggered.connect(self._on_edit_project)
        self.action_calculate.triggered.connect(self._on_calculate)
        self.action_how_to_use.triggered.connect(self._on_how_to_use)
        self.action_about.triggered.connect(self._on_about)

        # Connect new ResultsPanel signals for modal layout actions
        self.results_panel.add_vertex_requested.connect(self._on_add_vertex_clicked)
        self.results_panel.edit_vertex_requested.connect(self._on_edit_vertex_clicked)
        self.results_panel.delete_vertex_requested.connect(self._on_delete_vertex_clicked)
        self.results_panel.add_azimuth_requested.connect(self._on_add_azimuth_clicked)
        self.results_panel.validation_tab.message_clicked.connect(self._on_validation_message_clicked)

    def _create_menu_bar(self) -> None:
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        menu_file = menu_bar.addMenu("Arquivo")
        menu_file.addAction(self.action_new)
        menu_file.addAction(self.action_open)
        menu_file.addAction(self.action_import_data)
        menu_file.addAction(self.action_save)
        menu_file.addAction(self.action_save_as)
        menu_file.addAction(self.action_edit_project)
        menu_file.addSeparator()
        menu_file.addAction(self.action_exit)

        menu_edit = menu_bar.addMenu("Editar")
        menu_edit.addAction(self.action_undo)
        menu_edit.addAction(self.action_redo)

        menu_export = menu_bar.addMenu("Exportar")
        for fmt in ExporterRegistry.list_formats():
            menu_export.addAction(self.export_actions[fmt["format_id"]])

        menu_help = menu_bar.addMenu("Ajuda")
        menu_help.addAction(self.action_how_to_use)
        menu_help.addAction(self.action_about)

    def _create_tool_bar(self) -> None:
        tool_bar = QToolBar("Principal", self)
        tool_bar.setMovable(False)
        tool_bar.setIconSize(QSize(36, 36)) # ícones maiores (36x36 pixels para área visual excelente)
        tool_bar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon) # texto centralizado abaixo do ícone
        self.addToolBar(Qt.TopToolBarArea, tool_bar)

        tool_bar.addAction(self.action_new)
        tool_bar.addAction(self.action_open)
        tool_bar.addAction(self.action_import_data)
        tool_bar.addAction(self.action_save)
        tool_bar.addAction(self.action_save_as)
        tool_bar.addAction(self.action_calculate)
        tool_bar.addSeparator()
        for fmt in ExporterRegistry.list_formats():
            tool_bar.addAction(self.export_actions[fmt["format_id"]])

    def _create_central_widget(self) -> None:
        central_widget = QWidget(self)
        central_layout = QHBoxLayout(central_widget)
        central_layout.setContentsMargins(8, 8, 8, 8)
        central_layout.setSpacing(10)

        # Left Column: QGroupBox occupying full height and width for QGraphicsView/Scene
        drawing_group = QGroupBox("Área de Desenho", self)
        drawing_layout = QVBoxLayout(drawing_group)
        drawing_layout.setContentsMargins(6, 6, 6, 6)

        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(Qt.white)
        self.drawing_view = QGraphicsView(self.scene, self)
        self.drawing_view.setRenderHints(
            self.drawing_view.renderHints()
            | QPainter.Antialiasing
            | QPainter.SmoothPixmapTransform
        )
        drawing_layout.addWidget(self.drawing_view)

        self.drawing_hint = QLabel("Defina o Azimute Inicial e adicione vértices para desenhar.", self)
        self.drawing_hint.setAlignment(Qt.AlignCenter)
        drawing_layout.addWidget(self.drawing_hint)

        self.results_panel = ResultsPanel(self)

        # Splitter to allow responsive dividing of the Drawing Area and the Results Panel
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(drawing_group)
        splitter.addWidget(self.results_panel)
        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 4)

        central_layout.addWidget(splitter)
        self.setCentralWidget(central_widget)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # Responsive auto-fitting of drawing path
        self._fit_drawing_in_view()

    def _fit_drawing_in_view(self) -> None:
        rect = self.scene.itemsBoundingRect()
        if not rect.isEmpty():
            padding = 40.0
            rect.adjust(-padding, -padding, padding, padding)
            self.drawing_view.fitInView(rect, Qt.KeepAspectRatio)

    def _on_new_project(self) -> None:
        """Cria um novo projeto"""
        try:
            dialog = ProjectIdentificationDialog(self)
            if dialog.exec() != QDialog.Accepted:
                return

            vals = dialog.get_values()

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Novo Projeto",
                "",
                "Arquivos TOPO (*.topo)"
            )
            if not file_path:
                return

            pid = self.controller.novo_projeto(
                file_path,
                name=vals["name"],
                description=vals["survey_description"],
                author=vals["surveyor"],
                coordinate_system=vals["coordinate_system"],
                reference_point=vals["reference_point"],
            )

            # Persist configurations
            if self.controller.current_db is not None:
                config_vals = {
                    "institution": vals["institution"],
                    "surveyor": vals["surveyor"],
                    "survey_date": vals["survey_date"],
                    "survey_description": vals["survey_description"],
                    "client": vals["client"],
                    "location": vals["location"],
                }
                for k, v in config_vals.items():
                    cfg = Configuration(project_id=pid, key=k, value=v)
                    self.controller.current_db.set_configuration(cfg)

            self.current_file = Path(file_path)
            self.setWindowTitle(f"TopoCalc - {self.current_file.name}")
            self.statusBar().showMessage("Novo projeto criado")
            
            # Clear UI tables and redraw
            self.results_panel.clear_vertices_table()
            self._refresh_vertices_ui()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao criar projeto: {str(e)}")

    def _on_open_project(self) -> None:
        """Abre um projeto existente"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Abrir Projeto",
                "",
                "Arquivos TOPO (*.topo)"
            )
            if not file_path:
                return

            self.controller.abrir_projeto(file_path)
            self.current_file = Path(file_path)
            self.setWindowTitle(f"TopoCalc - {self.current_file.name}")
            self.statusBar().showMessage("Projeto aberto")

            self._refresh_vertices_ui()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir projeto: {str(e)}")

    def _on_import_data(self) -> None:
        """Importa vertices de CSV/Excel substituindo a tabela atual."""
        if self.controller.current_project is None or self.controller.current_db is None:
            QMessageBox.warning(self, "Aviso", "Abra ou crie um projeto antes de importar dados.")
            return

        answer = QMessageBox.question(
            self,
            "Importar dados",
            "A importação vai substituir os vértices atuais. Deseja continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar CSV/Excel",
            "",
            "Arquivos suportados (*.csv *.xlsx *.xlsm)",
        )
        if not file_path:
            return

        try:
            self.controller.importar_vertices(file_path, substituir=True)
            self._refresh_vertices_ui()
            self.statusBar().showMessage("Dados importados com sucesso")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao importar dados: {str(e)}")

    def _on_save_project(self) -> None:
        """Salva o projeto atual"""
        try:
            if self.current_file is None:
                self._on_save_as_project()
            else:
                self.controller.salvar_projeto()
                self.statusBar().showMessage("Projeto salvo")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar projeto: {str(e)}")

    def _on_save_as_project(self) -> None:
        """Salva o projeto em um novo local"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Projeto Como",
                "",
                "Arquivos TOPO (*.topo)"
            )
            if not file_path:
                return

            self.controller.salvar_como(file_path)
            self.current_file = Path(file_path)
            self.setWindowTitle(f"TopoCalc - {self.current_file.name}")
            self.statusBar().showMessage("Projeto salvo como")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar projeto: {str(e)}")

    def _on_export_format(self, format_id: str) -> None:
        """Handler unificado para todas as exportações baseado no ExporterRegistry"""
        try:
            # Check validation and block export if there are errors
            if not self._run_validation():
                self.results_panel.tabs.setCurrentWidget(self.results_panel.validation_tab)
                QMessageBox.critical(
                    self,
                    "Erro de Validação",
                    "A exportação foi bloqueada devido a erros de consistência no projeto. Verifique a aba 'Validação'."
                )
                return

            if not self.controller.last_calculation:
                QMessageBox.warning(self, "Aviso", "Nenhum cálculo disponível para exportar")
                return

            info = ExporterRegistry.get_format_info(format_id)
            
            kwargs = {}
            if format_id == "CSV":
                dialog = QDialog(self)
                dialog.setWindowTitle("Separador CSV")
                dialog.resize(260, 120)
                layout = QVBoxLayout(dialog)
                
                label = QLabel("Escolha o separador de colunas:", dialog)
                layout.addWidget(label)
                
                radio_comma = QRadioButton("Vírgula ( , )", dialog)
                radio_semi = QRadioButton("Ponto e Vírgula ( ; )", dialog)
                radio_semi.setChecked(True)
                
                btn_group = QButtonGroup(dialog)
                btn_group.addButton(radio_comma)
                btn_group.addButton(radio_semi)
                
                layout.addWidget(radio_comma)
                layout.addWidget(radio_semi)
                
                buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)
                
                if dialog.exec() != QDialog.Accepted:
                    return
                
                kwargs["separator"] = "," if radio_comma.isChecked() else ";"
                
            elif format_id == "PDF":
                dialog = PDFExportDialog(self)
                if dialog.exec() != QDialog.Accepted:
                    return
                template_id, selected_fields = dialog.get_values()
                kwargs["template_id"] = template_id
                kwargs["selected_fields"] = selected_fields

            # Escolher local de salvamento
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                f"Exportar {info['display_name']}",
                info["default_name"],
                info["file_filter"]
            )
            if not file_path:
                return

            resultado = self.controller.last_calculation
            project = self.controller.current_project
            if project is None:
                raise RuntimeError("Nenhum projeto carregado para exportação")

            tabela_final = resultado.tabela_final.to_dict(orient="records") if hasattr(resultado, "tabela_final") else []
            sketch_points = resultado.coordenadas_corrigidas
            
            kwargs["vertices"] = self.controller.current_vertices
            kwargs["resultado"] = resultado

            exporter = ExporterRegistry.get_exporter(format_id)
            exporter.export(
                filename=file_path,
                project=self._get_project_metadata(project),
                calculation_rows=tabela_final,
                coordinates_rows=tabela_final,
                sketch_points=sketch_points,
                area=resultado.area,
                perimeter=resultado.perimetro,
                precision=resultado.precisao,
                **kwargs
            )
            
            self.statusBar().showMessage(f"{info['display_name']} exportado com sucesso")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar {format_id}: {str(e)}")

    def _on_calculate(self) -> None:
        """Trigger calculation and update UI."""
        try:
            if len(self.controller.current_vertices) < 3:
                QMessageBox.warning(self, "Aviso", "Informe ao menos 3 vértices para calcular")
                return

            project = self.controller.current_project
            if project is None:
                return
            
            # Run validation and block calculations if any errors are present
            if not self._run_validation():
                self.results_panel.tabs.setCurrentWidget(self.results_panel.validation_tab)
                QMessageBox.critical(
                    self,
                    "Erro de Validação",
                    "Os cálculos foram bloqueados devido a erros de consistência no projeto. Verifique a aba 'Validação'."
                )
                return
            
            resultado = self.controller.calcular(project.azimute_inicial)
            self._atualizar_resultados(resultado)
            self.statusBar().showMessage("Cálculos executados")
            self._redraw_croqui()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao calcular: {str(e)}")

    def _on_edit_project(self) -> None:
        """Abre o diálogo para editar os metadados do projeto atual"""
        project = self.controller.current_project
        if project is None or self.controller.current_db is None:
            QMessageBox.warning(self, "Aviso", "Abra ou crie um projeto primeiro")
            return

        initial_values = self._get_project_metadata(project)
        dialog = ProjectIdentificationDialog(self, initial_values)
        if dialog.exec() == QDialog.Accepted:
            try:
                vals = dialog.get_values()

                # Update Project table fields
                project.name = vals["name"]
                project.author = vals["surveyor"]
                project.coordinate_system = vals["coordinate_system"]
                project.reference_point = vals["reference_point"]
                project.description = vals["survey_description"]
                self.controller.salvar_projeto()

                # Update Configurations table fields
                pid = project.id
                if pid is not None:
                    config_vals = {
                        "institution": vals["institution"],
                        "surveyor": vals["surveyor"],
                        "survey_date": vals["survey_date"],
                        "survey_description": vals["survey_description"],
                        "client": vals["client"],
                        "location": vals["location"],
                    }
                    for k, v in config_vals.items():
                        cfg = Configuration(project_id=pid, key=k, value=v)
                        self.controller.current_db.set_configuration(cfg)

                if self.current_file:
                    self.setWindowTitle(f"TopoCalc - {self.current_file.name}")
                self.statusBar().showMessage("Identificação do projeto atualizada")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar identificação: {e}")

    def _get_project_metadata(self, project) -> dict:
        """Retorna um dicionário com os campos do projeto mesclados com as configurações salvas."""
        meta = asdict(project)
        # Garantir chaves padrão/de fallback
        for key in ("institution", "surveyor", "survey_date", "survey_description", "client", "location"):
            if key not in meta:
                meta[key] = ""
        if self.controller.current_db is None or project.id is None:
            return meta
        pid = project.id
        try:
            for key in ("institution", "surveyor", "survey_date", "survey_description", "client", "location"):
                cfg = self.controller.current_db.get_configuration(pid, key)
                meta[key] = cfg.value if cfg and cfg.value is not None else ""
        except Exception:
            pass
        return meta

    def _on_validation_message_clicked(self, vertex_index: int, field: str) -> None:
        """Handler para cliques nas mensagens do painel de validação."""
        # 1. Switch to the Vértices tab (index 0)
        self.results_panel.tabs.setCurrentIndex(0)
        
        # 2. Map field name to column index in the table
        col = 0
        if field == "graus":
            col = 1
        elif field == "minutos":
            col = 2
        elif field == "segundos":
            col = 3
        elif field == "distancia":
            col = 4
        elif field == "observacao":
            col = 5
            
        # 3. Focus and select corresponding table cell
        self.results_panel.vertices_table.setCurrentCell(vertex_index, col)
        
        # 4. Highlight the corresponding vertex index in drawing croqui
        self.highlighted_vertex_idx = vertex_index
        self._redraw_croqui()

    def _run_validation(self) -> bool:
        """Executa a validação automática e atualiza a interface. Retorna True se não houver erros."""
        project = self.controller.current_project
        if project is None:
            return True
            
        from core.validation.validator import ProjectValidator
        
        result = ProjectValidator.validate(
            vertices=self.controller.current_vertices,
            azimute_inicial=project.azimute_inicial,
            coordenada_inicial=(0.0, 0.0),
            coordinate_system=project.coordinate_system
        )
        
        self.results_panel.validation_tab.update_messages(result.messages)
        
        return not result.has_errors

    def _on_how_to_use(self) -> None:
        """Abre a aba 'Como Utilizar' do diálogo de Ajuda."""
        self._show_help_dialog(active_tab_index=0)

    def _on_about(self) -> None:
        """Abre a aba 'Sobre' do diálogo de Ajuda."""
        self._show_help_dialog(active_tab_index=1)

    def _show_help_dialog(self, active_tab_index: int) -> None:
        """Abre o diálogo de Ajuda unificado com as abas 'Como Utilizar' e 'Sobre'."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajuda - TopoCalc")
        dialog.resize(800, 600)
        
        # Copiar ícone de MainWindow para a janela de ajuda
        icon = self.windowIcon()
        if not icon.isNull():
            dialog.setWindowIcon(icon)

        tabs = QTabWidget(dialog)

        # Tab 0: Como Utilizar (Manual Completo)
        manual_browser = QTextBrowser(dialog)
        manual_browser.setOpenExternalLinks(True)
        manual_browser.setStyleSheet("background-color: white; color: #1f2937; border: none;")
        manual_browser.setHtml(self._get_how_to_use_html())
        tabs.addTab(manual_browser, "Como Utilizar")

        # Tab 1: Sobre
        about_browser = QTextBrowser(dialog)
        about_browser.setOpenExternalLinks(True)
        about_browser.setStyleSheet("background-color: white; color: #1f2937; border: none;")
        about_browser.setHtml(self._get_about_html())
        tabs.addTab(about_browser, "Sobre")

        tabs.setCurrentIndex(active_tab_index)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok, dialog)
        buttons.accepted.connect(dialog.accept)

        layout = QVBoxLayout(dialog)
        layout.addWidget(tabs)
        layout.addWidget(buttons)

        dialog.exec()

    def _get_about_html(self) -> str:
        return """
        <div style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #ffffff; color: #1f2937; line-height: 1.6; padding: 10px;">
            <h2 style="color: #1a2b4c; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; margin-top: 0;">
                Sistema de Topografia Computacional TopoCalc
            </h2>
            <p style="margin: 8px 0;">
                <strong>Release:</strong> Alpha v0.2.0<br/>
                <strong>Data:</strong> 21 de junho de 2026<br/>
                <strong>Autor:</strong> Pablo Medina Camacho<br/>
                <strong>Email:</strong> <a href="mailto:pablo@pablomc.com" style="color: #0d9488; text-decoration: none;">pablo@pablomc.com</a><br/>
                <strong>Curso:</strong> Engenharia Civil Empresarial<br/>
                <strong>Instituição:</strong> Universidade Federal do Rio Grande (FURG)<br/>
                <strong>Linguagem:</strong> Python (PySide6 + bibliotecas científicas)<br/>
                <strong>Licença:</strong> Uso acadêmico e não comercial (similar à CC BY-NC 4.0)
            </p>
            <div style="background-color: #f3f4f6; border-left: 4px solid #0d9488; padding: 12px; margin-top: 16px; border-radius: 4px;">
                <p style="margin: 0; font-style: italic;">
                    "Sistema desenvolvido para cálculos de fechamento topográficos, exclusivo para poligonais fechadas."
                </p>
            </div>
        </div>
        """

    def _get_how_to_use_html(self) -> str:
        return """
        <div style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #ffffff; color: #1f2937; line-height: 1.6; padding: 10px;">
            <h1 style="color: #1a2b4c; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; margin-top: 0;">
                Manual de Utilização - TopoCalc
            </h1>
            
            <p>
                Bem-vindo ao <strong>TopoCalc</strong>, uma ferramenta desenvolvida para agilizar e dar precisão aos seus cálculos de poligonais topográficas. Este manual técnico orienta você sobre a inserção de dados, cálculos, consistência do projeto e exportação de resultados.
            </p>

            <h2 style="color: #0d9488; margin-top: 20px; border-bottom: 1px solid #e5e7eb; padding-bottom: 4px;">
                A) Entrada de Dados
            </h2>
            <ul>
                <li><strong>Inserção de Vértices:</strong> Utilize o painel lateral ou o menu correspondente para adicionar novos vértices. Cada vértice requer um nome identificador único (ex: V1, V2), o ângulo horizontal observado, a distância horizontal entre as estações e, opcionalmente, uma observação de campo.</li>
                <li><strong>Formato de Coordenadas:</strong> O sistema utiliza coordenadas cartesianas planas (Leste/X, Norte/Y). A coordenada inicial do primeiro vértice é arbitrada como (0.0, 0.0) para cálculo interno e propagação relativa de toda a poligonal.</li>
                <li><strong>Inserção de Ângulos (DMS):</strong> Os ângulos de deflexão ou ângulos internos devem ser informados no formato sexagesimal (Graus, Minutos e Segundos). O sistema impõe restrições para minutos e segundos, que devem estar no intervalo de 0 a 59.</li>
            </ul>

            <h2 style="color: #0d9488; margin-top: 20px; border-bottom: 1px solid #e5e7eb; padding-bottom: 4px;">
                B) Cálculos Disponíveis
            </h2>
            <p>O TopoCalc executa de forma automática e integrada as seguintes operações matemáticas:</p>
            <ul>
                <li><strong>Azimutes:</strong> Calculados a partir da orientação inicial (azimute de partida) informada pelo usuário e propagados consecutivamente vértice a vértice.</li>
                <li><strong>Rumos:</strong> Derivados diretamente dos azimutes calculados, apresentando a direção angular do alinhamento em relação aos eixos cardeais acompanhados de seus respectivos quadrantes (NE, SE, SW, NW).</li>
                <li><strong>Projeções Planas (Deltas):</strong> Decomposição trigonométrica dos alinhamentos em coordenadas parciais não corrigidas (Delta X = Distância &times; sen(Azimute) e Delta Y = Distância &times; cos(Azimute)).</li>
                <li><strong>Coordenadas Planimétricas:</strong> Determinação das coordenadas globais acumuladas X (E) e Y (N) para cada vértice a partir do ponto de partida.</li>
                <li><strong>Área pelo Método de Gauss:</strong> Cálculo exato da área de projeção do polígono fechado baseado nas coordenadas cartesianas dos vértices.</li>
                <li><strong>Perímetro:</strong> Somatório de todas as distâncias horizontais dos alinhamentos medidos.</li>
                <li><strong>Erro de Fechamento Angular:</strong> Diferença entre a soma observada dos ângulos internos e a soma teórica calculada por <code>(N - 2) &times; 180&deg;</code>, onde N é o número de vértices.</li>
                <li><strong>Erro de Fechamento Linear:</strong> Distância geométrica de fechamento obtida pela resultante dos desvios lineares acumulados nos eixos X e Y: <code>&radic;(Dx&sup2; + Dy&sup2;)</code>.</li>
                <li><strong>Ajuste pelo Método de Bowditch:</strong> Distribuição compensatória e proporcional do erro de fechamento linear ao longo das distâncias horizontais de cada alinhamento, corrigindo as projeções e gerando coordenadas ajustadas.</li>
            </ul>

            <h2 style="color: #0d9488; margin-top: 20px; border-bottom: 1px solid #e5e7eb; padding-bottom: 4px;">
                C) Formatos de Exportação
            </h2>
            <p>Os dados processados podem ser exportados para diferentes ferramentas profissionais de escritório e GIS:</p>
            <ul>
                <li><strong>CSV:</strong> Exportação tabular em formato simples. Permite escolher o separador de colunas (vírgula ou ponto e vírgula), ideal para importação em planilhas ou bancos de dados personalizados.</li>
                <li><strong>DXF (AutoCAD):</strong> Desenho vetorial bidimensional contendo as linhas da poligonal desenhadas, os marcadores de vértice e os rótulos de nomes dos pontos. Pronto para abertura em softwares CAD.</li>
                <li><strong>Excel (XLSX):</strong> Planilha formatada contendo as abas organizadas com dados de entrada, cálculos de projeções e coordenadas e o resumo estatístico final.</li>
                <li><strong>GeoJSON:</strong> Formato padrão GIS para representação de feições geográficas vetoriais (pontos e linhas), facilitando a integração em softwares como QGIS.</li>
                <li><strong>KML:</strong> Arquivo XML com os vértices e alinhamentos georreferenciados para visualização tridimensional direta no Google Earth.</li>
                <li><strong>Shapefile (SHP):</strong> Formato GIS proprietário composto pelos arquivos auxiliares necessários, exportando as geometrias de pontos e polígonos com tabelas de atributos associadas.</li>
                <li><strong>PDF (Relatório Técnico):</strong> Relatório oficial formatado contendo dados do projeto, tabelas completas de cálculo, fechamentos angulares e lineares e a representação gráfica da poligonal (croqui).</li>
            </ul>

            <h2 style="color: #0d9488; margin-top: 20px; border-bottom: 1px solid #e5e7eb; padding-bottom: 4px;">
                D) Importação de Dados
            </h2>
            <ul>
                <li><strong>Arquivos Suportados:</strong> Planilhas do Excel (<code>.xlsx</code>, <code>.xlsm</code>) ou arquivos de texto delimitados (<code>.csv</code>).</li>
                <li><strong>Formato Esperado:</strong> A tabela deve conter cabeçalhos mapeados com nomes de colunas válidos. O sistema suporta separadores de campo como ponto e vírgula (<code>;</code>) ou vírgula (<code>,</code>) e trata as decimais com pontos ou vírgulas.</li>
                <li><strong>Mapeamento Flexível de Colunas:</strong>
                    <table style="width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 11px;">
                        <thead>
                            <tr style="background-color: #f3f4f6;">
                                <th style="padding: 6px; border: 1px solid #e5e7eb; text-align: left;">Dado</th>
                                <th style="padding: 6px; border: 1px solid #e5e7eb; text-align: left;">Nomes de Colunas Aceitos (Sem acentos / case-insensitive)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="padding: 6px; border: 1px solid #e5e7eb;"><strong>Ponto / Vértice</strong></td>
                                <td style="padding: 6px; border: 1px solid #e5e7eb;">ponto, point, point name, nome do ponto, vertex, vertice, estacao, estação, est, station</td>
                            </tr>
                            <tr style="background-color: #f9fafb;">
                                <td style="padding: 6px; border: 1px solid #e5e7eb;"><strong>Ângulo G/M/S</strong></td>
                                <td style="padding: 6px; border: 1px solid #e5e7eb;">graus/g/grau/deg, minutos/m/min/minutes, segundos/s/sec/seconds</td>
                            </tr>
                            <tr>
                                <td style="padding: 6px; border: 1px solid #e5e7eb;"><strong>Ângulo Decimal</strong></td>
                                <td style="padding: 6px; border: 1px solid #e5e7eb;">angulo decimal, angulo, angulo_decimal, angle_decimal</td>
                            </tr>
                            <tr style="background-color: #f9fafb;">
                                <td style="padding: 6px; border: 1px solid #e5e7eb;"><strong>Distância (m)</strong></td>
                                <td style="padding: 6px; border: 1px solid #e5e7eb;">distancia, distance, distância, comprimento, dist, len, length</td>
                            </tr>
                            <tr>
                                <td style="padding: 6px; border: 1px solid #e5e7eb;"><strong>Observações</strong></td>
                                <td style="padding: 6px; border: 1px solid #e5e7eb;">observacao, observação, notes, nota, comentario, obs, observacoes</td>
                            </tr>
                        </tbody>
                    </table>
                </li>
                <li><strong>Conversão de Arquivos Grandes via Inteligência Artificial:</strong><br/>
                    Caso você possua dados brutos de campo extensos ou em formatos de texto proprietários desordenados, utilize o seguinte prompt em ferramentas de IA (como ChatGPT ou Gemini) para gerar seu CSV de importação instantaneamente:
                    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 10px; margin-top: 5px; border-radius: 4px; font-family: monospace; font-size: 10.5px; white-space: pre-wrap; color: #334155;">
Você é um assistente especialista em topografia. Preciso que converta os dados brutos de campo fornecidos a seguir em um formato CSV limpo estruturado para o software TopoCalc.

Instruções:
1. O delimitador deve ser ponto e vírgula (;).
2. Cabeçalho exato: Ponto;Graus;Minutos;Segundos;Distancia;Observacao
3. Identifique os ângulos e separe-os em Graus, Minutos e Segundos. Se forem decimais, converta-os para GMS.
4. Isole as distâncias horizontais (sem letras ou unidades). Use o ponto (.) como separador decimal para distância e segundos.
5. Retorne APENAS o código do arquivo CSV, sem explicações adicionais ou marcações explicativas.

Dados para converter:
[INSIRA SEUS DADOS AQUI]</div>
                </li>
                <li><strong>Limitações:</strong> A importação substitui todos os dados atuais na tabela de trabalho. Certifique-se de salvar seu projeto atual antes de realizar uma importação.</li>
            </ul>

            <h2 style="color: #0d9488; margin-top: 20px; border-bottom: 1px solid #e5e7eb; padding-bottom: 4px;">
                E) Validação Automática
            </h2>
            <p>O TopoCalc possui um sistema de verificação de consistência em tempo real para evitar erros de digitação e inconsistências físicas:</p>
            <ul>
                <li><strong>Avisos e Erros:</strong> A aba "Validação" exibe mensagens automáticas. <strong>Avisos</strong> apontam inconsistências leves que não impedem a execução (ex: descrição do projeto em branco ou coordenadas sem datum). <strong>Erros</strong> críticos bloqueiam a execução de cálculos e exportações (ex: menos de 3 vértices no polígono, nomes de vértices duplicados, valores de minutos/segundos inválidos ou distâncias negativas).</li>
                <li><strong>Rastreabilidade:</strong> Clique em qualquer mensagem de erro na lista de validação para selecionar automaticamente a célula correspondente na tabela de dados e destacá-la na área de desenho.</li>
            </ul>

            <h2 style="color: #0d9488; margin-top: 20px; border-bottom: 1px solid #e5e7eb; padding-bottom: 4px;">
                F) Relatórios em PDF
            </h2>
            <ul>
                <li><strong>Modelos Disponíveis (A3 vs A4):</strong> O modelo <strong>A4 Retrato</strong> é otimizado para relatórios técnicos encadernados de várias páginas com tabelas de dados verticais claras. O modelo <strong>A3 Paisagem</strong> é ideal para visualização em folha única contendo o desenho da poligonal em escala ampliada e tabelas completas horizontais.</li>
                <li><strong>Seleção de Campos:</strong> Ao exportar para PDF, uma janela permite que você marque quais dados devem constar no documento final, como os dados cadastrais do projeto, tabelas de cálculo, resumo estatístico e o croqui gráfico.</li>
            </ul>

            <h2 style="color: #0d9488; margin-top: 20px; border-bottom: 1px solid #e5e7eb; padding-bottom: 4px;">
                G) Interface e Navegação
            </h2>
            <ul>
                <li><strong>Função dos Botões Principais:</strong>
                    <ul>
                        <li><em>Novo:</em> Cria um novo projeto <code>.topo</code> solicitando dados de identificação e local de salvamento.</li>
                        <li><em>Abrir:</em> Carrega um projeto <code>.topo</code> salvo anteriormente do seu disco.</li>
                        <li><em>Importar CSV/Excel:</em> Importa em lote uma caderneta topográfica externa.</li>
                        <li><em>Salvar / Salvar Como:</em> Salva o projeto no local atual ou sob um novo nome/caminho.</li>
                        <li><em>Calcular:</em> Executa o processamento matemático completo dos dados de entrada.</li>
                        <li><em>Atalhos de Exportação:</em> Botões rápidos no menu e na barra de ferramentas para exportação direta em CSV, DXF, XLSX, GeoJSON, KML, SHP e PDF.</li>
                    </ul>
                </li>
                <li><strong>Navegação entre Abas:</strong> O painel inferior direito possui abas que organizam o fluxo de trabalho:
                    <ul>
                        <li><em>Vértices:</em> Caderneta de entrada para digitação de ângulos e distâncias.</li>
                        <li><em>Ângulos:</em> Exibição dos ângulos horizontais lidos e compensados.</li>
                        <li><em>Azimutes / Rumos:</em> Orientação calculada para cada alinhamento.</li>
                        <li><em>Projeções / Coordenadas:</em> Resultados espaciais e parciais antes e após o ajuste de Bowditch.</li>
                        <li><em>Validação:</em> Relatório de conformidade de integridade do projeto.</li>
                    </ul>
                </li>
            </ul>
        </div>
        """

    def _on_add_azimuth_clicked(self) -> None:
        """Abre o diálogo modal para definir o azimute inicial"""
        project = self.controller.current_project
        if project is None:
            QMessageBox.warning(self, "Aviso", "Abra ou crie um projeto primeiro.")
            return

        from core.calculations.engine import decimal_para_dms
        g, m, s = decimal_para_dms(project.azimute_inicial)

        dialog = AzimuteInicialDialog(g, m, s, self)
        if dialog.exec() == QDialog.Accepted:
            try:
                g_val, m_val, s_val = dialog.get_values()
                from core.calculations.engine import dms_para_graus, normalizar_azimute
                az_inicial = normalizar_azimute(dms_para_graus(g_val, m_val, s_val))

                project.azimute_inicial = az_inicial
                if self.controller.current_db:
                    self.controller.current_db.update_project(project)

                self.statusBar().showMessage(f"Azimute Inicial definido para {g_val}° {m_val}' {s_val:.2f}\"")
                self._refresh_vertices_ui()
            except ValueError as e:
                QMessageBox.warning(self, "Erro", f"Entrada inválida: {str(e)}")

    def _on_add_vertex_clicked(self) -> None:
        """Abre o diálogo modal para adicionar um vértice"""
        if self.controller.current_project is None:
            QMessageBox.warning(self, "Aviso", "Abra ou crie um projeto primeiro.")
            return

        dialog = VertexDialog("Adicionar Vértice", self)
        if dialog.exec() == QDialog.Accepted:
            try:
                dados = dialog.get_values()
                self.controller.adicionar_vertice(
                    ponto=dados["ponto"],
                    graus=dados["graus"],
                    minutos=dados["minutos"],
                    segundos=dados["segundos"],
                    distancia=dados["distancia"],
                    observacao=dados["observacao"],
                )
                self.statusBar().showMessage(f"Vértice '{dados['ponto']}' adicionado.")
                self._refresh_vertices_ui()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao adicionar vértice: {str(e)}")

    def _on_edit_vertex_clicked(self, row: int) -> None:
        """Abre o diálogo modal para editar o vértice selecionado"""
        if row < 0 or row >= len(self.controller.current_vertices):
            return

        v = self.controller.current_vertices[row]
        dialog = VertexDialog(
            "Editar Vértice", self,
            ponto=v.point_name,
            g=v.graus, m=v.minutos, s=v.segundos,
            dist=v.distancia, obs=v.observacao
        )

        if dialog.exec() == QDialog.Accepted:
            try:
                dados = dialog.get_values()
                self.controller.atualizar_vertice(
                    row,
                    ponto=dados["ponto"],
                    graus=dados["graus"],
                    minutos=dados["minutos"],
                    segundos=dados["segundos"],
                    distancia=dados["distancia"],
                    observacao=dados["observacao"],
                )
                self.statusBar().showMessage("Vértice atualizado.")
                self._refresh_vertices_ui()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao atualizar vértice: {str(e)}")

    def _on_delete_vertex_clicked(self, row: int) -> None:
        """Remove o vértice selecionado"""
        if row < 0 or row >= len(self.controller.current_vertices):
            return

        ponto = self.controller.current_vertices[row].point_name
        ans = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Deseja realmente excluir o vértice '{ponto}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans == QMessageBox.Yes:
            try:
                self.controller.excluir_vertice(row)
                self.statusBar().showMessage("Vértice excluído.")
                self._refresh_vertices_ui()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir vértice: {str(e)}")

    def _refresh_vertices_ui(self) -> None:
        """Recarrega a tabela de vértices e atualiza os resultados, se possível."""
        self.results_panel.clear_vertices_table()
        for vertex in self.controller.current_vertices:
            self.results_panel.add_vertex_row(
                vertex.point_name,
                vertex.graus,
                vertex.minutos,
                vertex.segundos,
                vertex.distancia,
                vertex.observacao,
            )

        # Executa cálculo em segundo plano para propagar azimutes e obter coordenadas
        try:
            if self.controller.current_project:
                az_inicial = self.controller.current_project.azimute_inicial
                if len(self.controller.current_vertices) >= 3:
                    resultado = self.controller.calcular(az_inicial)
                    self._atualizar_resultados(resultado)
                else:
                    self.results_panel.clear_tables()
            else:
                self.results_panel.clear_tables()
        except Exception:
            self.results_panel.clear_tables()

        self.highlighted_vertex_idx = None
        self._run_validation()
        self._redraw_croqui()

    def _redraw_croqui(self) -> None:
        """Redesenha em tempo real os pontos, o norte absoluto, e os ângulos internos"""
        self.scene.clear()

        project = self.controller.current_project
        if project is None:
            self.drawing_hint.setVisible(True)
            return

        self.drawing_hint.setVisible(False)
        vertices = self.controller.current_vertices

        # Pens and brushes for custom styling
        pen_line = QPen(QColor("#184a7d"))
        pen_line.setWidthF(2.0)

        brush_vertex = QBrush(QColor("#184a7d"))
        brush_text = QColor("#184a7d")

        # 1. North Arrow at origin (0, 0)
        arrow_length = 40.0
        self.scene.addLine(0, 0, 0, -arrow_length, QPen(QColor("#d32f2f"), 1.8))
        
        # Arrowhead
        arrow_head = QPainterPath()
        arrow_head.moveTo(-4, -arrow_length + 6)
        arrow_head.lineTo(0, -arrow_length)
        arrow_head.lineTo(4, -arrow_length + 6)
        arrow_head.closeSubpath()
        self.scene.addPath(arrow_head, QPen(QColor("#d32f2f"), 1.8), QBrush(QColor("#d32f2f")))

        # Label N
        txt_n = self.scene.addText("N", QFont("Arial", 9, QFont.Bold))
        txt_n.setDefaultTextColor(QColor("#d32f2f"))
        txt_n.setPos(-6, -arrow_length - 18)

        if not vertices:
            self._fit_drawing_in_view()
            return

        # 2. Sequential coordinate propagation
        az_current = project.azimute_inicial
        points = [(0.0, 0.0)]
        azimuths = []

        for i, v in enumerate(vertices):
            az_rad = math.radians(az_current)
            dx = v.distancia * math.sin(az_rad)
            dy = v.distancia * math.cos(az_rad)

            x_prev, y_prev = points[-1]
            points.append((x_prev + dx, y_prev + dy))
            azimuths.append(az_current)

            if i + 1 < len(vertices):
                ang_next = vertices[i + 1].angulo_decimal
                from core.calculations.engine import normalizar_azimute
                az_current = normalizar_azimute(az_current + 180.0 - ang_next)

        # Map to scene coordinates: Y-up maps to Qt's Y-down
        scene_points = [(x, -y) for x, y in points]

        # Draw lines connecting the points
        for i in range(len(scene_points) - 1):
            p1 = scene_points[i]
            p2 = scene_points[i + 1]
            self.scene.addLine(p1[0], p1[1], p2[0], p2[1], pen_line)

        # Draw point markers and point labels
        for i, (sx, sy) in enumerate(scene_points):
            if self.highlighted_vertex_idx is not None and i == self.highlighted_vertex_idx:
                # Highlighted vertex is larger, colored in red
                self.scene.addEllipse(sx - 6.5, sy - 6.5, 13, 13, QPen(QColor("#d32f2f"), 2.0), QBrush(QColor("#ffcdd2")))
            else:
                self.scene.addEllipse(sx - 3.5, sy - 3.5, 7, 7, QPen(QColor("#184a7d"), 1.0), brush_vertex)
            
            label_text = vertices[i].point_name if i < len(vertices) else f"P{i+1}"
            txt_label = self.scene.addText(label_text, QFont("Arial", 8, QFont.Bold))
            txt_label.setDefaultTextColor(brush_text)
            txt_label.setPos(sx + 5, sy - 12)

        # Draw internal angles annotations
        for i in range(1, len(scene_points) - 1):
            p_prev = scene_points[i - 1]
            p_curr = scene_points[i]
            p_next = scene_points[i + 1]

            # Inward and outward vectors from current vertex
            v_in_x = p_prev[0] - p_curr[0]
            v_in_y = p_prev[1] - p_curr[1]
            v_out_x = p_next[0] - p_curr[0]
            v_out_y = p_next[1] - p_curr[1]

            a_in = math.atan2(v_in_y, v_in_x)
            a_out = math.atan2(v_out_y, v_out_x)

            # Bisector direction for labeling
            bisect = (a_in + a_out) / 2.0
            
            # Place the text at a neat offset along the bisector angle
            offset = 16.0
            bx = p_curr[0] + offset * math.cos(bisect)
            by = p_curr[1] + offset * math.sin(bisect)

            v = vertices[i]
            angle_str = f"{v.graus}° {v.minutos:02d}' {v.segundos:02.0f}\""

            txt_ang = self.scene.addText(angle_str, QFont("Arial", 7.5))
            txt_ang.setDefaultTextColor(QColor("#a05a00"))
            txt_ang.setPos(bx - 20, by - 8)

        self._fit_drawing_in_view()

    def _atualizar_resultados(self, resultado) -> None:
        """Atualiza o painel de resultados com os cálculos"""
        self.results_panel.clear_tables()

        for i, (vertex, az, rumo, quad, dx, dy) in enumerate(zip(
            self.controller.current_vertices,
            resultado.azimutes,
            resultado.rumos,
            resultado.quadrantes,
            resultado.deltas_x,
            resultado.deltas_y,
        )):
            seq = i + 1
            self.results_panel.add_angulo_row(
                seq, vertex.point_name,
                str(vertex.graus), str(vertex.minutos), f"{vertex.segundos:.2f}"
            )
            self.results_panel.add_azimute_row(seq, vertex.point_name, f"{az:.4f}")
            self.results_panel.add_rumo_row(seq, vertex.point_name, rumo, quad)
            self.results_panel.add_projecao_row(
                seq, vertex.point_name,
                f"{dx:.4f}", f"{dy:.4f}", f"{vertex.distancia:.4f}"
            )

            if i < len(resultado.coordenadas_corrigidas):
                x, y = resultado.coordenadas_corrigidas[i]
                x_orig, y_orig = resultado.coordenadas[i]
                self.results_panel.add_coordenada_row(
                    seq, vertex.point_name,
                    f"{x_orig:.4f}", f"{y_orig:.4f}",
                    f"{x:.4f}", f"{y:.4f}"
                )

        from core.calculations.engine import _formatar_dms
        prec_val = resultado.precisao
        if prec_val is None:
            prec_str = "N/A"
        elif prec_val == float("inf") or not math.isfinite(prec_val):
            prec_str = "1:∞"
        else:
            prec_str = f"1:{prec_val:,.2f}".replace(",", ".")

        self.results_panel.update_summary(
            area_m2=f"{resultado.area:.4f}",
            area_ha=f"{resultado.area / 10000.0:.6f}",
            perimetro=f"{resultado.perimetro:.4f}",
            precisao=prec_str,
            num_estacoes=str(len(self.controller.current_vertices)),
            erro_linear=f"{resultado.erro_linear:.4f}",
            soma_angulos=_formatar_dms(resultado.soma_observada),
            erro_angular=_formatar_dms(resultado.erro_angular),
        )

    def _create_status_bar(self) -> None:
        status = QStatusBar(self)
        status.showMessage("Pronto")
        self.setStatusBar(status)
