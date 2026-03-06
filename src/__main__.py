#!/usr/bin/env python3
"""
CHUNGUS Compiler - Full Pipeline CLI

Compiles and executes CHUNGUS source files.

Usage:
    python -m src <file.chg>
    python -m src samples/program1.chg
    
This runs the complete compilation pipeline:
    1. Lexical Analysis (tokenization)
    2. Syntax Analysis (AST generation)
    3. Semantic Analysis (type checking)
    4. Code Generation (C code)
    5. Compilation & Execution (runtime)
"""

import sys
import subprocess
from pathlib import Path
from src.lexer.dfa_lexer import Lexer
from src.syntax.rd_parser import RDParser
from src.semantic.semantic_analyzer import SemanticAnalyzer
from src.codegen import analyze_codegen


def main():
    """Run the complete CHUNGUS compilation and execution pipeline."""
    
    # Parse arguments
    if len(sys.argv) < 2:
        print("CHUNGUS Compiler - Full Pipeline")
        print("\nUsage: python -m src <file.chg>")
        print("\nExample:")
        print("  python -m src samples/program1.chg")
        print("\nThis will:")
        print("  1. Compile the CHUNGUS source file")
        print("  2. Generate C code in output/")
        print("  3. Execute the program and show results")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    
    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    
    if input_file.suffix != '.chg':
        print(f"Warning: Expected .chg file, got: {input_file}")
        print("Continuing anyway...\n")
    
    # Read source code
    source = input_file.read_text()
    print(f"{'='*60}")
    print(f"CHUNGUS COMPILER - {input_file.name}")
    print(f"{'='*60}\n")
    
    # Phase 1: Lexical Analysis
    print("▸ Phase 1: Lexical Analysis")
    lexer = Lexer(source, debug=False)
    lexer.start()
    
    if lexer.log:
        print("  ✗ LEXICAL ERRORS:")
        print(lexer.log)
        sys.exit(1)
    
    print(f"  ✓ {len(lexer.token_stream)} tokens\n")
    
    # Phase 2: Syntax Analysis
    print("▸ Phase 2: Syntax Analysis")
    parser = RDParser(lexer.token_stream, source, debug=False)
    parse_result = parser.parse()
    
    if parse_result.errors:
        print("  ✗ SYNTAX ERRORS:")
        for error in parse_result.errors:
            print(f"  {error}")
        sys.exit(1)
    
    print(f"  ✓ AST generated\n")
    
    # Phase 3: Semantic Analysis
    print("▸ Phase 3: Semantic Analysis")
    semantic = SemanticAnalyzer(parse_result.tree, source, debug=False)
    semantic_result = semantic.analyze()
    
    if semantic_result.errors:
        print("  ✗ SEMANTIC ERRORS:")
        for error in semantic_result.errors:
            print(f"  {error}")
        sys.exit(1)
    
    print(f"  ✓ Type checking complete\n")
    
    # Phase 4: Code Generation
    print("▸ Phase 4: Code Generation")
    codegen_result = analyze_codegen(
        semantic_result.tree, 
        source, 
        symbol_table=semantic_result.symbol_table,
        debug=False
    )
    
    if not codegen_result.success:
        print("  ✗ CODE GENERATION ERRORS:")
        for error in codegen_result.errors:
            print(f"  {error}")
        sys.exit(1)
    
    # Save generated C code to output/ directory
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    c_file = output_dir / input_file.with_suffix('.c').name
    c_file.write_text(codegen_result.code)
    print(f"  ✓ Generated: {c_file.relative_to(Path.cwd())}\n")
    
    # Phase 5: Compilation & Execution
    print("▸ Phase 5: Compilation & Execution")
    
    # Paths
    exe_file = c_file.with_suffix('')
    runtime_c = Path(__file__).parent / "runtime" / "chungus_runtime.c"
    runtime_h_dir = Path(__file__).parent / "runtime"
    
    # Compile command
    compile_cmd = [
        "gcc", "-Wall", "-Wextra",
        f"-I{runtime_h_dir}",
        "-o", str(exe_file),
        str(c_file),
        str(runtime_c),
        "-lm"
    ]
    
    try:
        result = subprocess.run(compile_cmd, capture_output=True, text=True, check=True)
        print(f"  ✓ Compiled: {exe_file.relative_to(Path.cwd())}\n")
    except subprocess.CalledProcessError as e:
        print("  ✗ COMPILATION FAILED:")
        print(e.stderr)
        sys.exit(1)
    
    # Execute
    print(f"{'='*60}")
    print(f"OUTPUT")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            [f"./{exe_file.name}"],
            capture_output=True,
            text=True,
            check=True,
            cwd=exe_file.parent
        )
        print(result.stdout, end='')
        if result.stderr:
            print(result.stderr, end='', file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print("\n✗ RUNTIME ERROR:")
        print(e.stderr, file=sys.stderr)
        # Clean up executable
        exe_file.unlink(missing_ok=True)
        sys.exit(e.returncode)
    finally:
        # Clean up executable after running (keep C file)
        exe_file.unlink(missing_ok=True)
    
    print(f"\n{'='*60}")
    print("✓ Compilation and execution successful")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
