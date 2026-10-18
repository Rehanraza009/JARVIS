"""
Theme and QSS Stylesheet for JARVIS Desktop Application.
Color Palette:
- Deep Navy Background: #0B0F19, #111827
- Surface/Card: #1A2234, #1F293D
- Borders: #2D3748, #374151
- Electric Blue Accents: #00D2FF, #0284C7
- Restrained Purple: #8B5CF6, #7C3AED
- Success: #10B981
- Text Primary: #F9FAFB, Text Secondary: #9CA3AF
"""

DARK_THEME_QSS = """
QMainWindow, QDialog {
    background-color: #0B0F19;
    color: #F9FAFB;
}

QWidget {
    font-family: 'Segoe UI', 'SF Pro Display', -apple-system, sans-serif;
    font-size: 13px;
    color: #F9FAFB;
}

/* Tab Bar */
QTabWidget::pane {
    border: 1px solid #1F293D;
    background-color: #0F172A;
    border-radius: 8px;
    padding: 6px;
}

QTabBar::tab {
    background-color: #111827;
    color: #9CA3AF;
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background-color: #1F293D;
    color: #00D2FF;
    border-bottom: 2px solid #00D2FF;
}

QTabBar::tab:hover:!selected {
    background-color: #1A2234;
    color: #E5E7EB;
}

/* Buttons */
QPushButton {
    background-color: #1E293B;
    color: #F9FAFB;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #2E3C54;
    border-color: #00D2FF;
    color: #00D2FF;
}

QPushButton:pressed {
    background-color: #0F172A;
}

QPushButton#primary_button {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284C7, stop:1 #00D2FF);
    color: #0B0F19;
    border: none;
    font-weight: bold;
}

QPushButton#primary_button:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369A1, stop:1 #38BDF8);
}

QPushButton#accent_button {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7C3AED, stop:1 #8B5CF6);
    color: #FFFFFF;
    border: none;
    font-weight: bold;
}

QPushButton#accent_button:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6D28D9, stop:1 #A78BFA);
}

QPushButton#stop_button {
    background-color: #7F1D1D;
    color: #FECACA;
    border: 1px solid #DC2626;
}

QPushButton#stop_button:hover {
    background-color: #991B1B;
}

/* Inputs */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #111827;
    color: #F9FAFB;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px;
    selection-background-color: #0284C7;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #00D2FF;
}

/* Labels */
QLabel {
    color: #F3F4F6;
}

QLabel#title_label {
    font-size: 18px;
    font-weight: bold;
    color: #00D2FF;
}

QLabel#subtitle_label {
    font-size: 12px;
    color: #9CA3AF;
}

/* Table View */
QTableWidget {
    background-color: #0F172A;
    color: #E2E8F0;
    gridline-color: #1E293B;
    border: 1px solid #1E293B;
    border-radius: 6px;
    selection-background-color: #1E293B;
    selection-color: #00D2FF;
}

QHeaderView::section {
    background-color: #1E293B;
    color: #94A3B8;
    padding: 6px;
    border: none;
    font-weight: 600;
}

/* ScrollBars */
QScrollBar:vertical {
    background: #0B0F19;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #334155;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #00D2FF;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ComboBox */
QComboBox {
    background-color: #111827;
    color: #F9FAFB;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
}

QComboBox:hover {
    border-color: #00D2FF;
}

QComboBox QAbstractItemView {
    background-color: #111827;
    color: #F9FAFB;
    selection-background-color: #0284C7;
    selection-color: #FFFFFF;
    border: 1px solid #334155;
}

/* CheckBox */
QCheckBox {
    spacing: 8px;
    color: #E2E8F0;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #475569;
    background: #111827;
}

QCheckBox::indicator:checked {
    background: #00D2FF;
    border-color: #00D2FF;
}

/* GroupBox */
QGroupBox {
    border: 1px solid #1E293B;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 12px;
    font-weight: bold;
    color: #00D2FF;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background-color: #0B0F19;
}
"""
