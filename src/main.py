import tkinter as tk
import subprocess
import tempfile
from pathlib import Path
from src.gui import ChungusLexerGUI
from src.lexer.dfa_lexer import Lexer
from src.syntax.rd_parser import RDParser
from src.semantic.semantic_analyzer import SemanticAnalyzer
from src.codegen import analyze_codegen


def lexer_only_adapter(source: str):
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
    Adapter that runs full compilation pipeline and executes the generated code.
    
    Returns:
        tokens: List of Token objects (for display)
        errors: List of strings containing execution output or errors
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

    # Run code generator
    codegen_result = analyze_codegen(
        semantic_result.tree, 
        source, 
        symbol_table=semantic_result.symbol_table,
        debug=False
    )

    if not codegen_result.success:
        errors.append("Code Generation Error/s:")
        errors.extend(codegen_result.errors)
        return tokens, errors

    # Compile and execute the generated C code
    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as c_file:
            c_file.write(codegen_result.code)
            c_path = Path(c_file.name)
        
        exe_path = c_path.with_suffix('')
        runtime_c = Path(__file__).parent / "codegen" / "chungus_runtime.c"
        runtime_h_dir = Path(__file__).parent / "codegen"
        
        # Compile
        compile_cmd = [
            "gcc", "-Wall", "-Wextra",
            f"-I{runtime_h_dir}",
            "-o", str(exe_path),
            str(c_path),
            str(runtime_c),
            "-lm"
        ]
        
        result = subprocess.run(compile_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            errors.append("=== COMPILATION FAILED ===")
            errors.append(result.stderr)
            # Clean up
            c_path.unlink(missing_ok=True)
            return tokens, errors
        
        # Execute
        result = subprocess.run([str(exe_path)], capture_output=True, text=True, timeout=5)
        
        # Clean up
        c_path.unlink(missing_ok=True)
        exe_path.unlink(missing_ok=True)

        if result.returncode != 0:
            errors.append("=== RUNTIME ERROR ===")
            errors.append(result.stderr)
            return tokens, errors
        
        # Success - return execution output
        errors.append("=== PROGRAM OUTPUT ===")
        if result.stdout:
            errors.append(result.stdout.rstrip())
        else:
            errors.append("(no output)")

    except subprocess.TimeoutExpired:
        errors.append("=== EXECUTION TIMEOUT ===")
        errors.append("Program exceeded 5 second time limit")
        # Clean up
        c_path.unlink(missing_ok=True)
        exe_path.unlink(missing_ok=True)
    except Exception as e:
        errors.append("=== EXECUTION ERROR ===")
        errors.append(str(e))

    return tokens, errors


if __name__ == "__main__":
    root = tk.Tk()
    app = ChungusLexerGUI(
        root, 
        lexer_callback=lexer_only_adapter, 
        syntax_callback=syntax_adapter, 
        semantic_callback=semantic_adapter,
        codegen_callback=codegen_adapter
    )
    root.mainloop()