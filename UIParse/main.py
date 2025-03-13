import json
import sys
import xmltodict
import yaml  # Ensure you install PyYAML with `pip install pyyaml`
import xml.dom.minidom as minidom
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QPlainTextEdit,
    QMessageBox, QComboBox, QHBoxLayout
)
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QPainter
from PyQt6.QtCore import QRect, Qt
from PyQt6.QtWidgets import QWidget

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setFixedWidth(50)  # Adjust width for numbers

    def paintEvent(self, event):
        """ Paints line numbers alongside the editor """
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor("#1E1E1E"))  # Background color
        painter.setFont(self.editor.font())  # Ensure font matches output_area

        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()
        bottom = top + self.editor.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#CCCCCC"))  # Light gray for numbers
                painter.drawText(0, int(top), self.width(), int(self.fontMetrics().height()), 
                                Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.editor.blockBoundingRect(block).height()
            block_number += 1


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def highlightBlock(self, text):
        keywords = ['for', 'while', 'if', 'else', 'def', 'class', 'return', 'import', 'from', 'as']
        format_keyword = QTextCharFormat()
        format_keyword.setForeground(QColor("#569CD6"))
        format_keyword.setFontWeight(QFont.Weight.Bold)

        format_comment = QTextCharFormat()
        format_comment.setForeground(QColor("#6A9955"))
        
        for word in keywords:
            expression = f"\\b{word}\\b"
            index = text.find(word)
            while index >= 0:
                length = len(word)
                self.setFormat(index, length, format_keyword)
                index = text.find(word, index + length)

        # Highlight comments
        if '#' in text:
            index = text.find('#')
            self.setFormat(index, len(text) - index, format_comment)

class SimpleHighlighter(QSyntaxHighlighter):
    def highlightBlock(self, text):
        keywords = ['for', 'while', 'if', 'else', 'def', 'class', 'return', 'import', 'from', 'as']
        
        format_keyword = QTextCharFormat()
        format_keyword.setForeground(QColor("#569CD6"))
        format_keyword.setFontWeight(QFont.Weight.Bold)

        format_comment = QTextCharFormat()
        format_comment.setForeground(QColor("#6A9955"))
        
        for word in keywords:
            expression = f"\\b{word}\\b"
            index = text.find(word)
            while index >= 0:
                length = len(word)
                self.setFormat(index, length, format_keyword)
                index = text.find(word, index + length)

        # Highlight comments
        if '#' in text:
            index = text.find('#')
            self.setFormat(index, len(text) - index, format_comment)

class XAMLConverterApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("UiParse")
        self.setGeometry(200, 200, 800, 600)

        self.layout = QVBoxLayout()

        self.upload_btn = QPushButton("Upload .xaml")
        self.upload_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 5px; border-radius: 5px;")

        self.format_dropdown = QComboBox()
        self.format_dropdown.addItems(["Python-like Pseudocode", "Visual Basic (VB)", "YAML", "JSON", "XML (Formatted)"])

        self.convert_btn = QPushButton("Convert")
        self.convert_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 5px; border-radius: 5px;")
        self.convert_btn.clicked.connect(self.convert_xaml)

        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold; padding: 5px; border-radius: 5px;")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)

        self.save_btn = QPushButton("Save as File")
        self.save_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 5px; border-radius: 5px;")
        self.save_btn.clicked.connect(self.save_file)

        # New Reset Button
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setStyleSheet("background-color: #95a5a6; color: white; font-weight: bold; padding: 5px; border-radius: 5px;")
        self.reset_btn.clicked.connect(self.reset_output)
        # Create main text editor
        self.output_area = QPlainTextEdit(self)
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont("Consolas", 12))
        self.output_area.setStyleSheet("background-color: #282C34; color: #ABB2BF; padding-left: 10px;")

        # Create line number area (linked to output_area)
        self.line_numbers = LineNumberArea(self.output_area)

        # Ensure line numbers update dynamically
        self.output_area.blockCountChanged.connect(self.update_line_numbers)
        self.output_area.updateRequest.connect(self.update_line_numbers)

        # Synchronize scrolling
        self.output_area.verticalScrollBar().valueChanged.connect(self.sync_scroll)

        # Horizontal layout for line numbers and output area
        self.container_layout = QHBoxLayout()
        self.container_layout.setSpacing(0)  # Remove spacing to keep alignment
        self.container_layout.addWidget(self.line_numbers)
        self.container_layout.addWidget(self.output_area)

        self.highlighter = SimpleHighlighter(self.output_area.document())

        layout = QVBoxLayout()
        layout.addWidget(self.upload_btn)
        self.upload_btn.clicked.connect(self.upload_xaml)

        format_layout = QVBoxLayout()
        format_layout.addWidget(self.format_dropdown)

        layout.addWidget(self.upload_btn)
        layout.addWidget(self.format_dropdown)
        layout.addWidget(self.convert_btn)
        layout.addLayout(self.container_layout)

        btn_layout = QVBoxLayout()
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.reset_btn)

        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.xaml_data = None

    def update_line_numbers(self):
        """ Sync line numbers with output_area """
        self.line_numbers.repaint()
        self.line_numbers.update()


    def upload_xaml(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open XAML File", "", "XAML Files (*.xaml)")
        if file_path:
            with open(file_path, "r", encoding="utf-8") as file:
                self.xaml_data = file.read()
            QMessageBox.information(self, "Success", "File loaded successfully!")

    def convert_xaml(self):
        if not self.xaml_data:
            QMessageBox.warning(self, "Warning", "No XAML file uploaded!")
            return

        xaml_dict = xmltodict.parse(self.xaml_data)
        format_choice = self.format_dropdown.currentText()

        if format_choice == "Python-like Pseudocode":
            converted_code = self.to_pseudocode(xaml_dict)
        elif format_choice == "Visual Basic (VB)":
            converted_code = self.to_visual_basic(xaml_dict)
        elif format_choice == "YAML":
            converted_code = yaml.dump(xaml_dict, default_flow_style=False, sort_keys=False)
        elif format_choice == "JSON":
            converted_code = json.dumps(xaml_dict, indent=4)
        elif format_choice == "XML (Formatted)":
            xml_string = xmltodict.unparse(xaml_dict, pretty=True)
            converted_code = minidom.parseString(xml_string).toprettyxml()

        lines = converted_code.split("\n")
        line_numbers_text = "\n".join(f"{i+1}" for i in range(len(lines)))  # Generate line numbers

        self.output_area.setPlainText(converted_code)  # Set converted code
        self.update_line_numbers()  # Ensure line numbers update after setting text

    def to_pseudocode(self, xaml_dict, indent=0):
        pseudocode = ""
        spacing = "    " * indent
        if isinstance(xaml_dict, dict):
            for key, value in xaml_dict.items():
                pseudocode += f"{spacing}{key}:\n"
                pseudocode += self.to_pseudocode(value, indent + 1)
        elif isinstance(xaml_dict, list):
            for item in xaml_dict:
                pseudocode += self.to_pseudocode(item, indent)
        else:
            pseudocode += f"{'    '*indent}{xaml_dict}\n"
        return pseudocode

    def to_visual_basic(self, xaml_dict, indent=0):
        vb_code = ""
        spacing = "    " * indent
        if isinstance(xaml_dict, dict):
            for key, value in xaml_dict.items():
                vb_code += f"{spacing}{key}:\n"
                vb_code += self.to_visual_basic(value, indent + 1)
        elif isinstance(xaml_dict, list):
            for item in xaml_dict:
                vb_code += self.to_visual_basic(item, indent)
        else:
            vb_code += f"{spacing}' {xaml_dict}\n"
        return vb_code

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.output_area.toPlainText())
        QMessageBox.information(self, "Copied", "Code copied to clipboard!")

    def reset_output(self):
        self.output_area.clear()

    def save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "VB Script (*.vb);;Text File (*.txt)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(self.output_area.toPlainText())
            QMessageBox.information(self, "Saved", "File saved successfully!")

    def sync_scroll(self, value):
        """ Syncs the scrolling of line numbers and output text area """
        self.line_numbers.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = XAMLConverterApp()
    window.show()
    sys.exit(app.exec())
