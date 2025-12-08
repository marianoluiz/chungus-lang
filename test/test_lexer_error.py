import os
import sys
# Add src as root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import csv
import io
import pytest
from src.lexer.dfa_lexer import Lexer  # [`src.lexer.dfa_lexer.Lexer`](src/lexer/dfa_lexer.py)

def _run_lexer(src: str) -> str:
    lx = Lexer(src, debug=True)
    lx.start()
    return lx.log.strip()

def _rows():
    path = "test/error_data.csv"
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        print('reader: ', reader)
        for row in reader:
            print('row: ', row)
            # Some rows contain extra commas in Expected Output; join remaining cells
            if not row:
                continue
            src = row[0]
            expected = ",".join(row[1:]).strip() # if there are other cols, combine in
            # Normalize CRLFs if any
            expected = expected.replace("\r\n", "\n").replace("\r", "\n")
            yield src, expected

@pytest.mark.parametrize("src,expected", list(_rows()))
def test_error_data_csv_cases(src, expected):
    # Some rows contain quoted multi-line samples; normalize newlines
    src = io.StringIO(src).getvalue()
    log = _run_lexer(src)
    if expected == "NO LEXICAL ERROR/S":
        assert log == ""
    else:
        # Presence checks
        for line in expected.splitlines():
            if line.strip():
                assert line.strip() in log          # EXPECTED must be in LOG

        # Count helper
        def _count(label: str, expected_text: str, log_text: str):
            exp = sum(1 for line in expected_text.splitlines() if label in line)
            if exp > 0:
                act = log_text.count(label)
                assert act == exp, f"Expected {exp} {label} errors, got {act}"
    
        # Optional: assert exact count of delimiter errors inferred from expected
        # Exact counts for known error types
        _count("Invalid Delimiter", expected, log)
        _count("Invalid Character", expected, log)
        _count("Unclosed String", expected, log)
        _count("Unclosed Comment", expected, log)