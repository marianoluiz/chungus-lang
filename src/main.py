import os
import sys

import tkinter as tk
from src.gui import ChungusLexerGUI
from src.lexer.lexer import Lexer

def lexer_adapter(source: str):
    """
    Adapter that runs the Lexer and converts its output into a list of dicts:
      { "type": <token_type>, "lexeme": <lexeme>, "line": <1-based>, "col": <1-based> }
    and a list of error strings.
    """

    lexer = Lexer(source)
    lexer.start()
    tokens = []

    # Lexer.token_stream: [ ((lexeme, token_type), (line_index, col_index)), ... ]
    for (lex_pair, pos) in lexer.token_stream:

        lexeme, ttype = lex_pair
        line_idx, col_idx = pos

        tokens.append({
            "type": ttype,
            "lexeme": lexeme,
            "line": line_idx + 1,
            "col": col_idx + 1
        })

    errors = lexer.log.splitlines() if lexer.log else []
    return tokens, errors


if __name__ == "__main__":
    root = tk.Tk()
    app = ChungusLexerGUI(root, lexer_callback=lexer_adapter)
    root.mainloop()