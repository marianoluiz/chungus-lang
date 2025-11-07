import tkinter as tk
from tkinter import ttk, scrolledtext, font, messagebox, filedialog
from enum import Enum
import string
import platform

# =============================================================================
# 1. TOKEN DEFINITIONS (No changes here)
# =============================================================================
class TokenType(Enum):
    INT_LIT = 'INT_LIT'; FLOAT_LIT = 'FLOAT_LIT'; STRING_LIT = 'STRING_LIT'; IDENTIFIER = 'IDENTIFIER'
    KEYWORD_TRUE = 'KEYWORD_TRUE'; KEYWORD_FALSE = 'KEYWORD_FALSE'; KEYWORD_NULL = 'KEYWORD_NULL'
    KEYWORD_READ = 'KEYWORD_READ'; KEYWORD_SHOW = 'KEYWORD_SHOW'; KEYWORD_CLR = 'KEYWORD_CLR'; KEYWORD_EXIT = 'KEYWORD_EXIT'
    KEYWORD_IF = 'KEYWORD_IF'; KEYWORD_ELIF = 'KEYWORD_ELIF'; KEYWORD_ELSE = 'KEYWORD_ELSE'
    KEYWORD_WHILE = 'KEYWORD_WHILE'; KEYWORD_FOR = 'KEYWORD_FOR'; KEYWORD_IN = 'KEYWORD_IN'; KEYWORD_RANGE = 'KEYWORD_RANGE'; KEYWORD_SKIP = 'KEYWORD_SKIP'; KEYWORD_STOP = 'KEYWORD_STOP'
    KEYWORD_FN = 'KEYWORD_FN'; KEYWORD_RET = 'KEYWORD_RET'
    KEYWORD_TRY = 'KEYWORD_TRY'; KEYWORD_FAIL = 'KEYWORD_FAIL'; KEYWORD_ALWAYS = 'KEYWORD_ALWAYS'
    KEYWORD_INT = 'KEYWORD_INT'; KEYWORD_FLOAT = 'KEYWORD_FLOAT'
    KEYWORD_ARRAY_ADD = 'KEYWORD_ARRAY_ADD'; KEYWORD_ARRAY_REMOVE = 'KEYWORD_ARRAY_REMOVE'
    KEYWORD_AND = 'KEYWORD_AND'; KEYWORD_OR = 'KEYWORD_OR'; KEYWORD_TODO = 'KEYWORD_TODO'
    OP_PLUS = 'OP_PLUS'; OP_MINUS = 'OP_MINUS'; OP_MULTIPLY = 'OP_MULTIPLY'; OP_DIVIDE = 'OP_DIVIDE'; OP_MODULUS = 'OP_MODULUS'; OP_EXPONENT = 'OP_EXPONENT'; OP_FLOOR_DIV = 'OP_FLOOR_DIV'
    OP_ASSIGN = 'OP_ASSIGN'
    OP_EQUAL_TO = 'OP_EQUAL_TO'; OP_NOT_EQUAL = 'OP_NOT_EQUAL'; OP_LESS_THAN = 'OP_LESS_THAN'; OP_GREATER_THAN = 'OP_GREATER_THAN'; OP_LESS_EQUAL = 'OP_LESS_EQUAL'; OP_GREATER_EQUAL = 'OP_GREATER_EQUAL'
    OP_NOT = 'OP_NOT'
    OP_INCREMENT = 'OP_INCREMENT'; OP_DECREMENT = 'OP_DECREMENT'
    DELIM_LPAREN = 'DELIM_LPAREN'; DELIM_RPAREN = 'DELIM_RPAREN'; DELIM_LBRACKET = 'DELIM_LBRACKET'; DELIM_RBRACKET = 'DELIM_RBRACKET'; DELIM_COMMA = 'DELIM_COMMA'; DELIM_SQUOTE = 'DELIM_SQUOTE'
    COMMENT_SINGLE = 'COMMENT_SINGLE'; COMMENT_MULTI = 'COMMENT_MULTI'
    EOF = 'EOF'

KEYWORDS = {
    'true': TokenType.KEYWORD_TRUE, 'false': TokenType.KEYWORD_FALSE, 'null': TokenType.KEYWORD_NULL,
    'read': TokenType.KEYWORD_READ, 'show': TokenType.KEYWORD_SHOW, 'clr': TokenType.KEYWORD_CLR,
    'exit': TokenType.KEYWORD_EXIT, 'if': TokenType.KEYWORD_IF, 'elif': TokenType.KEYWORD_ELIF,
    'else': TokenType.KEYWORD_ELSE, 'while': TokenType.KEYWORD_WHILE, 'for': TokenType.KEYWORD_FOR,
    'in': TokenType.KEYWORD_IN, 'range': TokenType.KEYWORD_RANGE, 'skip': TokenType.KEYWORD_SKIP,
    'stop': TokenType.KEYWORD_STOP, 'fn': TokenType.KEYWORD_FN, 'ret': TokenType.KEYWORD_RET,
    'try': TokenType.KEYWORD_TRY, 'fail': TokenType.KEYWORD_FAIL, 'always': TokenType.KEYWORD_ALWAYS,
    'int': TokenType.KEYWORD_INT, 'float': TokenType.KEYWORD_FLOAT, 'array_add': TokenType.KEYWORD_ARRAY_ADD,
    'array_remove': TokenType.KEYWORD_ARRAY_REMOVE, 'and': TokenType.KEYWORD_AND, 'or': TokenType.KEYWORD_OR,
    'todo': TokenType.KEYWORD_TODO,
}

class Token:
    def __init__(self, type, lexeme, line, col):
        self.type = type; self.lexeme = lexeme; self.line = line; self.col = col
    def __repr__(self):
        return f"Token({self.type.name}, '{self.lexeme}', L{self.line}:C{self.col})"

# =============================================================================
# 2. THE LEXER (FINITE AUTOMATON) (No changes here)
# =============================================================================
class Lexer:
    # ... (Keep the entire Lexer class exactly as before) ...
    def __init__(self, source_code):
        self.source = source_code; self.pos = 0; self.line = 1; self.col = 1
        self.tokens = []; self.errors = []
    def tokenize(self):
        while not self.is_at_end():
            start_pos = self.pos; start_line = self.line; start_col = self.col
            char = self.advance()
            if char in ' \t': continue
            elif char == '\n': continue
            elif char == '#':
                if self.match('#') and self.match('#'): self.multi_line_comment(start_line, start_col)
                else: self.single_line_comment()
                continue
            elif char == '*':
                if self.match('*'): self.add_token(TokenType.OP_EXPONENT, '**')
                else: self.add_token(TokenType.OP_MULTIPLY, '*')
            elif char == '/':
                if self.match('/'): self.add_token(TokenType.OP_FLOOR_DIV, '//')
                else: self.add_token(TokenType.OP_DIVIDE, '/')
            elif char == '=':
                if self.match('='): self.add_token(TokenType.OP_EQUAL_TO, '==')
                else: self.add_token(TokenType.OP_ASSIGN, '=')
            elif char == '!':
                if self.match('='): self.add_token(TokenType.OP_NOT_EQUAL, '!=')
                else: self.add_token(TokenType.OP_NOT, '!')
            elif char == '<':
                if self.match('='): self.add_token(TokenType.OP_LESS_EQUAL, '<=')
                else: self.add_token(TokenType.OP_LESS_THAN, '<')
            elif char == '>':
                if self.match('='): self.add_token(TokenType.OP_GREATER_EQUAL, '>=')
                else: self.add_token(TokenType.OP_GREATER_THAN, '>')
            elif char == '+':
                if self.match('+'): self.add_token(TokenType.OP_INCREMENT, '++')
                else: self.add_token(TokenType.OP_PLUS, '+')
            elif char == '-':
                if self.match('-'): self.add_token(TokenType.OP_DECREMENT, '--')
                else: self.add_token(TokenType.OP_MINUS, '-')
            elif char == '%': self.add_token(TokenType.OP_MODULUS, '%')
            elif char == '(': self.add_token(TokenType.DELIM_LPAREN, '(')
            elif char == ')': self.add_token(TokenType.DELIM_RPAREN, ')')
            elif char == '[': self.add_token(TokenType.DELIM_LBRACKET, '[')
            elif char == ']': self.add_token(TokenType.DELIM_RBRACKET, ']')
            elif char == ',': self.add_token(TokenType.DELIM_COMMA, ',')
            elif char == "'": self.string_literal(start_line, start_col)
            elif char.isdigit(): self.number_literal(start_pos)
            elif char.isalpha() or char == '_': self.identifier(start_pos)
            else: self.log_error(start_line, start_col, f"Invalid character '{char}'")
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.col))
        return self.tokens, self.errors
    def single_line_comment(self):
        while self.peek() != '\n' and not self.is_at_end(): self.advance()
    def multi_line_comment(self, start_line, start_col):
        while not self.is_at_end():
            if self.peek() == '#' and self.peek_n(1) == '#' and self.peek_n(2) == '#':
                self.advance(); self.advance(); self.advance(); return
            if self.peek() == '\n': self.line += 1; self.col = 1
            self.advance()
        self.log_error(start_line, start_col, "Unterminated multi-line comment")
    def string_literal(self, start_line, start_col):
        start_pos = self.pos
        while self.peek() != "'" and not self.is_at_end():
            char = self.peek()
            if char == '\n':
                self.log_error(self.line, self.col, "Newline in string literal")
                self.add_token(TokenType.STRING_LIT, self.source[start_pos : self.pos]); return
            if char == '\\':
                if self.peek_n(1) in ("'", 'n', 't', '$', '\\'): self.advance()
            self.advance()
        if self.is_at_end(): self.log_error(start_line, start_col, "Unterminated string"); return
        self.advance()
        lexeme = self.source[start_pos - 1 : self.pos]; self.add_token(TokenType.STRING_LIT, lexeme)
    def number_literal(self, start_pos):
        is_float = False
        while self.peek().isdigit(): self.advance()
        if self.peek() == '.' and self.peek_n(1).isdigit():
            is_float = True; self.advance()
            while self.peek().isdigit(): self.advance()
        elif self.peek() == '.':
            self.advance(); lexeme = self.source[start_pos : self.pos]
            self.log_error(self.line, self.col, f"Invalid float literal '{lexeme}'"); return
        lexeme = self.source[start_pos : self.pos]
        if is_float: self.add_token(TokenType.FLOAT_LIT, lexeme)
        else: self.add_token(TokenType.INT_LIT, lexeme)
    def identifier(self, start_pos):
        while self.peek().isalnum() or self.peek() == '_': self.advance()
        lexeme = self.source[start_pos : self.pos]
        token_type = KEYWORDS.get(lexeme, TokenType.IDENTIFIER); self.add_token(token_type, lexeme)
    def is_at_end(self): return self.pos >= len(self.source)
    def advance(self):
        if self.is_at_end(): return '\0'
        char = self.source[self.pos]; self.pos += 1
        if char == '\n': self.line += 1; self.col = 1
        else: self.col += 1
        return char
    def peek(self): return self.source[self.pos] if not self.is_at_end() else '\0'
    def peek_n(self, n): return self.source[self.pos + n] if self.pos + n < len(self.source) else '\0'
    def match(self, expected):
        if self.is_at_end() or self.source[self.pos] != expected: return False
        self.pos += 1; self.col += 1; return True
    def add_token(self, type, lexeme): self.tokens.append(Token(type, lexeme, self.line, self.col - len(lexeme)))
    def log_error(self, line, col, message): self.errors.append(f"Lexical error: line {line} col {col} - {message}")

# =============================================================================
# 3. THE GRAPHICAL USER INTERFACE (GUI) (Added Big Chungus Theme)
# =============================================================================
class ChungusLexerGUI:
    def __init__(self, root):
        self.root = root
        root.title("Chungus Lexical Analyzer")
        root.geometry("1200x820")

        self.current_theme = tk.StringVar(value="Light (macOS)") # Variable for theme selection

        # --- Define Color Palettes ---
        self.themes = {
            "Light (macOS)": { "BG_COLOR": "#f5f5f7", "TEXT_AREA_BG": "#ffffff", "FG_COLOR": "#333333", "ACCENT_BLUE": "#007aff", "ACCENT_GREEN": "#34c759", "ACCENT_RED": "#ff3b30", "ACCENT_ORANGE": "#ff9500", "ACCENT_PURPLE": "#af52de", "BORDER_COLOR": "#d1d1d6", "TITLE_COLOR": "#1c1c1e", "SECONDARY_TEXT": "#6e6e73", "STATUS_BAR_BG": "#e5e5ea", "TREE_HEADING_BG": "#f9f9f9", "TREE_EVEN_ROW": "#fafafa", "BUTTON_FG": "white", "SELECT_BG": "#b3d7ff", "SELECT_FG": "#333333" },
            "Dark": { "BG_COLOR": "#1e1e1e", "TEXT_AREA_BG": "#2a2a2a", "FG_COLOR": "#d4d4d4", "ACCENT_BLUE": "#007acc", "ACCENT_GREEN": "#4ec9b0", "ACCENT_RED": "#f44747", "ACCENT_ORANGE": "#ce9178", "ACCENT_PURPLE": "#c586c0", "BORDER_COLOR": "#444444", "TITLE_COLOR": "#cccccc", "SECONDARY_TEXT": "#9e9e9e", "STATUS_BAR_BG": "#1a1a1a", "TREE_HEADING_BG": "#333333", "TREE_EVEN_ROW": "#303030", "BUTTON_FG": "#d4d4d4", "SELECT_BG": "#007acc", "SELECT_FG": "#d4d4d4" },
            "Oceanic Blue": { "BG_COLOR": "#e0f2f7", "TEXT_AREA_BG": "#ffffff", "FG_COLOR": "#004d40", "ACCENT_BLUE": "#0277bd", "ACCENT_GREEN": "#00695c", "ACCENT_RED": "#c62828", "ACCENT_ORANGE": "#e65100", "ACCENT_PURPLE": "#6a1b9a", "BORDER_COLOR": "#b0bec5", "TITLE_COLOR": "#01579b", "SECONDARY_TEXT": "#455a64", "STATUS_BAR_BG": "#cfd8dc", "TREE_HEADING_BG": "#e1f5fe", "TREE_EVEN_ROW": "#f5fcff", "BUTTON_FG": "white", "SELECT_BG": "#81d4fa", "SELECT_FG": "#004d40" },
            "Forest Green": { "BG_COLOR": "#263238", "TEXT_AREA_BG": "#37474f", "FG_COLOR": "#eceff1", "ACCENT_BLUE": "#80cbc4", "ACCENT_GREEN": "#a5d6a7", "ACCENT_RED": "#ef9a9a", "ACCENT_ORANGE": "#ffcc80", "ACCENT_PURPLE": "#ce93d8", "BORDER_COLOR": "#546e7a", "TITLE_COLOR": "#b0bec5", "SECONDARY_TEXT": "#90a4ae", "STATUS_BAR_BG": "#1a252a", "TREE_HEADING_BG": "#455a64", "TREE_EVEN_ROW": "#3c4f57", "BUTTON_FG": "#1a252a", "SELECT_BG": "#00695c", "SELECT_FG": "#eceff1" },
            "Big Chungus": { # NEW THEME!
                "BG_COLOR": "#add8e6", # Light Blue Sky
                "TEXT_AREA_BG": "#ffffff", # White Fur
                "FG_COLOR": "#404040", # Dark Grey Text
                "ACCENT_BLUE": "#ff4500", # OrangeRed (Button/Accent - Carrot)
                "ACCENT_GREEN": "#228b22", # Forest Green (Grass/Literals)
                "ACCENT_RED": "#dc143c", # Crimson Red (Bugs Details/Errors)
                "ACCENT_ORANGE": "#8b4513", # Saddle Brown (Operators?)
                "ACCENT_PURPLE": "#a9a9a9", # Dark Gray (Keywords - Bunny Gray)
                "BORDER_COLOR": "#87ceeb", # Sky Blue Border
                "TITLE_COLOR": "#ff4500", # OrangeRed Title
                "SECONDARY_TEXT": "#708090", # Slate Gray
                "STATUS_BAR_BG": "#f0f8ff", # Alice Blue
                "TREE_HEADING_BG": "#ffdead", # Navajo White
                "TREE_EVEN_ROW": "#fff8dc", # Cornsilk
                "BUTTON_FG": "white",
                "SELECT_BG": "#ffd700", # Gold Selection
                "SELECT_FG": "#404040"
            }
        }
        self.colors = self.themes[self.current_theme.get()]

        # --- Fonts ---
        os_name = platform.system()
        # ... (Font selection logic) ...
        if os_name == "Darwin": default_font_family = "SF Pro Text"; title_font_family = "SF Pro Display"; mono_font_family = "SF Mono"
        elif os_name == "Windows": default_font_family = "Segoe UI Variable Text"; title_font_family = "Segoe UI Variable Display"; mono_font_family = "Consolas"
        else: default_font_family = "Cantarell"; title_font_family = "Cantarell"; mono_font_family = "Monospace"
        try: self.title_font = font.Font(family=title_font_family, size=24, weight="bold");
        except: self.title_font = font.Font(family="Arial", size=24, weight="bold")
        try: self.label_font = font.Font(family=default_font_family, size=10);
        except: self.label_font = font.Font(family="Arial", size=10)
        try: self.label_font_bold = font.Font(family=default_font_family, size=11, weight="bold");
        except: self.label_font_bold = font.Font(family="Arial", size=11, weight="bold")
        try: self.code_font = font.Font(family=mono_font_family, size=11);
        except: self.code_font = font.Font(family="Courier New", size=11)
        try: self.token_font = font.Font(family=mono_font_family, size=10);
        except: self.token_font = font.Font(family="Courier New", size=10)
        try: self.token_font_bold = font.Font(family=mono_font_family, size=10, weight="bold");
        except: self.token_font_bold = font.Font(family="Courier New", size=10, weight="bold")
        try: self.status_font = font.Font(family=default_font_family, size=9);
        except: self.status_font = font.Font(family="Arial", size=9)


        # --- Build UI ---
        self.build_menu()
        self.build_widgets()
        self.apply_theme() # Apply initial theme

    def build_menu(self):
        """Builds the main menu bar."""
        self.menubar = tk.Menu(self.root)
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="Open File...", command=self.open_file)
        file_menu.add_command(label="Save Code As...", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(self.menubar, tearoff=0)
        theme_menu = tk.Menu(view_menu, tearoff=0)
        # Add radio buttons for each theme, including Big Chungus
        for theme_name in self.themes.keys():
            theme_menu.add_radiobutton(label=theme_name, variable=self.current_theme, value=theme_name, command=self.set_theme)
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        self.menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label="About Chungus Analyzer", command=self.show_about)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=self.menubar)

    def build_widgets(self):
        """Builds the main widgets of the application."""
        self.style = ttk.Style()
        try:
            os_name = platform.system()
            if os_name == "Darwin": self.style.theme_use('aqua')
            elif os_name == "Windows": self.style.theme_use('vista')
            else: self.style.theme_use('clam')
        except tk.TclError: self.style.theme_use('default')

        self.main_frame = tk.Frame(self.root, padx=25, pady=25)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.title_label = ttk.Label(self.main_frame, text="Chungus Lexical Analyzer", style='Title.TLabel', anchor="center")
        self.title_label.pack(pady=(0, 25))

        self.paned_window = tk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL, relief="flat", borderwidth=0, sashwidth=8, sashrelief="flat", showhandle=False)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        self.left_frame = tk.Frame(self.paned_window, padx=10, pady=10)
        self.paned_window.add(self.left_frame)

        self.code_label = ttk.Label(self.left_frame, text="Source Code", style='Bold.TLabel')
        self.code_label.pack(anchor="w", pady=(0, 8))
        self.code_input_frame = tk.Frame(self.left_frame, borderwidth=1, relief="solid")
        self.code_input_frame.pack(fill=tk.BOTH, expand=True)
        self.code_input = tk.Text(self.code_input_frame, height=20, font=self.code_font, wrap=tk.WORD, borderwidth=0, relief="flat", highlightthickness=0, padx=12, pady=12)
        self.code_scrollbar = ttk.Scrollbar(self.code_input_frame, orient=tk.VERTICAL, command=self.code_input.yview, style="Vertical.TScrollbar")
        self.code_input.configure(yscrollcommand=self.code_scrollbar.set)
        self.code_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.code_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.code_input.insert(tk.END, self.get_sample_code())
        self.code_input.bind("<FocusIn>", self.on_focus_in)
        self.code_input.bind("<FocusOut>", self.on_focus_out)
        self.code_input.bind("<KeyRelease>", self.update_status_bar)
        self.code_input.bind("<ButtonRelease>", self.update_status_bar)

        self.analyze_button = tk.Button(self.left_frame, text="Analyze Code", command=self.run_lexer, font=self.label_font_bold, relief="flat", borderwidth=0, padx=20, pady=10)
        self.analyze_button.pack(fill=tk.X, pady=18)

        self.error_label = ttk.Label(self.left_frame, text="Console Output", style='Bold.TLabel')
        self.error_label.pack(anchor="w", pady=(0, 8))
        self.error_output_frame = tk.Frame(self.left_frame, borderwidth=1, relief="solid")
        self.error_output_frame.pack(fill=tk.BOTH, expand=True)
        self.error_output = tk.Text(self.error_output_frame, height=6, font=self.token_font, wrap=tk.WORD, borderwidth=0, relief="flat", highlightthickness=0, padx=12, pady=12)
        self.error_scrollbar = ttk.Scrollbar(self.error_output_frame, orient=tk.VERTICAL, command=self.error_output.yview, style="Vertical.TScrollbar")
        self.error_output.configure(yscrollcommand=self.error_scrollbar.set)
        self.error_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.error_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.error_output.config(state=tk.DISABLED)
        self.error_output.bind("<FocusIn>", self.on_focus_in)
        self.error_output.bind("<FocusOut>", self.on_focus_out)

        self.right_frame = tk.Frame(self.paned_window, padx=10, pady=10)
        self.paned_window.add(self.right_frame)

        self.token_label = ttk.Label(self.right_frame, text="Generated Tokens", style='Bold.TLabel')
        self.token_label.pack(anchor="w", pady=(0, 8))
        self.tree_container_frame = tk.Frame(self.right_frame, bd=1, relief="solid")
        self.tree_container_frame.pack(fill=tk.BOTH, expand=True)
        self.token_tree = ttk.Treeview(self.tree_container_frame, columns=("Line", "Col", "Lexeme", "Token"), show="headings", style="Treeview")
        self.token_tree.heading("Line", text="Line", anchor='center') # Center align
        self.token_tree.heading("Col", text="Col", anchor='center')   # Center align
        self.token_tree.heading("Lexeme", text="Lexeme", anchor='w')
        self.token_tree.heading("Token", text="Token Type", anchor='w')

        self.token_tree.column("Line", width=60, anchor="center", stretch=False) # Center align
        self.token_tree.column("Col", width=60, anchor="center", stretch=False)  # Center align
        self.token_tree.column("Lexeme", width=200, anchor="w", stretch=True)
        self.token_tree.column("Token", width=200, anchor="w", stretch=True)

        self.tree_scrollbar = ttk.Scrollbar(self.tree_container_frame, orient=tk.VERTICAL, command=self.token_tree.yview, style="Vertical.TScrollbar")
        self.token_tree.configure(yscrollcommand=self.tree_scrollbar.set)
        self.tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.token_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.token_tree.bind("<FocusIn>", self.on_focus_in)
        self.token_tree.bind("<FocusOut>", self.on_focus_out)

        self.status_bar = tk.Frame(self.root, bd=1, relief='sunken')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = tk.Label(self.status_bar, text="Line: 1, Col: 1", font=self.status_font, anchor='w')
        self.status_label.pack(side=tk.LEFT, padx=5)

    def apply_theme(self):
        """Applies the current color theme to all widgets."""
        c = self.colors

        # Root and main frames
        self.root.configure(bg=c["BG_COLOR"])
        self.main_frame.configure(bg=c["BG_COLOR"])
        self.left_frame.configure(bg=c["BG_COLOR"])
        self.right_frame.configure(bg=c["BG_COLOR"])
        self.paned_window.configure(bg=c["BORDER_COLOR"], sashrelief='flat')

        # --- Reconfigure ttk styles ---
        self.style.configure('.', background=c["BG_COLOR"], foreground=c["FG_COLOR"])
        self.style.configure('TFrame', background=c["BG_COLOR"])
        self.style.configure('TLabel', background=c["BG_COLOR"], foreground=c["FG_COLOR"])
        self.style.configure('Title.TLabel', foreground=c["TITLE_COLOR"], background=c["BG_COLOR"], font=self.title_font)
        self.style.configure('Bold.TLabel', foreground=c["FG_COLOR"], background=c["BG_COLOR"], font=self.label_font_bold)
        self.style.configure('TPanedwindow', background=c["BG_COLOR"])

        # Treeview Styles - IMPORTANT to reconfigure these
        self.style.configure("Treeview", background=c["TEXT_AREA_BG"], foreground=c["FG_COLOR"], fieldbackground=c["TEXT_AREA_BG"], font=self.token_font)
        self.style.configure("Treeview.Heading", background=c["TREE_HEADING_BG"], foreground=c["FG_COLOR"], font=self.label_font_bold)
        self.style.map('Treeview', background=[('selected', c["ACCENT_BLUE"])], foreground=[('selected', c["BUTTON_FG"])])

        # Scrollbar Styles - IMPORTANT to reconfigure these
        self.style.configure("Vertical.TScrollbar", troughcolor=c["BG_COLOR"], background=c["STATUS_BAR_BG"], arrowcolor=c["SECONDARY_TEXT"])
        self.style.map("Vertical.TScrollbar", background=[('active', c["BORDER_COLOR"])])
        # --------------------------------

        # Update tk widget colors directly
        try: self.title_label.configure(background=c["BG_COLOR"], foreground=c["TITLE_COLOR"])
        except: pass
        try: self.code_label.configure(background=c["BG_COLOR"], foreground=c["FG_COLOR"])
        except: pass
        try: self.error_label.configure(background=c["BG_COLOR"], foreground=c["FG_COLOR"])
        except: pass
        try: self.token_label.configure(background=c["BG_COLOR"], foreground=c["FG_COLOR"])
        except: pass

        # Text Areas and Frames
        for frame in [self.code_input_frame, self.error_output_frame, self.tree_container_frame]:
            try: frame.configure(background=c["TEXT_AREA_BG"], highlightbackground=c["BORDER_COLOR"])
            except: pass
        for text_widget in [self.code_input, self.error_output]:
             try:
                 text_widget.configure(bg=c["TEXT_AREA_BG"], fg=c["FG_COLOR"], insertbackground=c["FG_COLOR"],
                                      selectbackground=c["SELECT_BG"],
                                      selectforeground=c["SELECT_FG"])
             except: pass

        # Button - Use ACCENT_BLUE from the theme's palette
        try:
            button_bg = c.get("ACCENT_BLUE", "#007aff") # Default to blue if not defined in theme
            button_fg = c.get("BUTTON_FG", "white")
            active_bg = "#005ec4" # Keep darker blue consistent for now

            # Special case for Big Chungus button color
            if self.current_theme.get() == "Big Chungus":
                 button_bg = c.get("ACCENT_BLUE") # Which is OrangeRed in this theme
                 active_bg = "#cc3700" # Darker OrangeRed

            self.analyze_button.configure(bg=button_bg, fg=button_fg,
                                          activebackground=active_bg,
                                          activeforeground=button_fg)
        except: pass


        # Status Bar
        try:
            self.status_bar.configure(bg=c["STATUS_BAR_BG"], relief='flat', bd=0)
            self.status_label.configure(bg=c["STATUS_BAR_BG"], fg=c["SECONDARY_TEXT"])
        except: pass

        # Treeview Tags (Re-apply colors based on theme)
        self.token_tree.tag_configure('keyword', foreground=c["ACCENT_PURPLE"], font=self.token_font_bold)
        self.token_tree.tag_configure('literal', foreground=c["ACCENT_GREEN"])
        self.token_tree.tag_configure('identifier', foreground=c["FG_COLOR"])
        self.token_tree.tag_configure('operator', foreground=c["ACCENT_ORANGE"])
        self.token_tree.tag_configure('delimiter', foreground=c["SECONDARY_TEXT"])
        self.token_tree.tag_configure('comment', foreground=c["SECONDARY_TEXT"], font=(self.token_font.actual()['family'], self.token_font.actual()['size'], 'italic'))
        self.token_tree.tag_configure('error', foreground=c["ACCENT_RED"])
        self.token_tree.tag_configure('linecol', foreground=c["SECONDARY_TEXT"])

        self.token_tree.tag_configure('oddrow', background=c["TEXT_AREA_BG"])
        self.token_tree.tag_configure('evenrow', background=c["TREE_EVEN_ROW"])

        # Update error/success message colors in console
        self.error_output.tag_configure("error", foreground=c["ACCENT_RED"])
        self.error_output.tag_configure("success", foreground=c["ACCENT_GREEN"])
        current_text = ""
        try:
            current_text = self.error_output.get("1.0", tk.END).strip()
            self.error_output.config(state=tk.NORMAL)
            self.error_output.delete("1.0", tk.END)
            if current_text.startswith(">>>"): self.error_output.insert(tk.END, current_text, "success")
            elif current_text: self.error_output.insert(tk.END, current_text, "error")
            self.error_output.config(state=tk.DISABLED)
        except: pass


    def set_theme(self):
        """Sets the application theme based on self.current_theme variable."""
        theme_name = self.current_theme.get()
        if theme_name in self.themes:
            self.colors = self.themes[theme_name]
            self.apply_theme()
            # Force redraw of treeview items to apply new row colors/tag colors
            self.run_lexer() # Re-run lexer to redraw treeview with new theme tags
        else:
            print(f"Warning: Theme '{theme_name}' not found.")

    # --- Event Handlers ---
    def on_focus_in(self, event):
        widget = event.widget; frame = None
        if widget == self.code_input: frame = self.code_input_frame
        elif widget == self.error_output: frame = self.error_output_frame
        elif widget == self.token_tree: frame = self.tree_container_frame
        if frame: frame.config(highlightbackground=self.colors["ACCENT_BLUE"], highlightthickness=2)

    def on_focus_out(self, event):
        widget = event.widget; frame = None
        if widget == self.code_input: frame = self.code_input_frame
        elif widget == self.error_output: frame = self.error_output_frame
        elif widget == self.token_tree: frame = self.tree_container_frame
        if frame: frame.config(highlightbackground=self.colors["BORDER_COLOR"], highlightthickness=1)

    def update_status_bar(self, event=None):
        try:
            cursor_pos = self.code_input.index(tk.INSERT)
            line, col = map(int, cursor_pos.split('.'))
            self.status_label.config(text=f"Line: {line}, Col: {col + 1}")
        except Exception: self.status_label.config(text="")

    def show_about(self):
         messagebox.showinfo(
            "About Chungus Lexical Analyzer",
            "Chungus Language Lexical Analyzer\n\n"
            "Version: 1.0\n"
            "Created by:\n"
            "- Goyena, Shawn Kieffer E.\n- Cantal, Henkepeck T.\n- Capiral, Luis Gabriel A.\n"
            "- Frias, Railey Miguel B.\n- King, Mariano Luiz B.\n- Manguni, John Gabriel H.\n\n"
            "Course Project - CISTM, PLM"
        )

    # --- File Operations ---
    def open_file(self):
        filepath = filedialog.askopenfilename(title="Open Chungus File", filetypes=[("Chungus Files", "*.chg *.chungus"), ("Text Files", "*.txt"), ("All Files", "*.*")])
        if not filepath: return
        try:
            with open(filepath, "r", encoding="utf-8") as f: content = f.read()
            self.code_input.delete("1.0", tk.END); self.code_input.insert("1.0", content)
            self.run_lexer()
        except Exception as e: messagebox.showerror("Error Opening File", f"Could not read file:\n{e}")

    def save_file(self):
        filepath = filedialog.asksaveasfilename(title="Save Chungus Code As...", defaultextension=".chg", filetypes=[("Chungus Files", "*.chg *.chungus"), ("Text Files", "*.txt"), ("All Files", "*.*")])
        if not filepath: return
        try:
            content = self.code_input.get("1.0", tk.END);
            if content.endswith('\n'): content = content[:-1] # Remove trailing newline
            with open(filepath, "w", encoding="utf-8") as f: f.write(content)
        except Exception as e: messagebox.showerror("Error Saving File", f"Could not save file:\n{e}")

    # --- Lexer Execution ---
    def run_lexer(self):
        """ Callback function for the 'Analyze' button. """
        self.error_output.config(state=tk.NORMAL)
        self.error_output.delete("1.0", tk.END)
        for item in self.token_tree.get_children(): self.token_tree.delete(item)

        source_code = self.code_input.get("1.0", tk.END)
        lexer = Lexer(source_code)
        tokens, errors = lexer.tokenize()

        # Re-apply theme colors to tags before inserting
        c = self.colors
        self.token_tree.tag_configure('keyword', foreground=c["ACCENT_PURPLE"], font=self.token_font_bold)
        self.token_tree.tag_configure('literal', foreground=c["ACCENT_GREEN"])
        self.token_tree.tag_configure('identifier', foreground=c["FG_COLOR"])
        self.token_tree.tag_configure('operator', foreground=c["ACCENT_ORANGE"])
        self.token_tree.tag_configure('delimiter', foreground=c["SECONDARY_TEXT"])
        self.token_tree.tag_configure('comment', foreground=c["SECONDARY_TEXT"], font=(self.token_font.actual()['family'], self.token_font.actual()['size'], 'italic'))
        self.token_tree.tag_configure('error', foreground=c["ACCENT_RED"])
        self.token_tree.tag_configure('linecol', foreground=c["SECONDARY_TEXT"])
        self.token_tree.tag_configure('oddrow', background=c["TEXT_AREA_BG"])
        self.token_tree.tag_configure('evenrow', background=c["TREE_EVEN_ROW"])

        for i, token in enumerate(tokens):
            tag = 'token'; token_type_name = token.type.name
            if token_type_name.startswith('KEYWORD'): tag = 'keyword'
            elif token_type_name.endswith('_LIT'): tag = 'literal'
            elif token_type_name == 'IDENTIFIER': tag = 'identifier'
            elif token_type_name.startswith('OP_'): tag = 'operator'
            elif token_type_name.startswith('DELIM_'): tag = 'delimiter'
            elif token_type_name.startswith('COMMENT_'): tag = 'comment'
            elif token_type_name == 'EOF': tag = 'error'
            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.token_tree.insert("", tk.END, values=(token.line, token.col, token.lexeme, token_type_name), tags=(tag, row_tag))


        self.error_output.tag_configure("error", foreground=self.colors["ACCENT_RED"])
        self.error_output.tag_configure("success", foreground=self.colors["ACCENT_GREEN"])
        if errors: self.error_output.insert(tk.END, "\n".join(errors), "error")
        else: self.error_output.insert(tk.END, ">>> Lexical analysis complete. No errors found.", "success")
        self.error_output.config(state=tk.DISABLED)

    def get_sample_code(self):
        """ Returns some sample Chungus code to pre-fill the text box. """
        # ... (Sample code remains the same) ...
        return """# Sample Chungus Code
###
  Multi-line comments are supported.
  Indentation matters! (2, 4, or 6 spaces)
###

fn greet(name = 'World')
  show 'Hello, $(name)!'

fn calculate_sum(a, b)
  # This function adds two numbers
  result = a + b
  ret result

# --- Main Program ---
greet('Chungus User')
greet() # Uses default value

num1 = 15.5
num2 = int('10') # Type casting example

total = calculate_sum(num1, num2)
show 'Sum of $(num1) and $(num2) is: $(total)'

# --- Loop Example ---
show '\\nLooping from 0 to 4:'
for i in range(5)
  show 'Iteration: $(i)'
  if i == 3
    show 'Skipping 3!'
    skip # Continue keyword

# --- Error Handling Example ---
try
  show '\\nAttempting division by zero...'
  invalid_result = 100 / 0
fail
  show 'Error: Division by zero caught!'
always
  show 'Cleanup: Error handling finished.'

# --- Error Examples ---
# invalid syntax here ?
# unterminated_string = 'hello
"""

# =============================================================================
# 4. RUN THE APPLICATION
# =============================================================================
if __name__ == "__main__":
    app_root = tk.Tk()
    try: from ctypes import windll; windll.shcore.SetProcessDpiAwareness(1)
    except ImportError: pass
    gui = ChungusLexerGUI(app_root)
    app_root.mainloop()