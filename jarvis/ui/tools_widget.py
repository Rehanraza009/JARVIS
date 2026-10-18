"""
System Tools, Quick Launchers, Document Inspector, and Audit Logs Widget.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QFileDialog, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from jarvis.tools.system_tools import system_tools
from jarvis.tools.doc_reader import doc_reader
from jarvis.memory.database import db_manager


class ToolsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.load_audit_logs()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Header
        title = QLabel("⚡ System Tools & Audit Logs")
        title.setObjectName("title_label")
        subtitle = QLabel("Safe desktop automation shortcuts, document reader, and audit trails.")
        subtitle.setObjectName("subtitle_label")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # 1. Quick Launchers Group
        launch_group = QGroupBox("Quick Application & Web Launchers")
        launch_layout = QVBoxLayout(launch_group)

        app_row = QHBoxLayout()
        app_row.addWidget(QLabel("Approved Apps:"))
        for name, label in [
            ("notepad", "📝 Notepad"),
            ("calc", "🔢 Calculator"),
            ("vscode", "💻 VS Code"),
            ("terminal", "⚡ PowerShell"),
            ("explorer", "📁 Explorer")
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, a=name: self._launch_app(a))
            app_row.addWidget(btn)
        app_row.addStretch()
        launch_layout.addLayout(app_row)

        site_row = QHBoxLayout()
        site_row.addWidget(QLabel("Approved Sites:"))
        for site, label in [
            ("github", "🐙 GitHub"),
            ("youtube", "▶️ YouTube"),
            ("chatgpt", "🤖 ChatGPT"),
            ("linkedin", "💼 LinkedIn"),
            ("google", "🌐 Google")
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, s=site: self._launch_site(s))
            site_row.addWidget(btn)
        site_row.addStretch()
        launch_layout.addLayout(site_row)

        layout.addWidget(launch_group)

        # 2. Document Reader Group
        doc_group = QGroupBox("Document & Code Reader")
        doc_layout = QVBoxLayout(doc_group)
        doc_btn_row = QHBoxLayout()

        select_btn = QPushButton("📂 Select File (.py, .pdf, .txt, .md)")
        select_btn.setObjectName("accent_button")
        select_btn.clicked.connect(self._select_document)
        doc_btn_row.addWidget(select_btn)

        self.doc_path_label = QLabel("No file selected.")
        self.doc_path_label.setStyleSheet("color: #94A3B8;")
        doc_btn_row.addWidget(self.doc_path_label, stretch=1)
        doc_layout.addLayout(doc_btn_row)

        self.doc_preview = QTextEdit()
        self.doc_preview.setPlaceholderText("File content preview will appear here...")
        self.doc_preview.setFixedHeight(110)
        self.doc_preview.setReadOnly(True)
        doc_layout.addWidget(self.doc_preview)

        layout.addWidget(doc_group)

        # 3. Activity Audit Log Group
        log_group = QGroupBox("Action Audit Trail (Security & Privacy Log)")
        log_layout = QVBoxLayout(log_group)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(["Timestamp", "Action", "Status", "Details"])
        self.log_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        log_layout.addWidget(self.log_table)

        layout.addWidget(log_group)

    def _launch_app(self, app_name: str):
        system_tools.open_app(app_name)
        self.load_audit_logs()

    def _launch_site(self, site_name: str):
        system_tools.open_website(site_name)
        self.load_audit_logs()

    def _select_document(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Document or Code File",
            "",
            "Supported Files (*.txt *.py *.md *.pdf *.json *.csv);;All Files (*.*)"
        )
        if file_path:
            self.doc_path_label.setText(file_path)
            res = doc_reader.read_file(file_path)
            if res["success"]:
                snippet = res["content"][:2000]
                if len(res["content"]) > 2000:
                    snippet += f"\n\n... [Truncated: Total {len(res['content'])} characters]"
                self.doc_preview.setText(snippet)
            else:
                self.doc_preview.setText(f"Error reading file: {res.get('error')}")

    def load_audit_logs(self):
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT 50")
                rows = cursor.fetchall()

            self.log_table.setRowCount(len(rows))
            for r_idx, r in enumerate(rows):
                self.log_table.setItem(r_idx, 0, QTableWidgetItem(str(r["timestamp"])[:19]))
                self.log_table.setItem(r_idx, 1, QTableWidgetItem(r["action_name"]))
                self.log_table.setItem(r_idx, 2, QTableWidgetItem(r["status"].upper()))
                self.log_table.setItem(r_idx, 3, QTableWidgetItem(r["details"]))
        except Exception:
            pass
