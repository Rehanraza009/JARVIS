"""
Memory & Profile Management Widget for JARVIS.
Allows inspecting, searching, adding, editing, deleting, exporting, and importing memories.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QPushButton,
    QLabel, QMessageBox, QDialog, QFormLayout, QComboBox,
    QFileDialog
)
from PySide6.QtCore import Qt, Slot
from jarvis.memory.memory_service import memory_service
from jarvis.core.events import bus


class MemoryDialog(QDialog):
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Save Personal Memory" if not initial_data else "Edit Memory")
        self.setFixedWidth(400)
        self.initial_data = initial_data

        layout = QFormLayout(self)

        self.category_box = QComboBox()
        self.category_box.addItems(["personal", "goal", "career", "project", "preference", "fact"])

        self.key_input = QLineEdit()
        self.content_input = QLineEdit()

        if initial_data:
            idx = self.category_box.findText(initial_data.get("category", "personal"))
            if idx >= 0:
                self.category_box.setCurrentIndex(idx)
            self.key_input.setText(initial_data.get("key", ""))
            self.content_input.setText(initial_data.get("content", ""))

        layout.addRow("Category:", self.category_box)
        layout.addRow("Short Key/Topic:", self.key_input)
        layout.addRow("Memory Content:", self.content_input)

        btn_box = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setObjectName("primary_button")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_box.addStretch()
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(save_btn)
        layout.addRow(btn_box)

    def get_data(self):
        return {
            "category": self.category_box.currentText(),
            "key": self.key_input.text().strip(),
            "content": self.content_input.text().strip()
        }


class MemoryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.load_memories()

        bus.memory_changed.connect(self.load_memories)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header info
        hdr_layout = QHBoxLayout()
        title = QLabel("🧠 Approved Personal Memories")
        title.setObjectName("title_label")
        subtitle = QLabel("User-controlled memory facts about Rehan Raza. Fully auditable & editable.")
        subtitle.setObjectName("subtitle_label")
        v_title = QVBoxLayout()
        v_title.addWidget(title)
        v_title.addWidget(subtitle)
        hdr_layout.addLayout(v_title)
        hdr_layout.addStretch()
        layout.addLayout(hdr_layout)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search saved memories by keyword...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)

        add_btn = QPushButton("➕ Add Memory")
        add_btn.setObjectName("primary_button")
        add_btn.clicked.connect(self._add_memory)
        search_layout.addWidget(add_btn)

        layout.addLayout(search_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Category", "Topic Key", "Remembered Fact", "Last Updated"])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.table)

        # Bottom Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        edit_btn = QPushButton("✏️ Edit Selected")
        edit_btn.clicked.connect(self._edit_selected)
        btn_layout.addWidget(edit_btn)

        del_btn = QPushButton("🗑️ Delete Selected")
        del_btn.clicked.connect(self._delete_selected)
        btn_layout.addWidget(del_btn)

        wipe_btn = QPushButton("🧹 Wipe All Memories")
        wipe_btn.setObjectName("stop_button")
        wipe_btn.clicked.connect(self._wipe_all)
        btn_layout.addWidget(wipe_btn)

        btn_layout.addStretch()

        export_btn = QPushButton("📤 Export JSON")
        export_btn.clicked.connect(self._export_json)
        btn_layout.addWidget(export_btn)

        import_btn = QPushButton("📥 Import JSON")
        import_btn.clicked.connect(self._import_json)
        btn_layout.addWidget(import_btn)

        layout.addLayout(btn_layout)

    def load_memories(self, memories=None):
        if memories is None:
            memories = memory_service.list_memories()

        self.table.setRowCount(len(memories))
        for row, item in enumerate(memories):
            self.table.setItem(row, 0, QTableWidgetItem(str(item["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(item["category"].capitalize()))
            self.table.setItem(row, 2, QTableWidgetItem(item["key"]))
            self.table.setItem(row, 3, QTableWidgetItem(item["content"]))
            self.table.setItem(row, 4, QTableWidgetItem(str(item["updated_at"])[:16]))

    def _on_search_changed(self, text: str):
        if not text.strip():
            self.load_memories()
        else:
            results = memory_service.search_memories(text, limit=50)
            self.load_memories(results)

    def _add_memory(self):
        dlg = MemoryDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            if data["key"] and data["content"]:
                memory_service.save_memory(
                    category=data["category"],
                    key=data["key"],
                    content=data["content"]
                )
                self.load_memories()

    def _edit_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select Row", "Please select a memory to edit.")
            return

        mem_id = int(self.table.item(row, 0).text())
        item = memory_service.get_memory(mem_id)
        if not item:
            return

        dlg = MemoryDialog(self, initial_data=item)
        if dlg.exec():
            data = dlg.get_data()
            memory_service.update_memory(
                memory_id=mem_id,
                content=data["content"],
                key=data["key"],
                category=data["category"]
            )
            self.load_memories()

    def _delete_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select Row", "Please select a memory to delete.")
            return

        mem_id = int(self.table.item(row, 0).text())
        if memory_service.delete_memory(mem_id):
            self.load_memories()

    def _wipe_all(self):
        reply = QMessageBox.question(
            self,
            "Confirm Wipe All",
            "Are you sure you want to delete all saved memories? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            memory_service.delete_all_memories()
            self.load_memories()

    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Memories", "jarvis_memories.json", "JSON Files (*.json)")
        if path:
            json_data = memory_service.export_memories_json()
            with open(path, "w", encoding="utf-8") as f:
                f.write(json_data)
            QMessageBox.information(self, "Export Success", f"Memories exported to {path}")

    def _import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Memories", "", "JSON Files (*.json)")
        if path:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            count = memory_service.import_memories_json(content)
            self.load_memories()
            QMessageBox.information(self, "Import Success", f"Successfully imported {count} memories.")
