import os
import sys
import csv
import subprocess
import tempfile
import pytest
from pathlib import Path

# Add project root to path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.lexer.dfa_lexer import Lexer
from src.syntax.rd_parser import RDParser
from src.semantic.semantic_analyzer import SemanticAnalyzer
from src.codegen import analyze_codegen

RUNTIME_C = Path(ROOT) / "src" / "runtime" / "chungus_runtime.c"
RUNTIME_H_DIR = Path(ROOT) / "src" / "runtime"


def _run_program(src: str, stdin_data: str = "") -> str:
    """
    Full pipeline: Lex → Parse → Semantic → Codegen → Compile → Execute.
    Returns the stdout of the final executable, stripped.
    Raises AssertionError with a descriptive message on any pipeline failure.
    """
    # Lex
    lexer = Lexer(src, debug=False)
    lexer.start()
    assert not lexer.log.strip(), f"Lexer error:\n{lexer.log.strip()}"

    # Parse
    parser = RDParser(lexer.token_stream, src, debug=False)
    parse_result = parser.parse()
    assert not parse_result.errors, f"Parser error:\n{'; '.join(parse_result.errors)}"

    # Semantic
    analyzer = SemanticAnalyzer(parse_result.tree, src, debug=False)
    sem_result = analyzer.analyze()
    assert not sem_result.errors, f"Semantic error:\n{chr(10).join(sem_result.errors)}"

    # Codegen
    cg_result = analyze_codegen(
        sem_result.tree,
        src,
        symbol_table=sem_result.symbol_table,
        debug=False,
    )
    assert cg_result.success, f"Codegen error:\n{chr(10).join(cg_result.errors)}"

    # Write generated C to a temp file
    with tempfile.TemporaryDirectory() as tmpdir:
        c_path = Path(tmpdir) / "program.c"
        exe_path = Path(tmpdir) / "program"

        c_path.write_text(cg_result.code)

        # Compile
        compile_cmd = [
            "gcc", "-Wall", "-Wextra",
            f"-I{RUNTIME_H_DIR}",
            "-o", str(exe_path),
            str(c_path),
            str(RUNTIME_C),
            "-lm",
        ]
        compile_result = subprocess.run(
            compile_cmd, capture_output=True, text=True
        )
        assert compile_result.returncode == 0, (
            f"GCC compile error:\n{compile_result.stderr}"
        )

        # Execute
        run_result = subprocess.run(
            [str(exe_path)],
            capture_output=True,
            text=True,
            timeout=10,
            input=stdin_data if stdin_data else None,
        )
        assert run_result.returncode == 0, (
            f"Runtime error (exit {run_result.returncode}):\n{run_result.stderr}"
        )

        return run_result.stdout.strip()


def _rows():
    csv_path = os.path.join(os.path.dirname(__file__), "test_codegen_data.csv")
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header

        for rownum, row in enumerate(reader, start=2):
            if len(row) < 3:
                continue

            src = row[0]
            stdin_data = row[1]
            expected = row[2].strip()

            # Normalize line endings (spreadsheets often insert CRLF)
            src = src.replace("\r\n", "\n").replace("\r", "\n")
            stdin_data = stdin_data.replace("\r\n", "\n").replace("\r", "\n")
            expected = expected.replace("\r\n", "\n").replace("\r", "\n")

            # Unescape literal \n in stdin field (e.g. "3\n7" → "3\n7")
            stdin_data = stdin_data.replace("\\n", "\n")

            # Normalize fullwidth semicolons
            src = src.replace("；", ";")

            if not src.strip():
                continue

            yield pytest.param(rownum, src, stdin_data, expected, id=f"row{rownum}")


@pytest.mark.parametrize("rownum,src,stdin_data,expected", _rows())
def test_codegen_output(rownum, src, stdin_data, expected):
    """
    For each row in test_codegen_data.csv:
      - Compile and run the CHUNGUS source code
      - Assert the program's stdout matches the expected output exactly
    """
    print(f"\n=== CSV row: {rownum} ===")
    print("=== Source Code ===")
    print(src)
    if stdin_data:
        print("=== Stdin ===")
        print(stdin_data)
    print("=== Expected Output ===")
    print(expected)

    actual = _run_program(src, stdin_data)

    print("=== Actual Output ===")
    print(actual)

    assert actual == expected, (
        f"Output mismatch:\n"
        f"  EXPECTED: {expected!r}\n"
        f"  ACTUAL:   {actual!r}"
    )
