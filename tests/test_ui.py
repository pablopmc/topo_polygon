from __future__ import annotations

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.widgets.results_panel import ResultsPanel


def test_ui_widgets_initialization() -> None:
    app = QApplication.instance() or QApplication([])
    
    panel = ResultsPanel()
    assert panel.tabs.count() == 7
    assert panel.tabs.tabText(0) == "Vértices"
    assert panel.tabs.tabText(1) == "Ângulos"
    assert panel.tabs.tabText(6) == "Validação"
    
    # Assert summary table structure
    assert panel.summary_table.rowCount() == 8
    assert panel.summary_table.columnCount() == 2
    assert panel.summary_table.item(0, 0).text() == "Área (m²)"
    assert panel.summary_table.item(3, 0).text() == "Precisão"

    
    window = MainWindow()
    assert window.windowTitle() == "TopoCalc"
    assert window.results_panel.tabs.tabText(0) == "Vértices"
