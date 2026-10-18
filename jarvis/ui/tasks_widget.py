"""
Tasks and Reminders Widget for JARVIS.
Displays to-do items, reminders, priorities, and allows quick creation & completion.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QPushButton,
    QLabel, QComboBox, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt, Slot
from jarvis.tools.tasks_manager import task_manager
from jarvis.core.events import bus


class TasksWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_filter = "pending"
        self._init_ui()
        self.load_tasks()

        bus.tasks_changed.connect(self.load_tasks)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header info
        hdr_layout = QHBoxLayout()
        title = QLabel("📋 Tasks & Reminders")
        title.setObjectName("title_label")
        subtitle = QLabel("Manage your daily plans, interview prep items, and reminders.")
        subtitle.setObjectName("subtitle_label")
        v_title = QVBoxLayout()
        v_title.addWidget(title)
        v_title.addWidget(subtitle)
        hdr_layout.addLayout(v_title)
        hdr_layout.addStretch()
        layout.addLayout(hdr_layout)

        # Quick Add Bar
        add_layout = QHBoxLayout()
        add_layout.setSpacing(8)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Task description (e.g. 'Revise binary tree algorithms')...")
        add_layout.addWidget(self.title_input, stretch=2)

        self.due_input = QLineEdit()
        self.due_input.setPlaceholderText("Due (e.g. 'Tomorrow', '5 PM')...")
        self.due_input.setFixedWidth(140)
        add_layout.addWidget(self.due_input)

        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Normal", "High", "Low"])
        self.priority_combo.setFixedWidth(100)
        add_layout.addWidget(self.priority_combo)

        add_btn = QPushButton("➕ Add Task")
        add_btn.setObjectName("primary_button")
        add_btn.clicked.connect(self._add_task)
        add_layout.addWidget(add_btn)

        layout.addLayout(add_layout)

        # Filter bar
        filter_layout = QHBoxLayout()
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Pending Only", "All Tasks", "Completed Only"])
        self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("Filter:"))
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()

        del_btn = QPushButton("🗑️ Delete Selected")
        del_btn.clicked.connect(self._delete_selected)
        filter_layout.addWidget(del_btn)

        layout.addLayout(filter_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Done", "ID", "Task Title", "Due Date", "Priority"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.table)

    def _on_filter_changed(self, text: str):
        if "Pending" in text:
            self.current_filter = "pending"
        elif "Completed" in text:
            self.current_filter = "completed"
        else:
            self.current_filter = None
        self.load_tasks()

    def load_tasks(self):
        tasks = task_manager.list_tasks(status=self.current_filter)
        self.table.setRowCount(len(tasks))

        for row, t in enumerate(tasks):
            # Checkbox
            chk = QCheckBox()
            is_done = t["status"] == "completed"
            chk.setChecked(is_done)
            chk.setEnabled(not is_done)
            chk.stateChanged.connect(lambda state, tid=t["id"]: self._on_task_checked(tid, state))
            self.table.setCellWidget(row, 0, chk)

            self.table.setItem(row, 1, QTableWidgetItem(str(t["id"])))
            self.table.setItem(row, 2, QTableWidgetItem(t["title"]))
            self.table.setItem(row, 3, QTableWidgetItem(t["due_date"] or "—"))
            self.table.setItem(row, 4, QTableWidgetItem(t["priority"].capitalize()))

    def _on_task_checked(self, task_id: int, state: int):
        if state == Qt.CheckState.Checked.value or state == 2:
            task_manager.complete_task(task_id)
            self.load_tasks()

    def _add_task(self):
        title = self.title_input.text().strip()
        if not title:
            return

        due = self.due_input.text().strip()
        prio = self.priority_combo.currentText().lower()
        task_manager.add_task(title=title, due_date=due, priority=prio)

        self.title_input.clear()
        self.due_input.clear()
        self.load_tasks()

    def _delete_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select Task", "Please select a task to delete.")
            return

        task_id = int(self.table.item(row, 1).text())
        if task_manager.delete_task(task_id):
            self.load_tasks()
