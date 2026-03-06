"""
CLI entry point for CHUNGUS code generator.

Usage:
    python -m src.codegen [input_file.chg]
    
If no input file is specified, reads from src/codegen/input_codegen.chg
"""

import sys
import subprocess
from pathlib import Path
from src.lexer.dfa_lexer import Lexer
from src.syntax.rd_parser import RDParser
from src.semantic.semantic_analyzer import SemanticAnalyzer
from src.codegen import analyze_codegen


def main():
    """Run the full compilation pipeline through code generation."""
    
    # Determine input file
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    else:
        input_file = Path(__file__).parent / "input_codegen.chg"
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    # Read source code
    source = input_file.read_text()
    print(f"=== Reading: {input_file.name} ===\n")
    print(source)
    print("\n" + "="*50 + "\n")
    
    # Phase 1: Lexical Analysis
    print("=== PHASE 1: LEXICAL ANALYSIS ===")
    lexer = Lexer(source, debug=False)
    lexer.start()
    
    if lexer.log:
        print("LEXICAL ERRORS:")
        print(lexer.log)
        sys.exit(1)
    
    print(f"✓ Lexical analysis complete: {len(lexer.token_stream)} tokens")
    print()
    
    # Phase 2: Syntax Analysis
    print("=== PHASE 2: SYNTAX ANALYSIS ===")
    parser = RDParser(lexer.token_stream, source, debug=False)
    parse_result = parser.parse()
    
    if parse_result.errors:
        print("SYNTAX ERRORS:")
        for error in parse_result.errors:
            print(error)
        sys.exit(1)
    
    print("✓ Syntax analysis complete: AST generated")
    print()
    
    # Phase 3: Semantic Analysis
    print("=== PHASE 3: SEMANTIC ANALYSIS ===")
    semantic = SemanticAnalyzer(parse_result.tree, source, debug=False)
    semantic_result = semantic.analyze()
    
    if semantic_result.errors:
        print("SEMANTIC ERRORS:")
        for error in semantic_result.errors:
            print(error)
        sys.exit(1)
    
    print("✓ Semantic analysis complete: AST annotated with types")
    print()
    
    # Phase 4: Code Generation
    print("=== PHASE 4: CODE GENERATION ===")
    codegen_result = analyze_codegen(
        semantic_result.tree, 
        source, 
        symbol_table=semantic_result.symbol_table,
        debug=True
    )
    
    if not codegen_result.success:
        print("CODE GENERATION ERRORS:")
        for error in codegen_result.errors:
            print(error)
        sys.exit(1)
    
    print("✓ Code generation complete")
    print()
    print("=== GENERATED CODE ===")
    print(codegen_result.code)
    print()
    
    # Save generated C code
    output_file = input_file.with_suffix('.c')
    output_file.write_text(codegen_result.code)
    print(f"✓ Saved to: {output_file}")
    print()
    
    # Phase 5: Compile and Run
    print("=== PHASE 5: COMPILE AND RUN ===")
    
    # Compile the C code
    exe_file = input_file.with_suffix('')  # Remove extension for executable
    runtime_c = Path(__file__).parent / "chungus_runtime.c"
    runtime_h_dir = Path(__file__).parent

    compile_cmd = [
        "gcc", "-Wall", "-Wextra",
        f"-I{runtime_h_dir}",
        "-o", str(exe_file),
        str(output_file),
        str(runtime_c),
        "-lm"
    ]

    print(f"Compiling: {' '.join(compile_cmd)}")
    try:
        result = subprocess.run(compile_cmd, capture_output=True, text=True, check=True)
        print(f"✓ Compilation successful: {exe_file}")
    except subprocess.CalledProcessError as e:
        print("COMPILATION ERRORS:")
        print(e.stderr)
        sys.exit(1)
    
    # Run the executable
    print(f"\nRunning: {exe_file.name}")
    print()
    try:
        result = subprocess.run([f"./{exe_file.name}"], capture_output=True, text=True, check=True, cwd=exe_file.parent if exe_file.parent.exists() else ".")
        print(result.stdout, end='')
        if result.stderr:
            print(result.stderr, end='')
    except subprocess.CalledProcessError as e:
        print("RUNTIME ERROR:")
        print(e.stderr)
        sys.exit(1)
    print(f"\n✓ Execution complete")


if __name__ == "__main__":
    main()
