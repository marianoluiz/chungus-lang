import os
import sys
import csv
import pytest
import re

# Add src as root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.lexer.dfa_lexer import Lexer
from src.syntax.rd_parser import RDParser


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
            # row:  ['abc123 = 10', 'NO SYNTAX ERROR'] ...
            src = row[0]                # The source code, col 1
            expected_error = row[1].strip()   # Expected Error, col 2

            # Normalize CRLFs and CR to LF if any, since spreadsheets do use CRLFs
            expected_error = expected_error.replace("\r\n", "\n").replace("\r", "\n")

            yield src, expected_error         # return one at a time

@pytest.mark.parametrize("src,expected_error", _rows())
def test_syntax(src, expected_error):
    """ the src, expected will be extracted from the _rows() at this parametrizing test """
    # pytest.mark.parametrize is LIKE a loop that runs testcase per testcase
    # _rows() returns a generator, which pytest automatically does the next()
    
    lx = _run_lexer(src)
    
    assert lx.log.strip() == "", f"Lexer produced errors:\n{lx.log}"

    # Build token dicts expected by RDParser
    tokens = lx.token_stream

    # Run parser
    parser = RDParser(tokens, src, debug=False)
    parse_result = parser.parse()
    
    actual_error = parse_result.errors[0] if parse_result.errors else '' # list to string

    if expected_error == "NO SYNTAX ERROR":
        assert not actual_error, f"Expected no syntax errors, got: {actual_error}"
    else:

        # looks for the pattern "line <number> col <number>" anywhere in the string.
        line_col_match = re.search(r"line (\d+) col (\d+)", expected_error)

        if not line_col_match:
            raise ValueError(f"Expected error string missing line/col info:\n{expected_error}")

        ref_line = int(line_col_match.group(1))
        ref_col = int(line_col_match.group(2))
        
        # Splits the string at "Expected any:" and takes the last part, which contains all tokens:
        # Splits the last string at every comma, creating a list
        ref_tokens = [tok.strip() for tok in expected_error.split("Expected any:")[-1].split(",")]

        # looks for the pattern "line <number> col <number>" anywhere in the string.
        line_col_match = re.search(r"line (\d+) col (\d+)", actual_error)
        actual_line = int(line_col_match.group(1))
        actual_col = int(line_col_match.group(2))

        actual_tokens = [tok.strip() for tok in actual_error.split("Expected any:")[-1].split(",")]

        # Debug prints
        print("=== Source Code ===")
        print(src)
        print("=== Expected Syntax Error ===")
        print(f'line {ref_line} col {ref_col}')
        print(ref_tokens)
        print("=== Actual Syntax Error ===")
        print(actual_tokens)
        print(f'line {actual_line} col {actual_col}')

        assert ref_line == actual_line, f"Line mismatch: {ref_line} != {actual_line}"
        assert ref_col == actual_col, f"Column mismatch: {ref_col} != {actual_col}"
        assert ref_tokens == actual_tokens, f"Tokens mismatch: {ref_tokens} != {actual_tokens}"
