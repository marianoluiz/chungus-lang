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
    return lx.log.strip()

def _rows():
    path = "test/lexer/test_lexer_errors_data.csv"
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header

        for row in reader:
            # row:  ['abc123 = 10', 'NO LEXICAL ERROR/S'] ...
            src = row[0]                # The source code, col 1
            expected = row[1].strip()   # Expected Error, col 2

            # Normalize CRLFs and CR to LF if any, since spreadsheets do use CRLFs
            expected = expected.replace("\r\n", "\n").replace("\r", "\n")

            yield src, expected         # return one at a time


@pytest.mark.parametrize("src,expected", _rows())
def test_lexer_logs(src, expected):
    """ the src, expected will be extracted from the _rows() at this parametrizing test """
    # pytest.mark.parametrize is LIKE a loop that runs testcase per testcase
    # _rows() returns a generator, which pytest automatically does the next()

    print("SRC INPUT:")
    print(src)
    print("EXPECTED:")
    print(expected)
    
    log = _run_lexer(src)
    
    if expected == "NO LEXICAL ERROR/S":
        assert log == ""
    else:
        # Presence checks
        for line in expected.splitlines():
            if line.strip():                        # If the result is empty (""), skip that line.
                assert line.strip() in log          # EXPECTED must be in LOG

        # Count helper
        def _count(label: str, expected_text: str, log_text: str):
            # expected count
            # counts how many lines in expected_text contain the substring label.
            exp = sum(1 for line in expected_text.splitlines() if label in line)

            # actual count
            act = log_text.count(label)
            print(f"Expected {exp} {label} errors, got {act}")
            assert act == exp, f"Expected {exp} {label} errors, got {act}"

        # Exact counts for known error types
        _count("Invalid Delimiter", expected, log)
        _count("Invalid Character", expected, log)