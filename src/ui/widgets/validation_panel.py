from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QStyle,
)
from core.validation.validation_result import ValidationLevel, ValidationMessage


class ValidationPanel(QWidget):
    """Painel de exibição das mensagens de validação do projeto."""
    
    # Sinal emitido ao clicar em uma mensagem, passando (vertex_index, field_name)
    message_clicked = Signal(int, str)
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        self.table = QTableWidget(0, 3, self)
        self.table.setHorizontalHeaderLabels(["Tipo", "Mensagem", "Vértice/Campo"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemClicked.connect(self._on_item_clicked)
        self.table.itemDoubleClicked.connect(self._on_item_clicked)
        
        # Make row height 3 times larger to display all text comfortably, and enable word wrap
        self.table.setWordWrap(True)
        v_header = self.table.verticalHeader()
        v_header.setDefaultSectionSize(v_header.defaultSectionSize() * 3)
        
        layout.addWidget(self.table)
        
        self.messages_data: list[tuple[int | None, str | None]] = []
        
    def update_messages(self, messages: list[ValidationMessage]) -> None:
        self.table.setRowCount(0)
        self.messages_data = []
        
        for msg in messages:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # 1. Type / Icon
            type_item = QTableWidgetItem(msg.level.value)
            type_item.setTextAlignment(Qt.AlignCenter)
            
            # Apply QStyle standard icons and color coding
            style = self.style()
            if msg.level == ValidationLevel.ERROR:
                type_item.setIcon(style.standardIcon(QStyle.SP_MessageBoxCritical))
                type_item.setForeground(QColor("#d32f2f"))
            elif msg.level == ValidationLevel.WARNING:
                type_item.setIcon(style.standardIcon(QStyle.SP_MessageBoxWarning))
                type_item.setForeground(QColor("#f57c00"))
            else:
                type_item.setIcon(style.standardIcon(QStyle.SP_MessageBoxInformation))
                type_item.setForeground(QColor("#1976d2"))
                
            self.table.setItem(row, 0, type_item)
            
            # 2. Message
            msg_item = QTableWidgetItem(msg.message)
            msg_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.table.setItem(row, 1, msg_item)
            
            # 3. Vertex / Field info
            field_info = ""
            if msg.vertex_index is not None:
                field_info = f"Vértice #{msg.vertex_index + 1}"
                if msg.field:
                    field_info += f" / {msg.field.capitalize()}"
            elif msg.field:
                field_info = msg.field.capitalize()
            else:
                field_info = "-"
                
            info_item = QTableWidgetItem(field_info)
            info_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, info_item)
            
            # Save data mapping
            self.messages_data.append((msg.vertex_index, msg.field))
            
        self.table.resizeColumnToContents(0)
        self.table.resizeColumnToContents(2)
        
    def _on_item_clicked(self, item: QTableWidgetItem) -> None:
        row = item.row()
        if 0 <= row < len(self.messages_data):
            v_idx, field = self.messages_data[row]
            if v_idx is not None:
                self.message_clicked.emit(v_idx, field or "")
