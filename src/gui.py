import datetime
import os
import platform
import queue
import re
import subprocess
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, font, messagebox, ttk

try:
    import customtkinter as ctk
except ImportError as exc:
    raise ImportError(
        "CustomTkinter is required for the Chungus Compiler UI. "
        "Install dependencies with: pip install -r requirements.txt"
    ) from exc


# ==============================================================================
# 1. LANGUAGE CONFIGURATION
# ==============================================================================

KEYWORDS = sorted(
    [
        "true",
        "false",
        "read",
        "show",
        "if",
        "elif",
        "else",
        "while",
        "for",
        "in",
        "range",
        "int",
        "float",
        "str_to_arr",
        "arr_to_str",
        "length",
        "compare",
        "type",
        "and",
        "or",
        "fn",
        "ret",
        "todo",
        "close",
    ]
)

LITERALS = {
    "int_literal",
    "float_literal",
    "str_literal",
    "bool_literal",
}

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

DELIMS = {
    "(",
    ")",
    "[",
    "]",
    ",",
    ";",
    ":",
}


# ==============================================================================
# 2. UI HELPER CLASSES
# ==============================================================================

class ToolTip:
    def __init__(self, widget, text=""):
        self.waittime = 450
        self.wraplength = 240
        self.widget = widget
        self.text = text
        self.id = None
        self.tw = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
        self.id = None

    def showtip(self, event=None):
        if not self.text:
            return
        x = self.widget.winfo_rootx() + 18
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tw,
            text=self.text,
            justify="left",
            background="#111827",
            foreground="#f9fafb",
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=5,
            wraplength=self.wraplength,
            font=("Segoe UI", 9),
        )
        label.pack()

    def hidetip(self):
        if self.tw:
            self.tw.destroy()
        self.tw = None


class TextLineNumbers(tk.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textwidget = None
        self.bg_color = "#ffffff"
        self.fg_color = "#6b7280"

    def attach(self, text_widget):
        self.textwidget = text_widget

    def redraw(self, *args):
        self.delete("all")
        if not self.textwidget:
            return

        self.config(bg=self.bg_color)
        end_index = self.textwidget.index("end")
        total_lines = int(end_index.split(".")[0])

        for line_num in range(1, total_lines + 1):
            dline = self.textwidget.dlineinfo(f"{line_num}.0")
            if dline is None:
                continue
            self.create_text(
                38,
                dline[1],
                anchor="ne",
                text=str(line_num),
                fill=self.fg_color,
                font=self.textwidget.cget("font"),
            )


# ==============================================================================
# 3. MAIN APPLICATION CONTROLLER
# ==============================================================================

class ChungusLexerGUI:
    def __init__(
        self,
        root,
        lexer_callback=None,
        syntax_callback=None,
        semantic_callback=None,
        codegen_callback=None,
    ):
        self.root = root
        self.lexer_callback = lexer_callback
        self.syntax_callback = syntax_callback
        self.semantic_callback = semantic_callback
        self.codegen_callback = codegen_callback

        self.current_theme = tk.StringVar(value="Studio")
        self.search_open = False
        self.last_search_idx = "1.0"
        self.current_font_size = 12
        self._highlight_job = None

        self._running_proc = None
        self._proc_lock = threading.Lock()
        self._last_term_activity = 0.0
        self._output_char_count = 0
        self._io_events = queue.Queue(maxsize=4000)
        self._io_pump_active = False

        self.themes = self.build_themes()
        self.colors = self.themes[self.current_theme.get()]

        self.setup_window()
        self.init_fonts()
        self.build_ui_structure()
        self.apply_theme()
        self.on_code_change()

    def build_themes(self):
        return {
            "Studio": {
                "BG_COLOR": "#101418",
                "HEADER_BG": "#101418",
                "PANEL_BG": "#171c22",
                "SURFACE_BG": "#20262e",
                "TEXT_AREA_BG": "#0b0f14",
                "FG_COLOR": "#edf2f7",
                "TITLE_COLOR": "#f6c453",
                "SECONDARY_TEXT": "#9aa7b5",
                "STATUS_BAR_BG": "#171c22",
                "TREE_HEADING_BG": "#242b34",
                "TREE_EVEN_ROW": "#131820",
                "BORDER_COLOR": "#323b46",
                "ACCENT_BLUE": "#3ba7ff",
                "ACCENT_GREEN": "#48d597",
                "ACCENT_RED": "#ff5c73",
                "ACCENT_ORANGE": "#f6c453",
                "ACCENT_PURPLE": "#a78bfa",
                "BUTTON_FG": "#071014",
                "SELECT_BG": "#315f83",
                "SELECT_FG": "#ffffff",
                "BTN_TOOL_BG": "#20262e",
                "BTN_TOOL_FG": "#edf2f7",
                "TERM_BG": "#070a0f",
                "TERM_FG": "#d9e2ec",
                "TERM_INPUT_BG": "#101820",
            },
            "Dark": {
                "BG_COLOR": "#111317",
                "HEADER_BG": "#151922",
                "PANEL_BG": "#191d26",
                "SURFACE_BG": "#202633",
                "TEXT_AREA_BG": "#0f1218",
                "FG_COLOR": "#e5e7eb",
                "TITLE_COLOR": "#f8fafc",
                "SECONDARY_TEXT": "#9ca3af",
                "STATUS_BAR_BG": "#151922",
                "TREE_HEADING_BG": "#252b38",
                "TREE_EVEN_ROW": "#171b24",
                "BORDER_COLOR": "#303848",
                "ACCENT_BLUE": "#5b8def",
                "ACCENT_GREEN": "#3fb950",
                "ACCENT_RED": "#f85149",
                "ACCENT_ORANGE": "#d29922",
                "ACCENT_PURPLE": "#bc8cff",
                "BUTTON_FG": "#ffffff",
                "SELECT_BG": "#355d9f",
                "SELECT_FG": "#ffffff",
                "BTN_TOOL_BG": "#252b38",
                "BTN_TOOL_FG": "#e5e7eb",
                "TERM_BG": "#080b11",
                "TERM_FG": "#d1d5db",
                "TERM_INPUT_BG": "#111827",
            },
            "Light": {
                "BG_COLOR": "#f5f7fb",
                "HEADER_BG": "#ffffff",
                "PANEL_BG": "#ffffff",
                "SURFACE_BG": "#eef2f7",
                "TEXT_AREA_BG": "#ffffff",
                "FG_COLOR": "#1f2937",
                "TITLE_COLOR": "#111827",
                "SECONDARY_TEXT": "#6b7280",
                "STATUS_BAR_BG": "#e8edf5",
                "TREE_HEADING_BG": "#eef2f7",
                "TREE_EVEN_ROW": "#f8fafc",
                "BORDER_COLOR": "#d5dbe6",
                "ACCENT_BLUE": "#2563eb",
                "ACCENT_GREEN": "#059669",
                "ACCENT_RED": "#dc2626",
                "ACCENT_ORANGE": "#d97706",
                "ACCENT_PURPLE": "#7c3aed",
                "BUTTON_FG": "#ffffff",
                "SELECT_BG": "#bfdbfe",
                "SELECT_FG": "#111827",
                "BTN_TOOL_BG": "#e5e7eb",
                "BTN_TOOL_FG": "#111827",
                "TERM_BG": "#111827",
                "TERM_FG": "#f9fafb",
                "TERM_INPUT_BG": "#1f2937",
            },
            "Big Chungus": {
                "BG_COLOR": "#add8e6",
                "HEADER_BG": "#add8e6",
                "PANEL_BG": "#f0f8ff",
                "SURFACE_BG": "#ffdead",
                "TEXT_AREA_BG": "#ffffff",
                "FG_COLOR": "#404040",
                "TITLE_COLOR": "#ff4500",
                "SECONDARY_TEXT": "#708090",
                "STATUS_BAR_BG": "#f0f8ff",
                "TREE_HEADING_BG": "#ffdead",
                "TREE_EVEN_ROW": "#fff8dc",
                "BORDER_COLOR": "#87ceeb",
                "ACCENT_BLUE": "#ff4500",
                "ACCENT_GREEN": "#228b22",
                "ACCENT_RED": "#dc143c",
                "ACCENT_ORANGE": "#8b4513",
                "ACCENT_PURPLE": "#a9a9a9",
                "BUTTON_FG": "#ffffff",
                "SELECT_BG": "#ffd700",
                "SELECT_FG": "#404040",
                "BTN_TOOL_BG": "#87ceeb",
                "BTN_TOOL_FG": "#404040",
                "TERM_BG": "#1a1a2e",
                "TERM_FG": "#ffd700",
                "TERM_INPUT_BG": "#16213e",
            },
            "Oceanic": {
                "BG_COLOR": "#dff3f7",
                "HEADER_BG": "#e9fbff",
                "PANEL_BG": "#ffffff",
                "SURFACE_BG": "#d8edf4",
                "TEXT_AREA_BG": "#ffffff",
                "FG_COLOR": "#063f46",
                "TITLE_COLOR": "#015a7a",
                "SECONDARY_TEXT": "#45636a",
                "STATUS_BAR_BG": "#c9dde5",
                "TREE_HEADING_BG": "#d8edf4",
                "TREE_EVEN_ROW": "#f5fcff",
                "BORDER_COLOR": "#a9c9d4",
                "ACCENT_BLUE": "#0277bd",
                "ACCENT_GREEN": "#00796b",
                "ACCENT_RED": "#c62828",
                "ACCENT_ORANGE": "#ef6c00",
                "ACCENT_PURPLE": "#6a1b9a",
                "BUTTON_FG": "#ffffff",
                "SELECT_BG": "#81d4fa",
                "SELECT_FG": "#063f46",
                "BTN_TOOL_BG": "#c5e7f1",
                "BTN_TOOL_FG": "#063f46",
                "TERM_BG": "#0d1b2a",
                "TERM_FG": "#a8d8ea",
                "TERM_INPUT_BG": "#112233",
            },
            "Forest": {
                "BG_COLOR": "#192420",
                "HEADER_BG": "#1f2d28",
                "PANEL_BG": "#26352f",
                "SURFACE_BG": "#31453c",
                "TEXT_AREA_BG": "#101914",
                "FG_COLOR": "#e8f3eb",
                "TITLE_COLOR": "#c8facc",
                "SECONDARY_TEXT": "#a0b6a7",
                "STATUS_BAR_BG": "#16201c",
                "TREE_HEADING_BG": "#31453c",
                "TREE_EVEN_ROW": "#223029",
                "BORDER_COLOR": "#435d50",
                "ACCENT_BLUE": "#7dd3fc",
                "ACCENT_GREEN": "#86efac",
                "ACCENT_RED": "#fca5a5",
                "ACCENT_ORANGE": "#fdba74",
                "ACCENT_PURPLE": "#d8b4fe",
                "BUTTON_FG": "#102018",
                "SELECT_BG": "#166534",
                "SELECT_FG": "#ffffff",
                "BTN_TOOL_BG": "#31453c",
                "BTN_TOOL_FG": "#e8f3eb",
                "TERM_BG": "#07110c",
                "TERM_FG": "#bbf7d0",
                "TERM_INPUT_BG": "#102018",
            },
            "Synthwave": {
                "BG_COLOR": "#251b34",
                "HEADER_BG": "#2f2244",
                "PANEL_BG": "#21172e",
                "SURFACE_BG": "#3c2b59",
                "TEXT_AREA_BG": "#1a1325",
                "FG_COLOR": "#ffd6fb",
                "TITLE_COLOR": "#05ffa1",
                "SECONDARY_TEXT": "#c084fc",
                "STATUS_BAR_BG": "#191221",
                "TREE_HEADING_BG": "#3e2f5b",
                "TREE_EVEN_ROW": "#2b213a",
                "BORDER_COLOR": "#01cdfe",
                "ACCENT_BLUE": "#01cdfe",
                "ACCENT_GREEN": "#05ffa1",
                "ACCENT_RED": "#ff0055",
                "ACCENT_ORANGE": "#fffb96",
                "ACCENT_PURPLE": "#ff71ce",
                "BUTTON_FG": "#191221",
                "SELECT_BG": "#ff71ce",
                "SELECT_FG": "#2b213a",
                "BTN_TOOL_BG": "#3e2f5b",
                "BTN_TOOL_FG": "#01cdfe",
                "TERM_BG": "#0d0013",
                "TERM_FG": "#05ffa1",
                "TERM_INPUT_BG": "#1a0026",
            },
        }

    def setup_window(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.root.title("Chungus Compiler")
        self.root.geometry("1440x920")
        self.root.minsize(1120, 720)

    def init_fonts(self):
        os_name = platform.system()
        if os_name == "Darwin":
            base_font, title_family, mono_family = "SF Pro Text", "Avenir Next", "SF Mono"
        elif os_name == "Windows":
            base_font, title_family, mono_family = "Segoe UI", "Segoe UI Semibold", "Consolas"
        else:
            base_font, title_family, mono_family = "DejaVu Sans", "DejaVu Sans", "DejaVu Sans Mono"

        self.font_families = {
            "base": base_font,
            "title": title_family,
            "mono": mono_family,
        }
        self.fonts = {
            "title": font.Font(family=title_family, size=26, weight="bold"),
            "header": font.Font(family=base_font, size=13, weight="bold"),
            "subheader": font.Font(family=base_font, size=11, weight="bold"),
            "ui_reg": font.Font(family=base_font, size=10),
            "ui_small": font.Font(family=base_font, size=9),
            "code": font.Font(family=mono_family, size=self.current_font_size),
            "mono_small": font.Font(family=mono_family, size=10),
            "mono_bold": font.Font(family=mono_family, size=10, weight="bold"),
            "terminal": font.Font(family=mono_family, size=11),
        }
        self.ctk_fonts = {
            "title": ctk.CTkFont(family=title_family, size=26, weight="bold"),
            "header": ctk.CTkFont(family=base_font, size=13, weight="bold"),
            "subheader": ctk.CTkFont(family=base_font, size=11, weight="bold"),
            "ui_reg": ctk.CTkFont(family=base_font, size=10),
            "ui_small": ctk.CTkFont(family=base_font, size=9),
        }

    # ==========================================================================
    # 4. UI CONSTRUCTION
    # ==========================================================================

    def build_ui_structure(self):
        self.build_menu()
        self.main_container = ctk.CTkFrame(self.root, corner_radius=0)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        self.build_header()
        self.build_toolbar()
        self.body_frame = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.body_frame.pack(fill=tk.BOTH, expand=True)
        self.build_workspace()
        self.build_status_bar()

    def build_menu(self):
        self.menubar = tk.Menu(self.root)

        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="Open Source File...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Source Code...", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menubar.add_cascade(label="File", menu=file_menu)

        run_menu = tk.Menu(self.menubar, tearoff=0)
        run_menu.add_command(label="Run Lexer", command=self.run_lexer)
        run_menu.add_command(label="Run Syntax", command=self.run_syntax)
        run_menu.add_command(label="Run Semantic", command=self.run_semantic)
        run_menu.add_command(label="Compile and Run", command=self.run_codegen)
        run_menu.add_separator()
        run_menu.add_command(label="Stop Running Program", command=self.kill_process)
        self.menubar.add_cascade(label="Run", menu=run_menu)

        view_menu = tk.Menu(self.menubar, tearoff=0)
        theme_menu = tk.Menu(view_menu, tearoff=0)
        for theme_name in self.themes:
            theme_menu.add_radiobutton(
                label=theme_name,
                variable=self.current_theme,
                value=theme_name,
                command=self.set_theme,
            )
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        view_menu.add_command(label="Find in Code", command=self.toggle_search_bar, accelerator="Ctrl+F")
        view_menu.add_separator()
        view_menu.add_command(label="Increase Font", command=self.increase_font, accelerator="Ctrl++")
        view_menu.add_command(label="Decrease Font", command=self.decrease_font, accelerator="Ctrl+-")
        self.menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        self.menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=self.menubar)
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-f>", lambda e: self.toggle_search_bar())
        self.root.bind("<Control-plus>", lambda e: self.increase_font())
        self.root.bind("<Control-equal>", lambda e: self.increase_font())
        self.root.bind("<Control-minus>", lambda e: self.decrease_font())
        self.root.bind("<F5>", lambda e: self.run_codegen())

    def build_header(self):
        self.header_frame = ctk.CTkFrame(self.main_container, corner_radius=0)
        self.header_frame.pack(fill=tk.X, padx=0, pady=0)

        self.header_inner = ctk.CTkFrame(self.header_frame, corner_radius=0, fg_color="transparent")
        self.header_inner.pack(fill=tk.X, padx=18, pady=(14, 8))

        title_block = ctk.CTkFrame(self.header_inner, corner_radius=0, fg_color="transparent")
        title_block.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.title_label = ctk.CTkLabel(
            title_block,
            text="Chungus Compiler",
            font=self.ctk_fonts["title"],
            anchor="w",
        )
        self.title_label.pack(anchor="w")
        self.title_rule = ctk.CTkFrame(title_block, height=2, width=220, corner_radius=2)
        self.title_rule.pack(anchor="w", pady=(6, 0))

        controls = ctk.CTkFrame(self.header_inner, corner_radius=0, fg_color="transparent")
        controls.pack(side=tk.RIGHT)

        self.theme_selector = ctk.CTkOptionMenu(
            controls,
            values=list(self.themes.keys()),
            variable=self.current_theme,
            command=lambda _choice: self.set_theme(),
            width=150,
            height=34,
            corner_radius=8,
            font=self.ctk_fonts["ui_reg"],
            dropdown_font=self.ctk_fonts["ui_reg"],
        )
        self.theme_selector.pack(side=tk.LEFT)

    def build_toolbar(self):
        self.toolbar = ctk.CTkFrame(self.main_container, corner_radius=10)
        self.toolbar.pack(fill=tk.X, padx=18, pady=(0, 10))

        file_tools = ctk.CTkFrame(self.toolbar, corner_radius=0, fg_color="transparent")
        file_tools.pack(side=tk.LEFT, padx=10, pady=10)

        self.btn_open = self._make_tool_button(file_tools, "Open", self.open_file, width=70)
        self.btn_save = self._make_tool_button(file_tools, "Save", self.save_file, width=70)
        self.btn_find = self._make_tool_button(file_tools, "Find", self.toggle_search_bar, width=70)

        divider_a = ctk.CTkFrame(self.toolbar, width=1, height=36, corner_radius=0)
        divider_a.pack(side=tk.LEFT, padx=8, pady=10)

        pipeline = ctk.CTkFrame(self.toolbar, corner_radius=0, fg_color="transparent")
        pipeline.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=10)

        self.btn_lexer = self._make_primary_button(pipeline, "Lexical", self.run_lexer, width=122)
        self.btn_syntax = self._make_primary_button(pipeline, "Syntax", self.run_syntax, width=122)
        self.btn_semantic = self._make_primary_button(pipeline, "Semantic", self.run_semantic, width=132)
        self.btn_codegen = self._make_primary_button(pipeline, "Run Program", self.run_codegen, width=136)

        divider_b = ctk.CTkFrame(self.toolbar, width=1, height=36, corner_radius=0)
        divider_b.pack(side=tk.LEFT, padx=8, pady=10)

        utility_tools = ctk.CTkFrame(self.toolbar, corner_radius=0, fg_color="transparent")
        utility_tools.pack(side=tk.RIGHT, padx=10, pady=10)
        self.btn_zoom_out = self._make_tool_button(utility_tools, "A-", self.decrease_font, width=48)
        self.btn_zoom_in = self._make_tool_button(utility_tools, "A+", self.increase_font, width=48)
        self.btn_clear = self._make_tool_button(utility_tools, "Clear", self.clear_console, width=70)
        self.btn_kill = self._make_danger_button(utility_tools, "Stop", self.kill_process, width=70)
        self.btn_kill.configure(state="disabled")

        self.toolbar_dividers = [divider_a, divider_b]

    def _make_primary_button(self, master, text, command, width=92, fill=False):
        btn = ctk.CTkButton(
            master,
            text=text,
            command=command,
            width=width,
            height=34,
            corner_radius=8,
            font=self.ctk_fonts["subheader"],
        )
        if fill:
            btn.pack(fill=tk.X, padx=12, pady=4)
        else:
            btn.pack(side=tk.LEFT, padx=4)
        return btn

    def _make_tool_button(self, master, text, command, width=74, fill=False):
        btn = ctk.CTkButton(
            master,
            text=text,
            command=command,
            width=width,
            height=34,
            corner_radius=8,
            font=self.ctk_fonts["ui_reg"],
        )
        if fill:
            btn.pack(fill=tk.X, padx=12, pady=4)
        else:
            btn.pack(side=tk.LEFT, padx=4)
        return btn

    def _make_danger_button(self, master, text, command, width=74, fill=False):
        btn = ctk.CTkButton(
            master,
            text=text,
            command=command,
            width=width,
            height=34,
            corner_radius=8,
            font=self.ctk_fonts["ui_reg"],
        )
        if fill:
            btn.pack(fill=tk.X, padx=12, pady=4)
        else:
            btn.pack(side=tk.LEFT, padx=4)
        return btn

    def build_workspace(self):
        self.workspace_frame = ctk.CTkFrame(self.body_frame, corner_radius=0)
        self.workspace_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 12))

        self.paned_main = tk.PanedWindow(
            self.workspace_frame,
            orient=tk.HORIZONTAL,
            sashwidth=8,
            bd=0,
            showhandle=False,
        )
        self.paned_main.pack(fill=tk.BOTH, expand=True)

        self.left_pane = tk.PanedWindow(
            self.paned_main,
            orient=tk.VERTICAL,
            sashwidth=8,
            bd=0,
            showhandle=False,
        )
        self.paned_main.add(self.left_pane, minsize=520, stretch="always")

        self.editor_frame = ctk.CTkFrame(self.left_pane, corner_radius=8)
        self.left_pane.add(self.editor_frame, stretch="always", minsize=330)
        self.build_editor_area()

        self.console_frame = ctk.CTkFrame(self.left_pane, corner_radius=8)
        self.left_pane.add(self.console_frame, stretch="never", minsize=210)
        self.build_console_area()

        self.right_pane = ctk.CTkFrame(self.paned_main, corner_radius=8)
        self.paned_main.add(self.right_pane, minsize=380, stretch="never")
        self.build_analysis_area()

    def build_editor_area(self):
        header = ctk.CTkFrame(self.editor_frame, corner_radius=0, fg_color="transparent")
        header.pack(fill=tk.X, padx=12, pady=(10, 8))

        self.editor_header_lbl = ctk.CTkLabel(
            header,
            text="Source Code",
            font=self.ctk_fonts["header"],
            anchor="w",
        )
        self.editor_header_lbl.pack(side=tk.LEFT)

        self.search_frame = ctk.CTkFrame(self.editor_frame, corner_radius=8)
        self.search_label = ctk.CTkLabel(self.search_frame, text="Find", font=self.ctk_fonts["ui_small"])
        self.search_label.pack(side=tk.LEFT, padx=(10, 4), pady=8)
        self.entry_search = ctk.CTkEntry(
            self.search_frame,
            width=260,
            height=30,
            corner_radius=8,
            font=self.ctk_fonts["ui_reg"],
        )
        self.entry_search.pack(side=tk.LEFT, padx=5, pady=8)
        self.entry_search.bind("<Return>", self.find_next)
        self.btn_find_next = ctk.CTkButton(
            self.search_frame,
            text="Next",
            command=self.find_next,
            width=64,
            height=30,
            corner_radius=8,
            font=self.ctk_fonts["ui_small"],
        )
        self.btn_find_next.pack(side=tk.LEFT, padx=4, pady=8)
        self.btn_find_close = ctk.CTkButton(
            self.search_frame,
            text="Close",
            command=self.toggle_search_bar,
            width=64,
            height=30,
            corner_radius=8,
            font=self.ctk_fonts["ui_small"],
        )
        self.btn_find_close.pack(side=tk.RIGHT, padx=8, pady=8)

        self.text_container = tk.Frame(self.editor_frame, bd=0, highlightthickness=1)
        self.text_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        self.v_scroll = ttk.Scrollbar(self.text_container, orient=tk.VERTICAL, command=self._editor_yview)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.line_numbers = TextLineNumbers(self.text_container, width=48, highlightthickness=0, bd=0)
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        self.code_input = tk.Text(
            self.text_container,
            font=self.fonts["code"],
            undo=True,
            wrap=tk.NONE,
            yscrollcommand=self._editor_yscroll,
            padx=14,
            pady=12,
            borderwidth=0,
            highlightthickness=0,
            insertwidth=2,
        )
        self.code_input.config(tabs="1c")
        self.code_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.line_numbers.attach(self.code_input)

        self.autocomplete_listbox = tk.Listbox(
            self.text_container,
            height=6,
            bd=1,
            relief="solid",
            font=self.fonts["ui_reg"],
            exportselection=False,
        )

        self.code_input.bind("<Configure>", self.on_code_change)
        self.code_input.bind("<MouseWheel>", self._on_editor_mousewheel)
        self.code_input.bind("<Button-1>", self.update_cursor_info)
        self.code_input.bind("<Key>", lambda e: self.root.after(1, self.on_code_change))
        self.code_input.bind("<Return>", lambda e: self.root.after(1, self.on_code_change))
        self.code_input.bind("<BackSpace>", lambda e: self.root.after(1, self.on_code_change))
        self.code_input.bind("<Delete>", lambda e: self.root.after(1, self.on_code_change))
        self.code_input.bind("<Control-v>", lambda e: self.root.after(25, self.on_code_change))
        self.code_input.bind("<Control-V>", lambda e: self.root.after(25, self.on_code_change))
        self.code_input.bind("<KeyRelease>", self.check_autocomplete)
        self.code_input.bind("<Tab>", self.accept_autocomplete)
        self.code_input.bind("<Return>", self.accept_autocomplete, add="+")
        self.code_input.bind("<Up>", self.nav_autocomplete_up)
        self.code_input.bind("<Down>", self.nav_autocomplete_down)
        self.code_input.bind("<Escape>", self.hide_autocomplete)
        self.code_input.bind("<FocusOut>", self.hide_autocomplete)

    def build_console_area(self):
        header = ctk.CTkFrame(self.console_frame, corner_radius=0, fg_color="transparent")
        header.pack(fill=tk.X, padx=12, pady=(10, 8))

        self.console_header_lbl = ctk.CTkLabel(
            header,
            text="Terminal / Output",
            font=self.ctk_fonts["header"],
            anchor="w",
        )
        self.console_header_lbl.pack(side=tk.LEFT)

        self.term_status_lbl = ctk.CTkLabel(header, text="", font=self.ctk_fonts["ui_small"], width=90)
        self.term_status_lbl.pack(side=tk.LEFT, padx=(10, 0))

        self.input_bar = tk.Frame(self.console_frame, bd=0, highlightthickness=2)
        self.input_bar.pack(fill=tk.X, padx=12, pady=(0, 8))
        self.input_title_lbl = tk.Label(
            self.input_bar,
            text="Program Input",
            font=self.fonts["ui_small"],
            anchor="w",
            padx=10,
        )
        self.input_title_lbl.pack(side=tk.LEFT, pady=8)
        self._prompt_lbl = tk.Label(self.input_bar, text=">", font=self.fonts["header"], width=2)
        self._prompt_lbl.pack(side=tk.LEFT, padx=(4, 0), pady=8)

        self.term_input_var = tk.StringVar()
        self.term_entry = tk.Entry(
            self.input_bar,
            textvariable=self.term_input_var,
            font=self.fonts["terminal"],
            relief="flat",
            bd=0,
            highlightthickness=1,
            insertwidth=2,
        )
        self.term_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8, pady=8, ipady=7)
        self.term_entry.bind("<KeyPress>", self._on_term_keypress)
        self.term_entry.bind("<Return>", self._on_term_enter)
        self.term_entry.bind("<KP_Enter>", self._on_term_enter)
        self.btn_send_input = ctk.CTkButton(
            self.input_bar,
            text="Send",
            command=self.send_terminal_input,
            width=72,
            height=32,
            corner_radius=8,
            font=self.ctk_fonts["subheader"],
        )
        self.btn_send_input.pack(side=tk.RIGHT, padx=(0, 8), pady=7)

        self.output_container = tk.Frame(self.console_frame, bd=0, highlightthickness=1)
        self.output_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        scroll = ttk.Scrollbar(self.output_container, orient=tk.VERTICAL)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.error_output = tk.Text(
            self.output_container,
            font=self.fonts["terminal"],
            state=tk.DISABLED,
            wrap=tk.WORD,
            yscrollcommand=scroll.set,
            borderwidth=0,
            highlightthickness=0,
            padx=12,
            pady=10,
        )
        scroll.config(command=self.error_output.yview)
        self.error_output.pack(fill=tk.BOTH, expand=True)

    def build_analysis_area(self):
        header = ctk.CTkFrame(self.right_pane, corner_radius=0, fg_color="transparent")
        header.pack(fill=tk.X, padx=12, pady=(10, 8))

        self.analysis_header_lbl = ctk.CTkLabel(
            header,
            text="Compiler Analysis",
            font=self.ctk_fonts["header"],
            anchor="w",
        )
        self.analysis_header_lbl.pack(side=tk.LEFT)

        self.token_count_lbl = ctk.CTkLabel(header, text="0 tokens", font=self.ctk_fonts["ui_small"], anchor="e")
        self.token_count_lbl.pack(side=tk.RIGHT)

        self.notebook = ttk.Notebook(self.right_pane)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        self.tab_tokens = tk.Frame(self.notebook)
        self.notebook.add(self.tab_tokens, text="Token Stream")

        cols = ("Line", "Col", "Lexeme", "Token")
        self.token_tree = ttk.Treeview(self.tab_tokens, columns=cols, show="headings", selectmode="browse")

        vsb = ttk.Scrollbar(self.tab_tokens, orient="vertical", command=self.token_tree.yview)
        hsb = ttk.Scrollbar(self.tab_tokens, orient="horizontal", command=self.token_tree.xview)
        self.token_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.token_tree.pack(fill=tk.BOTH, expand=True)

        self.token_tree.heading("Line", text="Ln", command=lambda: self.sort_column("Line", False))
        self.token_tree.heading("Col", text="Col", command=lambda: self.sort_column("Col", False))
        self.token_tree.heading("Lexeme", text="Lexeme", command=lambda: self.sort_column("Lexeme", False))
        self.token_tree.heading("Token", text="Token Type", command=lambda: self.sort_column("Token", False))

        self.token_tree.column("Line", width=56, anchor="center", stretch=False)
        self.token_tree.column("Col", width=56, anchor="center", stretch=False)
        self.token_tree.column("Lexeme", width=160, anchor="w")
        self.token_tree.column("Token", width=170, anchor="w")

    def build_status_bar(self):
        self.status_bar = ctk.CTkFrame(self.main_container, height=30, corner_radius=0)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_msg = ctk.CTkLabel(self.status_bar, text="Ready", font=self.ctk_fonts["ui_small"], anchor="w")
        self.status_msg.pack(side=tk.LEFT, padx=12)

        self.status_time = ctk.CTkLabel(self.status_bar, text="", font=self.ctk_fonts["ui_small"])
        self.status_time.pack(side=tk.RIGHT, padx=12)

        self.status_cursor = ctk.CTkLabel(self.status_bar, text="Ln 1, Col 1", font=self.ctk_fonts["ui_small"])
        self.status_cursor.pack(side=tk.RIGHT, padx=8)
        self.update_time()

    # ==========================================================================
    # 5. INTERACTIVE TERMINAL LOGIC
    # ==========================================================================

    def _show_input_bar(self):
        c = self.colors
        self.input_bar.config(bg=c["TERM_INPUT_BG"], highlightbackground=c["ACCENT_GREEN"])
        self.input_title_lbl.config(bg=c["TERM_INPUT_BG"], fg=c["ACCENT_GREEN"])
        self._prompt_lbl.config(bg=c["TERM_INPUT_BG"], fg=c["ACCENT_GREEN"])
        self.term_entry.config(
            state="normal",
            bg=c["TEXT_AREA_BG"],
            fg=c["TERM_FG"],
            insertbackground=c["TERM_FG"],
            highlightbackground=c["ACCENT_GREEN"],
            highlightcolor=c["ACCENT_GREEN"],
        )
        self.btn_send_input.configure(
            fg_color=c["ACCENT_GREEN"],
            hover_color=c["ACCENT_BLUE"],
            text_color=c["BUTTON_FG"],
            border_color=c["ACCENT_GREEN"],
        )
        self.term_input_var.set("")
        self.term_entry.focus_set()
        self._last_term_activity = time.monotonic()
        self._output_char_count = 0
        self.term_status_lbl.configure(text="RUNNING", text_color=c["ACCENT_GREEN"])
        self.btn_kill.configure(state="normal")

    def _hide_input_bar(self):
        c = self.colors
        self.input_bar.config(bg=c["SURFACE_BG"], highlightbackground=c["BORDER_COLOR"])
        self.input_title_lbl.config(bg=c["SURFACE_BG"], fg=c["SECONDARY_TEXT"])
        self._prompt_lbl.config(bg=c["SURFACE_BG"], fg=c["SECONDARY_TEXT"])
        self.term_entry.config(
            state="normal",
            bg=c["TEXT_AREA_BG"],
            fg=c["FG_COLOR"],
            insertbackground=c["FG_COLOR"],
            highlightbackground=c["BORDER_COLOR"],
            highlightcolor=c["ACCENT_BLUE"],
        )
        self.btn_send_input.configure(
            fg_color=c["BTN_TOOL_BG"],
            hover_color=c["BORDER_COLOR"],
            text_color=c["BTN_TOOL_FG"],
            border_color=c["BORDER_COLOR"],
        )
        self.term_status_lbl.configure(text="")
        self.btn_kill.configure(state="disabled")

    def _on_term_enter(self, event=None):
        self.send_terminal_input()
        return "break"

    def send_terminal_input(self):
        text = self.term_input_var.get()
        self._last_term_activity = time.monotonic()

        with self._proc_lock:
            proc = self._running_proc

        if proc is None or proc.poll() is not None:
            self.status_msg.configure(text="Run Program first before sending input.")
            self._term_write("[Input not sent: no program is running]\n", tag="info")
            return

        self.term_input_var.set("")
        self._term_write(text + "\n", tag="term_input")
        self.status_msg.configure(text="Input sent to running program.")
        try:
            proc.stdin.write((text + "\n").encode("utf-8", errors="replace"))
            proc.stdin.flush()
        except (BrokenPipeError, OSError, AttributeError):
            self.status_msg.configure(text="Could not send input; the program is no longer accepting input.")

    def _on_term_keypress(self, event=None):
        self._last_term_activity = time.monotonic()

    def kill_process(self):
        with self._proc_lock:
            proc = self._running_proc
        if proc and proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass
            self._term_write("\n[Process killed by user]\n", tag="term_error")

    def _term_write(self, text, tag=None):
        def _do():
            self.error_output.config(state=tk.NORMAL)
            self.error_output.insert(tk.END, text, tag or "")
            self.error_output.see(tk.END)
            self.error_output.config(state=tk.DISABLED)

        self.root.after(0, _do)

    def _start_io_pump(self):
        if self._io_pump_active:
            return
        self._io_pump_active = True
        self.root.after(30, self._drain_io_events)

    def _drain_io_events(self):
        processed = 0
        pending_output = []
        finish_rc = None

        while processed < 300:
            try:
                event = self._io_events.get_nowait()
            except queue.Empty:
                break

            processed += 1
            kind = event[0]
            if kind == "output":
                _, text, tag = event
                self._output_char_count += len(text)
                pending_output.append((text, tag))
            elif kind == "finish":
                _, rc = event
                finish_rc = rc
                self._io_pump_active = False
                break

        if pending_output:
            self.error_output.config(state=tk.NORMAL)
            for text, tag in pending_output:
                self.error_output.insert(tk.END, text, tag or "")
            self.error_output.see(tk.END)
            self.error_output.config(state=tk.DISABLED)

        if finish_rc is not None:
            self._hide_input_bar()
            self.btn_codegen.configure(state="normal")
            self._set_stage("Runtime", "success" if finish_rc == 0 else "error")
            if finish_rc == 0:
                self._term_write("\n=== Program finished (exit 0) ===\n", tag="success")
                self.status_msg.configure(text="Program finished successfully.")
            else:
                self._term_write(f"\n=== Program exited with code {finish_rc} ===\n", tag="term_error")
                self.status_msg.configure(text=f"Program exited with code {finish_rc}.")

        if self._io_pump_active:
            self.root.after(30, self._drain_io_events)

    # ==========================================================================
    # 6. AUTOCOMPLETE AND EDITOR LOGIC
    # ==========================================================================

    def _editor_yscroll(self, first, last):
        self.v_scroll.set(first, last)
        self.line_numbers.redraw()

    def _editor_yview(self, *args):
        self.code_input.yview(*args)
        self.line_numbers.redraw()

    def _on_editor_mousewheel(self, event=None):
        self.root.after(1, self.line_numbers.redraw)

    def check_autocomplete(self, event=None):
        if event and event.keysym in ["Up", "Down", "Left", "Right", "Return", "BackSpace", "Tab", "Escape"]:
            return
        try:
            current_pos = self.code_input.index(tk.INSERT)
            line, _col = current_pos.split(".")
            text_line = self.code_input.get(f"{line}.0", current_pos)
            if not text_line or (not text_line[-1].isalnum() and text_line[-1] != "_"):
                self.hide_autocomplete()
                return

            partial_word = ""
            for char in reversed(text_line):
                if char.isalnum() or char == "_":
                    partial_word = char + partial_word
                else:
                    break

            if not partial_word:
                self.hide_autocomplete()
                return

            matches = [keyword for keyword in KEYWORDS if keyword.startswith(partial_word)]
            if matches:
                self.show_autocomplete(matches, partial_word)
            else:
                self.hide_autocomplete()
        except Exception:
            self.hide_autocomplete()

    def show_autocomplete(self, matches, partial_word):
        self.autocomplete_listbox.delete(0, tk.END)
        for match in matches:
            self.autocomplete_listbox.insert(tk.END, match)
        self.autocomplete_listbox.select_set(0)

        bbox = self.code_input.bbox(tk.INSERT)
        if bbox:
            x, y, _w, h = bbox
            x += self.line_numbers.winfo_width() + 10
            y += h + 10
            self.autocomplete_listbox.place(x=x, y=y)
            self.autocomplete_listbox.lift()

    def hide_autocomplete(self, event=None):
        self.autocomplete_listbox.place_forget()

    def nav_autocomplete_up(self, event):
        if self.autocomplete_listbox.winfo_ismapped():
            cur = self.autocomplete_listbox.curselection()
            if cur and cur[0] > 0:
                self.autocomplete_listbox.select_clear(cur[0])
                self.autocomplete_listbox.select_set(cur[0] - 1)
                self.autocomplete_listbox.see(cur[0] - 1)
            return "break"
        return None

    def nav_autocomplete_down(self, event):
        if self.autocomplete_listbox.winfo_ismapped():
            cur = self.autocomplete_listbox.curselection()
            if cur and cur[0] < self.autocomplete_listbox.size() - 1:
                self.autocomplete_listbox.select_clear(cur[0])
                self.autocomplete_listbox.select_set(cur[0] + 1)
                self.autocomplete_listbox.see(cur[0] + 1)
            return "break"
        return None

    def accept_autocomplete(self, event):
        if self.autocomplete_listbox.winfo_ismapped():
            selection = self.autocomplete_listbox.curselection()
            if selection:
                word = self.autocomplete_listbox.get(selection[0])
                current_pos = self.code_input.index(tk.INSERT)
                line, col = current_pos.split(".")
                text_line = self.code_input.get(f"{line}.0", current_pos)

                partial_len = 0
                for char in reversed(text_line):
                    if char.isalnum() or char == "_":
                        partial_len += 1
                    else:
                        break

                start_del = f"{line}.{int(col) - partial_len}"
                self.code_input.delete(start_del, current_pos)
                self.code_input.insert(start_del, word + " ")
                self.hide_autocomplete()
                self.root.after(1, self.on_code_change)
                return "break"
        return None

    def _schedule_highlighting(self):
        if self._highlight_job:
            self.root.after_cancel(self._highlight_job)
        self._highlight_job = self.root.after(80, self._highlight_editor)

    def _highlight_editor(self):
        self._highlight_job = None
        content = self.code_input.get("1.0", "end-1c")
        for tag in ("code_keyword", "code_string", "code_number", "code_comment", "code_builtin"):
            self.code_input.tag_remove(tag, "1.0", tk.END)

        keyword_pattern = r"\b(" + "|".join(re.escape(k) for k in KEYWORDS) + r")\b"
        for match in re.finditer(keyword_pattern, content):
            tag = "code_builtin" if match.group(0) in {"str_to_arr", "arr_to_str", "length", "compare", "type", "range"} else "code_keyword"
            self._tag_range(tag, match.start(), match.end())

        for match in re.finditer(r"'[^'\n]*(?:\n[^'\n]*)*'", content):
            self._tag_range("code_string", match.start(), match.end())

        for match in re.finditer(r"(?<![\w.])~?\d+(?:\.\d+)?(?![\w.])", content):
            self._tag_range("code_number", match.start(), match.end())

        for match in re.finditer(r"#.*", content):
            self._tag_range("code_comment", match.start(), match.end())

    def _tag_range(self, tag, start, end):
        self.code_input.tag_add(tag, f"1.0+{start}c", f"1.0+{end}c")

    # ==========================================================================
    # 7. GENERAL FUNCTIONALITY
    # ==========================================================================

    def update_time(self):
        self.status_time.configure(text=datetime.datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self.update_time)

    def on_code_change(self, event=None):
        self.line_numbers.redraw()
        self.update_cursor_info()
        self._schedule_highlighting()

    def update_cursor_info(self, event=None):
        try:
            pos = self.code_input.index(tk.INSERT)
            line, col = pos.split(".")
            self.status_cursor.configure(text=f"Ln {line}, Col {int(col) + 1}")
        except Exception:
            pass

    def increase_font(self):
        self.current_font_size += 2
        self.fonts["code"].configure(size=self.current_font_size)
        self.fonts["mono_bold"].configure(size=max(self.current_font_size - 1, 8))
        self.fonts["mono_small"].configure(size=max(self.current_font_size - 2, 8))
        ttk.Style().configure("Treeview", rowheight=int(self.current_font_size * 2.2), font=self.fonts["ui_reg"])
        self.autocomplete_listbox.config(font=self.fonts["ui_reg"])
        self.on_code_change()

    def decrease_font(self):
        if self.current_font_size > 8:
            self.current_font_size -= 2
            self.fonts["code"].configure(size=self.current_font_size)
            self.fonts["mono_bold"].configure(size=max(self.current_font_size - 1, 8))
            self.fonts["mono_small"].configure(size=max(self.current_font_size - 2, 8))
            ttk.Style().configure("Treeview", rowheight=int(self.current_font_size * 2.2), font=self.fonts["ui_reg"])
            self.autocomplete_listbox.config(font=self.fonts["ui_reg"])
            self.on_code_change()

    def toggle_search_bar(self):
        if self.search_open:
            self.search_frame.pack_forget()
            self.search_open = False
            self.code_input.tag_remove("found", "1.0", tk.END)
        else:
            self.search_frame.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(0, 8), before=self.text_container)
            self.entry_search.focus_set()
            self.search_open = True

    def find_next(self, event=None):
        term = self.entry_search.get()
        if not term:
            return
        self.code_input.tag_remove("found", "1.0", tk.END)
        idx = self.code_input.search(term, self.last_search_idx, nocase=True, stopindex=tk.END)
        if not idx:
            idx = self.code_input.search(term, "1.0", nocase=True, stopindex=self.last_search_idx)
        if idx:
            end_idx = f"{idx}+{len(term)}c"
            self.code_input.tag_add("found", idx, end_idx)
            self.code_input.tag_config("found", background=self.colors["ACCENT_ORANGE"], foreground="#111111")
            self.code_input.see(idx)
            self.last_search_idx = end_idx
            self.status_msg.configure(text=f"Found '{term}' at {idx}")
        else:
            self.status_msg.configure(text=f"'{term}' not found.")
            self.last_search_idx = "1.0"

    def clear_console(self):
        self.error_output.config(state=tk.NORMAL)
        self.error_output.delete("1.0", tk.END)
        self.error_output.config(state=tk.DISABLED)
        self.status_msg.configure(text="Console cleared.")

    def sort_column(self, col, reverse):
        values = [(self.token_tree.set(k, col), k) for k in self.token_tree.get_children("")]
        try:
            values.sort(key=lambda item: int(item[0]), reverse=reverse)
        except ValueError:
            values.sort(reverse=reverse)

        for index, (_val, key) in enumerate(values):
            self.token_tree.move(key, "", index)
            cur_tags = [tag for tag in self.token_tree.item(key, "tags") if tag not in ("evenrow", "oddrow")]
            cur_tags.append("evenrow" if index % 2 == 0 else "oddrow")
            self.token_tree.item(key, tags=cur_tags)
        self.token_tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def open_output_folder(self):
        output_dir = Path(__file__).resolve().parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        try:
            if platform.system() == "Windows":
                os.startfile(output_dir)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(output_dir)])
            else:
                subprocess.Popen(["xdg-open", str(output_dir)])
            self.status_msg.configure(text=f"Opened output folder: {output_dir}")
        except Exception as exc:
            messagebox.showerror("Open Output Folder", f"Could not open output folder:\n{exc}")

    # ==========================================================================
    # 8. THEME ENGINE
    # ==========================================================================

    def apply_theme(self):
        c = self.colors
        ctk.set_appearance_mode("light" if self.current_theme.get() in {"Light", "Big Chungus", "Oceanic"} else "dark")

        style = ttk.Style()
        style.theme_use("clam")

        self.root.configure(fg_color=c["BG_COLOR"])
        self.main_container.configure(fg_color=c["BG_COLOR"])
        self.body_frame.configure(fg_color=c["BG_COLOR"])
        self.header_frame.configure(fg_color=c["HEADER_BG"])
        self.header_inner.configure(fg_color=c["HEADER_BG"])
        self.toolbar.configure(fg_color=c["PANEL_BG"], border_width=1, border_color=c["BORDER_COLOR"])
        self.workspace_frame.configure(fg_color=c["BG_COLOR"])
        self.editor_frame.configure(fg_color=c["PANEL_BG"], border_width=1, border_color=c["BORDER_COLOR"])
        self.console_frame.configure(fg_color=c["PANEL_BG"], border_width=1, border_color=c["BORDER_COLOR"])
        self.right_pane.configure(fg_color=c["PANEL_BG"], border_width=1, border_color=c["BORDER_COLOR"])
        self.status_bar.configure(fg_color=c["STATUS_BAR_BG"])

        self.title_label.configure(text_color=c["TITLE_COLOR"])
        self.title_rule.configure(fg_color=c["ACCENT_ORANGE"])
        self.editor_header_lbl.configure(text_color=c["TITLE_COLOR"])
        self.console_header_lbl.configure(text_color=c["TITLE_COLOR"])
        self.analysis_header_lbl.configure(text_color=c["TITLE_COLOR"])
        self.token_count_lbl.configure(text_color=c["SECONDARY_TEXT"])
        for divider in self.toolbar_dividers:
            divider.configure(fg_color=c["BORDER_COLOR"])

        self.paned_main.config(bg=c["BG_COLOR"], sashrelief="flat")
        self.left_pane.config(bg=c["BG_COLOR"], sashrelief="flat")

        self._style_buttons()

        self.search_frame.configure(fg_color=c["SURFACE_BG"], border_width=1, border_color=c["BORDER_COLOR"])
        self.search_label.configure(text_color=c["SECONDARY_TEXT"])
        self.entry_search.configure(
            fg_color=c["TEXT_AREA_BG"],
            text_color=c["FG_COLOR"],
            border_color=c["BORDER_COLOR"],
        )

        self.text_container.config(bg=c["BORDER_COLOR"], highlightbackground=c["BORDER_COLOR"])
        self.output_container.config(bg=c["BORDER_COLOR"], highlightbackground=c["BORDER_COLOR"])

        self.code_input.config(
            bg=c["TEXT_AREA_BG"],
            fg=c["FG_COLOR"],
            insertbackground=c["FG_COLOR"],
            selectbackground=c["SELECT_BG"],
            selectforeground=c["SELECT_FG"],
        )
        self.error_output.config(
            bg=c["TERM_BG"],
            fg=c["TERM_FG"],
            insertbackground=c["TERM_FG"],
            selectbackground=c["SELECT_BG"],
            selectforeground=c["SELECT_FG"],
        )
        self.autocomplete_listbox.config(
            bg=c["SURFACE_BG"],
            fg=c["FG_COLOR"],
            selectbackground=c["ACCENT_BLUE"],
            selectforeground=c["BUTTON_FG"],
            highlightbackground=c["BORDER_COLOR"],
        )
        with self._proc_lock:
            proc = self._running_proc
        if proc and proc.poll() is None:
            self.input_bar.config(bg=c["TERM_INPUT_BG"], highlightbackground=c["ACCENT_GREEN"])
            self.input_title_lbl.config(bg=c["TERM_INPUT_BG"], fg=c["ACCENT_GREEN"])
            self._prompt_lbl.config(bg=c["TERM_INPUT_BG"], fg=c["ACCENT_GREEN"])
            self.btn_send_input.configure(
                fg_color=c["ACCENT_GREEN"],
                hover_color=c["ACCENT_BLUE"],
                text_color=c["BUTTON_FG"],
            )
            self.term_entry.config(
                bg=c["TEXT_AREA_BG"],
                fg=c["TERM_FG"],
                insertbackground=c["TERM_FG"],
                highlightbackground=c["ACCENT_GREEN"],
                highlightcolor=c["ACCENT_GREEN"],
            )
        else:
            self.input_bar.config(bg=c["SURFACE_BG"], highlightbackground=c["BORDER_COLOR"])
            self.input_title_lbl.config(bg=c["SURFACE_BG"], fg=c["SECONDARY_TEXT"])
            self._prompt_lbl.config(bg=c["SURFACE_BG"], fg=c["SECONDARY_TEXT"])
            self.btn_send_input.configure(
                fg_color=c["BTN_TOOL_BG"],
                hover_color=c["BORDER_COLOR"],
                text_color=c["BTN_TOOL_FG"],
            )
            self.term_entry.config(
                bg=c["TEXT_AREA_BG"],
                fg=c["FG_COLOR"],
                insertbackground=c["FG_COLOR"],
                highlightbackground=c["BORDER_COLOR"],
                highlightcolor=c["ACCENT_BLUE"],
            )

        self.line_numbers.bg_color = c["SURFACE_BG"]
        self.line_numbers.fg_color = c["SECONDARY_TEXT"]
        self.line_numbers.redraw()

        self.status_msg.configure(text_color=c["ACCENT_BLUE"])
        self.status_cursor.configure(text_color=c["SECONDARY_TEXT"])
        self.status_time.configure(text_color=c["SECONDARY_TEXT"])

        row_h = int(self.current_font_size * 2.2)
        style.configure(
            "Treeview",
            background=c["TEXT_AREA_BG"],
            foreground=c["FG_COLOR"],
            fieldbackground=c["TEXT_AREA_BG"],
            font=self.fonts["ui_reg"],
            borderwidth=0,
            rowheight=row_h,
        )
        style.configure(
            "Treeview.Heading",
            background=c["TREE_HEADING_BG"],
            foreground=c["FG_COLOR"],
            font=self.fonts["mono_bold"],
            relief="flat",
            borderwidth=0,
        )
        style.map(
            "Treeview",
            background=[("selected", c["SELECT_BG"])],
            foreground=[("selected", c["SELECT_FG"])],
        )
        style.configure("TNotebook", background=c["PANEL_BG"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=c["TREE_HEADING_BG"],
            foreground=c["FG_COLOR"],
            padding=[14, 7],
            font=self.fonts["ui_reg"],
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", c["TEXT_AREA_BG"])],
            foreground=[("selected", c["ACCENT_BLUE"])],
        )

        self.configure_tags()

    def _style_buttons(self):
        c = self.colors
        tool_buttons = [
            self.btn_open,
            self.btn_save,
            self.btn_find,
            self.btn_zoom_out,
            self.btn_zoom_in,
            self.btn_clear,
            self.btn_find_next,
            self.btn_find_close,
        ]

        pipeline_styles = [
            (self.btn_lexer, c["ACCENT_BLUE"]),
            (self.btn_syntax, c["ACCENT_PURPLE"]),
            (self.btn_semantic, c["ACCENT_GREEN"]),
            (self.btn_codegen, c["ACCENT_ORANGE"]),
        ]
        for btn, color in pipeline_styles:
            btn.configure(
                fg_color=color,
                hover_color=c["TITLE_COLOR"],
                text_color=c["BUTTON_FG"],
                border_width=1,
                border_color=c["BORDER_COLOR"],
            )
        for btn in tool_buttons:
            btn.configure(
                fg_color=c["BTN_TOOL_BG"],
                hover_color=c["BORDER_COLOR"],
                text_color=c["BTN_TOOL_FG"],
                border_width=1,
                border_color=c["BORDER_COLOR"],
            )
        self.btn_kill.configure(
            fg_color=c["ACCENT_RED"],
            hover_color="#991b1b",
            text_color="#ffffff",
            border_width=0,
        )
        self.btn_send_input.configure(
            fg_color=c["BTN_TOOL_BG"],
            hover_color=c["BORDER_COLOR"],
            text_color=c["BTN_TOOL_FG"],
            border_width=1,
            border_color=c["BORDER_COLOR"],
        )
        self.theme_selector.configure(
            fg_color=c["BTN_TOOL_BG"],
            button_color=c["ACCENT_BLUE"],
            button_hover_color=c["ACCENT_GREEN"],
            text_color=c["BTN_TOOL_FG"],
            dropdown_fg_color=c["SURFACE_BG"],
            dropdown_text_color=c["FG_COLOR"],
            dropdown_hover_color=c["BORDER_COLOR"],
        )

    def _set_stage(self, stage, state="active"):
        return

    def configure_tags(self):
        c = self.colors
        self.token_tree.tag_configure("keyword", foreground=c["ACCENT_PURPLE"], font=self.fonts["mono_bold"])
        self.token_tree.tag_configure("literal", foreground=c["ACCENT_GREEN"])
        self.token_tree.tag_configure("identifier", foreground=c["FG_COLOR"])
        self.token_tree.tag_configure("operator", foreground=c["ACCENT_ORANGE"])
        self.token_tree.tag_configure("delimiter", foreground=c["SECONDARY_TEXT"])
        self.token_tree.tag_configure(
            "comment",
            foreground=c["SECONDARY_TEXT"],
            font=(self.fonts["code"].actual()["family"], 10, "italic"),
        )
        self.token_tree.tag_configure("error", foreground=c["ACCENT_RED"])
        self.token_tree.tag_configure("oddrow", background=c["TEXT_AREA_BG"])
        self.token_tree.tag_configure("evenrow", background=c["TREE_EVEN_ROW"])

        self.error_output.tag_configure("error", foreground=c["ACCENT_RED"], font=self.fonts["mono_bold"])
        self.error_output.tag_configure("term_error", foreground="#ff6b6b")
        self.error_output.tag_configure("success", foreground=c["ACCENT_GREEN"], font=self.fonts["mono_bold"])
        self.error_output.tag_configure("info", foreground=c["ACCENT_BLUE"])
        self.error_output.tag_configure("term_input", foreground=c["ACCENT_GREEN"])

        self.code_input.tag_configure("code_keyword", foreground=c["ACCENT_BLUE"])
        self.code_input.tag_configure("code_builtin", foreground=c["ACCENT_PURPLE"])
        self.code_input.tag_configure("code_string", foreground=c["ACCENT_GREEN"])
        self.code_input.tag_configure("code_number", foreground=c["ACCENT_ORANGE"])
        self.code_input.tag_configure("code_comment", foreground=c["SECONDARY_TEXT"])

    def set_theme(self):
        theme = self.current_theme.get()
        if theme in self.themes:
            self.colors = self.themes[theme]
            self.apply_theme()
            self.refresh_token_display_only()
            self._highlight_editor()

    def refresh_token_display_only(self):
        for i, item in enumerate(self.token_tree.get_children()):
            tags = [tag for tag in self.token_tree.item(item, "tags") if tag not in ("evenrow", "oddrow")]
            tags.append("evenrow" if i % 2 == 0 else "oddrow")
            self.token_tree.item(item, tags=tags)

    # ==========================================================================
    # 9. FILE OPERATIONS
    # ==========================================================================

    def open_file(self):
        filepath = filedialog.askopenfilename(
            title="Open Source File",
            filetypes=[
                ("Chungus Files", "*.chg *.chungus"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*"),
            ],
        )
        if not filepath:
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.code_input.delete("1.0", tk.END)
            self.code_input.insert("1.0", content)
            self.on_code_change()
            self.status_msg.configure(text=f"Opened: {filepath}")
            self.run_lexer()
        except Exception as exc:
            messagebox.showerror("Error Opening File", f"Could not read file:\n{exc}")

    def save_file(self):
        filepath = filedialog.asksaveasfilename(
            title="Save Source Code",
            defaultextension=".chg",
            filetypes=[
                ("Chungus Files", "*.chg *.chungus"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*"),
            ],
        )
        if not filepath:
            return
        try:
            content = self.code_input.get("1.0", tk.END)
            if content.endswith("\n"):
                content = content[:-1]
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            self.status_msg.configure(text=f"Saved: {filepath}")
        except Exception as exc:
            messagebox.showerror("Error Saving File", f"Could not save file:\n{exc}")

    def show_about(self):
        messagebox.showinfo(
            "About Chungus Compiler",
            "Chungus Compiler\n\n"
            "Created by:\n"
            "- Goyena, Shawn Kieffer E.\n"
            "- Cantal, Henkepeck T.\n"
            "- Capiral, Luis Gabriel A.\n"
            "- Frias, Railey Miguel B.\n"
            "- King, Mariano Luiz B.\n"
            "- Manguni, John Gabriel H.\n\n"
            "Course Project - CISTM, PLM",
        )

    # ==========================================================================
    # 10. COMPILER EXECUTION LOGIC
    # ==========================================================================

    def _clear_terminal(self):
        self.error_output.config(state=tk.NORMAL)
        self.error_output.delete("1.0", tk.END)
        self.error_output.config(state=tk.DISABLED)

    def run_lexer(self):
        self.status_msg.configure(text="Running lexer...")
        self._set_stage("Lexer")
        self._clear_terminal()
        for item in self.token_tree.get_children():
            self.token_tree.delete(item)
        self.token_count_lbl.configure(text="0 tokens")

        source_code = self.code_input.get("1.0", "end-1c").expandtabs(4)
        if not callable(self.lexer_callback):
            self._show_mock_instructions("Lexer")
            return
        try:
            tokens, errors = self.lexer_callback(source_code)
        except Exception as exc:
            messagebox.showerror("Lexer Internal Error", str(exc))
            self.status_msg.configure(text="Lexer failed.")
            self._set_stage("Lexer", "error")
            return

        self._populate_tokens(tokens)
        self.error_output.config(state=tk.NORMAL)
        if errors:
            self.error_output.insert(tk.END, "\n".join(errors), "error")
            self.status_msg.configure(text=f"Lexer finished with {len(errors)} errors.")
            self._set_stage("Lexer", "error")
        else:
            self.error_output.insert(tk.END, ">>> Lexical analysis complete. No errors found.", "success")
            self.status_msg.configure(text="Lexer finished successfully.")
            self._set_stage("Lexer", "success")
        self.error_output.config(state=tk.DISABLED)

    def run_syntax(self):
        self.status_msg.configure(text="Running parser...")
        self._set_stage("Parser")
        self._clear_terminal()
        for item in self.token_tree.get_children():
            self.token_tree.delete(item)
        self.token_count_lbl.configure(text="0 tokens")

        source_code = self.code_input.get("1.0", "end-1c").expandtabs(4)
        if not callable(self.syntax_callback):
            self._show_mock_instructions("Syntax")
            return
        try:
            tokens, errors = self.syntax_callback(source_code)
        except Exception as exc:
            messagebox.showerror("Parser Internal Error", str(exc))
            self.status_msg.configure(text="Parser failed.")
            self._set_stage("Parser", "error")
            return

        self._populate_tokens(tokens)
        self.error_output.config(state=tk.NORMAL)
        if errors:
            self.error_output.insert(tk.END, "\n".join(errors), "error")
            self.status_msg.configure(text=f"Syntax analysis finished with {len(errors)} errors.")
            self._set_stage("Parser", "error")
        else:
            self.error_output.insert(tk.END, ">>> Syntax analysis complete. No errors found.", "success")
            self.status_msg.configure(text="Syntax analysis finished successfully.")
            self._set_stage("Parser", "success")
        self.error_output.config(state=tk.DISABLED)

    def run_semantic(self):
        self.status_msg.configure(text="Running semantic analyzer...")
        self._set_stage("Semantic")
        self._clear_terminal()
        for item in self.token_tree.get_children():
            self.token_tree.delete(item)
        self.token_count_lbl.configure(text="0 tokens")

        source_code = self.code_input.get("1.0", "end-1c").expandtabs(4)
        if not callable(self.semantic_callback):
            messagebox.showinfo("Semantic Analyzer", "No semantic analyzer callback provided.")
            self.status_msg.configure(text="Semantic analyzer not configured.")
            return
        try:
            tokens, errors = self.semantic_callback(source_code)
        except Exception as exc:
            messagebox.showerror("Semantic Analyzer Internal Error", str(exc))
            self.status_msg.configure(text="Semantic analysis failed.")
            self._set_stage("Semantic", "error")
            return

        self._populate_tokens(tokens)
        self.error_output.config(state=tk.NORMAL)
        if errors:
            self.error_output.insert(tk.END, "Errors found during semantic analysis:\n", "info")
            self.error_output.insert(tk.END, "\n".join(errors), "error")
            self.status_msg.configure(text=f"Semantic analysis finished with {len(errors)} errors.")
            self._set_stage("Semantic", "error")
        else:
            self.error_output.insert(tk.END, ">>> Semantic analysis complete. No errors found.", "success")
            self.status_msg.configure(text="Semantic analysis finished successfully.")
            self._set_stage("Semantic", "success")
        self.error_output.config(state=tk.DISABLED)

    def run_codegen(self):
        if not callable(self.codegen_callback):
            messagebox.showinfo("Code Generator", "No code generator callback provided.")
            self.status_msg.configure(text="Code generator not configured.")
            return

        self._clear_terminal()
        for item in self.token_tree.get_children():
            self.token_tree.delete(item)
        self.token_count_lbl.configure(text="0 tokens")

        self.btn_codegen.configure(state="disabled")
        self.status_msg.configure(text="Compiling and launching program...")
        self._set_stage("Codegen")

        source_code = self.code_input.get("1.0", "end-1c").expandtabs(4)

        def _worker():
            try:
                result = self.codegen_callback(source_code)
                if len(result) == 3:
                    tokens, errors, proc = result
                else:
                    tokens, errors = result
                    proc = None
            except Exception as exc:
                tokens, errors, proc = [], [f"Code Generator Internal Error: {exc}"], None

            self.root.after(0, lambda: self._finish_codegen(tokens, errors, proc))

        threading.Thread(target=_worker, daemon=True).start()

    def _finish_codegen(self, tokens, errors, proc=None):
        self._populate_tokens(tokens)

        if errors:
            self.error_output.config(state=tk.NORMAL)
            self.error_output.delete("1.0", tk.END)
            for line in errors:
                if isinstance(line, bytes):
                    line = line.decode("utf-8", errors="replace")
                tag = "error" if "Error" in line else ("info" if "===" in line else "")
                self.error_output.insert(tk.END, line + "\n", tag)
            self.error_output.config(state=tk.DISABLED)
            self.status_msg.configure(text="Compilation failed.")
            self.btn_codegen.configure(state="normal")
            self._set_stage("Codegen", "error")
            return

        self._set_stage("Codegen", "success")

        if proc is None:
            self._term_write(">>> Done. Generated C output was saved in the output folder.\n", tag="success")
            self.status_msg.configure(text="Done.")
            self.btn_codegen.configure(state="normal")
            return

        with self._proc_lock:
            self._running_proc = proc

        self._show_input_bar()
        self.status_msg.configure(text="Program running...")
        self._term_write("=== Program running. Type in Program Input, then press Enter or Send. ===\n", tag="info")
        self._set_stage("Runtime")
        self._start_io_pump()

        def _stream_output():
            start = time.monotonic()
            self._last_term_activity = start
            hard_timeout = 300.0
            silent_timeout = 300.0
            max_output_chars = 1_000_000
            stop_requested = threading.Event()
            output_count = 0
            count_lock = threading.Lock()

            def _reader(stream, tag):
                nonlocal output_count
                while not stop_requested.is_set():
                    try:
                        chunk = stream.read(4096)
                    except Exception:
                        break

                    if chunk in (b"", ""):
                        break

                    if isinstance(chunk, bytes):
                        chunk = chunk.decode("utf-8", errors="replace")

                    self._last_term_activity = time.monotonic()

                    with count_lock:
                        output_count += len(chunk)
                        too_much_output = output_count > max_output_chars

                    if too_much_output:
                        try:
                            self._io_events.put_nowait(
                                ("output", "\n[Execution stopped: excessive output detected]\n", "term_error")
                            )
                        except queue.Full:
                            pass
                        try:
                            proc.kill()
                        except Exception:
                            pass
                        stop_requested.set()
                        break

                    try:
                        self._io_events.put(("output", chunk, tag), timeout=0.2)
                    except queue.Full:
                        try:
                            self._io_events.put_nowait(
                                ("output", "\n[Execution stopped: terminal queue overflow]\n", "term_error")
                            )
                        except queue.Full:
                            pass
                        try:
                            proc.kill()
                        except Exception:
                            pass
                        stop_requested.set()
                        break

            readers = []
            if proc.stdout:
                readers.append(threading.Thread(target=_reader, args=(proc.stdout, None), daemon=True))
            if proc.stderr:
                readers.append(threading.Thread(target=_reader, args=(proc.stderr, "term_error"), daemon=True))

            for reader in readers:
                reader.start()

            while True:
                now = time.monotonic()
                if now - start > hard_timeout:
                    self._io_events.put(("output", "\n[Execution timeout: exceeded 300s runtime]\n", "term_error"))
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    stop_requested.set()
                    break

                if now - self._last_term_activity > silent_timeout:
                    self._io_events.put(
                        ("output", "\n[Execution timeout: no terminal activity for 300s]\n", "term_error")
                    )
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    stop_requested.set()
                    break

                if proc.poll() is not None:
                    break

                time.sleep(0.05)

            rc = proc.wait()

            for reader in readers:
                reader.join(timeout=0.2)

            with self._proc_lock:
                self._running_proc = None
            self._io_events.put(("finish", rc))

        threading.Thread(target=_stream_output, daemon=True).start()

    def _populate_tokens(self, tokens):
        for i, token in enumerate(tokens):
            token_type_name = getattr(token, "type", token.get("type") if isinstance(token, dict) else "")
            if hasattr(token_type_name, "name"):
                token_type_name = token_type_name.name
            line = getattr(token, "line", token.get("line") if isinstance(token, dict) else "")
            col = getattr(token, "col", token.get("col") if isinstance(token, dict) else "")
            raw_lexeme = getattr(token, "lexeme", token.get("lexeme") if isinstance(token, dict) else str(token))
            lexeme = str(raw_lexeme).replace("\n", "\\n").replace("\r", "\\r").replace("\t", "    ")

            token_type = str(token_type_name).lower()
            lexeme_lower = str(raw_lexeme).lower()
            tag = "identifier"
            if token_type in LITERALS or lexeme_lower in {"true", "false"}:
                tag = "literal"
            elif token_type == "comment":
                tag = "comment"
            elif lexeme_lower in OPERATORS:
                tag = "operator"
            elif lexeme_lower in DELIMS:
                tag = "delimiter"
            elif lexeme_lower in KEYWORDS or token_type in KEYWORDS:
                tag = "keyword"

            row_tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.token_tree.insert("", tk.END, values=(line, col, lexeme, token_type_name), tags=(tag, row_tag))

        self.token_count_lbl.configure(text=f"{len(tokens)} token{'s' if len(tokens) != 1 else ''}")

    def _show_mock_instructions(self, mode):
        self.error_output.config(state=tk.NORMAL)
        self.error_output.insert(
            tk.END,
            f"No {mode.lower()} backend connected.\n\n"
            f"Provide a callable {mode.lower()}_callback = lambda src: (tokens, errors)\n"
            "Tokens should include type, lexeme, line, and col fields.\n",
            "error",
        )
        self.error_output.config(state=tk.DISABLED)
