from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import queue
import re
import subprocess
import threading
import time
from typing import Callable, Iterable

from PySide6.QtCore import QEvent, QEasingCurve, QPropertyAnimation, QRect, QSize, QStringListModel, Qt, QThread, Signal
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QFontDatabase,
    QPainter,
    QPalette,
    QKeySequence,
    QShortcut,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextFormat,
    QSyntaxHighlighter,
)
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QCompleter,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

KEYWORDS = sorted(
    [
        "and",
        "arr_to_str",
        "close",
        "compare",
        "elif",
        "else",
        "false",
        "float",
        "fn",
        "for",
        "if",
        "in",
        "int",
        "length",
        "or",
        "range",
        "read",
        "ret",
        "show",
        "str_to_arr",
        "todo",
        "true",
        "type",
        "while",
    ]
)

LITERALS = {"int_literal", "float_literal", "str_literal", "bool_literal"}
OPERATORS = {
    "++",
    "--",
    "//",
    "**",
    "==",
    "!=",
    ">",
    "<",
    ">=",
    "<=",
    "+",
    "-",
    "*",
    "/",
    "%",
    "=",
    "!",
}
DELIMS = {"(", ")", "[", "]", ",", ";", ":"}

SNIPPETS = {
    "true / false": "is_admin = true;\nlogged_in = false;\n",
    "read": "user_input = read;\n",
    "show": "show value;\n",
    "if / elif / else": "if score >= 90:\n    show 'A';\nelif score >= 75:\n    show 'B';\nelse:\n    show 'C';\nclose\n",
    "while": "x = 1;\nwhile x <= 5:\n    show x;\n    x = x + 1;\nclose\n",
    "for / in / range": "for i in range(5):\n    show i;\nclose\n",
    "int": "x = int('5');\n",
    "float": "y = float('3.14');\n",
    "str_to_arr": "word = 'hello';\narr = str_to_arr(word);\n",
    "arr_to_str": "mixed = [1, 'A', true];\nresult = arr_to_str(mixed);\n",
    "length": "result = str_to_arr('hello');\nfor i in range(length(result)):\n    out = result[i];\n    show out;\n    show '\\n';\nclose\n",
    "compare": "result = compare('abc', 'abd');\nshow result;\n",
    "type": "x = 3.14;\nt = type(x);\n\nif t == 'float':\n    show 'The variable is a float.';\nclose\n",
    "and": "result = true and false;\nshow result;\n",
    "or": "result = true or false;\nshow result;\n",
    "fn": "fn square(x):\n    todo;\n    ret x * x;\nclose\n",
    "ret": "ret value;\n",
    "todo": "todo;\n",
    "close": "if score >= 90:\n    show 'A';\nelse:\n    show 'B';\nclose\n",
}

THEMES = {
    "Light (macOS)": {
        "bg": "#f5f5f7",
        "surface": "#ffffff",
        "surface_2": "#e5e5ea",
        "surface_3": "#f9f9f9",
        "text": "#333333",
        "muted": "#6e6e73",
        "border": "#d1d1d6",
        "accent": "#007aff",
        "accent_2": "#34c759",
        "danger": "#ff3b30",
        "warning": "#ff9500",
        "purple": "#af52de",
        "editor": "#ffffff",
        "editor_line": "#f0f7ff",
        "terminal": "#1e1e1e",
        "terminal_text": "#000000",
        "btn_analyze": "#af52de",
        "btn_run": "#34c759",
        "btn_danger": "#ff3b30",
        "btn_layout": "#007aff",
        "btn_utility": "#6e6e73",
    },
    "Dark": {
        "bg": "#090b0f",
        "surface": "#11151b",
        "surface_2": "#181d25",
        "surface_3": "#202732",
        "text": "#e8edf5",
        "muted": "#8f9aaa",
        "border": "#2b3442",
        "accent": "#3b82f6",
        "accent_2": "#10b981",
        "danger": "#f44747",
        "warning": "#f59e0b",
        "purple": "#8b5cf6",
        "editor": "#0b0f14",
        "editor_line": "#111827",
        "terminal": "#05070a",
        "terminal_text": "#d8e2ef",
        "btn_analyze": "#6366f1",
        "btn_run": "#059669",
        "btn_danger": "#f44747",
        "btn_layout": "#2563eb",
        "btn_utility": "#475569",
    },
    "Oceanic Blue": {
        "bg": "#e0f2f7",
        "surface": "#ffffff",
        "surface_2": "#cfd8dc",
        "surface_3": "#e1f5fe",
        "text": "#004d40",
        "muted": "#455a64",
        "border": "#b0bec5",
        "accent": "#0277bd",
        "accent_2": "#00695c",
        "danger": "#c62828",
        "warning": "#e65100",
        "purple": "#0288d1",
        "editor": "#ffffff",
        "editor_line": "#e6f7ff",
        "terminal": "#0d1b2a",
        "terminal_text": "#000000",
        "btn_analyze": "#0288d1",
        "btn_run": "#00695c",
        "btn_danger": "#c62828",
        "btn_layout": "#0277bd",
        "btn_utility": "#455a64",
    },
    "Forest Green": {
        "bg": "#10251b",
        "surface": "#173524",
        "surface_2": "#214832",
        "surface_3": "#2d5f42",
        "text": "#ecfff3",
        "muted": "#9fd5b3",
        "border": "#3b7652",
        "accent": "#2dd4bf",
        "accent_2": "#22c55e",
        "danger": "#f87171",
        "warning": "#facc15",
        "purple": "#86efac",
        "editor": "#0f2118",
        "editor_line": "#183c28",
        "terminal": "#06120c",
        "terminal_text": "#b8ffd0",
        "btn_analyze": "#2dd4bf",
        "btn_run": "#22c55e",
        "btn_danger": "#ef4444",
        "btn_layout": "#16a34a",
        "btn_utility": "#4d7c59",
    },
    "Big Chungus": {
        "bg": "#add8e6",
        "surface": "#ffffff",
        "surface_2": "#f0f8ff",
        "surface_3": "#ffdead",
        "text": "#404040",
        "muted": "#708090",
        "border": "#87ceeb",
        "accent": "#ff4500",
        "accent_2": "#228b22",
        "danger": "#dc143c",
        "warning": "#8b4513",
        "purple": "#a9a9a9",
        "editor": "#ffffff",
        "editor_line": "#fff2df",
        "terminal": "#1a1a2e",
        "terminal_text": "#000000",
        "btn_analyze": "#ff4500",
        "btn_run": "#228b22",
        "btn_danger": "#dc143c",
        "btn_layout": "#ff4500",
        "btn_utility": "#708090",
    },
    "Disney Magic": {
        "bg": "#fff0f5",
        "surface": "#ffffff",
        "surface_2": "#e6e6fa",
        "surface_3": "#ffe4e1",
        "text": "#4b0082",
        "muted": "#8b008b",
        "border": "#ffb6c1",
        "accent": "#1e90ff",
        "accent_2": "#32cd32",
        "danger": "#ff1493",
        "warning": "#ffa500",
        "purple": "#9370db",
        "editor": "#ffffff",
        "editor_line": "#fff4fb",
        "terminal": "#1a0a2e",
        "terminal_text": "#e0aaff",
        "btn_analyze": "#9370db",
        "btn_run": "#32cd32",
        "btn_danger": "#ff1493",
        "btn_layout": "#1e90ff",
        "btn_utility": "#8b008b",
    },
    "Synthwave 84": {
        "bg": "#21182f",
        "surface": "#2a2039",
        "surface_2": "#352747",
        "surface_3": "#44305e",
        "text": "#f9e7ff",
        "muted": "#caa7de",
        "border": "#6f4e9c",
        "accent": "#01cdfe",
        "accent_2": "#05ffa1",
        "danger": "#ff4f8b",
        "warning": "#ffcf5a",
        "purple": "#ff71ce",
        "editor": "#1d152b",
        "editor_line": "#2b1f40",
        "terminal": "#10091c",
        "terminal_text": "#b8fff1",
        "btn_analyze": "#b967ff",
        "btn_run": "#05b86f",
        "btn_danger": "#ff4f8b",
        "btn_layout": "#0094b8",
        "btn_utility": "#6f4e9c",
    },
    "Aurora Glass": {
        "bg": "#eef8ff",
        "surface": "#ffffff",
        "surface_2": "#dff4ff",
        "surface_3": "#d8f7ee",
        "text": "#183047",
        "muted": "#5c728a",
        "border": "#9ccfe4",
        "accent": "#0096c7",
        "accent_2": "#00a878",
        "danger": "#e63946",
        "warning": "#f77f00",
        "purple": "#6c63ff",
        "editor": "#fbfeff",
        "editor_line": "#e6f8ff",
        "terminal": "#122032",
        "terminal_text": "#000000",
        "btn_analyze": "#6c63ff",
        "btn_run": "#00a878",
        "btn_danger": "#e63946",
        "btn_layout": "#0096c7",
        "btn_utility": "#607d9a",
    },
}


@dataclass
class EditorBuffer:
    content: str = ""
    path: Path | None = None
    modified: bool = False
    panes: list["EditorPane"] = field(default_factory=list)


@dataclass
class Diagnostic:
    phase: str
    message: str
    line: int | None = None
    col: int | None = None


class LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    focused = Signal(object)
    cursor_moved = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.cursorPositionChanged.connect(self.emit_cursor_position)
        self.update_line_number_area_width(0)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setUndoRedoEnabled(True)
        self.completer = None
        self.highlight_current_line()

    def set_keywords(self, words: list[str]):
        self.completer = QCompleter(words, self)
        self.completer.setModel(QStringListModel(words, self.completer))
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated.connect(self.insert_completion)

    def text_under_cursor(self) -> str:
        cursor = self.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        return cursor.selectedText()

    def insert_completion(self, completion: str):
        cursor = self.textCursor()
        prefix = self.text_under_cursor()
        cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, len(prefix))
        cursor.insertText(completion)
        self.setTextCursor(cursor)

    def line_number_area_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        return 18 + self.fontMetrics().horizontalAdvance("9") * digits

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect: QRect, dy: int):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.focused.emit(self)

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            key = event.key()
            text = event.text()
            window = self.window()
            if key in (Qt.Key_Plus, Qt.Key_Equal) or text in ("+", "="):
                if hasattr(window, "increase_font"):
                    window.increase_font()
                    return
            if key in (Qt.Key_Minus, Qt.Key_Underscore) or text in ("-", "_"):
                if hasattr(window, "decrease_font"):
                    window.decrease_font()
                    return
        if self.completer and self.completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                event.ignore()
                return
        super().keyPressEvent(event)
        self.focused.emit(self)
        if not self.completer:
            return
        prefix = self.text_under_cursor()
        if len(prefix) < 2 or not prefix[-1:].isalnum():
            self.completer.popup().hide()
            return
        self.completer.setCompletionPrefix(prefix)
        if self.completer.completionCount() == 0:
            self.completer.popup().hide()
            return
        rect = self.cursorRect()
        rect.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(rect)

    def emit_cursor_position(self):
        cursor = self.textCursor()
        self.cursor_moved.emit(cursor.blockNumber() + 1, cursor.positionInBlock() + 1)

    def highlight_current_line(self):
        selections = []
        selection = QTextEdit.ExtraSelection()
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        selection.format.setBackground(QColor(getattr(self, "current_line_color", "#eef6ff")))
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        selections.append(selection)
        self.setExtraSelections(selections)

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(getattr(self, "gutter_color", "#f1f3f5")))
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        color = QColor(getattr(self, "gutter_text_color", "#7a7f87"))

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(color)
                painter.drawText(0, top, self.line_number_area.width() - 8, self.fontMetrics().height(), Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1


class ChungusHighlighter(QSyntaxHighlighter):
    def __init__(self, document, theme: dict[str, str]):
        super().__init__(document)
        self.theme = theme
        self._build_rules()

    def set_theme(self, theme: dict[str, str]):
        self.theme = theme
        self._build_rules()
        self.rehighlight()

    def _fmt(self, color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Bold)
        if italic:
            fmt.setFontItalic(True)
        return fmt

    def _build_rules(self):
        self.rules = [
            (re.compile(r"\b(" + "|".join(re.escape(k) for k in KEYWORDS) + r")\b"), self._fmt(self.theme["purple"], True)),
            (re.compile(r"'[^'\n]*'"), self._fmt(self.theme["accent_2"])),
            (re.compile(r"\b\d+(\.\d+)?\b"), self._fmt(self.theme["warning"])),
            (re.compile(r"(//.*)$"), self._fmt(self.theme["muted"], italic=True)),
            (re.compile(r"(\+\+|--|//|\*\*|==|!=|>=|<=|[+\-*/%=!<>])"), self._fmt(self.theme["accent"])),
        ]

    def highlightBlock(self, text: str):
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class EditorPane(QWidget):
    close_requested = Signal(object)

    def __init__(self, buffer: EditorBuffer, theme: dict[str, str], parent=None):
        super().__init__(parent)
        self.buffer = buffer
        self.buffer.panes.append(self)
        self.editor = CodeEditor()
        self.editor.set_keywords(KEYWORDS)
        self.path_label = QLabel(self.display_name())
        self.path_label.setObjectName("paneTitle")
        self.close_button = QPushButton("x")
        self.close_button.setObjectName("paneClose")
        self.close_button.setFixedSize(24, 24)
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.clicked.connect(lambda: self.close_requested.emit(self))
        self.highlighter = ChungusHighlighter(self.editor.document(), theme)
        self.editor.setPlainText(buffer.content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        header = QWidget()
        header.setObjectName("paneHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 6, 0)
        header_layout.setSpacing(4)
        header_layout.addWidget(self.path_label, 1)
        header_layout.addWidget(self.close_button, 0)
        layout.addWidget(header)
        layout.addWidget(self.editor)

    def display_name(self) -> str:
        if self.buffer.path:
            suffix = " *" if self.buffer.modified else ""
            return f"  {self.buffer.path.name}{suffix}"
        return "  Untitled *" if self.buffer.modified else "  Untitled"

    def refresh_title(self):
        self.path_label.setText(self.display_name())

    def set_buffer(self, buffer: EditorBuffer, theme: dict[str, str]):
        if self in self.buffer.panes:
            self.buffer.panes.remove(self)
        self.buffer = buffer
        self.buffer.panes.append(self)
        self.editor.blockSignals(True)
        self.editor.setPlainText(buffer.content)
        self.editor.blockSignals(False)
        self.highlighter.setDocument(self.editor.document())
        self.highlighter.set_theme(theme)
        self.refresh_title()

    def apply_theme(self, theme: dict[str, str], font: QFont):
        self.editor.setFont(font)
        self.editor.gutter_color = theme["surface_2"]
        self.editor.gutter_text_color = theme["muted"]
        self.editor.current_line_color = theme["editor_line"]
        self.editor.setStyleSheet(
            f"""
            QPlainTextEdit {{
                background: {theme["editor"]};
                color: {theme["text"]};
                border: 0;
                font-size: {font.pointSize()}pt;
                selection-background-color: {theme["accent"]};
                selection-color: {theme["surface"]};
                padding: 8px;
            }}
            """
        )
        self.editor.document().setDefaultFont(font)
        palette = self.editor.palette()
        palette.setColor(QPalette.Base, QColor(theme["editor"]))
        palette.setColor(QPalette.Text, QColor(theme["text"]))
        palette.setColor(QPalette.Highlight, QColor(theme["accent"]))
        palette.setColor(QPalette.HighlightedText, QColor(theme["surface"]))
        self.editor.setPalette(palette)
        self.editor.viewport().setStyleSheet(f"background: {theme['editor']};")
        self.path_label.setStyleSheet(
            f"""
            QLabel#paneTitle {{
                background: {theme["surface_2"]};
                color: {theme["muted"]};
                padding: 6px 8px;
                font-weight: 600;
            }}
            """
        )
        self.findChild(QWidget, "paneHeader").setStyleSheet(
            f"""
            QWidget#paneHeader {{
                background: {theme["surface_2"]};
                border-bottom: 1px solid {theme["border"]};
            }}
            """
        )
        self.close_button.setStyleSheet(
            f"""
            QPushButton#paneClose {{
                background: {theme["surface_3"]};
                color: {theme["text"]};
                border: 1px solid {theme["border"]};
                border-radius: 12px;
                padding: 0;
                font-weight: 800;
            }}
            QPushButton#paneClose:hover {{
                background: {theme["danger"]};
                color: #ffffff;
                border-color: {theme["danger"]};
            }}
            """
        )
        self.highlighter.set_theme(theme)
        self.editor.update_line_number_area_width(0)
        self.editor.highlight_current_line()


class CompilerWorker(QThread):
    finished = Signal(str, object, list, object)

    def __init__(self, phase: str, source: str, callback: Callable):
        super().__init__()
        self.phase = phase
        self.source = source
        self.callback = callback

    def run(self):
        try:
            result = self.callback(self.source)
            if self.phase == "Run Program":
                tokens, errors, proc = result if len(result) == 3 else (result[0], result[1], None)
                self.finished.emit(self.phase, tokens, errors, proc)
            else:
                tokens, errors = result
                self.finished.emit(self.phase, tokens, errors, None)
        except Exception as exc:
            self.finished.emit(self.phase, [], [f"{self.phase} internal error: {exc}"], None)


class ProcessStreamer(QThread):
    output = Signal(str, str)
    done = Signal(int)

    def __init__(
        self,
        proc: subprocess.Popen,
        hard_timeout: float | None = None,
        silent_timeout: float | None = None,
        max_output_chars: int = 1_000_000,
    ):
        super().__init__()
        self.proc = proc
        self.stop_requested = threading.Event()
        # timeouts: None = no limit
        self.hard_timeout = hard_timeout
        self.silent_timeout = silent_timeout
        self.max_output_chars = max_output_chars

    def stop(self):
        self.stop_requested.set()
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.kill()
            except Exception:
                pass

    def send_input(self, text: str):
        if not self.proc or self.proc.poll() is not None or not self.proc.stdin:
            return
        try:
            self.proc.stdin.write((text + "\n").encode("utf-8", errors="replace"))
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError):
            pass

    def run(self):
        # Bounded queue to avoid unbounded memory growth on spamming programs
        events: queue.Queue[tuple[str, str]] = queue.Queue(maxsize=4000)
        output_count = 0
        output_count_lock = threading.Lock()

        def reader(stream, tag):
            nonlocal output_count
            while not self.stop_requested.is_set():
                try:
                    chunk = stream.read(4096)
                except Exception:
                    break
                if chunk in (b"", ""):
                    break
                if isinstance(chunk, bytes):
                    chunk = chunk.decode("utf-8", errors="replace")

                # Track total output safely
                with output_count_lock:
                    output_count += len(chunk)
                    too_much = output_count > (self.max_output_chars or 1_000_000)

                if too_much:
                    try:
                        events.put_nowait(("\n[Execution stopped: excessive output detected]\n", "stderr"))
                    except queue.Full:
                        pass
                    try:
                        self.proc.kill()
                    except Exception:
                        pass
                    self.stop_requested.set()
                    break

                # Try to enqueue, but handle overflow gracefully
                try:
                    events.put((chunk, tag), timeout=0.2)
                except queue.Full:
                    try:
                        events.put_nowait(("\n[Execution stopped: terminal queue overflow]\n", "stderr"))
                    except queue.Full:
                        pass
                    try:
                        self.proc.kill()
                    except Exception:
                        pass
                    self.stop_requested.set()
                    break

        threads = []
        if self.proc.stdout:
            threads.append(threading.Thread(target=reader, args=(self.proc.stdout, "stdout"), daemon=True))
        if self.proc.stderr:
            threads.append(threading.Thread(target=reader, args=(self.proc.stderr, "stderr"), daemon=True))
        for thread in threads:
            thread.start()

        # Watchdog / pump loop
        started = time.monotonic()
        last_activity = started
        HARD_TIMEOUT = self.hard_timeout
        SILENT_TIMEOUT = self.silent_timeout

        while True:
            now = time.monotonic()

            # Drain a batch of queued events and coalesce them by tag to reduce signal frequency
            processed = 0
            pending: dict[str, list[str]] = {}
            while processed < 300:
                try:
                    text, tag = events.get_nowait()
                except queue.Empty:
                    break
                last_activity = time.monotonic()
                pending.setdefault(tag or "stdout", []).append(text)
                processed += 1

            # Emit coalesced chunks (limit size per emit to avoid huge signals)
            MAX_EMIT = 65536
            for tag, chunks in pending.items():
                agg = "".join(chunks)
                start = 0
                while start < len(agg):
                    part = agg[start : start + MAX_EMIT]
                    self.output.emit(part, tag)
                    start += MAX_EMIT

            # Hard runtime cutoff
            if HARD_TIMEOUT is not None and now - started > HARD_TIMEOUT:
                try:
                    events.put_nowait(("\n[Execution timeout: exceeded 300s runtime]\n", "stderr"))
                except queue.Full:
                    pass
                try:
                    self.proc.kill()
                except Exception:
                    pass
                self.stop_requested.set()
                break

            # Silent timeout (no output and no input)
            if SILENT_TIMEOUT is not None and now - last_activity > SILENT_TIMEOUT:
                try:
                    events.put_nowait(("\n[Execution timeout: no terminal activity for 300s]\n", "stderr"))
                except queue.Full:
                    pass
                try:
                    self.proc.kill()
                except Exception:
                    pass
                self.stop_requested.set()
                break

            if self.proc.poll() is not None:
                break

            time.sleep(0.03)

        # final drain — coalesce remaining events before emitting
        remaining: dict[str, list[str]] = {}
        while not events.empty():
            try:
                text, tag = events.get_nowait()
            except queue.Empty:
                break
            remaining.setdefault(tag or "stdout", []).append(text)

        MAX_EMIT = 65536
        for tag, chunks in remaining.items():
            agg = "".join(chunks)
            start = 0
            while start < len(agg):
                part = agg[start : start + MAX_EMIT]
                self.output.emit(part, tag)
                start += MAX_EMIT

        # join reader threads briefly
        for t in threads:
            t.join(timeout=0.2)

        try:
            rc = self.proc.wait()
        except Exception:
            rc = -1

        self.done.emit(rc)


class ChungusCompilerGUI(QMainWindow):
    def __init__(
        self,
        lexer_callback=None,
        syntax_callback=None,
        semantic_callback=None,
        codegen_callback=None,
    ):
        super().__init__()
        self.lexer_callback = lexer_callback
        self.syntax_callback = syntax_callback
        self.semantic_callback = semantic_callback
        self.codegen_callback = codegen_callback
        self.theme_name = "Oceanic Blue"
        self.theme = THEMES[self.theme_name]
        self.active_pane: EditorPane | None = None
        self.buffers: list[EditorBuffer] = []
        self.compiler_worker: CompilerWorker | None = None
        self.streamer: ProcessStreamer | None = None
        self._syncing = False

        self.setWindowTitle("CHUNGUS COMPILER")
        self.resize(1440, 920)
        self.setMinimumSize(1100, 720)

        self.code_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.code_font.setPointSize(11)
        self.current_font_size = 11

        self._build_actions()
        self._build_shortcuts()
        self._build_menu()
        self._build_toolbar()
        self._build_layout()
        self._build_status_bar()
        self._new_editor_pane(EditorBuffer())
        self._load_sample_on_start()
        self.apply_theme(self.theme_name)
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)

    def _build_actions(self):
        self.open_action = QAction("Open", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self.open_file)

        self.save_action = QAction("Save", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_file)

        self.find_action = QAction("Find", self)
        self.find_action.setShortcut("Ctrl+F")
        self.find_action.triggered.connect(lambda: self.search_box.setFocus())

        self.split_h_action = QAction("Split", self)
        self.split_h_action.triggered.connect(lambda: self.split_editor(Qt.Horizontal))

        self.zoom_in_action = QAction("Zoom In", self)
        self.zoom_in_action.setShortcut("Ctrl++")
        self.zoom_in_action.triggered.connect(self.increase_font)

        self.zoom_out_action = QAction("Zoom Out", self)
        self.zoom_out_action.setShortcut("Ctrl+-")
        self.zoom_out_action.triggered.connect(self.decrease_font)

    def _build_shortcuts(self):
        for sequence in ("Ctrl++", "Ctrl+=", "Ctrl+Plus"):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ApplicationShortcut)
            shortcut.activated.connect(self.increase_font)
        for sequence in ("Ctrl+-", "Ctrl+_", "Ctrl+Minus"):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ApplicationShortcut)
            shortcut.activated.connect(self.decrease_font)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.KeyPress and event.modifiers() & Qt.ControlModifier:
            key = event.key()
            if key in (Qt.Key_Plus, Qt.Key_Equal):
                self.increase_font()
                return True
            if key in (Qt.Key_Minus, Qt.Key_Underscore):
                self.decrease_font()
                return True
        return super().eventFilter(watched, event)

    def _build_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        edit_menu = menu.addMenu("Edit")
        edit_menu.addAction(self.find_action)
        edit_menu.addAction(self.split_h_action)

        view_menu = menu.addMenu("View")
        theme_menu = view_menu.addMenu("Theme")
        for name in THEMES:
            action = QAction(name, self)
            action.triggered.connect(lambda _, n=name: self.apply_theme(n))
            theme_menu.addAction(action)
        view_menu.addSeparator()
        view_menu.addAction(self.zoom_in_action)
        view_menu.addAction(self.zoom_out_action)

        snippet_menu = menu.addMenu("Snippet")
        snippet_menu.addAction("Show / Hide Snippets", self.toggle_snippets)
        snippet_menu.addSeparator()
        for name in SNIPPETS:
            action = QAction(name, self)
            action.triggered.connect(lambda _checked=False, n=name: self.insert_snippet_by_name(n))
            snippet_menu.addAction(action)

        help_menu = menu.addMenu("Help")
        help_menu.addAction("About Chungus Compiler", self.show_about)

    def _build_toolbar(self):
        toolbar = QToolBar("Compiler Commands")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(toolbar)

        self.btn_lexer = self._tool_button("▶ Lexer", lambda: self.run_phase("Lexer", self.lexer_callback), "analyze")
        self.btn_syntax = self._tool_button("▶ Syntax", lambda: self.run_phase("Syntax", self.syntax_callback), "analyze")
        self.btn_semantic = self._tool_button("▶ Semantic", lambda: self.run_phase("Semantic", self.semantic_callback), "analyze")
        self.btn_codegen = self._tool_button("▶ Run", lambda: self.run_phase("Run Program", self.codegen_callback), "run")
        self.btn_stop = self._tool_button("Stop", self.stop_process, "danger")
        self.btn_split_h = self._tool_button("Split", lambda: self.split_editor(Qt.Horizontal), "layout")
        self.btn_clear = self._tool_button("Clear", self.clear_bottom_panels, "utility")

        for group in [
            [self.btn_lexer, self.btn_syntax, self.btn_semantic],
            [self.btn_codegen, self.btn_stop],
        ]:
            for btn in group:
                toolbar.addWidget(btn)
            toolbar.addSeparator()
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        toolbar.addWidget(self.btn_split_h)
        toolbar.addWidget(self.btn_clear)
        self.btn_stop.setEnabled(False)

    def _tool_button(self, label: str, callback: Callable, role: str) -> QPushButton:
        button = QPushButton(label)
        button.setProperty("buttonRole", role)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(callback)
        button.setMinimumSize(92, 36)
        return button

    def _nav_button(self, label: str, callback: Callable) -> QPushButton:
        button = QPushButton(label)
        button.setObjectName("findNavButton")
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(callback)
        button.setFixedSize(34, 34)
        return button

    def _build_layout(self):
        root_splitter = QSplitter(Qt.Horizontal)
        self.root_splitter = root_splitter
        self.setCentralWidget(root_splitter)

        self.snippet_drawer = self._build_snippets()
        self.snippet_drawer.setMinimumWidth(0)
        self.snippet_drawer.setMaximumWidth(0)
        self.snippet_drawer.setVisible(False)
        root_splitter.addWidget(self.snippet_drawer)

        content_splitter = QSplitter(Qt.Horizontal)
        root_splitter.addWidget(content_splitter)

        center_splitter = QSplitter(Qt.Vertical)
        content_splitter.addWidget(center_splitter)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(12, 10, 8, 8)
        center_layout.setSpacing(8)

        title_row = QHBoxLayout()
        self.app_title = QLabel("CHUNGUS COMPILER")
        self.app_title.setObjectName("appTitle")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Find in active editor")
        self.search_box.returnPressed.connect(self.find_next)
        self.search_box.textChanged.connect(self.highlight_search)
        self.search_box.setMinimumWidth(250)
        self.btn_find_prev = self._nav_button("▲", self.find_previous)
        self.btn_find_next = self._nav_button("▼", self.find_next)
        title_row.addWidget(self.app_title)
        title_row.addStretch(1)
        title_row.addWidget(self.search_box)
        title_row.addWidget(self.btn_find_prev)
        title_row.addWidget(self.btn_find_next)
        center_layout.addLayout(title_row)

        self.editor_splitter = QSplitter(Qt.Horizontal)
        center_layout.addWidget(self.editor_splitter)
        center_splitter.addWidget(center)

        self.bottom_tabs = QTabWidget()
        self._build_bottom_panel()
        center_splitter.addWidget(self.bottom_tabs)
        center_splitter.setSizes([560, 360])

        self.inspector = QTabWidget()
        self.inspector.setMinimumWidth(390)
        self._build_inspector()
        content_splitter.addWidget(self.inspector)
        content_splitter.setSizes([1040, 440])
        root_splitter.setSizes([0, 1480])

    def _build_snippets(self):
        container = QWidget()
        container.setObjectName("snippetDrawer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 8, 8)
        layout.setSpacing(8)
        title = QLabel("Code Snippets")
        title.setObjectName("sideTitle")
        self.snippet_list = QListWidget()
        for name in SNIPPETS:
            item = QListWidgetItem(name)
            item.setToolTip(SNIPPETS[name])
            self.snippet_list.addItem(item)
        self.snippet_list.itemDoubleClicked.connect(self.insert_snippet)
        layout.addWidget(title)
        layout.addWidget(self.snippet_list)
        return container

    def toggle_snippets(self):
        opening = self.snippet_drawer.maximumWidth() == 0
        start = self.snippet_drawer.maximumWidth()
        end = 270 if opening else 0
        if opening:
            self.snippet_drawer.setVisible(True)
            self.root_splitter.setSizes([270, max(900, self.width() - 270)])
        else:
            self.root_splitter.setSizes([0, max(900, self.width())])
        self.snippet_animation = QPropertyAnimation(self.snippet_drawer, b"maximumWidth", self)
        self.snippet_animation.setDuration(220)
        self.snippet_animation.setStartValue(start)
        self.snippet_animation.setEndValue(end)
        self.snippet_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.snippet_animation.finished.connect(lambda: self.snippet_drawer.setVisible(opening))
        self.snippet_animation.start()

    def _build_inspector(self):
        self.token_filter = QLineEdit()
        self.token_filter.setPlaceholderText("Filter tokens")
        self.token_filter.textChanged.connect(self.filter_tokens)
        token_widget = QWidget()
        token_layout = QVBoxLayout(token_widget)
        token_layout.setContentsMargins(0, 0, 0, 0)
        token_layout.addWidget(self.token_filter)
        self.token_table = QTableWidget(0, 4)
        self.token_table.setHorizontalHeaderLabels(["Line", "Col", "Lexeme", "Token"])
        self.token_table.verticalHeader().setVisible(False)
        self.token_table.setShowGrid(False)
        self.token_table.setAlternatingRowColors(True)
        self.token_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.token_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.token_table.horizontalHeader().setStretchLastSection(True)
        self.token_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.token_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.token_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.token_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.token_table.setSortingEnabled(False)
        token_layout.addWidget(self.token_table)
        self.inspector.addTab(token_widget, "Token Stream")

    def _build_bottom_panel(self):
        self.problems_table = QTableWidget(0, 4)
        self.problems_table.setHorizontalHeaderLabels(["Phase", "Line", "Col", "Message"])
        self.problems_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.problems_table.cellDoubleClicked.connect(self.goto_problem)
        self.bottom_tabs.addTab(self.problems_table, "Problems")

        self.output_view = QPlainTextEdit()
        self.output_view.setReadOnly(True)
        self.output_view.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.bottom_tabs.addTab(self.output_view, "Output")

        terminal_widget = QWidget()
        terminal_layout = QVBoxLayout(terminal_widget)
        terminal_layout.setContentsMargins(0, 0, 0, 0)
        self.terminal_view = QPlainTextEdit()
        self.terminal_view.setReadOnly(True)
        self.terminal_view.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.terminal_input = QLineEdit()
        self.terminal_input.setPlaceholderText("Program input")
        self.terminal_input.returnPressed.connect(self.send_terminal_input)
        self.terminal_input.setEnabled(False)
        terminal_layout.addWidget(self.terminal_view)
        terminal_layout.addWidget(self.terminal_input)
        self.bottom_tabs.addTab(terminal_widget, "Terminal")

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.bottom_tabs.addTab(self.log_view, "Compilation Log")

    def _build_status_bar(self):
        status = QStatusBar()
        self.setStatusBar(status)
        self.status_phase = QLabel("Ready")
        self.status_file = QLabel("Untitled")
        self.status_cursor = QLabel("Ln 1, Col 1")
        self.status_errors = QLabel("0 problems")
        self.status_runtime = QLabel("Idle")
        status.addWidget(self.status_phase, 2)
        status.addWidget(self.status_file, 3)
        status.addPermanentWidget(self.status_errors)
        status.addPermanentWidget(self.status_cursor)
        status.addPermanentWidget(self.status_runtime)

    def _new_editor_pane(self, buffer: EditorBuffer, orientation: Qt.Orientation | None = None) -> EditorPane:
        if buffer not in self.buffers:
            self.buffers.append(buffer)
        if orientation is not None:
            self.editor_splitter.setOrientation(orientation)
        pane = EditorPane(buffer, self.theme)
        pane.editor.textChanged.connect(lambda p=pane: self.editor_text_changed(p))
        pane.editor.focused.connect(lambda _editor, p=pane: self.set_active_pane(p))
        pane.editor.cursor_moved.connect(self.update_cursor_status)
        pane.close_requested.connect(self.close_split)
        pane.apply_theme(self.theme, self.code_font)
        self.editor_splitter.addWidget(pane)
        self.set_active_pane(pane)
        self.update_split_close_buttons()
        return pane

    def editor_panes(self) -> list[EditorPane]:
        panes = []
        if not hasattr(self, "editor_splitter"):
            return panes
        for index in range(self.editor_splitter.count()):
            pane = self.editor_splitter.widget(index)
            if isinstance(pane, EditorPane):
                panes.append(pane)
        return panes

    def _load_sample_on_start(self):
        sample = PROJECT_ROOT / "samples" / "program1.chg"
        if sample.exists() and self.active_pane:
            self.load_path_into_pane(sample, self.active_pane, analyze=False)

    def set_active_pane(self, pane: EditorPane):
        self.active_pane = pane
        self.status_file.setText(str(pane.buffer.path) if pane.buffer.path else "Untitled")
        pane.editor.emit_cursor_position()

    def active_editor(self) -> CodeEditor | None:
        return self.active_pane.editor if self.active_pane else None

    def editor_text_changed(self, pane: EditorPane):
        if self._syncing:
            return
        self._syncing = True
        buffer = pane.buffer
        buffer.content = pane.editor.toPlainText()
        buffer.modified = True
        for other in list(buffer.panes):
            other.refresh_title()
            if other is pane:
                continue
            cursor_pos = other.editor.textCursor().position()
            other.editor.blockSignals(True)
            other.editor.setPlainText(buffer.content)
            cursor = other.editor.textCursor()
            cursor.setPosition(min(cursor_pos, len(buffer.content)))
            other.editor.setTextCursor(cursor)
            other.editor.blockSignals(False)
        self._syncing = False

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Source File",
            str(PROJECT_ROOT),
            "Chungus Files (*.chg *.chungus);;Text Files (*.txt);;All Files (*.*)",
        )
        if path and self.active_pane:
            self.load_path_into_pane(Path(path), self.active_pane)

    def load_path_into_pane(self, path: Path, pane: EditorPane, analyze: bool = True):
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "Open Source File", f"Could not read file:\n{exc}")
            return
        existing = next((b for b in self.buffers if b.path == path), None)
        buffer = existing or EditorBuffer(content=content, path=path, modified=False)
        if buffer not in self.buffers:
            self.buffers.append(buffer)
        buffer.content = content
        buffer.modified = False
        pane.set_buffer(buffer, self.theme)
        pane.apply_theme(self.theme, self.code_font)
        self.set_active_pane(pane)
        self.log(f"Opened {path}")
        if analyze:
            self.run_phase("Lexer", self.lexer_callback, quiet=True)

    def save_file(self):
        if not self.active_pane:
            return
        buffer = self.active_pane.buffer
        if not buffer.path:
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Source Code",
                str(PROJECT_ROOT / "untitled.chg"),
                "Chungus Files (*.chg *.chungus);;Text Files (*.txt);;All Files (*.*)",
            )
            if not path:
                return
            buffer.path = Path(path)
        try:
            buffer.path.write_text(buffer.content, encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "Save Source Code", f"Could not save file:\n{exc}")
            return
        buffer.modified = False
        for pane in buffer.panes:
            pane.refresh_title()
        self.status_file.setText(str(buffer.path))
        self.log(f"Saved {buffer.path}")

    def split_editor(self, orientation: Qt.Orientation):
        if not self.active_pane:
            return
        self._new_editor_pane(self.active_pane.buffer, orientation)

    def close_split(self, pane: EditorPane):
        if self.editor_splitter.count() <= 1:
            return
        if pane in pane.buffer.panes:
            pane.buffer.panes.remove(pane)
        pane.setParent(None)
        pane.deleteLater()
        first = self.editor_splitter.widget(0)
        if isinstance(first, EditorPane):
            self.set_active_pane(first)
        self.update_split_close_buttons()

    def update_split_close_buttons(self):
        can_close = self.editor_splitter.count() > 1
        for i in range(self.editor_splitter.count()):
            pane = self.editor_splitter.widget(i)
            if isinstance(pane, EditorPane):
                pane.close_button.setVisible(can_close)

    def insert_snippet(self, item: QListWidgetItem):
        self.insert_snippet_by_name(item.text())

    def insert_snippet_by_name(self, name: str):
        editor = self.active_editor()
        if not editor:
            return
        snippet = SNIPPETS[name]
        editor.textCursor().insertText(snippet)
        editor.setFocus()

    def find_next(self):
        editor = self.active_editor()
        term = self.search_box.text()
        if not editor or not term:
            return
        if not editor.find(term):
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            editor.setTextCursor(cursor)
            editor.find(term)

    def find_previous(self):
        editor = self.active_editor()
        term = self.search_box.text()
        if not editor or not term:
            return
        if not editor.find(term, QTextDocument.FindBackward):
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.End)
            editor.setTextCursor(cursor)
            editor.find(term, QTextDocument.FindBackward)

    def highlight_search(self):
        # Qt's native incremental find is less noisy than persistent custom marks here.
        pass

    def run_phase(self, phase: str, callback: Callable, quiet: bool = False):
        if not callable(callback):
            QMessageBox.information(self, phase, f"{phase} backend is not configured.")
            return
        if self.compiler_worker and self.compiler_worker.isRunning():
            return
        source = self.active_pane.buffer.content if self.active_pane else ""
        if not quiet:
            self.clear_analysis_for_run()
        self.set_phase_status(f"{phase} running")
        self.log(f"{phase} started")
        self.compiler_worker = CompilerWorker(phase, source.expandtabs(4), callback)
        self.compiler_worker.finished.connect(self.finish_phase)
        self.compiler_worker.start()

    def finish_phase(self, phase: str, tokens, errors: list, proc):
        self.populate_tokens(tokens)
        diagnostics = self.extract_diagnostics(phase, errors)
        self.populate_diagnostics(diagnostics)
        self.status_errors.setText(f"{len(diagnostics)} problems")

        if errors:
            text = "\n".join(str(e) for e in errors)
            self.output_view.setPlainText(text)
            self.log(f"{phase} finished with {len(errors)} reported messages")
            self.set_phase_status(f"{phase} failed")
            self.bottom_tabs.setCurrentWidget(self.problems_table)
        else:
            self.output_view.setPlainText(f">>> {phase} complete. No errors found.")
            self.log(f"{phase} finished successfully")
            self.set_phase_status(f"{phase} complete")

        if phase == "Run Program":
            if proc is not None:
                self.start_process_stream(proc)
            else:
                self.btn_codegen.setEnabled(True)

    def start_process_stream(self, proc):
        self.terminal_view.clear()
        self.terminal_input.setEnabled(True)
        self.terminal_input.setFocus()
        self.btn_stop.setEnabled(True)
        self.btn_codegen.setEnabled(False)
        self.set_runtime_status("Running")
        self.bottom_tabs.setCurrentWidget(self.terminal_view.parentWidget())
        self.streamer = ProcessStreamer(proc)
        self.streamer.output.connect(self.append_terminal)
        self.streamer.done.connect(self.process_done)
        self.streamer.start()

    def append_terminal(self, text: str, tag: str):
        cursor = self.terminal_view.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        # Render stderr in danger color, user-typed input with reduced opacity, otherwise normal terminal text
        if tag == "stderr":
            color = QColor(self.theme["danger"])
        elif tag in ("term_input", "stdin"):
            color = QColor(self.theme.get("muted", self.theme["terminal_text"]))
            # reduce opacity for user inputs to visually separate them from program output
            color.setAlpha(160)
        else:
            color = QColor(self.theme["terminal_text"])
        fmt.setForeground(color)
        cursor.insertText(text, fmt)
        self.terminal_view.setTextCursor(cursor)
        self.terminal_view.ensureCursorVisible()

    def send_terminal_input(self):
        text = self.terminal_input.text()
        self.terminal_input.clear()
        if not text:
            return
        # show user input in terminal with muted opacity
        self.append_terminal(text + "\n", "term_input")
        if self.streamer:
            self.streamer.send_input(text)

    def stop_process(self):
        if self.streamer:
            self.streamer.stop()
            self.append_terminal("\n[Process killed by user]\n", "stderr")

    def process_done(self, rc: int):
        self.terminal_input.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.btn_codegen.setEnabled(True)
        self.set_runtime_status("Idle")
        if rc == 0:
            self.append_terminal("\n=== Program finished (exit 0) ===\n", "stdout")
            self.set_phase_status("Program finished successfully")
        else:
            self.append_terminal(f"\n=== Program exited with code {rc} ===\n", "stderr")
            self.set_phase_status(f"Program exited with code {rc}")

    def clear_analysis_for_run(self):
        self.output_view.clear()
        self.problems_table.setRowCount(0)
        self.token_table.setRowCount(0)

    def clear_bottom_panels(self):
        self.output_view.clear()
        self.terminal_view.clear()
        self.log_view.clear()
        self.problems_table.setRowCount(0)
        self.status_errors.setText("0 problems")

    def populate_tokens(self, tokens: Iterable):
        self.token_table.setSortingEnabled(False)
        self.token_table.setRowCount(0)
        for token in tokens or []:
            token_type = getattr(token, "type", token.get("type") if isinstance(token, dict) else "")
            if hasattr(token_type, "name"):
                token_type = token_type.name
            line = getattr(token, "line", token.get("line") if isinstance(token, dict) else "")
            col = getattr(token, "col", token.get("col") if isinstance(token, dict) else "")
            raw_lexeme = getattr(token, "lexeme", token.get("lexeme") if isinstance(token, dict) else str(token))
            lexeme = str(raw_lexeme).replace("\n", "\\n").replace("\r", "\\r").replace("\t", "    ")
            if str(token_type).lower() in {"whitespace", "whitespaces"}:
                lexeme = "space" if not lexeme.strip() else lexeme
            row = self.token_table.rowCount()
            self.token_table.insertRow(row)
            for column, value in enumerate([line, col, lexeme, token_type]):
                item = QTableWidgetItem(str(value))
                if column in (0, 1):
                    item.setTextAlignment(Qt.AlignCenter)
                self.token_table.setItem(row, column, item)
        self.filter_tokens()
        self.token_table.resizeRowsToContents()

    def filter_tokens(self):
        term = self.token_filter.text().lower()
        for row in range(self.token_table.rowCount()):
            visible = not term
            if term:
                for col in range(self.token_table.columnCount()):
                    item = self.token_table.item(row, col)
                    if item and term in item.text().lower():
                        visible = True
                        break
            self.token_table.setRowHidden(row, not visible)

    def extract_diagnostics(self, phase: str, errors: list) -> list[Diagnostic]:
        diagnostics = []
        for error in errors or []:
            message = str(error)
            line = None
            col = None
            match = re.search(r"(?:line|ln)\s*[:=]?\s*(\d+).*?(?:col|column)\s*[:=]?\s*(\d+)", message, re.I | re.S)
            if match:
                line = int(match.group(1))
                col = int(match.group(2))
            else:
                caret = re.search(r"^\s*(\d+)\s*\|(.+?)\n\s*\|(\s*)\^", message, re.M)
                if caret:
                    line = int(caret.group(1))
                    col = len(caret.group(3)) + 1
            diagnostics.append(Diagnostic(phase=phase, message=message, line=line, col=col))
        return diagnostics

    def populate_diagnostics(self, diagnostics: list[Diagnostic]):
        self.problems_table.setRowCount(0)
        for diag in diagnostics:
            row = self.problems_table.rowCount()
            self.problems_table.insertRow(row)
            values = [
                diag.phase,
                "" if diag.line is None else str(diag.line),
                "" if diag.col is None else str(diag.col),
                diag.message.replace("\n", "  "),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 3:
                    item.setFont(self.code_font)
                if col in (1, 2):
                    item.setTextAlignment(Qt.AlignCenter)
                self.problems_table.setItem(row, col, item)

    def goto_problem(self, row: int, _column: int):
        editor = self.active_editor()
        if not editor:
            return
        line_item = self.problems_table.item(row, 1)
        col_item = self.problems_table.item(row, 2)
        if not line_item or not line_item.text():
            return
        line = int(line_item.text())
        col = int(col_item.text() or "1")
        cursor = editor.textCursor()
        block = editor.document().findBlockByLineNumber(max(0, line - 1))
        if block.isValid():
            cursor.setPosition(block.position() + max(0, col - 1))
            editor.setTextCursor(cursor)
            editor.setFocus()

    def update_cursor_status(self, line: int, col: int):
        self.status_cursor.setText(f"Ln {line}, Col {col}")

    def increase_font(self):
        if self.current_font_size >= 24:
            return
        self.current_font_size += 1
        self.apply_zoom()

    def decrease_font(self):
        if self.current_font_size <= 8:
            return
        self.current_font_size -= 1
        self.apply_zoom()

    def apply_zoom(self):
        self.code_font.setPointSize(self.current_font_size)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(self.stylesheet())
        for pane in self.editor_panes():
            pane.apply_theme(self.theme, self.code_font)
        ui_font = QFont()
        ui_font.setPointSize(max(9, self.current_font_size - 1))
        terminal_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        terminal_font.setPointSize(self.current_font_size)
        monospace_family = terminal_font.family()
        for widget in [self.output_view, self.terminal_view, self.log_view]:
            widget.document().setDefaultFont(terminal_font)
        for widget in [
            self.token_table,
            self.problems_table,
            self.output_view,
            self.terminal_view,
            self.log_view,
            self.token_filter,
            self.search_box,
            self.terminal_input,
            self.snippet_list,
        ]:
            widget.setFont(terminal_font if isinstance(widget, QPlainTextEdit) else ui_font)
        for widget in [self.output_view, self.terminal_view, self.log_view]:
            widget.setStyleSheet(
                widget.styleSheet()
                + f"\nQPlainTextEdit {{ font-family: '{monospace_family}'; }}\n"
            )
        row_height = max(28, int(self.current_font_size * 2.4))
        self.token_table.verticalHeader().setDefaultSectionSize(row_height)
        self.problems_table.verticalHeader().setDefaultSectionSize(row_height)

    def set_phase_status(self, text: str):
        self.status_phase.setText(text)
        if hasattr(self, "phase_badge"):
            self.phase_badge.setText(text.upper())

    def set_runtime_status(self, text: str):
        self.status_runtime.setText(text)
        if hasattr(self, "runtime_badge"):
            self.runtime_badge.setText(text.upper())

    def log(self, message: str):
        self.log_view.appendPlainText(message)

    def show_about(self):
        QMessageBox.information(
            self,
            "About Chungus Compiler",
            "Chungus Language Compiler Environment\n\n"
            "Created by:\n"
            "- Goyena, Shawn Kieffer E.\n- Cantal, Henkepeck T.\n- Capiral, Luis Gabriel A.\n"
            "- Frias, Railey Miguel B.\n- King, Mariano Luiz B.\n- Manguni, John Gabriel H.\n\n"
            "Course Project - CISTM, PLM",
        )

    def apply_theme(self, name: str):
        if name not in THEMES:
            return
        self.theme_name = name
        self.theme = THEMES[name]
        app = QApplication.instance()
        if app:
            app.setStyleSheet(self.stylesheet())
            self.refresh_theme_polish()
        for pane in self.editor_panes():
            pane.apply_theme(self.theme, self.code_font)

    def refresh_theme_polish(self):
        app = QApplication.instance()
        if not app:
            return
        for widget in self.findChildren(QWidget):
            app.style().unpolish(widget)
            app.style().polish(widget)
            widget.update()

    def stylesheet(self) -> str:
        t = self.theme
        table_font_size = max(9, self.current_font_size - 1)
        return f"""
        QMainWindow, QWidget {{
            background: {t["bg"]};
            color: {t["text"]};
            font-family: "Segoe UI", "Inter", sans-serif;
            font-size: 10pt;
        }}
        QMenuBar, QMenu, QToolBar, QStatusBar {{
            background: {t["surface"]};
            color: {t["text"]};
            border-color: {t["border"]};
        }}
        QToolBar {{
            spacing: 6px;
            padding: 6px;
            border-bottom: 1px solid {t["border"]};
        }}
        QSplitter::handle {{
            background: {t["border"]};
        }}
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        QSplitter::handle:vertical {{
            height: 2px;
        }}
        QPushButton {{
            background: {t["surface_2"]};
            color: {t["text"]};
            border: 1px solid {t["border"]};
            border-radius: 6px;
            padding: 6px 10px;
            font-weight: 600;
        }}
        QPushButton[buttonRole="file"] {{
            background: #2563eb;
            color: #ffffff;
            border-color: #2563eb;
        }}
        QPushButton[buttonRole="analyze"] {{
            background: {t["btn_analyze"]};
            color: #ffffff;
            border-color: {t["btn_analyze"]};
            border-bottom: 3px solid {t["purple"]};
        }}
        QPushButton[buttonRole="run"] {{
            background: {t["btn_run"]};
            color: #ffffff;
            border-color: {t["btn_run"]};
            border-bottom: 3px solid {t["accent_2"]};
        }}
        QPushButton[buttonRole="danger"] {{
            background: {t["btn_danger"]};
            color: #ffffff;
            border-color: {t["btn_danger"]};
            border-bottom: 3px solid {t["danger"]};
        }}
        QPushButton[buttonRole="layout"] {{
            background: {t["btn_layout"]};
            color: #ffffff;
            border-color: {t["btn_layout"]};
            border-bottom: 3px solid {t["accent"]};
        }}
        QPushButton[buttonRole="utility"] {{
            background: {t["btn_utility"]};
            color: #ffffff;
            border-color: {t["btn_utility"]};
            border-bottom: 3px solid {t["muted"]};
        }}
        QPushButton:hover {{
            border-color: {t["warning"]};
            color: #ffffff;
        }}
        QPushButton:pressed {{
            padding-top: 7px;
            padding-bottom: 5px;
        }}
        QPushButton:disabled {{
            color: {t["muted"]};
            background: {t["surface_2"]};
        }}
        QLabel#appTitle {{
            color: {t["text"]};
            font-size: 19pt;
            font-weight: 800;
            padding: 8px 4px;
        }}
        QLabel#sideTitle {{
            background: {t["surface_2"]};
            color: {t["text"]};
            border: 1px solid {t["border"]};
            border-radius: 6px;
            padding: 8px 10px;
            font-weight: 800;
        }}
        QWidget#snippetDrawer {{
            background: {t["surface"]};
            border-right: 1px solid {t["border"]};
        }}
        QLineEdit {{
            background: {t["surface"]};
            color: {t["text"]};
            border: 1px solid {t["border"]};
            border-radius: 6px;
            padding: 6px 8px;
        }}
        QPushButton#findNavButton {{
            background: {t["surface_2"]};
            color: {t["accent"]};
            border: 1px solid {t["border"]};
            border-radius: 6px;
            padding: 0;
            font-weight: 900;
        }}
        QPushButton#findNavButton:hover {{
            background: {t["accent"]};
            color: #ffffff;
            border-color: {t["accent"]};
        }}
        QTabWidget::pane {{
            border: 1px solid {t["border"]};
            background: {t["surface"]};
        }}
        QTabBar::tab {{
            background: {t["surface_2"]};
            color: {t["muted"]};
            padding: 7px 10px;
            border: 1px solid {t["border"]};
            border-bottom: 0;
        }}
        QTabBar::tab:selected {{
            background: {t["surface"]};
            color: {t["accent"]};
            font-weight: 700;
        }}
        QListWidget, QTableWidget {{
            background: {t["surface"]};
            color: {t["text"]};
            border: 1px solid {t["border"]};
            gridline-color: {t["border"]};
            selection-background-color: {t["accent"]};
            selection-color: {t["surface"]};
            font-size: {table_font_size}pt;
        }}
        QPlainTextEdit {{
            background: {t["surface"]};
            color: {t["terminal_text"]};
            border: 1px solid {t["border"]};
            font-family: monospace;
            selection-background-color: {t["accent"]};
            selection-color: {t["surface"]};
            font-size: {table_font_size}pt;
        }}
        QTableWidget {{
            alternate-background-color: {t["surface_2"]};
        }}
        QHeaderView::section {{
            background: {t["surface_2"]};
            color: {t["text"]};
            border: 0;
            border-right: 1px solid {t["border"]};
            border-bottom: 1px solid {t["border"]};
            padding: 6px;
            font-weight: 700;
        }}
        QStatusBar QLabel {{
            color: {t["muted"]};
            padding: 0 6px;
        }}
        """


ChungusLexerGUI = ChungusCompilerGUI
