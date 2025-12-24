import tkinter as tk
from src.gui import ChungusLexerGUI
from src.lexer.dfa_lexer import Lexer
from src.syntax.syntax_test import Parser
# from src.syntax.rd_parser import RDParser

def lexer_adapter(source: str):
    """
    Adapter that runs the Lexer and converts its output into a list of dicts:
      { "type": <token_type>, "lexeme": <lexeme>, "line": <1-based>, "col": <1-based> }
    and a list of error strings.
    """

    tokens = []
    errors = []

    lexer = Lexer(source, debug=False)
    lexer.start()

    # Lexer.token_stream: [ ((type, lexeme), (line, col)), ... ]
    for (lex_pair, pos) in lexer.token_stream:

        lexeme, ttype = lex_pair
        line_idx, col_idx = pos

        tokens.append({
            "type": ttype,
            "lexeme": lexeme,
            "line": line_idx + 1,
            "col": col_idx + 1
        })


    
    if lexer.log:
        errors.append("Lexical Error/s:")
        errors.extend(lexer.log.splitlines())
        # End if have lexical error
        return tokens, errors

    # Run Lark syntax parser and surface parser errors (if any)
    # parser = Parser()
    # parse_result = parser.parse(source)

    # if parse_result.errors:
    #     # parser.parse returns SyntaxResult; append parser.log (human readable)
    #     errors.append("Syntax Error/s:")
    #     errors.append(parse_result.log or "\n".join(parse_result.errors))

    # parser = RDParser(tokens, source, debug=True)
    # parse_result = parser.parse()

    # if parse_result.errors:
    #     errors.append("Syntax Error/s:")
    #     errors.extend(parse_result.errors.splitlines())

    return tokens, errors

if __name__ == "__main__":
    root = tk.Tk()
    app = ChungusLexerGUI(root, lexer_callback=lexer_adapter)
    root.mainloop()