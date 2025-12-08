import os
import sys
# Add src as root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from pathlib import Path
import pytest

from src.lexer.dfa_lexer import Lexer  # [`src.lexer.dfa_lexer.Lexer`](src/lexer/dfa_lexer.py)

SAMPLES_DIR = Path(__file__).parent / "statements_samples"

# Ordered token-type sequences for stricter testing (whitespace/newlines ignored)
EXPECTED_SEQUENCES = {
    "assignment.chg": ["id", "=", "int_literal", "id", "=", "int_literal", "id", "=", "id", "+", "id", "show", "str_literal"],
    "array_add.chg": [
        "id", "=", "[", "int_literal", ",", "int_literal", ",", "int_literal", "]",
        "array_add", "(", "id", ",", "int_literal", ")",
        "show", "str_literal"
    ],
    "array_index.chg": ["id", "=", "[", "int_literal", ",", "int_literal", ",", "int_literal", ",", "int_literal", "]", 
                        "show", "str_literal"],
    "array_remove.chg": ["id", "=", "[", "str_literal", ",", "str_literal", ",", "str_literal", ",", "str_literal", "]", 
                         "array_remove", "(", "id", ",", "int_literal", ")", 
                         "show", "str_literal"],
    "close_statement.chg": ["if", "true", "show", "str_literal", "close"],
    "conditional.chg": ["id", "=", "int_literal", "if", "id", ">=", "int_literal", "show", "str_literal", "elif", "id", ">=", "int_literal", "show", "str_literal", "else", "show", "str_literal", "close"],
    "error_handling.chg": ["try", "id", "=", "int_literal", "/", "int_literal", "fail", "show", "str_literal", "always", "show", "str_literal", 'close'],
    "for_loop.chg": ["for", "id", "in", "range", "(", "int_literal", ",", "int_literal", ")", "show", "str_literal", "close"],
    "function.chg": ['fn', 'id', '(', 'id', ')', 'id', '=', 'id', '*', 'id', 'ret', 'id', 'close', 'id', '=', 'id', '(', 'int_literal', ')', 'show', 'str_literal'],
    "input.chg": ['show', 'str_literal', 'id', '=', 'read', 'show', 'str_literal'],
    "loop_control.chg": ['for', 'id', 'in', 'range', '(', 'int_literal', ',', 'int_literal', ')', 'if', 'id', '==', 'int_literal', 'skip', 'close', 'if', 'id', '==', 'int_literal', 'stop', 'close', 'show', 'str_literal', 'close'],
    "output.chg": ["id", "=", "str_literal", "show", "str_literal"],
    "system.chg": ['show', 'str_literal', 'clr', 'show', 'str_literal', 'exit'],
    "todo.chg": ["fn", "id", "(", ")", "todo", "close"],
    "type_cast.chg": ["show", "str_literal", "id", "=", "read", "id", "=", "int", "(", "id", ")", "id", "=", "float", "(", "id", ")", "show", 'str_literal', "show", "str_literal"],
    "unary.chg": ["comment", "id", "=", "int_literal", "id", "++", "id", "--", "show", "str_literal"],
    "while_loop.chg": ["id", "=", "int_literal", "while", "id", ">", "int_literal", "show", "str_literal", "id", "=", "id", "-", "int_literal", "close"],
}

def _lex(source: str):
    lx = Lexer(source, debug=False)
    lx.start()
    return lx

def _types_in_order(lx):
    # Preserve order, drop whitespace/newlines
    return [ttype for ((lexeme, ttype), _) in lx.token_stream if ttype not in ("whitespace", "newline")]

@pytest.mark.parametrize("sample_name", sorted(EXPECTED_SEQUENCES.keys()))
def test_statement_token_sequence(sample_name):
    source = (SAMPLES_DIR / sample_name).read_text(encoding="utf-8")
    lx = _lex(source)
    seq = _types_in_order(lx)
    expected = EXPECTED_SEQUENCES[sample_name]
    assert seq == expected, f"{sample_name}\nExpected: {expected}\nGot:      {seq}"