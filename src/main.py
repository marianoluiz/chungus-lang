import tkinter as tk
import subprocess
from pathlib import Path
import os
import time
import selectors
from src.gui import ChungusLexerGUI
from src.lexer.dfa_lexer import Lexer
from src.syntax.rd_parser import RDParser
# from src.constants.syntax_test import Parser
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


def codegen_adapter(source: str, stdin_data=None):
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

    # Save generated C code to output/ directory
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Use timestamp for GUI-generated files to avoid conflicts
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    c_path = output_dir / f"gui_output_{timestamp}.c"
    c_path.write_text(codegen_result.code)
    
    # Compile and execute the generated C code
    try:
        exe_path = c_path.with_suffix('')
        runtime_c = Path(__file__).parent / "runtime" / "chungus_runtime.c"
        runtime_h_dir = Path(__file__).parent / "runtime"

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
            errors.append("Compilation Error:")
            errors.append(result.stderr)
            return tokens, errors
        
        # Execute (stdin_data is used by GUI when source contains `read`)
        # Use streamed capture with guards so infinite loops / very chatty
        # programs do not freeze the GUI thread.
        TIMEOUT_SECONDS = 5.0
        MAX_OUTPUT_CHARS = 50000

        proc = subprocess.Popen(
            [str(exe_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        # Feed stdin (if any) and close to avoid child waiting forever.
        if proc.stdin:
            if stdin_data is not None:
                proc.stdin.write(stdin_data)
            proc.stdin.close()

        selector = selectors.DefaultSelector()
        out_parts = []
        err_parts = []
        captured_chars = 0
        stop_reason = None  # "timeout" | "output-limit" | None

        def _register_stream(stream):
            if stream is None:
                return
            try:
                os.set_blocking(stream.fileno(), False)
            except Exception:
                pass
            selector.register(stream, selectors.EVENT_READ)

        _register_stream(proc.stdout)
        _register_stream(proc.stderr)

        start = time.monotonic()

        while True:
            # Timeout guard
            if stop_reason is None and (time.monotonic() - start) > TIMEOUT_SECONDS:
                stop_reason = "timeout"
                try:
                    proc.kill()
                except Exception:
                    pass

            # Read available output chunks
            events = selector.select(timeout=0.05)
            for key, _ in events:
                stream = key.fileobj
                try:
                    chunk = stream.read()
                except Exception:
                    chunk = ""

                # EOF: unregister stream
                if chunk == "":
                    try:
                        selector.unregister(stream)
                    except Exception:
                        pass
                    continue

                # Enforce output cap
                if captured_chars < MAX_OUTPUT_CHARS:
                    remaining = MAX_OUTPUT_CHARS - captured_chars
                    kept = chunk[:remaining]
                    captured_chars += len(kept)

                    if stream is proc.stdout:
                        out_parts.append(kept)
                    else:
                        err_parts.append(kept)

                    if len(chunk) > remaining and stop_reason is None:
                        stop_reason = "output-limit"
                        try:
                            proc.kill()
                        except Exception:
                            pass
                elif stop_reason is None:
                    stop_reason = "output-limit"
                    try:
                        proc.kill()
                    except Exception:
                        pass

            # Exit loop when process ended and streams drained
            if proc.poll() is not None and not selector.get_map():
                break

        # Build final output text
        stdout_text = "".join(out_parts)
        stderr_text = "".join(err_parts)

        # Report partial output first, then guard reason/runtime status
        if stdout_text:
            errors.append(stdout_text.rstrip())
        if stderr_text:
            errors.append(stderr_text.rstrip())

        if stop_reason == "timeout":
            errors.append("Execution Timeout: Program exceeded 5 second time limit")
            return tokens, errors

        if stop_reason == "output-limit":
            errors.append(f"Execution Stopped: Output exceeded {MAX_OUTPUT_CHARS} characters")
            return tokens, errors

        if proc.returncode != 0:
            if not stderr_text:
                errors.append(f"Runtime Error: Process exited with code {proc.returncode}")
            return tokens, errors
        
        # Clean up executable after running (keep C file)
        # exe_path.unlink(missing_ok=True)

    except Exception as e:
        errors.append("Execution Error:")
        errors.append(str(e))
        # Clean up executable
        # exe_path.unlink(missing_ok=True)

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