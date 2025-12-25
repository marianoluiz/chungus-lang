from src.lexer.dfa_lexer import Lexer
from src.syntax.rd_parser import RDParser
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

    # Tokens: [ {type, token_type, line_index, col_index}, ... ]
    parser = RDParser(tokens, source_code, debug=True)
    parse_result = parser.parse()

    if parse_result.errors:
        errors.append("Syntax Error/s:")
        errors.extend(parse_result.errors)

    # Display AST tree
    if parse_result.tree is not None:
        print_ast(parse_result.tree)
    else:
        print("No AST generated.")

    return tokens, errors

if __name__ == '__main__':
    tokens, errors = main()
    
    # print("\n\nTOKENS:")
    # for t in tokens:
    #     print(
    #         f"{t['type']:<12} {t['lexeme']!r:<10} "
    #         f"(line {t['line']}, col {t['col']})"
    #     )
    
    if errors:
        print("\nERRORS:")
        print("\n".join(errors))