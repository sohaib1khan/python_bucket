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
        self.setFixedWidth(50)  

    def update_width(self):
        """ Dynamically adjust width based on number of digits in line numbers """
        digits = max(1, len(str(self.editor.blockCount())))
        space = 3 + self.editor.fontMetrics().horizontalAdvance('9') * digits
        self.setFixedWidth(space)

    def paintEvent(self, event):
        """ Paint line numbers alongside text """
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor("#1E1E1E"))  
        painter.setFont(self.editor.font())

        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()
        bottom = top + self.editor.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                current_block = self.editor.textCursor().block()

                # Highlight active line number
                if block == current_block:
                    painter.fillRect(0, int(top), self.width(), int(self.fontMetrics().height()), QColor("#3E3E3E"))

                painter.setPen(QColor("#CCCCCC"))
                painter.drawText(0, int(top), self.width() - 5, int(self.fontMetrics().height()), Qt.AlignmentFlag.AlignRight, number)

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

class MultiSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document, language):
        super().__init__(document)
        self.language = language
    
    def highlightBlock(self, text):
        if self.language == "Python":
            keywords = ['for', 'while', 'if', 'else', 'def', 'class', 'return', 'import', 'from', 'as']
            color_keyword = QColor("#569CD6")
            color_comment = QColor("#6A9955")
            color_string = QColor("#CE9178")
        elif self.language in ["JSON", "YAML", "XML"]:
            keywords = []
            color_keyword = QColor("#D19A66")
            color_comment = QColor("#6A9955")
            color_string = QColor("#98C379")
        elif self.language == "VB":
            keywords = ["Dim", "As", "Sub", "Function", "End", "If", "Then", "Else", "For", "Next", "Do", "Loop"]
            color_keyword = QColor("#C586C0")
            color_comment = QColor("#6A9955")
            color_string = QColor("#CE9178")
        else:
            return  

        format_keyword = QTextCharFormat()
        format_keyword.setForeground(color_keyword)
        format_keyword.setFontWeight(QFont.Weight.Bold)

        format_comment = QTextCharFormat()
        format_comment.setForeground(color_comment)

        format_string = QTextCharFormat()
        format_string.setForeground(color_string)

        for word in keywords:
            index = text.find(word)
            while index >= 0:
                length = len(word)
                self.setFormat(index, length, format_keyword)
                index = text.find(word, index + length)

        # Highlight comments
        if "#" in text:
            index = text.find("#")
            self.setFormat(index, len(text) - index, format_comment)

        # Highlight strings
        in_string = False
        start = -1
        for i, char in enumerate(text):
            if char in ('"', "'"):
                if in_string:
                    self.setFormat(start, i - start + 1, format_string)


class XAMLConverterApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("UiParse")
        self.setGeometry(200, 200, 800, 600)

        self.layout = QVBoxLayout()

        # Initialize output text editor first
        self.output_area = QPlainTextEdit(self)
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont("Consolas", 12))
        self.output_area.setStyleSheet("""
            background-color: #2B2B2B; 
            color: #E0E0E0; 
            font-family: Consolas, Monospace;
            font-size: 12pt;
            padding: 5px;
        """)

        # Create line number area (linked to output_area)
        self.line_numbers = LineNumberArea(self.output_area)

        # Correct placement: Connect signals AFTER output_area & line_numbers are initialized
        self.output_area.blockCountChanged.connect(self.line_numbers.update_width)  # Now correctly exists
        self.output_area.updateRequest.connect(self.line_numbers.update)
        self.output_area.verticalScrollBar().valueChanged.connect(self.line_numbers.update)

        # Layout for text editor & line numbers
        self.container_layout = QHBoxLayout()
        self.container_layout.setSpacing(0)  # Remove spacing to keep alignment
        self.container_layout.addWidget(self.line_numbers)
        self.container_layout.addWidget(self.output_area)

        # UI Components (Buttons, Dropdown, etc.)
        self.upload_btn = QPushButton("Upload .xaml")
        self.upload_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 5px; border-radius: 5px;")
        self.upload_btn.clicked.connect(self.upload_xaml)

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

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setStyleSheet("background-color: #95a5a6; color: white; font-weight: bold; padding: 5px; border-radius: 5px;")
        self.reset_btn.clicked.connect(self.reset_output)

        # Add Components to Layout
        layout = QVBoxLayout()
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
            language = "Python"
        elif format_choice == "Visual Basic (VB)":
            converted_code = self.to_visual_basic(xaml_dict)
            language = "VB"
        elif format_choice == "YAML":
            converted_code = yaml.dump(xaml_dict, default_flow_style=False, sort_keys=False)
            language = "YAML"
        elif format_choice == "JSON":
            converted_code = json.dumps(xaml_dict, indent=4)
            language = "JSON"
        elif format_choice == "XML (Formatted)":
            xml_string = xmltodict.unparse(xaml_dict, pretty=True)
            converted_code = minidom.parseString(xml_string).toprettyxml()
            language = "XML"

        self.output_area.setPlainText(converted_code)
        self.highlighter = MultiSyntaxHighlighter(self.output_area.document(), language)  
        self.update_line_numbers()


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
