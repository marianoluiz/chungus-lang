from typing import List
from src.lexer.dfa_lexer import Lexer
from src.syntax.rd_parser import RDParser
from src.constants.token import Token
import os

# ------------------- Pretty Print -------------------
def print_ast(node, prefix: str = "", is_last: bool = True):
    # choose branch symbol
    connector = "└─ " if is_last else "├─ "

    # display node
    if node.value is not None:
        print(prefix + connector + f"{node.kind}: {node.value}")
    else:
        print(prefix + connector + f"{node.kind}")

    # prepare prefix for children
    # If this node is the last child → future siblings above are done → just spaces:
    # this prefix runs for all recursive stacks
    new_prefix = prefix + ("   " if is_last else "│  ")

    # display children
    count = len(node.children)
    for i, child in enumerate(node.children):
        is_last_child = (i == count - 1)
        print_ast(child, new_prefix, is_last_child)

def main():
    # This takes the input folder path
    test_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'syntax_input.chg'))
    
    try:
        with open(test_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Test file not found: {test_path}")
        return
    
    tokens = []
    errors = []

    lexer = Lexer(source_code, debug=False)
    lexer.start()

    # Lexer.token_stream: [ ((type, lexeme), (line, col)), ... ]
    tokens: List[Token] = lexer.token_stream
    
    # Tokens: [ {type, token_type, line_index, col_index}, ... ]
    parser = RDParser(tokens, source_code, debug=True)
    parse_result = parser.parse()

    if lexer.log:
        errors.append("Lexical Error/s:")
        errors.extend(lexer.log.splitlines())
        # End if have lexical error
        return tokens, errors, parse_result

    if parse_result.errors:
        errors.append("Syntax Error/s:")
        errors.extend(parse_result.errors)

    return tokens, errors, parse_result

if __name__ == '__main__':
    tokens, errors, parse_result = main()
    
    # print("\n\nTOKENS:")
    # for t in tokens:
    #     print(
    #         f"{t['type']:<12} {t['lexeme']!r:<10} "
    #         f"(line {t['line']}, col {t['col']})"
    #     )
    
    if parse_result.tree is not None:
        print_ast(parse_result.tree)
    else:
        print("No AST generated.")
        
    if errors:
        print("\nERRORS:")
        print("\n".join(errors))