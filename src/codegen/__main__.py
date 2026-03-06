"""
CLI entry point for CHUNGUS code generator.

Generates C code from CHUNGUS source files.

Usage:
    python -m src.codegen [input_file.chg]
    
If no input file is specified, reads from src/codegen/input_codegen.chg

To compile and run the generated C code:
    python -m src.runtime <generated_file.c>
"""

import sys
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
    
    # Save generated C code to output/ directory
    output_dir = Path(__file__).parent.parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / input_file.with_suffix('.c').name
    output_file.write_text(codegen_result.code)
    print(f"✓ Saved to: {output_file}")
    print()
    print("To compile and run:")
    print(f"  python -m src.runtime {output_file}")


if __name__ == "__main__":
    main()
