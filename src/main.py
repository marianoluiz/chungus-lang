import tkinter as tk
from src.gui import ChungusLexerGUI
from src.lexer.dfa_lexer import Lexer
from src.syntax.rd_parser import RDParser
from src.semantic.semantic_analyzer import SemanticAnalyzer


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


if __name__ == "__main__":
    root = tk.Tk()
    app = ChungusLexerGUI(root, lexer_callback=lexer_only_adapter, syntax_callback=syntax_adapter, semantic_callback=semantic_adapter)
    root.mainloop()