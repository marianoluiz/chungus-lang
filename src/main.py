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



    lexer = Lexer(source, debug=False)
    lexer.start()
    
    tokens = lexer.token_stream
    errors = []

    if lexer.log:
        errors.append("Lexical Error/s:")
        errors.extend(lexer.log.splitlines())
        # End if have lexical error
        return tokens, errors

    parser = Parser()
    parse_result = parser.parse(source)

    if parse_result.errors:
        # parser.parse returns SyntaxResult; append parser.log (human readable)
        errors.append("Syntax Error/s:")
        errors.append(parse_result.log or "\n".join(parse_result.errors))

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