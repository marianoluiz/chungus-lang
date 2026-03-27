import tkinter as tk
from tkinter import ttk, font, messagebox, filedialog
import platform
import datetime
import threading
import re

# ==============================================================================
# 1. LANGUAGE CONFIGURATION
# ==============================================================================

KEYWORDS = sorted([
    'true', 'false', 'read', 'show', 
    'if', 'elif', 'else', 'while', 'for', 'in', 'range',
    'try', 'fail', 'always', 
    'int', 'float', 'and', 'or', 
    'fn', 'ret', 'todo', 'close'
])

LITERALS = {
    'int_literal', 'float_literal', 'str_literal', 'bool_literal'
}

OPERATORS = {
    '++', '--', '//', '**', '==', '!=', '>', '<', 
    '>=', '<=', '+', '-', '*', '/', '%', '=', '!'
}

DELIMS = {
    '(', ')', '[', ']', ',', ';', ':'
}

# ==============================================================================
# 2. UI HELPER CLASSES
# ==============================================================================

class ToolTip(object):
    def __init__(self, widget, text='widget info'):
        self.waittime = 500
        self.wraplength = 180
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None): self.schedule()
    def leave(self, event=None): self.unschedule(); self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id: self.widget.after_cancel(id)

    def showtip(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw: tw.destroy()


class TextLineNumbers(tk.Canvas):
    def __init__(self, *args, **kwargs):
        tk.Canvas.__init__(self, *args, **kwargs)
        self.textwidget = None
        self.bg_color = "#ffffff"
        self.fg_color = "#000000"

    def attach(self, text_widget):
        self.textwidget = text_widget

    def redraw(self, *args):
        """Redraw line numbers - called on any text change"""
        self.delete("all")
        if not self.textwidget:
            return
            
        self.config(bg=self.bg_color)
        
        # Get total number of lines in the text widget
        end_index = self.textwidget.index("end")
        total_lines = int(end_index.split(".")[0])
        
        # Iterate through all lines and draw visible ones
        for line_num in range(1, total_lines + 1):
            line_index = f"{line_num}.0"
            dline = self.textwidget.dlineinfo(line_index)
            if dline is None:
                continue  # Line not visible, skip it
            y = dline[1]
            self.create_text(
                35, 
                y, 
                anchor="ne", 
                text=str(line_num),
                fill=self.fg_color, 
                font=self.textwidget.cget("font")
            )


# ==============================================================================
# 3. MAIN APPLICATION CONTROLLER
# ==============================================================================

class ChungusLexerGUI:
    def __init__(self, root, lexer_callback=None, syntax_callback=None,
                 semantic_callback=None, codegen_callback=None):
        self.root = root
        self.setup_window()

        self.lexer_callback = lexer_callback
        self.syntax_callback = syntax_callback
        self.semantic_callback = semantic_callback
        self.codegen_callback = codegen_callback

        # App State
        self.current_theme = tk.StringVar(value="Oceanic Blue")
        self.search_open = False
        self.last_search_idx = "1.0"
        self.current_font_size = 12

        # Interactive terminal state
        self._running_proc = None          # subprocess.Popen when a program is live
        self._proc_lock = threading.Lock() # guard _running_proc | thread lock - prevents racing conditions

        self.themes = {
            "Light (macOS)": {
                "BG_COLOR": "#f5f5f7", "TEXT_AREA_BG": "#ffffff", "FG_COLOR": "#333333",
                "ACCENT_BLUE": "#007aff", "ACCENT_GREEN": "#34c759", "ACCENT_RED": "#ff3b30",
                "ACCENT_ORANGE": "#ff9500", "ACCENT_PURPLE": "#af52de", "BORDER_COLOR": "#d1d1d6",
                "TITLE_COLOR": "#1c1c1e", "SECONDARY_TEXT": "#6e6e73", "STATUS_BAR_BG": "#e5e5ea",
                "TREE_HEADING_BG": "#f9f9f9", "TREE_EVEN_ROW": "#fafafa", "BUTTON_FG": "white",
                "SELECT_BG": "#b3d7ff", "SELECT_FG": "#333333", "HEADER_BG": "#ffffff",
                "BTN_TOOL_BG": "#e5e5ea", "BTN_TOOL_FG": "#333333",
                "TERM_BG": "#1e1e1e", "TERM_FG": "#f0f0f0", "TERM_INPUT_BG": "#2a2a2a",
            },
            "Dark": {
                "BG_COLOR": "#1e1e1e", "TEXT_AREA_BG": "#2a2a2a", "FG_COLOR": "#d4d4d4",
                "ACCENT_BLUE": "#007acc", "ACCENT_GREEN": "#4ec9b0", "ACCENT_RED": "#f44747",
                "ACCENT_ORANGE": "#ce9178", "ACCENT_PURPLE": "#c586c0", "BORDER_COLOR": "#444444",
                "TITLE_COLOR": "#cccccc", "SECONDARY_TEXT": "#9e9e9e", "STATUS_BAR_BG": "#1a1a1a",
                "TREE_HEADING_BG": "#333333", "TREE_EVEN_ROW": "#303030", "BUTTON_FG": "#d4d4d4",
                "SELECT_BG": "#007acc", "SELECT_FG": "#d4d4d4", "HEADER_BG": "#1e1e1e",
                "BTN_TOOL_BG": "#3c3c3c", "BTN_TOOL_FG": "#ffffff",
                "TERM_BG": "#0d0d0d", "TERM_FG": "#d4d4d4", "TERM_INPUT_BG": "#1a1a1a",
            },
            "Oceanic Blue": {
                "BG_COLOR": "#e0f2f7", "TEXT_AREA_BG": "#ffffff", "FG_COLOR": "#004d40",
                "ACCENT_BLUE": "#0277bd", "ACCENT_GREEN": "#00695c", "ACCENT_RED": "#c62828",
                "ACCENT_ORANGE": "#e65100", "ACCENT_PURPLE": "#6a1b9a", "BORDER_COLOR": "#b0bec5",
                "TITLE_COLOR": "#01579b", "SECONDARY_TEXT": "#455a64", "STATUS_BAR_BG": "#cfd8dc",
                "TREE_HEADING_BG": "#e1f5fe", "TREE_EVEN_ROW": "#f5fcff", "BUTTON_FG": "white",
                "SELECT_BG": "#81d4fa", "SELECT_FG": "#004d40", "HEADER_BG": "#e0f2f7",
                "BTN_TOOL_BG": "#81d4fa", "BTN_TOOL_FG": "#004d40",
                "TERM_BG": "#0d1b2a", "TERM_FG": "#a8d8ea", "TERM_INPUT_BG": "#112233",
            },
            "Forest Green": {
                "BG_COLOR": "#263238", "TEXT_AREA_BG": "#37474f", "FG_COLOR": "#eceff1",
                "ACCENT_BLUE": "#80cbc4", "ACCENT_GREEN": "#a5d6a7", "ACCENT_RED": "#ef9a9a",
                "ACCENT_ORANGE": "#ffcc80", "ACCENT_PURPLE": "#ce93d8", "BORDER_COLOR": "#546e7a",
                "TITLE_COLOR": "#b0bec5", "SECONDARY_TEXT": "#90a4ae", "STATUS_BAR_BG": "#1a252a",
                "TREE_HEADING_BG": "#455a64", "TREE_EVEN_ROW": "#3c4f57", "BUTTON_FG": "#1a252a",
                "SELECT_BG": "#00695c", "SELECT_FG": "#eceff1", "HEADER_BG": "#263238",
                "BTN_TOOL_BG": "#546e7a", "BTN_TOOL_FG": "#ffffff",
                "TERM_BG": "#0a1a0a", "TERM_FG": "#a5d6a7", "TERM_INPUT_BG": "#122212",
            },
            "Big Chungus": {
                "BG_COLOR": "#add8e6", "TEXT_AREA_BG": "#ffffff", "FG_COLOR": "#404040",
                "ACCENT_BLUE": "#ff4500", "ACCENT_GREEN": "#228b22", "ACCENT_RED": "#dc143c",
                "ACCENT_ORANGE": "#8b4513", "ACCENT_PURPLE": "#a9a9a9", "BORDER_COLOR": "#87ceeb",
                "TITLE_COLOR": "#ff4500", "SECONDARY_TEXT": "#708090", "STATUS_BAR_BG": "#f0f8ff",
                "TREE_HEADING_BG": "#ffdead", "TREE_EVEN_ROW": "#fff8dc", "BUTTON_FG": "white",
                "SELECT_BG": "#ffd700", "SELECT_FG": "#404040", "HEADER_BG": "#add8e6",
                "BTN_TOOL_BG": "#87ceeb", "BTN_TOOL_FG": "#404040",
                "TERM_BG": "#1a1a2e", "TERM_FG": "#ffd700", "TERM_INPUT_BG": "#16213e",
            },
            "Disney Magic": {
                "BG_COLOR": "#fff0f5", "TEXT_AREA_BG": "#ffffff", "FG_COLOR": "#4b0082",
                "ACCENT_BLUE": "#1e90ff", "ACCENT_GREEN": "#32cd32", "ACCENT_RED": "#ff1493",
                "ACCENT_ORANGE": "#ffa500", "ACCENT_PURPLE": "#9370db", "BORDER_COLOR": "#ffb6c1",
                "TITLE_COLOR": "#c71585", "SECONDARY_TEXT": "#8b008b", "STATUS_BAR_BG": "#e6e6fa",
                "TREE_HEADING_BG": "#ffe4e1", "TREE_EVEN_ROW": "#fffaf0", "BUTTON_FG": "white",
                "SELECT_BG": "#87cefa", "SELECT_FG": "#ffffff", "HEADER_BG": "#fff0f5",
                "BTN_TOOL_BG": "#ffb6c1", "BTN_TOOL_FG": "#4b0082",
                "TERM_BG": "#1a0a2e", "TERM_FG": "#e0aaff", "TERM_INPUT_BG": "#2d1b4e",
            },
            "Synthwave 84": {
                "BG_COLOR": "#2b213a", "TEXT_AREA_BG": "#241b2f", "FG_COLOR": "#ff71ce",
                "ACCENT_BLUE": "#01cdfe", "ACCENT_GREEN": "#05ffa1", "ACCENT_RED": "#ff0055",
                "ACCENT_ORANGE": "#b967ff", "ACCENT_PURPLE": "#fffb96", "BORDER_COLOR": "#01cdfe",
                "TITLE_COLOR": "#05ffa1", "SECONDARY_TEXT": "#b967ff", "STATUS_BAR_BG": "#191221",
                "TREE_HEADING_BG": "#3e2f5b", "TREE_EVEN_ROW": "#2b213a", "BUTTON_FG": "#191221",
                "SELECT_BG": "#ff71ce", "SELECT_FG": "#2b213a", "HEADER_BG": "#241b2f",
                "BTN_TOOL_BG": "#3e2f5b", "BTN_TOOL_FG": "#01cdfe",
                "TERM_BG": "#0d0013", "TERM_FG": "#05ffa1", "TERM_INPUT_BG": "#1a0026",
            },
        }
        self.colors = self.themes[self.current_theme.get()]

        self.init_fonts()
        self.build_ui_structure()
        self.apply_theme()

        self.code_input.bind("<<Change>>", self.on_code_change)
        self.code_input.bind("<Configure>", self.on_code_change)

    def setup_window(self):
        self.root.title("Chungus Compiler Environment")
        self.root.geometry("1300x900")
        self.root.minsize(1024, 700)

    def init_fonts(self):
        os_name = platform.system()
        if os_name == "Darwin":
            base_font, title_family, mono_family = "SF Pro Text", "Avenir Next", "SF Mono"
        elif os_name == "Windows":
            base_font, title_family, mono_family = "Segoe UI", "Segoe UI Black", "Consolas"
        else:
            base_font, title_family, mono_family = "DejaVu Sans", "DejaVu Sans", "DejaVu Sans Mono"

        self.fonts = {
            "title":      font.Font(family=title_family, size=28, weight="bold"),
            "header":     font.Font(family=title_family, size=20, weight="bold"),
            "subheader":  font.Font(family=base_font,   size=12, weight="bold"),
            "ui_reg":     font.Font(family=base_font,   size=10),
            "ui_small":   font.Font(family=base_font,   size=9),
            "code":       font.Font(family=mono_family, size=self.current_font_size),
            "mono_small": font.Font(family=mono_family, size=10),
            "mono_bold":  font.Font(family=mono_family, size=10, weight="bold"),
            "terminal":   font.Font(family=mono_family, size=11),
        }

    # ==========================================================================
    # 4. UI CONSTRUCTION
    # ==========================================================================

    def build_ui_structure(self):
        self.build_menu()
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        self.build_header()
        self.build_toolbar()
        self.build_workspace()
        self.build_status_bar()

    def build_menu(self):
        self.menubar = tk.Menu(self.root)

        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="Open Source File...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Source Code...", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit Environment", command=self.root.quit)
        self.menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(self.menubar, tearoff=0)
        theme_menu = tk.Menu(view_menu, tearoff=0)
        for theme_name in self.themes.keys():
            theme_menu.add_radiobutton(label=theme_name, variable=self.current_theme,
                                       value=theme_name, command=self.set_theme)
        view_menu.add_cascade(label="Interface Theme", menu=theme_menu)

        font_menu = tk.Menu(view_menu, tearoff=0)
        font_menu.add_command(label="Increase Font (Zoom In)", command=self.increase_font)
        font_menu.add_command(label="Decrease Font (Zoom Out)", command=self.decrease_font)
        view_menu.add_cascade(label="Editor Zoom", menu=font_menu)
        self.menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        self.menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=self.menubar)
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-plus>', lambda e: self.increase_font())
        self.root.bind('<Control-minus>', lambda e: self.decrease_font())

    def build_header(self):
        self.header_frame = tk.Frame(self.main_container, padx=20, pady=15)
        self.header_frame.pack(fill=tk.X, side=tk.TOP)
        self.title_label = tk.Label(self.header_frame, text="CHUNGUS COMPILER",
                                    font=self.fonts['title'], anchor='center')
        self.title_label.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

    def build_toolbar(self):
        self.toolbar = tk.Frame(self.main_container, bd=1, relief="raised")
        self.toolbar.pack(fill=tk.X, side=tk.TOP, pady=(0, 5))

        btn_container = tk.Frame(self.toolbar)
        btn_container.pack(side=tk.LEFT, padx=15, pady=8)

        self.btn_lexer = tk.Button(btn_container, text="▶ RUN LEXER",
                                   command=self.run_lexer, font=self.fonts['subheader'],
                                   relief="raised", borderwidth=0, padx=20, pady=8, cursor="hand2")
        self.btn_lexer.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_syntax = tk.Button(btn_container, text="▶ RUN SYNTAX",
                                    command=self.run_syntax, font=self.fonts['subheader'],
                                    relief="raised", borderwidth=0, padx=20, pady=8, cursor="hand2")
        self.btn_syntax.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_semantic = tk.Button(btn_container, text="▶ RUN SEMANTIC",
                                      command=self.run_semantic, font=self.fonts['subheader'],
                                      relief="raised", borderwidth=0, padx=20, pady=8, cursor="hand2")
        self.btn_semantic.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_codegen = tk.Button(btn_container, text="▶ RUN PROGRAM",
                                     command=self.run_codegen, font=self.fonts['subheader'],
                                     relief="raised", borderwidth=0, padx=20, pady=8, cursor="hand2")
        self.btn_codegen.pack(side=tk.LEFT, padx=(0, 10))

        tools_container = tk.Frame(self.toolbar)
        tools_container.pack(side=tk.RIGHT, padx=15)

        self.btn_find = tk.Button(tools_container, text="🔍 Find in Code",
                                  command=self.toggle_search_bar, font=self.fonts['ui_reg'],
                                  relief="flat", padx=15, pady=6, cursor="hand2")
        self.btn_find.pack(side=tk.LEFT, padx=5)

        self.btn_clear = tk.Button(tools_container, text="🗑 Clear Output",
                                   command=self.clear_console, font=self.fonts['ui_reg'],
                                   relief="flat", padx=15, pady=6, cursor="hand2")
        self.btn_clear.pack(side=tk.LEFT, padx=5)

        self.btn_kill = tk.Button(tools_container, text="⏹ Kill Process",
                                  command=self.kill_process, font=self.fonts['ui_reg'],
                                  relief="flat", padx=15, pady=6, cursor="hand2", state=tk.DISABLED)
        self.btn_kill.pack(side=tk.LEFT, padx=5)

    def build_workspace(self):
        self.paned_main = tk.PanedWindow(self.main_container, orient=tk.HORIZONTAL,
                                         sashwidth=8, bd=0)
        self.paned_main.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.left_pane = tk.PanedWindow(self.paned_main, orient=tk.VERTICAL, sashwidth=8, bd=0)
        self.paned_main.add(self.left_pane, minsize=400, stretch="always")

        self.editor_frame = tk.Frame(self.left_pane)
        self.left_pane.add(self.editor_frame, stretch="always", minsize=300)
        self.build_editor_area()

        self.console_frame = tk.Frame(self.left_pane)
        self.left_pane.add(self.console_frame, stretch="never", minsize=180)
        self.build_console_area()

        self.right_pane = tk.Frame(self.paned_main)
        self.paned_main.add(self.right_pane, minsize=350, stretch="never")
        self.build_analysis_area()


    def build_editor_area(self):
        lbl_frame = tk.Frame(self.editor_frame)
        lbl_frame.pack(fill=tk.X, side=tk.TOP, pady=(0, 2))
        self.editor_header_lbl = tk.Label(lbl_frame, text="  SOURCE CODE  ",
                                          font=self.fonts['mono_bold'], anchor='w')
        self.editor_header_lbl.pack(side=tk.LEFT, fill=tk.Y)

        self.search_frame = tk.Frame(self.editor_frame, bd=1, relief="raised", padx=5, pady=5)
        tk.Label(self.search_frame, text="Find:", font=self.fonts['ui_small']).pack(side=tk.LEFT, padx=2)
        self.entry_search = tk.Entry(self.search_frame, font=self.fonts['ui_reg'], width=25)
        self.entry_search.pack(side=tk.LEFT, padx=5)
        self.entry_search.bind("<Return>", self.find_next)
        tk.Button(self.search_frame, text="Next", command=self.find_next,
                  font=self.fonts['ui_small']).pack(side=tk.LEFT, padx=2)
        tk.Button(self.search_frame, text="✖", command=self.toggle_search_bar,
                  font=self.fonts['ui_small'], relief="flat", fg="red").pack(side=tk.RIGHT, padx=5)

        self.text_container = tk.Frame(self.editor_frame, bd=2, relief="flat")
        self.text_container.pack(fill=tk.BOTH, expand=True)

        self.v_scroll = ttk.Scrollbar(self.text_container, orient=tk.VERTICAL)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.code_input = tk.Text(self.text_container, font=self.fonts['code'], undo=True,
                                  wrap=tk.NONE, yscrollcommand=self.v_scroll.set,
                                  padx=10, pady=10, borderwidth=0, highlightthickness=0)
        self.code_input.config(tabs='1c')  # Set tab stops to 4 spaces visually

        self.v_scroll.config(command=self.code_input.yview)

        self.line_numbers = TextLineNumbers(self.text_container, width=40)
        self.line_numbers.attach(self.code_input)
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        self.code_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.code_input.bind("<<Change>>", self.on_code_change)
        self.code_input.bind("<Configure>", self.on_code_change)
        self.code_input.bind("<MouseWheel>", self.on_code_change)
        self.code_input.bind("<Button-1>", self.update_cursor_info)

        # new bindings to trigger line number updates
        self.code_input.bind("<Key>", self.on_code_change)
        self.code_input.bind("<Return>", lambda e: self.root.after(10, self.on_code_change))
        self.code_input.bind("<BackSpace>", lambda e: self.root.after(10, self.on_code_change))
        self.code_input.bind("<Delete>", lambda e: self.root.after(10, self.on_code_change))
        self.code_input.bind("<Control-v>", lambda e: self.root.after(50, self.on_code_change))
        self.code_input.bind("<Control-V>", lambda e: self.root.after(50, self.on_code_change))

        self.autocomplete_listbox = tk.Listbox(self.text_container, height=5, bd=1,
                                               relief="solid", font=self.fonts['ui_reg'],
                                               exportselection=False)
        self.code_input.bind("<KeyRelease>", self.check_autocomplete)
        self.code_input.bind("<Tab>", self.accept_autocomplete)
        self.code_input.bind("<Return>", self.accept_autocomplete)
        self.code_input.bind("<Up>", self.nav_autocomplete_up)
        self.code_input.bind("<Down>", self.nav_autocomplete_down)
        self.code_input.bind("<FocusOut>", self.hide_autocomplete)


    def build_console_area(self):
        # ── Header row ──────────────────────────────────────────────────────
        header = tk.Frame(self.console_frame, height=25)
        header.pack(fill=tk.X, side=tk.TOP, pady=(5, 0))

        self.console_header_lbl = tk.Label(header, text="  TERMINAL / OUTPUT  ",
                                           font=self.fonts['mono_bold'], anchor='w')
        self.console_header_lbl.pack(side=tk.LEFT, fill=tk.Y)

        # small indicator label: "● RUNNING" shown while a process is live
        self.term_status_lbl = tk.Label(header, text="", font=self.fonts['ui_small'], padx=8)
        self.term_status_lbl.pack(side=tk.LEFT)

        # ── Output text area ─────────────────────────────────────────────────
        out_container = tk.Frame(self.console_frame, bd=2, relief="flat")
        out_container.pack(fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(out_container, orient=tk.VERTICAL)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.error_output = tk.Text(out_container, font=self.fonts['terminal'],
                                    state=tk.DISABLED, wrap=tk.WORD,
                                    yscrollcommand=scroll.set,
                                    borderwidth=0, highlightthickness=0,
                                    padx=10, pady=8)
        scroll.config(command=self.error_output.yview)
        self.error_output.pack(fill=tk.BOTH, expand=True)

        # ── Input bar (hidden until a program is running) ────────────────────
        self.input_bar = tk.Frame(self.console_frame, bd=0)
        # NOT packed yet — shown only when process is live

        prompt_lbl = tk.Label(self.input_bar, text="›", font=self.fonts['terminal'],
                              padx=6, pady=4)
        prompt_lbl.pack(side=tk.LEFT)
        self._prompt_lbl = prompt_lbl

        self.term_input_var = tk.StringVar()
        self.term_entry = tk.Entry(self.input_bar, textvariable=self.term_input_var,
                                   font=self.fonts['terminal'],
                                   borderwidth=0, highlightthickness=1,
                                   relief="flat")
        self.term_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6), pady=4)
        self.term_entry.bind("<Return>", self._on_term_enter) # Key binding for input field
        self.term_entry.bind("<KP_Enter>", self._on_term_enter)

    def build_analysis_area(self):
        self.notebook = ttk.Notebook(self.right_pane)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_tokens = tk.Frame(self.notebook)
        self.notebook.add(self.tab_tokens, text="  Token Stream  ")

        cols = ("Line", "Col", "Lexeme", "Token")
        self.token_tree = ttk.Treeview(self.tab_tokens, columns=cols,
                                       show="headings", selectmode="browse")

        vsb = ttk.Scrollbar(self.tab_tokens, orient="vertical", command=self.token_tree.yview)
        hsb = ttk.Scrollbar(self.tab_tokens, orient="horizontal", command=self.token_tree.xview)
        self.token_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.token_tree.pack(fill=tk.BOTH, expand=True)

        self.token_tree.heading("Line",   text="Ln",         command=lambda: self.sort_column("Line",   False))
        self.token_tree.heading("Col",    text="Col",        command=lambda: self.sort_column("Col",    False))
        self.token_tree.heading("Lexeme", text="Lexeme",     command=lambda: self.sort_column("Lexeme", False))
        self.token_tree.heading("Token",  text="Token Type", command=lambda: self.sort_column("Token",  False))

        self.token_tree.column("Line",   width=50,  anchor="center")
        self.token_tree.column("Col",    width=50,  anchor="center")
        self.token_tree.column("Lexeme", width=150, anchor="w")
        self.token_tree.column("Token",  width=150, anchor="w")

    def build_status_bar(self):
        self.status_bar = tk.Frame(self.main_container, height=30, bd=0)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_cursor = tk.Label(self.status_bar, text="Ln 1, Col 1",
                                      font=self.fonts['ui_small'], relief="flat", padx=10)
        self.status_cursor.pack(side=tk.RIGHT)

        self.status_msg = tk.Label(self.status_bar, text="Ready",
                                   font=self.fonts['ui_small'], relief="flat", padx=10)
        self.status_msg.pack(side=tk.LEFT)

        self.status_time = tk.Label(self.status_bar, text="",
                                    font=self.fonts['ui_small'], relief="flat", padx=10)
        self.status_time.pack(side=tk.RIGHT)
        self.update_time()

    # ==========================================================================
    # 5. INTERACTIVE TERMINAL LOGIC
    # ==========================================================================

    def _show_input_bar(self):
        """Make the input entry bar visible and focused."""
        c = self.colors
        self.input_bar.pack(fill=tk.X, side=tk.BOTTOM, before=self.console_frame.winfo_children()[1])
        self.term_entry.config(bg=c["TERM_INPUT_BG"], fg=c["TERM_FG"],
                               insertbackground=c["TERM_FG"],
                               highlightcolor=c["ACCENT_BLUE"],
                               highlightbackground=c["BORDER_COLOR"])
        self._prompt_lbl.config(bg=c["TERM_INPUT_BG"], fg=c["ACCENT_GREEN"])
        self.input_bar.config(bg=c["TERM_INPUT_BG"])
        self.term_input_var.set("")
        self.term_entry.focus_set()

        self.term_status_lbl.config(text="● RUNNING", fg=self.colors["ACCENT_GREEN"],
                                    bg=self.colors["BG_COLOR"])
        
        # enable kill btn
        self.btn_kill.config(state=tk.NORMAL)

    def _hide_input_bar(self):
        """Hide the input bar when no process is running."""
        self.input_bar.pack_forget()
        self.term_status_lbl.config(text="")
        self.btn_kill.config(state=tk.DISABLED)


    def _on_term_enter(self, event=None):
        """Called when user presses Enter in the terminal input bar."""
        text = self.term_input_var.get()
        self.term_input_var.set("")

        with self._proc_lock:
            proc = self._running_proc

        if proc is None or proc.poll() is not None:
            return

        # Echo the typed input in the terminal (like a real terminal)
        self._term_write(text + "\n", tag="term_input")

        # Send to the process stdin
        try:
            proc.stdin.write(text + "\n")
            proc.stdin.flush()
        except (BrokenPipeError, OSError):
            pass  # process may have already ended

    def kill_process(self):
        """Force-kill the running process."""
        with self._proc_lock:
            proc = self._running_proc
        if proc and proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass
        self._term_write("\n[Process killed by user]\n", tag="term_error")

    def _term_write(self, text, tag=None):
        """Thread-safe write to the terminal output widget."""
        def _do():
            self.error_output.config(state=tk.NORMAL)
            if tag:
                self.error_output.insert(tk.END, text, tag)
            else:
                self.error_output.insert(tk.END, text)
            self.error_output.see(tk.END)
            self.error_output.config(state=tk.DISABLED)
        self.root.after(0, _do)

    # ==========================================================================
    # 6. AUTOCOMPLETE LOGIC
    # ==========================================================================

    def check_autocomplete(self, event=None):
        if event.keysym in ["Up", "Down", "Left", "Right", "Return", "BackSpace", "Tab", "Escape"]:
            return
        try:
            current_pos = self.code_input.index(tk.INSERT)
            line, col = current_pos.split('.')
            text_line = self.code_input.get(f"{line}.0", current_pos)
            if not text_line or (not text_line[-1].isalnum() and text_line[-1] != '_'):
                self.hide_autocomplete(); return
            partial_word = ""
            for char in reversed(text_line):
                if char.isalnum() or char == '_': partial_word = char + partial_word
                else: break
            if not partial_word: self.hide_autocomplete(); return
            matches = [k for k in KEYWORDS if k.startswith(partial_word)]
            if matches: self.show_autocomplete(matches, partial_word)
            else: self.hide_autocomplete()
        except Exception: self.hide_autocomplete()

    def show_autocomplete(self, matches, partial_word):
        self.autocomplete_listbox.delete(0, tk.END)
        for match in matches: self.autocomplete_listbox.insert(tk.END, match)
        self.autocomplete_listbox.select_set(0)
        bbox = self.code_input.bbox("insert")
        if bbox:
            x, y, w, h = bbox
            self.autocomplete_listbox.place(x=x, y=y+h)
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

    def nav_autocomplete_down(self, event):
        if self.autocomplete_listbox.winfo_ismapped():
            cur = self.autocomplete_listbox.curselection()
            if cur and cur[0] < self.autocomplete_listbox.size() - 1:
                self.autocomplete_listbox.select_clear(cur[0])
                self.autocomplete_listbox.select_set(cur[0] + 1)
                self.autocomplete_listbox.see(cur[0] + 1)
            return "break"

    def accept_autocomplete(self, event):
        if self.autocomplete_listbox.winfo_ismapped():
            selection = self.autocomplete_listbox.curselection()
            if selection:
                word = self.autocomplete_listbox.get(selection[0])
                current_pos = self.code_input.index(tk.INSERT)
                line, col = current_pos.split('.')
                text_line = self.code_input.get(f"{line}.0", current_pos)
                
                # Calculate how many characters from the end are part of the word
                partial_len = 0
                for char in reversed(text_line):
                    if char.isalnum() or char == '_':
                        partial_len += 1
                    else:
                        break
                
                start_del = f"{line}.{int(col) - partial_len}"
                self.code_input.delete(start_del, current_pos)
                self.code_input.insert(start_del, word + " ")
                self.hide_autocomplete()
                return "break"
        return None

    # ==========================================================================
    # 7. GENERAL FUNCTIONALITY
    # ==========================================================================

    def update_time(self):
        self.status_time.config(text=datetime.datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self.update_time)

    def on_code_change(self, event=None):
        self.line_numbers.redraw()
        self.update_cursor_info()

    def update_cursor_info(self, event=None):
        try:
            pos = self.code_input.index(tk.INSERT)
            line, col = pos.split('.')
            self.status_cursor.config(text=f"Ln {line}, Col {int(col)+1}")
        except: pass

    def increase_font(self):
        self.current_font_size += 2
        self.fonts['code'].configure(size=self.current_font_size)
        self.fonts['mono_bold'].configure(size=self.current_font_size - 1)
        self.fonts['mono_small'].configure(size=self.current_font_size - 2)
        style = ttk.Style()
        style.configure("Treeview", rowheight=int(self.current_font_size * 2.2), font=self.fonts['ui_reg'])
        self.autocomplete_listbox.config(font=self.fonts['ui_reg'])
        self.on_code_change()

    def decrease_font(self):
        if self.current_font_size > 8:
            self.current_font_size -= 2
            self.fonts['code'].configure(size=self.current_font_size)
            self.fonts['mono_bold'].configure(size=self.current_font_size - 1)
            self.fonts['mono_small'].configure(size=self.current_font_size - 2)
            style = ttk.Style()
            style.configure("Treeview", rowheight=int(self.current_font_size * 2.2), font=self.fonts['ui_reg'])
            self.autocomplete_listbox.config(font=self.fonts['ui_reg'])
            self.on_code_change()

    def toggle_search_bar(self):
        if self.search_open:
            self.search_frame.forget(); self.search_open = False
            self.code_input.tag_remove('found', '1.0', tk.END)
        else:
            self.search_frame.pack(side=tk.TOP, fill=tk.X, before=self.text_container, pady=(0, 5))
            self.entry_search.focus_set(); self.search_open = True

    def find_next(self, event=None):
        term = self.entry_search.get()
        if not term: return
        self.code_input.tag_remove('found', '1.0', tk.END)
        idx = self.code_input.search(term, self.last_search_idx, nocase=True, stopindex=tk.END)
        if not idx:
            idx = self.code_input.search(term, "1.0", nocase=True, stopindex=self.last_search_idx)
        if idx:
            end_idx = f"{idx}+{len(term)}c"
            self.code_input.tag_add('found', idx, end_idx)
            self.code_input.tag_config('found', background='yellow', foreground='black')
            self.code_input.see(idx)
            self.last_search_idx = end_idx
            self.status_msg.config(text=f"Found '{term}' at {idx}")
        else:
            self.status_msg.config(text=f"'{term}' not found.")
            self.last_search_idx = "1.0"

    def clear_console(self):
        self.error_output.config(state=tk.NORMAL)
        self.error_output.delete("1.0", tk.END)
        self.error_output.config(state=tk.DISABLED)
        self.status_msg.config(text="Console cleared.")

    def sort_column(self, col, reverse):
        l = [(self.token_tree.set(k, col), k) for k in self.token_tree.get_children('')]
        try: l.sort(key=lambda t: int(t[0]), reverse=reverse)
        except ValueError: l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l):
            self.token_tree.move(k, '', index)
            cur_tags = [t for t in self.token_tree.item(k, "tags") if t not in ('evenrow', 'oddrow')]
            self.token_tree.item(k, tags=cur_tags + ['evenrow' if index % 2 == 0 else 'oddrow'])
        self.token_tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    # ==========================================================================
    # 8. THEME ENGINE
    # ==========================================================================

    def apply_theme(self):
        c = self.colors
        style = ttk.Style()
        style.theme_use('clam')

        self.root.config(bg=c["BG_COLOR"])
        self.main_container.config(bg=c["BG_COLOR"])
        self.header_frame.config(bg=c["HEADER_BG"])
        self.toolbar.config(bg=c["BG_COLOR"])
        self.status_bar.config(bg=c["STATUS_BAR_BG"])
        self.search_frame.config(bg=c["BG_COLOR"])
        self.title_label.config(bg=c["HEADER_BG"], fg=c["TITLE_COLOR"])

        self.paned_main.config(bg=c["BG_COLOR"], sashrelief="flat")
        self.left_pane.config(bg=c["BG_COLOR"], sashrelief="flat")
        self.right_pane.config(bg=c["BG_COLOR"])
        self.editor_frame.config(bg=c["BG_COLOR"])
        self.console_frame.config(bg=c["BG_COLOR"])

        for lbl in [self.editor_header_lbl, self.console_header_lbl]:
            lbl.config(bg=c["BG_COLOR"], fg=c["TITLE_COLOR"])

        btn_bg = c["ACCENT_RED"] if self.current_theme.get() == "Synthwave 84" else c["ACCENT_BLUE"]
        btn_fg = c["BUTTON_FG"]
        for btn in [self.btn_lexer, self.btn_syntax, self.btn_semantic, self.btn_codegen]:
            btn.config(bg=btn_bg, fg=btn_fg, activebackground=c["ACCENT_GREEN"], activeforeground=btn_fg)

        tool_bg = c.get("BTN_TOOL_BG", "#dddddd")
        tool_fg = c.get("BTN_TOOL_FG", "#000000")
        for btn in [self.btn_clear, self.btn_find]:
            btn.config(bg=tool_bg, fg=tool_fg, activebackground=c["BORDER_COLOR"], bd=0)
        self.btn_kill.config(bg="#c62828", fg="white", activebackground="#b71c1c", bd=0)

        self.text_container.config(bg=c["BORDER_COLOR"])
        self.code_input.config(bg=c["TEXT_AREA_BG"], fg=c["FG_COLOR"],
                               insertbackground=c["FG_COLOR"],
                               selectbackground=c["SELECT_BG"], selectforeground=c["SELECT_FG"])

        # Terminal output area 
        self.error_output.config(bg=c["STATUS_BAR_BG"], fg=c["FG_COLOR"],
                                 selectbackground=c["SELECT_BG"])

        self.autocomplete_listbox.config(bg=c["STATUS_BAR_BG"], fg=c["FG_COLOR"],
                                         selectbackground=c["ACCENT_BLUE"],
                                         selectforeground=c["BUTTON_FG"])

        self.line_numbers.bg_color = c["TREE_HEADING_BG"]
        self.line_numbers.fg_color = c["SECONDARY_TEXT"]
        self.line_numbers.redraw()

        self.status_cursor.config(bg=c["STATUS_BAR_BG"], fg=c["SECONDARY_TEXT"])
        self.status_msg.config(bg=c["STATUS_BAR_BG"], fg=c["ACCENT_BLUE"])
        self.status_time.config(bg=c["STATUS_BAR_BG"], fg=c["SECONDARY_TEXT"])

        row_h = int(self.current_font_size * 2.2)
        style.configure("Treeview", background=c["TEXT_AREA_BG"], foreground=c["FG_COLOR"],
                        fieldbackground=c["TEXT_AREA_BG"], font=self.fonts['ui_reg'],
                        borderwidth=0, rowheight=row_h)
        style.configure("Treeview.Heading", background=c["TREE_HEADING_BG"],
                        foreground=c["FG_COLOR"], font=self.fonts['mono_bold'], relief="flat")
        style.map("Treeview",
                  background=[('selected', c["SELECT_BG"])],
                  foreground=[('selected', c["SELECT_FG"])])
        style.configure("TNotebook", background=c["BG_COLOR"], borderwidth=0)
        style.configure("TNotebook.Tab", background=c["TREE_HEADING_BG"],
                        foreground=c["FG_COLOR"], padding=[12, 4], font=self.fonts['ui_reg'])
        style.map("TNotebook.Tab",
                  background=[("selected", c["TEXT_AREA_BG"])],
                  foreground=[("selected", c["ACCENT_BLUE"])])

        self.configure_tags()

    def configure_tags(self):
        c = self.colors
        self.token_tree.tag_configure('keyword',    foreground=c["ACCENT_PURPLE"], font=self.fonts['mono_bold'])
        self.token_tree.tag_configure('literal',    foreground=c["ACCENT_GREEN"])
        self.token_tree.tag_configure('identifier', foreground=c["FG_COLOR"])
        self.token_tree.tag_configure('operator',   foreground=c["ACCENT_ORANGE"])
        self.token_tree.tag_configure('delimiter',  foreground=c["SECONDARY_TEXT"])
        self.token_tree.tag_configure('comment',    foreground=c["SECONDARY_TEXT"],
                                      font=(self.fonts['code'].actual()['family'], 10, 'italic'))
        self.token_tree.tag_configure('error',      foreground=c["ACCENT_RED"])
        self.token_tree.tag_configure('oddrow',     background=c["TEXT_AREA_BG"])
        self.token_tree.tag_configure('evenrow',    background=c["TREE_EVEN_ROW"])

        # Terminal-specific tags
        self.error_output.tag_configure("error",      foreground=c["ACCENT_RED"],   font=self.fonts['mono_bold'])
        self.error_output.tag_configure("term_error",  foreground="#ff6b6b")
        self.error_output.tag_configure("success",    foreground=c["ACCENT_GREEN"], font=self.fonts['mono_bold'])
        self.error_output.tag_configure("info",       foreground=c["ACCENT_BLUE"])
        self.error_output.tag_configure("term_input", foreground=c["ACCENT_GREEN"]) # echoed user input

    def set_theme(self):
        theme = self.current_theme.get()
        if theme in self.themes:
            self.colors = self.themes[theme]
            self.apply_theme()
            self.refresh_token_display_only()

    def refresh_token_display_only(self):
        for i, item in enumerate(self.token_tree.get_children()):
            tags = [t for t in self.token_tree.item(item, "tags") if t not in ('evenrow', 'oddrow')]
            tags.append('evenrow' if i % 2 == 0 else 'oddrow')
            self.token_tree.item(item, tags=tags)

    # ==========================================================================
    # 9. FILE OPERATIONS
    # ==========================================================================

    def open_file(self):
        filepath = filedialog.askopenfilename(
            title="Open Source File",
            filetypes=[("Chungus Files", "*.chg *.chungus"), ("Text Files", "*.txt"), ("All Files", "*.*")])
        if not filepath: return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.code_input.delete("1.0", tk.END)
            self.code_input.insert("1.0", content)
            self.on_code_change()
            self.status_msg.config(text=f"Opened: {filepath}")
            self.run_lexer()
        except Exception as e:
            messagebox.showerror("Error Opening File", f"Could not read file:\n{e}")

    def save_file(self):
        filepath = filedialog.asksaveasfilename(
            title="Save Source Code", defaultextension=".chg",
            filetypes=[("Chungus Files", "*.chg *.chungus"), ("Text Files", "*.txt"), ("All Files", "*.*")])
        if not filepath: return
        try:
            content = self.code_input.get("1.0", tk.END)
            if content.endswith('\n'): content = content[:-1]
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            self.status_msg.config(text=f"Saved: {filepath}")
        except Exception as e:
            messagebox.showerror("Error Saving File", f"Could not save file:\n{e}")

    def show_about(self):
        messagebox.showinfo("About Chungus Compiler",
            "Chungus Language Compiler Environment\n\n"
            "Created by:\n"
            "- Goyena, Shawn Kieffer E.\n- Cantal, Henkepeck T.\n- Capiral, Luis Gabriel A.\n"
            "- Frias, Railey Miguel B.\n- King, Mariano Luiz B.\n- Manguni, John Gabriel H.\n\n"
            "Course Project - CISTM, PLM")

    # ==========================================================================
    # 10. COMPILER EXECUTION LOGIC
    # ==========================================================================

    def _clear_terminal(self):
        self.error_output.config(state=tk.NORMAL)
        self.error_output.delete("1.0", tk.END)
        self.error_output.config(state=tk.DISABLED)


    def run_lexer(self):
        self.status_msg.config(text="Running Lexer...")
        self._clear_terminal()
        for item in self.token_tree.get_children(): self.token_tree.delete(item)

        source_code = self.code_input.get("1.0", "end-1c").expandtabs(4)
        if not callable(self.lexer_callback):
            self._show_mock_instructions("Lexer"); return
        try:
            tokens, errors = self.lexer_callback(source_code)
        except Exception as e:
            messagebox.showerror("Lexer Internal Error", str(e))
            self.status_msg.config(text="Lexer Failed."); return

        self._populate_tokens(tokens)
        self.error_output.config(state=tk.NORMAL)
        if errors:
            self.error_output.insert(tk.END, "\n".join(errors), "error")
            self.status_msg.config(text=f"Lexer finished with {len(errors)} errors.")
        else:
            self.error_output.insert(tk.END, ">>> Lexical analysis complete. No errors found.", "success")
            self.status_msg.config(text="Lexer finished successfully.")
        self.error_output.config(state=tk.DISABLED)


    def run_syntax(self):
        self.status_msg.config(text="Running Parser...")
        self._clear_terminal()
        for item in self.token_tree.get_children(): self.token_tree.delete(item)

        source_code = self.code_input.get("1.0", "end-1c").expandtabs(4)
        if not callable(self.syntax_callback):
            self._show_mock_instructions("Syntax"); return
        try:
            tokens, errors = self.syntax_callback(source_code)
        except Exception as e:
            messagebox.showerror("Parser Internal Error", str(e))
            self.status_msg.config(text="Parser Failed."); return

        self._populate_tokens(tokens)
        self.error_output.config(state=tk.NORMAL)
        if errors:
            self.error_output.insert(tk.END, "\n".join(errors), "error")
            self.status_msg.config(text=f"Syntax analysis finished with {len(errors)} errors.")
        else:
            self.error_output.insert(tk.END, ">>> Syntax analysis complete. No errors found.", "success")
            self.status_msg.config(text="Syntax analysis finished successfully.")
        self.error_output.config(state=tk.DISABLED)


    def run_semantic(self):
        self.status_msg.config(text="Running Semantic Analyzer...")
        self._clear_terminal()
        for item in self.token_tree.get_children(): self.token_tree.delete(item)

        source_code = self.code_input.get("1.0", "end-1c").expandtabs(4)
        if not callable(self.semantic_callback):
            messagebox.showinfo("Semantic Analyzer", "No semantic analyzer callback provided.")
            self.status_msg.config(text="Semantic analyzer not configured."); return
        try:
            tokens, errors = self.semantic_callback(source_code)
        except Exception as e:
            messagebox.showerror("Semantic Analyzer Internal Error", str(e))
            self.status_msg.config(text="Semantic Analysis Failed."); return

        self._populate_tokens(tokens)
        self.error_output.config(state=tk.NORMAL)
        if errors:
            self.error_output.insert(tk.END, "Errors found during semantic analysis:\n", "info")
            self.error_output.insert(tk.END, "\n".join(errors), "error")
            self.status_msg.config(text=f"Semantic analysis finished with {len(errors)} errors.")
        else:
            self.error_output.insert(tk.END, ">>> Semantic analysis complete. No errors found.", "success")
            self.status_msg.config(text="Semantic analysis finished successfully.")
        self.error_output.config(state=tk.DISABLED)


    def run_codegen(self):
        if not callable(self.codegen_callback):
            messagebox.showinfo("Code Generator", "No code generator callback provided.")
            self.status_msg.config(text="Code generator not configured."); return

        self._clear_terminal()

        # delete table of tokens
        for item in self.token_tree.get_children(): self.token_tree.delete(item)

        self.btn_codegen.config(state=tk.DISABLED)
        self.status_msg.config(text="Compiling...")

        # self._term_write("Compiling...\n", tag="info")

        source_code = self.code_input.get("1.0", "end-1c").expandtabs(4)

        def _worker():
            try:
                # codegen_callback now returns (tokens, errors, proc_or_None)
                result = self.codegen_callback(source_code)
                if len(result) == 3:
                    tokens, errors, proc = result
                else:
                    tokens, errors = result
                    proc = None
            except Exception as exc:
                tokens, errors, proc = [], [f"Code Generator Internal Error: {exc}"], None
        
            # returns to main thread
            self.root.after(0, lambda: self._finish_codegen(tokens, errors, proc))

        # Create a new thread that runs _worker in the background
        threading.Thread(target=_worker, daemon=True).start()

    def _finish_codegen(self, tokens, errors, proc=None):
        """Called on the main thread after compilation finishes."""
        self._populate_tokens(tokens)

        if errors:
            # Compilation/semantic errors — display and stop
            self.error_output.config(state=tk.NORMAL)
            self.error_output.delete("1.0", tk.END)
            for line in errors:
                if isinstance(line, bytes): line = line.decode('utf-8', errors='replace')
                tag = "error" if "Error" in line else ("info" if "===" in line else None)
                self.error_output.insert(tk.END, line + "\n", tag or "")
            self.error_output.config(state=tk.DISABLED)
            self.status_msg.config(text="Compilation failed.")
            self.btn_codegen.config(state=tk.NORMAL)
            return

        if proc is None:
            # No process to run (unexpected)
            self._term_write(">>> Done (no output).\n", tag="success")
            self.status_msg.config(text="Done.")
            self.btn_codegen.config(state=tk.NORMAL)
            return

        # ── Live process: wire up streaming I/O ─────────────────────────────
        with self._proc_lock:
            self._running_proc = proc   # Store for kill button

        self._show_input_bar()          # Show the input bar at bottom
        self.status_msg.config(text="Program running...")

        # self._term_write("=== Program started ===\n", tag="info")

        def _stream_output():
            """Read stdout/stderr line-by-line and push to terminal."""

            # Setting Up Non-Blocking Reading
            # selectors lets us check "is there data to read?" without waiting
            import selectors, os, time

            # watches multiple streams at once
            sel = selectors.DefaultSelector()
            for stream in [proc.stdout, proc.stderr]:
                if stream:
                    try: os.set_blocking(stream.fileno(), False) # makes reads return immediately (not wait)
                    except Exception: pass

                    # Watch this stream and notify me when it has data ready to be read.
                    sel.register(stream, selectors.EVENT_READ)

            start = time.monotonic()
            TIMEOUT = 30.0   # generous — user is interacting

            while True:
                if time.monotonic() - start > TIMEOUT:
                    self._term_write("\n[Execution Timeout: 30s]\n", tag="term_error")
                    try: proc.kill()
                    except Exception: pass
                    break

                events = sel.select(timeout=0.05)  # Wait up to 0.05 seconds for data
                for key, _ in events:
                    stream = key.fileobj
                    try: chunk = stream.read()     # Read available data
                    except Exception: chunk = ""

                    if chunk == "":
                        # means the stream has been closed, so we unregister
                        try: sel.unregister(stream)
                        except Exception: pass
                        continue

                    tag = "term_error" if stream is proc.stderr else None
                    self._term_write(chunk, tag=tag)

                if proc.poll() is not None and not sel.get_map():
                    break

            rc = proc.wait() # wait then returns the exit code. (0 = success, other = error); 

            # with statement is a context manager that handles cleanup for ANY resource that needs cleanup
            # thread lock - prevents racing conditions
            with self._proc_lock:
                self._running_proc = None # No longer runnin

            def _done():
                self._hide_input_bar()  # Hide input bar
                self.btn_codegen.config(state=tk.NORMAL)
                if rc == 0:
                    self._term_write("\n=== Program finished (exit 0) ===\n", tag="success")
                    self.status_msg.config(text="Program finished successfully.")
                else:
                    self._term_write(f"\n=== Program exited with code {rc} ===\n", tag="term_error")
                    self.status_msg.config(text=f"Program exited with code {rc}.")

            # tkinter switching from a background thread to the main GUI thread
            self.root.after(0, _done)

        threading.Thread(target=_stream_output, daemon=True).start()

    def _populate_tokens(self, tokens):
        """ populate table from lexical """
        for i, token in enumerate(tokens):
            token_type_name = getattr(token, "type", token.get("type") if isinstance(token, dict) else "")
            if hasattr(token_type_name, "name"): token_type_name = token_type_name.name
            line = getattr(token, "line", token.get("line") if isinstance(token, dict) else "")
            col  = getattr(token, "col",  token.get("col")  if isinstance(token, dict) else "")
            raw_lexeme = getattr(token, "lexeme", token.get("lexeme") if isinstance(token, dict) else str(token))
            lexeme = raw_lexeme.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '    ')

            t  = str(token_type_name).lower()
            lx = str(raw_lexeme).lower()
            tag = 'identifier'
            if t in LITERALS:       tag = 'literal'
            elif t == 'comment':    tag = 'comment'
            elif lx in OPERATORS:   tag = 'operator'
            elif lx in DELIMS:      tag = 'delimiter'
            elif t in KEYWORDS:     tag = 'keyword'

            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.token_tree.insert("", tk.END, values=(line, col, lexeme, token_type_name),
                                   tags=(tag, row_tag))

    def _show_mock_instructions(self, mode):
        self.error_output.config(state=tk.NORMAL)
        self.error_output.insert(tk.END,
            f"No {mode.lower()} backend connected.\n\n"
            f"Provide a callable gui.{mode.lower()}_callback = lambda src: (tokens, errors)\n"
            "Where tokens is a list of objects/dicts with fields: type, lexeme, line, col.\n\n",
            "error")
        self.error_output.config(state=tk.DISABLED)