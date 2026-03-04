from typing import List
from src.lexer.dfa_lexer import Lexer
from src.semantic.semantic_analyzer import SemanticAnalyzer
from src.syntax.rd_parser import RDParser
from src.constants.token import Token
import os

# ------------------- Pretty Print -------------------
def print_ast(node, symbol_table=None, prefix: str = "", is_last: bool = True):
    # choose branch symbol
    connector = "└─ " if is_last else "├─ "

    # display node with value, line, col, and inferred_type
    node_str = f"{node.kind}"
    if node.value is not None:
        node_str += f": {node.value}"
    if hasattr(node, 'line') and hasattr(node, 'col') and node.line is not None:
        node_str += f"  @({node.line},{node.col})"
    if hasattr(node, 'inferred_type') and node.inferred_type is not None:
        node_str += f"  [type: {node.inferred_type}]"
    
    # Show constant value if available (for ANY node type, not just id)
    if hasattr(node, 'constant_value') and node.constant_value is not None:
        const_val = node.constant_value
        # Format based on Python type
        if isinstance(const_val, bool):
            const_display = "true" if const_val else "false"
            node_str += f"  [const: {const_display}]"
        elif isinstance(const_val, str):
            node_str += f"  [const: '{const_val}']"
        elif isinstance(const_val, int):
            node_str += f"  [const: {const_val}]"
        elif isinstance(const_val, float):
            # Show as int if it's a whole number
            if const_val == int(const_val):
                node_str += f"  [const: {int(const_val)}]"
            else:
                node_str += f"  [const: {const_val}]"
    # Fallback: If it's an identifier, also check symbol table
    elif node.kind == "id" and node.value and symbol_table:
        symbol = symbol_table.lookup(node.value)
        if symbol and symbol.constant_value is not None:
            const_val = symbol.constant_value
            if isinstance(const_val, bool):
                const_display = "true" if const_val else "false"
                node_str += f"  [const: {const_display}]"
            elif isinstance(const_val, str):
                node_str += f"  [const: '{const_val}']"
            elif isinstance(const_val, (int, float)):
                if isinstance(const_val, float) and const_val == int(const_val):
                    node_str += f"  [const: {int(const_val)}]"
                else:
                    node_str += f"  [const: {const_val}]"
    
    print(prefix + connector + node_str)

    # prepare prefix for children
    # If this node is the last child → future siblings above are done → just spaces:
    # this prefix runs for all recursive stacks
    new_prefix = prefix + ("   " if is_last else "│  ")

    # display children
    count = len(node.children)
    for i, child in enumerate(node.children):
        is_last_child = (i == count - 1)
        print_ast(child, symbol_table, new_prefix, is_last_child)

def main():
    # This takes the input folder path
    test_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'semantic_input.chg'))
    
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
    syntax = RDParser(tokens, source_code, debug=True)
    syntax_result = syntax.parse()

    semantic = SemanticAnalyzer(syntax_result.tree, source_code, debug=True)
    semantic_result = semantic.analyze()

    if lexer.log:
        errors.append("Lexical Error/s:")
        errors.extend(lexer.log.splitlines())
        # End if have lexical error
        return tokens, errors, syntax_result, semantic_result

    if syntax_result.errors:
        errors.append("Syntax Error:")
        errors.extend(syntax_result.errors)
        # End if have syntax error
        return tokens, errors, syntax_result, semantic_result

    if semantic_result.errors:
        errors.append("Semantic Error/s:")
        errors.extend(semantic_result.errors)

        return tokens, errors, syntax_result, semantic_result


    return tokens, errors, syntax_result, semantic_result


if __name__ == '__main__':
    tokens, errors, syntax_result, semantic_result = main()
    
    # print("\n\nTOKENS:")
    # for t in tokens:
    #     print(
    #         f"{t['type']:<12} {t['lexeme']!r:<10} "
    #         f"(line {t['line']}, col {t['col']})"
    #     )
    
    if semantic_result.tree is not None:
        print("\n\nAST with Type Annotations:")
        print_ast(semantic_result.tree, semantic_result.symbol_table)
    else:
        print("No AST generated.")

    if errors:
        print("\nERRORS:")
        print("\n".join(errors))