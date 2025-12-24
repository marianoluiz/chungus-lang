import os
import sys
import csv
import pytest

# Add src as root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.lexer.dfa_lexer import Lexer
from src.syntax.rd_parser import RDParser


def ast_to_string(node, prefix: str = "", is_last: bool = True) -> str:
    """Return the AST as a readable tree string instead of printing."""
    lines = []

    # Choose branch symbol
    connector = "└─ " if is_last else "├─ "

    # Display node
    if node.value is not None:
        lines.append(prefix + connector + f"{node.kind}: {node.value}")
    else:
        lines.append(prefix + connector + f"{node.kind}")

    # Prepare prefix for children
    new_prefix = prefix + ("   " if is_last else "│  ")

    # Process children recursively
    count = len(node.children)
    for i, child in enumerate(node.children):
        is_last_child = (i == count - 1)
        lines.append(ast_to_string(child, new_prefix, is_last_child))

    return "\n".join(lines)


def _run_lexer(src: str) -> str:
    lx = Lexer(src, debug=False)
    lx.start()
    return lx

def _rows():
    path = "test/syntax/test_syntax_data.csv"
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header

        for row in reader:
            # row:  ['abc123 = 10', 'NO LEXICAL ERROR/S'] ...
            src = row[1]                # The source code, col 1
            expected_ast = row[2] 
            expected_error = row[3].strip()   # Expected Error, col 2

            # Normalize CRLFs and CR to LF if any, since spreadsheets do use CRLFs
            expected_ast = expected_ast.replace("\r\n", "\n").replace("\r", "\n")
            expected_error = expected_error.replace("\r\n", "\n").replace("\r", "\n")

            yield src, expected_ast, expected_error         # return one at a time

@pytest.mark.parametrize("src,expected_ast,expected_error", _rows())
def test_syntax(src, expected_ast, expected_error):
    """ the src, expected will be extracted from the _rows() at this parametrizing test """
    # pytest.mark.parametrize is LIKE a loop that runs testcase per testcase
    # _rows() returns a generator, which pytest automatically does the next()
    
    lx = _run_lexer(src)
    
    assert lx.log.strip() == "", f"Lexer produced errors:\n{lx.log}"
       
    # Build token dicts expected by RDParser
    tokens = []
    for (lex_pair, pos) in lx.token_stream:
        lexeme, ttype = lex_pair
        line_idx, col_idx = pos
        tokens.append({
            "type": ttype,
            "lexeme": lexeme,
            "line": line_idx + 1,
            "col": col_idx + 1
    })

    # Run parser
    parser = RDParser(tokens, src, debug=False)
    parse_result = parser.parse()

    # convert string to Python object safely
    actual_ast_str = ast_to_string(parse_result.tree)
    expected_errors_list = [] if expected_error.lower() == "" else [expected_error]

    # Debug: show source code
    print("=== Source Code ===")
    print(src)
    print("=== Expected AST ===")
    print(expected_ast)
    print("=== Actual AST ===")
    print(actual_ast_str)

    # must match
    assert expected_ast == actual_ast_str, \
        f"\nExpected AST:\n{expected_ast}\n\nActual AST:\n{actual_ast_str}"
    assert expected_errors_list == parse_result.errors, \
        f"Expected errors: {expected_errors_list}\nActual errors: {parse_result.errors}"