import ast
import os
import sys
import csv
import pytest

# Add src as root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.lexer.dfa_lexer import Lexer

def _run_lexer(src: str) -> str:
    lx = Lexer(src, debug=False)
    lx.start()
    return lx.token_stream

def _rows():
    path = "test/lexer/test_lexer_tokens_data.csv"
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header

        for row in reader:
            # row:  ['abc123 = 10', 'NO LEXICAL ERROR/S'] ...
            src = row[0]                # The source code, col 1
            expected = row[1].strip()   # Expected Tokens, col 2
            test_details = row[2]

            # Normalize CRLFs and CR to LF if any, since spreadsheets do use CRLFs
            expected = expected.replace("\r\n", "\n").replace("\r", "\n")
            yield src, expected, test_details   # return one at a time


def _get_types_in_order(lex_token_stream):
    """ Get all types from source code """
    return [
        tok.type 
        for tok in lex_token_stream
        if (tok.type not in ("whitespace", "newline"))
    ]

@pytest.mark.parametrize("src, expected, test_details", _rows())
def test_lexer_tokens(src, expected, test_details):
    # pytest.mark.parametrize is LIKE a loop that runs testcase per testcase
    # _rows() returns a generator, which pytest automatically does the next()

    lex_token_stream = _run_lexer(src)
    seq_ttypes = _get_types_in_order(lex_token_stream)

    # Convert expected string to a list,
    # ast.literal_eval safely interprets the string as a Python literal
    expected_list = ast.literal_eval(expected)

    assert seq_ttypes == expected_list, f"Details: {test_details}\nExpected: {expected_list}\n Got:    {seq_ttypes}"