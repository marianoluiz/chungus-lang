import os
import sys
import csv
import pytest

# Add project root to path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.lexer.dfa_lexer import Lexer
from src.syntax.rd_parser import RDParser
from src.semantic.semantic_analyzer import SemanticAnalyzer


def _run_semantic(src: str) -> str:
    """
    Run the full pipeline (Lexer → Parser → SemanticAnalyzer) on source code.
    Returns a joined string of all semantic error messages, or "" if no errors.
    Stops early if lexer or parser errors are found (semantic check skipped).
    """
    # Step 1: Lex
    lexer = Lexer(src, debug=False)
    lexer.start()

    if lexer.log.strip():
        # Lexical errors prevent semantic check
        return f"[LEXER ERROR] {lexer.log.strip()}"

    # Step 2: Parse
    parser = RDParser(lexer.token_stream, src, debug=False)
    parse_result = parser.parse()

    if parse_result.errors:
        return f"[PARSER ERROR] {'; '.join(parse_result.errors)}"

    # Step 3: Analyze
    analyzer = SemanticAnalyzer(parse_result.tree, src, debug=False)
    result = analyzer.analyze()

    return "\n".join(result.errors).strip()


def _rows():
    path = "test/semantic/test_semantic_data.csv"
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header

        for rownum, row in enumerate(reader, start=2):  # header is row 1
            src = row[0]
            expected = row[1].strip()

            # Normalize CRLFs (spreadsheets often insert them)
            src = src.replace("\r\n", "\n").replace("\r", "\n")
            expected = expected.replace("\r\n", "\n").replace("\r", "\n")

            # Normalize fullwidth semicolons to ASCII
            src = src.replace("；", ";")

            if not src.strip():
                continue

            yield pytest.param(rownum, src, expected, id=f"row{rownum}")


@pytest.mark.parametrize("rownum,src,expected", _rows())
def test_semantic(rownum, src, expected):
    """
    For each row in test_semantic_data.csv:
      - If expected == "NO SEMANTIC ERROR/S", assert no errors are reported.
      - Otherwise, assert every expected error substring appears in the actual output.
    """
    log = _run_semantic(src)

    print(f"=== CSV row: {rownum} ===")
    print("=== Source Code ===")
    print(src)
    print("=== Expected ===")
    print(expected)
    print("=== Actual ===")
    print(log)

    if expected == "NO SEMANTIC ERROR/S":
        assert log == "", f"Expected no semantic errors, but got:\n{log}"
    else:
        # Presence checks: every non-empty expected line must appear in output
        for line in expected.splitlines():
            if line.strip():
                assert line.strip() in log, (
                    f"Expected error substring not found:\n"
                    f"  EXPECTED: {line.strip()!r}\n"
                    f"  ACTUAL:   {log!r}"
                )

        # Exact count checks for known semantic error types
        def _count(label: str, expected_text: str, log_text: str):
            exp = sum(1 for l in expected_text.splitlines() if label in l)
            act = log_text.count(label)
            assert act == exp, f"Expected {exp} '{label}' error(s), got {act}"

        _count("Variable", expected, log)
        _count("Function", expected, log)
        _count("Type Mismatch", expected, log)
        _count("Array", expected, log)