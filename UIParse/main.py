
import json
import sys
import xmltodict
import yaml # Ensure you install PyYAML with `pip install pyyaml`
import xml.dom.minidom as minidom
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QPlainTextEdit,
    QMessageBox, QComboBox, QHBoxLayout
)
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QSyntaxHighlighter
from PyQt6.QtCore import Qt

class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def highlightBlock(self, text):
        keywords = ['for', 'while', 'if', 'else', 'def', 'class', 'return', 'import', 'from', 'as']
        format_keyword = QTextCharFormat()
        format_keyword.setForeground(QColor("#569CD6"))
        format_keyword.setFontWeight(QFont.Weight.Bold)

        format_comment = QTextCharFormat()
        format_comment = QTextCharFormat()
        format_comment = QTextCharFormat()
        format_comment = QTextCharFormat()
        format_comment = QTextCharFormat()
        format_comment = QTextCharFormat()
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

        self.output_area = QPlainTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont("Consolas", 12))
        self.output_area.setStyleSheet("background-color: #282C34; color: #ABB2BF;")

        self.highlighter = SimpleHighlighter(self.output_area.document())


        layout = QVBoxLayout()
        layout.addWidget(self.upload_btn)
        self.upload_btn.clicked.connect(self.upload_xaml)

        format_layout = QVBoxLayout()
        format_layout = QVBoxLayout()
        format_layout = QVBoxLayout()
        format_layout.addWidget(self.format_dropdown)

        layout.addWidget(self.upload_btn)
        layout.addWidget(self.format_dropdown)
        layout.addWidget(self.convert_btn)
        layout.addWidget(self.output_area)

        btn_layout = QVBoxLayout()
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.xaml_data = None

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




        self.output_area.setPlainText(converted_code)

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

    def save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "VB Script (*.vb);;Text File (*.txt)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(self.output_area.toPlainText())
            QMessageBox.information(self, "Saved", "File saved successfully!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = XAMLConverterApp()
    window.show()
    sys.exit(app.exec())
