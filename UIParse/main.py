import os
import sys
import json
import yaml
import xmltodict
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
from collections import defaultdict, Counter, deque

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QPlainTextEdit,
    QMessageBox, QComboBox, QHBoxLayout, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QLabel, QHeaderView
)
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QPainter
from PyQt6.QtCore import QRect, Qt

# -------------------------
# Helpers for UiPath parsing
# -------------------------

def _lname(tag: str) -> str:
    return tag.split('}')[-1] if '}' in tag else tag

ASSET_ACTS = {"GetAsset", "GetCredential", "GetRobotAsset"}
INVOKE_ACT = "InvokeWorkflowFile"

def parse_xaml_file(path: str):
    """Parse a single XAML and return activities, invokes, assets, annotations."""
    acts = []
    invokes = []
    assets = []
    annotations = []
    try:
        for event, elem in ET.iterparse(path, events=("start",)):
            name = _lname(elem.tag)

            # pull common attributes (namespace-agnostic)
            rec = {"tag": name}
            for attr in ("DisplayName", "Selector", "TimeoutMS", "ContinueOnError", "WorkflowFile",
                         "AssetName", "Name", "Value"):
                if attr in elem.attrib:
                    rec[attr] = elem.attrib.get(attr)
                else:
                    for k, v in elem.attrib.items():
                        if k.endswith(attr):
                            rec[attr] = v

            # collect invokes
            if name == INVOKE_ACT:
                wf = rec.get("WorkflowFile")
                if wf:
                    invokes.append({"workflow": wf, "display": rec.get("DisplayName")})

            # collect assets
            if name in ASSET_ACTS:
                assets.append({
                    "activity": name,
                    "asset": rec.get("AssetName") or rec.get("Name"),
                    "display": rec.get("DisplayName")
                })

            # collect annotations: sap2010:Annotation.AnnotationText
            for k, v in elem.attrib.items():
                if k.endswith("Annotation.AnnotationText") and v:
                    annotations.append({"for": rec.get("DisplayName") or name, "note": v})

            # trimmed activity rows (skip containers)
            if name not in {"Sequence", "Flowchart", "State", "StateMachine", "TryCatch", "ActivityAction"}:
                acts.append({
                    "tag": name,
                    "display": rec.get("DisplayName"),
                    "selector": (rec.get("Selector") or "")[:220],
                    "timeout": rec.get("TimeoutMS"),
                    "coerror": rec.get("ContinueOnError")
                })

            elem.clear()
    except ET.ParseError as e:
        return {"error": f"ParseError in {os.path.basename(path)}: {e}"}

    return {"activities": acts, "invokes": invokes, "assets": assets, "annotations": annotations}

def read_project_main(project_json_path: str) -> str:
    with open(project_json_path, "r", encoding="utf-8") as f:
        pj = json.load(f)
    return pj.get("main", "Main.xaml")

def build_project_map(root: str):
    """Walk from project.json main → follow invokes → return graph + reports."""
    pj_path = os.path.join(root, "project.json")
    if not os.path.exists(pj_path):
        return {"error": f"project.json not found in {root}"}

    main = read_project_main(pj_path)
    q = deque([main])
    seen = set()
    graph = defaultdict(list)
    file_reports = {}
    all_assets = []
    activity_counter = Counter()

    def norm(base, rel):
        p = os.path.normpath(os.path.join(os.path.dirname(base), rel))
        return os.path.relpath(p, root)

    while q:
        cur = q.popleft()
        if cur in seen:
            continue
        seen.add(cur)
        full = os.path.join(root, cur)
        if not os.path.exists(full):
            file_reports[cur] = {"error": f"Missing file: {cur}"}
            continue

        rep = parse_xaml_file(full)
        file_reports[cur] = rep

        # Graph edges
        for inv in rep.get("invokes", []):
            wf = inv["workflow"]
            tgt = norm(cur, wf)
            tgt_full = os.path.join(root, tgt)
            graph[cur].append(tgt if os.path.exists(tgt_full) else f"{wf} (MISSING)")
            if os.path.exists(tgt_full):
                q.append(tgt)

        # Assets + Activity counts
        for a in rep.get("assets", []):
            a["file"] = cur
            all_assets.append(a)
        for a in rep.get("activities", []):
            activity_counter[a["tag"]] += 1

    # Summarize assets
    assets_summary = defaultdict(lambda: {"count": 0, "files": set(), "kinds": set()})
    for a in all_assets:
        name = a.get("asset")
        if not name:
            continue
        assets_summary[name]["count"] += 1
        assets_summary[name]["files"].add(a["file"])
        assets_summary[name]["kinds"].add(a["activity"])

    assets_table = []
    for name, meta in sorted(assets_summary.items()):
        assets_table.append({
            "AssetName": name,
            "Refs": meta["count"],
            "Kinds": ",".join(sorted(meta["kinds"])),
            "Files": ", ".join(sorted(meta["files"]))
        })

    return {
        "entry": main,
        "graph": dict(graph),
        "files": file_reports,
        "assets_table": assets_table,
        "activity_counts": dict(activity_counter),
    }

def make_outline_text(result):
    if "error" in result:
        return f"ERROR: {result['error']}"

    lines = [f"# Entry: {result['entry']}"]
    for xaml, rep in result["files"].items():
        lines.append(f"\n## {xaml}")
        if "error" in rep:
            lines.append(f"- ERROR: {rep['error']}")
            continue

        # Top activities (grouped)
        c = Counter(a["tag"] for a in rep["activities"])
        if c:
            tops = ", ".join(f"{k}×{v}" for k, v in c.most_common(10))
            lines.append(f"- Top activities: {tops}")

        # Invokes
        inv = rep.get("invokes", [])
        if inv:
            lines.append("- Invokes:")
            for i in inv:
                lines.append(f"  - {i['workflow']} ({i.get('display') or 'no display'})")

        # Annotations (show a few)
        ann = rep.get("annotations", [])
        for a in ann[:10]:
            lines.append(f"- Note [{a['for']}]: {a['note']}")

        # Sample steps
        steps = rep["activities"][:30]
        if steps:
            lines.append("- Sample steps:")
            for s in steps:
                desc = s["display"] or s["tag"]
                sel = f" selector={s['selector']}" if s.get("selector") else ""
                coe = f" coe={s['coerror']}" if s.get("coerror") else ""
                lines.append(f"  · {s['tag']}: {desc}{sel}{coe}")

    # Global activity counts
    lines.append("\n## Global activity counts (top 25)")
    c_all = Counter()
    for rep in result["files"].values():
        if isinstance(rep, dict) and "activities" in rep:
            for a in rep["activities"]:
                c_all[a["tag"]] += 1
    for k, v in c_all.most_common(25):
        lines.append(f"- {k}: {v}")

    return "\n".join(lines)


# -------------------------
# UI Components
# -------------------------

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setFixedWidth(50)
    def update_width(self):
        digits = max(1, len(str(self.editor.blockCount())))
        space = 3 + self.editor.fontMetrics().horizontalAdvance('9') * digits
        self.setFixedWidth(space)
    def paintEvent(self, event):
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
                if block == current_block:
                    painter.fillRect(0, int(top), self.width(), int(self.fontMetrics().height()), QColor("#3E3E3E"))
                painter.setPen(QColor("#CCCCCC"))
                painter.drawText(0, int(top), self.width() - 5, int(self.fontMetrics().height()),
                                 Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.editor.blockBoundingRect(block).height()
            block_number += 1

class MultiSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document, language):
        super().__init__(document)
        self.language = language
    def highlightBlock(self, text):
        if self.language == "Python":
            keywords = ['for', 'while', 'if', 'else', 'def', 'class', 'return', 'import', 'from', 'as']
            color_keyword = QColor("#569CD6"); color_comment = QColor("#6A9955"); color_string = QColor("#CE9178")
        elif self.language in ["JSON", "YAML", "XML"]:
            keywords = []; color_keyword = QColor("#D19A66"); color_comment = QColor("#6A9955"); color_string = QColor("#98C379")
        elif self.language == "VB":
            keywords = ["Dim", "As", "Sub", "Function", "End", "If", "Then", "Else", "For", "Next", "Do", "Loop"]
            color_keyword = QColor("#C586C0"); color_comment = QColor("#6A9955"); color_string = QColor("#CE9178")
        else:
            return
        format_keyword = QTextCharFormat(); format_keyword.setForeground(color_keyword); format_keyword.setFontWeight(QFont.Weight.Bold)
        format_comment = QTextCharFormat(); format_comment.setForeground(color_comment)
        format_string = QTextCharFormat(); format_string.setForeground(color_string)
        for word in keywords:
            index = text.find(word)
            while index >= 0:
                self.setFormat(index, len(word), format_keyword)
                index = text.find(word, index + len(word))
        if "#" in text:
            index = text.find("#")
            self.setFormat(index, len(text) - index, format_comment)
        # naive string highlight
        in_string = False; start = -1
        for i, ch in enumerate(text):
            if ch in ('"', "'"):
                if in_string:
                    self.setFormat(start, i - start + 1, format_string)
                    in_string = False
                else:
                    in_string = True; start = i

class XAMLConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UiParse")
        self.setGeometry(200, 200, 1100, 700)

        self.xaml_data = None
        self.project_root = None
        self.result_cache = None

        # ---------- Top controls ----------
        top_bar = QHBoxLayout()

        self.open_xaml_btn = QPushButton("Open .xaml")
        self.open_xaml_btn.setStyleSheet("background-color:#3498db;color:white;font-weight:bold;padding:6px;border-radius:6px;")
        self.open_xaml_btn.clicked.connect(self.upload_xaml)
        top_bar.addWidget(self.open_xaml_btn)

        self.open_project_btn = QPushButton("Open Project Folder")
        self.open_project_btn.setStyleSheet("background-color:#8e44ad;color:white;font-weight:bold;padding:6px;border-radius:6px;")
        self.open_project_btn.clicked.connect(self.open_project)
        top_bar.addWidget(self.open_project_btn)

        self.build_map_btn = QPushButton("Build Map")
        self.build_map_btn.setStyleSheet("background-color:#2ecc71;color:white;font-weight:bold;padding:6px;border-radius:6px;")
        self.build_map_btn.clicked.connect(self.build_map)
        top_bar.addWidget(self.build_map_btn)

        self.format_dropdown = QComboBox()
        self.format_dropdown.addItems(["Python-like Pseudocode", "Visual Basic (VB)", "YAML", "JSON", "XML (Formatted)"])
        top_bar.addWidget(self.format_dropdown)

        self.convert_btn = QPushButton("Convert Current XAML")
        self.convert_btn.setStyleSheet("background-color:#27ae60;color:white;font-weight:bold;padding:6px;border-radius:6px;")
        self.convert_btn.clicked.connect(self.convert_xaml)
        top_bar.addWidget(self.convert_btn)

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setStyleSheet("background-color:#f39c12;color:white;font-weight:bold;padding:6px;border-radius:6px;")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        top_bar.addWidget(self.copy_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet("background-color:#e74c3c;color:white;font-weight:bold;padding:6px;border-radius:6px;")
        self.save_btn.clicked.connect(self.save_file)
        top_bar.addWidget(self.save_btn)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setStyleSheet("background-color:#95a5a6;color:white;font-weight:bold;padding:6px;border-radius:6px;")
        self.reset_btn.clicked.connect(self.reset_output)
        top_bar.addWidget(self.reset_btn)

        # ---------- Tabs ----------
        self.tabs = QTabWidget()
        # Raw output
        self.output_area = QPlainTextEdit(self); self.output_area.setReadOnly(True); self.output_area.setFont(QFont("Consolas", 12))
        self.output_area.setStyleSheet("background-color:#2B2B2B;color:#E0E0E0;font-family:Consolas,Monospace;font-size:12pt;padding:6px;")
        self.line_numbers = LineNumberArea(self.output_area)
        self.output_area.blockCountChanged.connect(self.line_numbers.update_width)
        self.output_area.updateRequest.connect(self.line_numbers.update)
        self.output_area.verticalScrollBar().valueChanged.connect(self.line_numbers.update)
        raw_layout = QHBoxLayout(); raw_layout.setSpacing(0)
        raw_layout.addWidget(self.line_numbers); raw_layout.addWidget(self.output_area)
        raw_container = QWidget(); raw_container.setLayout(raw_layout)
        self.tabs.addTab(raw_container, "Raw")

        # Outline tab
        self.outline_view = QPlainTextEdit(self); self.outline_view.setReadOnly(True); self.outline_view.setFont(QFont("Consolas", 11))
        self.tabs.addTab(self.outline_view, "Outline")

        # Assets tab
        self.assets_table = QTableWidget(0, 4)
        self.assets_table.setHorizontalHeaderLabels(["AssetName", "Refs", "Kinds", "Files"])
        self.assets_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.assets_table, "Assets")

        # Graph tab
        self.graph_tree = QTreeWidget()
        self.graph_tree.setHeaderLabels(["Workflow Graph (double-click node to show file outline sample)"])
        self.graph_tree.itemDoubleClicked.connect(self.on_graph_item_double_click)
        self.tabs.addTab(self.graph_tree, "Graph")

        # Layout root
        root = QVBoxLayout()
        root.addLayout(top_bar)
        root.addWidget(self.tabs)
        self.setLayout(root)

        # Highlighter for Raw tab (changes per format)
        self.highlighter = None
        self.current_language = "Python"

    # ---------- File/Project actions ----------
    def upload_xaml(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open XAML File", "", "XAML Files (*.xaml)")
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                self.xaml_data = f.read()
            self.output_area.setPlainText(self.xaml_data)
            self.current_language = "XML"
            self.highlighter = MultiSyntaxHighlighter(self.output_area.document(), "XML")
            QMessageBox.information(self, "Success", f"Loaded: {os.path.basename(file_path)}")

    def open_project(self):
        folder = QFileDialog.getExistingDirectory(self, "Open UiPath Project Folder", "")
        if folder:
            self.project_root = folder
            QMessageBox.information(self, "Project", f"Set project root:\n{folder}")

    def build_map(self):
        if not self.project_root:
            QMessageBox.warning(self, "Warning", "Please choose a UiPath project folder first.")
            return
        result = build_project_map(self.project_root)
        self.result_cache = result

        # Fill Outline tab
        self.outline_view.setPlainText(make_outline_text(result))

        # Fill Assets tab
        self.assets_table.setRowCount(0)
        for row in result.get("assets_table", []):
            r = self.assets_table.rowCount()
            self.assets_table.insertRow(r)
            self.assets_table.setItem(r, 0, QTableWidgetItem(row.get("AssetName", "")))
            self.assets_table.setItem(r, 1, QTableWidgetItem(str(row.get("Refs", 0))))
            self.assets_table.setItem(r, 2, QTableWidgetItem(row.get("Kinds", "")))
            self.assets_table.setItem(r, 3, QTableWidgetItem(row.get("Files", "")))

        # Fill Graph tab
        self.graph_tree.clear()
        if "error" in result:
            QTreeWidgetItem(self.graph_tree, [result["error"]])
        else:
            root_item = QTreeWidgetItem(self.graph_tree, [f"Entry: {result['entry']}"])
            added = set()
            def add_children(parent_item, parent_key):
                for child in result["graph"].get(parent_key, []):
                    if (parent_key, child) in added:
                        continue
                    added.add((parent_key, child))
                    ci = QTreeWidgetItem(parent_item, [child])
                    if child in result["graph"]:
                        add_children(ci, child)
            add_children(root_item, result["entry"])
            self.graph_tree.expandAll()

        QMessageBox.information(self, "Done", "Project map built.")

    # ---------- Converters (single XAML) ----------
    def convert_xaml(self):
        if not self.xaml_data:
            QMessageBox.warning(self, "Warning", "No XAML file loaded in Raw tab!")
            return

        xaml_dict = xmltodict.parse(self.xaml_data)
        format_choice = self.format_dropdown.currentText()

        if format_choice == "Python-like Pseudocode":
            converted_code = self.to_pseudocode(xaml_dict); language = "Python"
        elif format_choice == "Visual Basic (VB)":
            converted_code = self.to_visual_basic(xaml_dict); language = "VB"
        elif format_choice == "YAML":
            converted_code = yaml.dump(xaml_dict, default_flow_style=False, sort_keys=False); language = "YAML"
        elif format_choice == "JSON":
            converted_code = json.dumps(xaml_dict, indent=4); language = "JSON"
        elif format_choice == "XML (Formatted)":
            xml_string = xmltodict.unparse(xaml_dict, pretty=True)
            converted_code = minidom.parseString(xml_string).toprettyxml()
            language = "XML"
        else:
            converted_code = ""
            language = "Python"

        self.output_area.setPlainText(converted_code)
        self.highlighter = MultiSyntaxHighlighter(self.output_area.document(), language)
        self.current_language = language

    # ---------- Pretty printers ----------
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

    # ---------- Utilities ----------
    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        # prefer Outline tab if selected, else Raw
        w = self.tabs.currentWidget()
        if w is self.outline_view:
            clipboard.setText(self.outline_view.toPlainText())
        else:
            clipboard.setText(self.output_area.toPlainText())
        QMessageBox.information(self, "Copied", "Copied current tab content to clipboard.")

    def reset_output(self):
        self.output_area.clear()
        self.outline_view.clear()
        self.assets_table.setRowCount(0)
        self.graph_tree.clear()
        self.xaml_data = None
        self.result_cache = None

    def save_file(self):
        content = ""
        # save whichever tab is active (Outline or Raw)
        if self.tabs.currentWidget() is self.outline_view:
            content = self.outline_view.toPlainText()
            default_filter = "Markdown (*.md);;Text File (*.txt)"
        elif self.tabs.currentWidget() is self.graph_tree:
            # export graph as simple text
            content = self._export_graph_text()
            default_filter = "Text File (*.txt)"
        else:
            content = self.output_area.toPlainText()
            default_filter = "Text File (*.txt)"

        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", default_filter)
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Saved", f"Saved: {os.path.basename(file_path)}")

    def _export_graph_text(self):
        if not self.result_cache or "graph" not in self.result_cache:
            return ""
        lines = [f"Entry: {self.result_cache.get('entry','(unknown)')}"]
        for parent, children in self.result_cache["graph"].items():
            for ch in children:
                lines.append(f"{parent} -> {ch}")
        return "\n".join(lines)

    def on_graph_item_double_click(self, item, col):
        if not self.result_cache or "files" not in self.result_cache:
            return
        # Try to show sample for this node if it is a file key
        key = item.text(0)
        rep = self.result_cache["files"].get(key)
        if not rep:
            return
        # Show the first 30 steps similar to outline
        if "error" in rep:
            self.outline_view.setPlainText(f"ERROR: {rep['error']}")
            self.tabs.setCurrentWidget(self.outline_view)
            return
        lines = [f"## {key}", "- Sample steps:"]
        for s in rep.get("activities", [])[:30]:
            desc = s["display"] or s["tag"]
            sel = f" selector={s['selector']}" if s.get("selector") else ""
            coe = f" coe={s['coerror']}" if s.get("coerror") else ""
            lines.append(f"  · {s['tag']}: {desc}{sel}{coe}")
        self.outline_view.setPlainText("\n".join(lines))
        self.tabs.setCurrentWidget(self.outline_view)


# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = XAMLConverterApp()
    window.show()
    sys.exit(app.exec())
