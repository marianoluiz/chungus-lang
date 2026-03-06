import sys
from pathlib import Path
from typing import List
from src.lexer.dfa_lexer import Lexer
from src.syntax.rd_parser import RDParser
from src.constants.token import Token

# ------------------- Pretty Print -------------------
def print_ast(node, prefix: str = "", is_last: bool = True, show_pos=False):
    # choose branch symbol
    connector = "└─ " if is_last else "├─ "

    # build label
    label = node.kind

    if node.value is not None:
        label += f": {node.value}"
    
    if show_pos and node.line is not None and node.col is not None:
        label += f"  @({node.line},{node.col})"

    print(prefix + connector + label)

    # prepare prefix for children
    # If this node is the last child → future siblings above are done → just spaces:
    # this prefix runs for all recursive stacks
    new_prefix = prefix + ("   " if is_last else "│  ")

    # display children
    count = len(node.children)
    for i, child in enumerate(node.children):
        is_last_child = (i == count - 1)
        print_ast(child, new_prefix, is_last_child, show_pos=show_pos)

def main():
    # Determine input file
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    else:
        input_file = Path(__file__).parent / "input_syntax.chg"
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    # Read source code
    source_code = input_file.read_text(encoding='utf-8')
    
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
        print_ast(parse_result.tree, show_pos=True)
    else:
        print("No AST generated.")

    if errors:
        print("\nERRORS:")
        print("\n".join(errors))