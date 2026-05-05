import datetime
import subprocess
from pathlib import Path
import sys

from PySide6.QtWidgets import QApplication

from src.gui import ChungusLexerGUI
from src.lexer.dfa_lexer import Lexer
from src.syntax.rd_parser import RDParser
# from src.constants.syntax_test import Parser
from src.semantic.semantic_analyzer import SemanticAnalyzer
from src.codegen import analyze_codegen
import platform 

def lexer_adapter(source: str):
    """
    Adapter that runs only the Lexer and converts its output into a list of dicts:
      { "type": <token_type>, "lexeme": <lexeme>, "line": <1-based>, "col": <1-based> }
    and a list of error strings.
    """
    lexer = Lexer(source, debug=False)
    lexer.start()

    tokens = lexer.token_stream
    errors = []

    if lexer.log:
        errors.append("Lexical Error/s:")
        errors.extend(lexer.log.splitlines())

    return tokens, errors


def syntax_adapter(source: str):
    """
    Adapter that runs both the Lexer and Parser and converts its output into a list of dicts:
      { "type": <token_type>, "lexeme": <lexeme>, "line": <1-based>, "col": <1-based> }
    and a list of error strings.
    """
    lexer = Lexer(source, debug=False)
    lexer.start()

    tokens = lexer.token_stream
    errors = []

    if lexer.log:
        errors.append("Lexical Error/s:")
        errors.extend(lexer.log.splitlines())
        return tokens, errors

    # Recursive Descent Parser
    parser = RDParser(tokens, source, debug=False)
    parse_result = parser.parse()

    # Syntax Test
    # parser = Parser()
    # parse_result = parser.parse(source)

    if parse_result.errors:
        errors.append("Syntax Error:")
        errors.extend(parse_result.errors)
  
    return tokens, errors


def semantic_adapter(source: str):
    """
    Adapter that runs Lexer, Parser, and Semantic Analyzer.
    
    Returns:
        tokens: List of Token objects
        errors: List of error strings
    """
    lexer = Lexer(source, debug=False)
    lexer.start()

    tokens = lexer.token_stream
    errors = []

    if lexer.log:
        errors.append("Lexical Error/s:")
        errors.extend(lexer.log.splitlines())
        return tokens, errors

    # Run syntax parser
    parser = RDParser(tokens, source, debug=False)
    parse_result = parser.parse()

    if parse_result.errors:
        errors.append("Syntax Error:")
        errors.extend(parse_result.errors)
        return tokens, errors

    # Run semantic analyzer
    semantic = SemanticAnalyzer(parse_result.tree, source, debug=False)
    semantic_result = semantic.analyze()

    if semantic_result.errors:
        errors.append("Semantic Error/s:")
        errors.extend(semantic_result.errors)

    return tokens, errors


def codegen_adapter(source: str):
    """
    Runs the full compilation pipeline.
 
    Returns:
        (tokens, errors, proc)
        - If compilation fails: proc is None, errors contains the messages.
        - If compilation succeeds: proc is a live subprocess.Popen with
          stdin/stdout/stderr pipes open. The GUI streams I/O directly.
    """
    #  Lexer 
    lexer = Lexer(source, debug=False)
    lexer.start()
    tokens = lexer.token_stream
    errors = []
 
    if lexer.log:
        errors.append("Lexical Error/s:")
        errors.extend(lexer.log.splitlines())
        return tokens, errors, None
 
    #  Parser 
    parser = RDParser(tokens, source, debug=False)
    parse_result = parser.parse()
    if parse_result.errors:
        errors.append("Syntax Error:")
        errors.extend(parse_result.errors)
        return tokens, errors, None
 
    #  Semantic analyzer 
    semantic = SemanticAnalyzer(parse_result.tree, source, debug=False)
    semantic_result = semantic.analyze()
    if semantic_result.errors:
        errors.append("Semantic Error/s:")
        errors.extend(semantic_result.errors)
        return tokens, errors, None
 
    #  Code generator 
    codegen_result = analyze_codegen(
        semantic_result.tree,
        source,
        symbol_table=semantic_result.symbol_table,
        debug=False,
    )
    if not codegen_result.success:
        errors.append("Code Generation Error/s:")
        errors.extend(codegen_result.errors)
        return tokens, errors, None

    #  Write generated C source 
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    c_path = output_dir / f"gui_output_{timestamp}.c"
    c_path.write_text(codegen_result.code)
 
    #  Detect OS and choose compiler 
    system = platform.system()
    
    if system == "Windows":
        # On Windows, look for gcc (MinGW) or clang
        compiler = "gcc"  # or "clang" if you have it installed
        exe_path = c_path.with_suffix('.exe')  # Add .exe extension
    else:
        # macOS/Linux
        compiler = "gcc"
        exe_path = c_path.with_suffix('')  # No extension on Unix

    runtime_c   = Path(__file__).parent / "runtime" / "chungus_runtime.c"
    runtime_h_dir = Path(__file__).parent / "runtime"

    # ── Compile with gcc ─────────────────────────────────────────────────────
    compile_cmd = [
        compiler, "-Wall", "-Wextra",
        f"-I{str(runtime_h_dir)}",
        "-o", str(exe_path),
        str(c_path),
        str(runtime_c),
        "-lm"
    ]

    # On Windows, add -lm might not be needed (math is in libc)
    if system == "Windows":
        # Remove -lm on Windows (or keep if MinGW handles it)
        compile_cmd = [c for c in compile_cmd if c != "-lm"]

    compile_result = subprocess.run(
        compile_cmd,
        capture_output=True,
        text=True,
    )
    if compile_result.returncode != 0:
        errors.append("Compilation Error:")
        errors.append(compile_result.stderr)
        return tokens, errors, None
 
    # ── Launch executable — keep stdin/stdout/stderr open for live I/O ───────
    proc = subprocess.Popen(
        [str(exe_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,         # data is handled as raw bytes not py string
        bufsize=0,          # unbuffered — important for interactive input
    )
 
    # Return the live process to the GUI; it will stream I/O itself. Error is empty since we didn't encounter any
    return tokens, [], proc

 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChungusLexerGUI(
        lexer_callback=lexer_adapter,
        syntax_callback=syntax_adapter,
        semantic_callback=semantic_adapter,
        codegen_callback=codegen_adapter,
    )
    window.show()
    sys.exit(app.exec())
